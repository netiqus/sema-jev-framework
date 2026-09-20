# API keys and application integration

**🇬🇧 English** · [🇨🇿 Česky](credentials.cz.md)

The credential interface is defined by the library. The host application chooses
where to obtain the key: an environment variable, a secret manager, an OS keyring
or its own settings. No particular secret store or user-interface framework is required.

## The installed library

| Provider | Explicit parameter | Environment fallback |
|---|---|---|
| `OpenRouter` | `OpenRouter(api_key=key)` | `OPENROUTER_API_KEY` |
| `TypeSafe` | `TypeSafe(api_key=key)` | `TYPESAFE_API_KEY` |

Precedence is **explicit `api_key` → environment**. Only `api_key=None` selects
the environment fallback. An explicitly empty key is an error, not a request
to use another credential. Surrounding whitespace is stripped. The environment
is read at request time, not import time or provider construction.

For an application that already manages credentials:

```python
from sema_jev import Gate, OpenRouter


def make_gate(runtime_key: str) -> Gate:
    return Gate(
        "Does `message` explicitly request a refund?",
        provider=OpenRouter(api_key=runtime_key),
    )
```

The application calls `make_gate` with a key obtained from its chosen source.
For separate user credentials, create the corresponding provider with an explicit
key; do not swap a process-wide environment variable between concurrent requests.

The library displays no credential dialog, discovers no `.env` files, accesses
no keyring and writes no key to disk. A supplied key stays on the provider object
in memory and is sent in the authentication header to that provider. Public
OpenRouter price queries do not carry it. It is not part of policy JSON, normal
decision JSON, the built-in audit or the example HTML report.

Missing or empty credentials produce `review` with `error="missing_api_key"`
through `Gate.check`, before any network request. The news demo performs an earlier
missing-key check and exits with an explanation. It never substitutes fake answers.
The news HTML report is static: it contains neither a key field nor a live API client.

## This repository's development launcher

`dev.sh` offers an additional convenience outside the installed library:

1. It inherits the process environment.
2. It optionally reads `config/runtime.env` **in the runtime directory**.
3. Values from that file fill only missing environment variables; an existing
   environment variable wins, even if its value is empty.
4. It starts the example with that environment. Only the two provider key names
   above are accepted in the runtime file.

With the standard layout, the file is
`~/dev-out/sema-jev-framework/config/runtime.env`. Create it from
[`runtime.env.example`](../examples/runtime.env.example) and use permissions
`0600` on Linux. Fill it locally in an editor. Keep the populated file out of
`dev`, source control and cloud-synchronised source folders. Do not put a real key
in an example or a command-line argument.

Running a Python example directly bypasses this file loader: provide the process
environment yourself. CI live evaluation obtains its key from GitHub Actions
secrets; normal CI uses offline fixtures and requires no real key.

## What application authors decide

They choose credential acquisition, account-specific access, persistence and
rotation. The framework defines how a provider receives a key and what happens
when it is absent. MIT licensing of this code does not provide an API credential;
the application's provider account is still needed for live requests.

[API](api.en.md) · [Operations](operations.en.md) · [Project](../README.md)
