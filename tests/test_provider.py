import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from sema_jev import Gate, OpenRouter, TypeSafe
from sema_jev.wire import JsonTransport, ProviderError


class RecordingTransport(JsonTransport):
    def __init__(self):
        self.calls = []

    def request(self, url, *, headers, payload, timeout):
        self.calls.append((url, headers, payload))
        if payload is None:
            return {"data": {"pricing": {"prompt": "0.000000042", "completion": "0"}}}
        return {
            "model": payload["model"],
            "answers": {
                "requirement": {
                    "type": "choice",
                    "choice": "supported",
                    "confidence": 0.99,
                    "probabilities": {
                        "supported": 0.99,
                        "contradicted": 0.005,
                        "insufficient": 0.005,
                    },
                }
            },
            "usage": {"input_tokens": 1000, "output_tokens": 10, "cost": 0.000042},
        }


def test_contract_pricing_cache_and_key_redaction():
    transport = RecordingTransport()
    provider = OpenRouter(api_key="unit-test-secret", transport=transport)
    g = Gate("Met?", provider=provider)
    first, second = g.check("x"), g.check("y")
    assert first.passed and second.passed and len(transport.calls) == 3
    url, headers, payload = transport.calls[0]
    assert url.endswith("/api/alpha/decisions")
    assert payload["state"] == "x" and "questions" in payload
    assert headers["Authorization"] == "Bearer unit-test-secret"
    assert "unit-test-secret" not in repr(provider) + json.dumps(first.to_dict())
    assert transport.calls[1][1] == {}  # Public pricing must not carry credentials.
    assert first.cost.input_usd == first.cost.billed_usd


def test_direct_adapter_does_not_invent_price():
    transport = RecordingTransport()
    g = Gate("Met?", provider=TypeSafe(api_key="fake", transport=transport))
    d = g.check("x")
    assert d.passed and len(transport.calls) == 1
    assert transport.calls[0][0] == "https://api.typesafe.ai/v1/systemone"
    assert d.cost.input_usd is None


def test_missing_key_no_network(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    provider = OpenRouter(transport=RecordingTransport())
    assert Gate("Met?", provider=provider).check("x").error == "missing_api_key"
    assert provider._transport.calls == []


def test_price_failure_retains_decision_and_bill():
    class Unavailable(RecordingTransport):
        def request(self, url, **kwargs):
            if kwargs["payload"] is None:
                raise ProviderError("timeout")
            return super().request(url, **kwargs)

    d = Gate("Met?", provider=OpenRouter(api_key="fake", transport=Unavailable())).check("x")
    assert d.passed and d.cost.billed_usd is not None and d.cost.input_usd is None
    assert d.cost.price_error == "pricing_unavailable"


@pytest.fixture
def http_server():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            calls.append(self.path)
            status = int(self.path[1:]) if self.path[1:].isdigit() else 200
            self.send_response(status)
            if status == 302:
                self.send_header("Location", "/credential-leak")
            self.end_headers()
            if self.path == "/invalid":
                self.wfile.write(b'{"x":NaN}')
            elif self.path == "/large":
                self.wfile.write(b"x" * 2_000_001)
            else:
                self.wfile.write(b'{"ok":true}')

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", calls
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize(
    "path,code",
    [
        ("401", "authentication"),
        ("403", "permission"),
        ("429", "rate_limit"),
        ("529", "overloaded"),
        ("500", "http_error"),
        ("302", "http_error"),
        ("invalid", "invalid_response"),
        ("large", "response_too_large"),
    ],
)
def test_transport_faults_no_retries_or_redirects(http_server, path, code):
    base, calls = http_server
    with pytest.raises(ProviderError) as caught:
        JsonTransport().request(
            base + "/" + path, headers={"Authorization": "Bearer fake"}, payload={}, timeout=2
        )
    assert caught.value.code == code and len(calls) == 1


def test_real_transport_roundtrip(http_server):
    base, calls = http_server
    assert JsonTransport().request(base + "/ok", headers={}, payload={"state": "x"}, timeout=2) == {
        "ok": True
    }


@pytest.mark.parametrize(
    "failure", [ConnectionResetError("private detail"), OSError("private detail")]
)
def test_socket_failures_are_sanitized(monkeypatch, failure):
    import urllib.request

    class BrokenOpener:
        def open(self, *args, **kwargs):
            raise failure

    monkeypatch.setattr(urllib.request, "build_opener", lambda *a: BrokenOpener())
    with pytest.raises(ProviderError, match="^network$"):
        JsonTransport().request("http://127.0.0.1/test", headers={}, payload={}, timeout=1)
