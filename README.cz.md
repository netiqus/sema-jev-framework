# Sema Jev Framework

**Rozhodovací brány podle významu vstupu pro Python.**

[![CI](https://github.com/netiqus/sema-jev-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/netiqus/sema-jev-framework/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Alpha](https://img.shields.io/badge/status-experimental_alpha-orange)](docs/limitations.cz.md)

[🇬🇧 English](README.en.md) · **🇨🇿 Česky**

Sema Jev je malá nezávislá Python knihovna pro rozhodovací brány založené na
významu vstupu v existujících aplikacích. [Jev od TypeSafe](https://typesafe.ai/)
posoudí podklady; Sema Jev zkontroluje odpověď, použije verzovaná pravidla
a vrátí explicitní `pass`, `fail` nebo `review` spolu s údaji o tokenech
a nákladech. Další akci řídí tvoje aplikace.

```python
from sema_jev import Gate, Status

gate = Gate("Does `message` explicitly request a refund?")
result = gate.check({"message": "Please refund the duplicate payment."})

if result.status == Status.PASS:
    print("Send to the refund queue")
elif result.status == Status.FAIL:
    print("Keep in general support")
else:
    print("Request more evidence or a human review")
```

**0.2.0a3 · experimentální alfa · Python 3.11+ · bez běhových závislostí**

Projekt organizace [netiqus](https://github.com/netiqus) pod licencí MIT.
Jde o nezávislý projekt bez příslušnosti k TypeSafe AI či schválení tvůrci Jev.
Ověřeno na Linuxu s Pythonem 3.11–3.14. Windows zatím ověřený není.

[Rychlý start](#rychlý-start) · [Ukázka článků](#vyzkoušej-editor-článků) · [API](docs/api.cz.md) · [Integrace agenty](docs/agent-integration.cz.md) · [Omezení](docs/limitations.cz.md)

## Proč tento projekt

Sema Jev vzniklo z praktických experimentů v netiqus. Sdílí jeden pohled na to,
jak významová rozhodnutí snadno vyzkoušet, prozkoumat a použít v běžné Python
aplikaci. Knihovna, příklady a průvodci nabízejí nápady, které si můžeš přizpůsobit
vlastní práci. Smyslem projektu je pomoci někomu pochopit možnosti nebo vyřešit
praktický problém.

## Kam se hodí

| Aplikace potřebuje… | Model může posoudit… | V aplikaci zůstává… |
|---|---|---|
| Zařadit zprávu | Zda odesílatel skutečně žádá vrácení peněz | Oprávnění účtu a provedení platby |
| Porovnat články | Zda autor tvrzení podporuje, nebo jen cituje | Definice znaků a následné zařazení |
| Zkontrolovat vygenerovaný návrh | Zda řeší požadovanou změnu | Kompilátor, testy a schvalovací pravidla |
| Doplnit neúplný výstup | Které deklarované požadavky nejsou splněné | Opravná funkce s omezeným počtem pokusů |

Na přesná fakta používej běžné kontroly v Pythonu. Významová kontrola se hodí pro
úsudek o dodaném textu či podkladech. Úspěšné posouzení je podklad pro pracovní
postup, nikoli důkaz správnosti nebo oprávnění provést akci.

Sema Jev se zaměřuje na samostatné začlenění do Python aplikace: explicitní
výsledky, verzovaná pravidla, pevné kontroly a účet za dotaz.
[Metodický průvodce](docs/methodology.cz.md#související-přístupy) jej zasazuje
do kontextu sémantických operátorů a integrací ve větších frameworcích.

## Rychlý start

Balíček **zatím není na PyPI**. Instaluj z klonu repozitáře nebo sestaveného wheelu.
Sestavený wheel najdeš v [GitHub Releases](https://github.com/netiqus/sema-jev-framework/releases).

```bash
git clone https://github.com/netiqus/sema-jev-framework.git
cd sema-jev-framework
python3 -m venv ../sema-jev-env
source ../sema-jev-env/bin/activate
python -m pip install .
```

Příkazy jsou pro linuxový shell a drží virtuální prostředí mimo zdroj.
V existující aplikaci instaluj do jejího prostředí. Wheel lze nainstalovat přes
`python -m pip install /path/to/package.whl`.

Pro první živý dotaz ulož úvodní Python příklad jako `first_gate.py` vedle složky
repozitáře. `OPENROUTER_API_KEY` předej správcem tajemství nebo prostředím aplikace.
Při ručním testu tento skrytý vstup zabrání uložení klíče do historie shellu:

```bash
python - <<'PYCODE'
import os
import runpy
from getpass import getpass

os.environ["OPENROUTER_API_KEY"] = getpass("OpenRouter API key: ")
runpy.run_path("../first_gate.py", run_name="__main__")
PYCODE
```

Příklad odešle jedno **placené** posouzení do OpenRouter/Jev. Načtení ceníku je
samostatné; import balíčku nic nevolá. Dotazy se automaticky neopakují.
Knihovna nevyhledává `.env` soubory ani neukládá klíče.
Další možnosti včetně explicitního předání klíče popisuje [autentizace](docs/credentials.cz.md).

Bez klíče začni [offline příkladem](examples/offline.py), který používá výslovně
označené simulované odpovědi:

```bash
python examples/offline.py
```

Ověřuje průchod integrací, nikoli porozumění modelu.

## Tři výsledky, výslovné zpracování

| Výsledek | Význam | Typický další krok |
|---|---|---|
| `pass` | Všechny požadované kontroly prošly nastavenými pravidly | Pokračovat |
| `fail` | Alespoň jedna kontrola doložila nesplněný požadavek | Zařadit jinam nebo opravit |
| `review` | Žádná kontrola nedoložila selhání, ale nestačí podklady, jistota nebo služba | Doplnit podklady nebo prověřit |

Doložené selhání má přednost před nejistotou jiné kontroly. Pro jednotlivé znaky
použij `result.checks`. `result.error` rozlišuje chybu poskytovatele.
`if result:` záměrně vyvolá chybu; použij `.passed` nebo `.status`.

Výchozí podpora odpovědi `0.85` a confidence `0.60` jsou počáteční nastavení,
**nikoli změřená přesnost**. Model se může mýlit i s vysokou jistotou. O použitelnosti
kontroly ve tvé oblasti rozhodují otázky, příklady a ověřovací data.

## Vyzkoušej editor článků

Dva delší fiktivní články popisují stejnou diplomatickou návštěvu s odlišným
názorovým rámováním. Editor ukazuje přesné otázky a definice odpovědí, aby bylo
zřejmé, co experiment skutečně měří.

- Výchozí články, kritéria i rozhraní jsou anglicky; české protějšky jsou přibalené.
- Uprav oba texty, přidej kritéria, změň prahy a prohlédni úplný dotaz.
- Nejdřív náhled bez API, potom výslovně spusť nejvýše dvě placená posouzení.
- Porovnej jednotlivé znaky, nejistoty, vstupní/výstupní tokeny a náklady.
- Exportuj verzovanou politiku a použij ji přes `Gate(Policy.load(path))`.

S nainstalovaným Pythonem a [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
./dev.sh news-lab             # local server; no model call on startup
./dev.sh news --lang en       # HTML preview without API calls
./dev.sh news-lab --lang cz   # Czech interface, articles and default criteria
```

Editor otevři na `http://127.0.0.1:8770/`. Launcher vypíše oddělený runtime adresář;
volitelné klíče patří do jeho `config/runtime.env`.
Viz [průvodce ukázkou](examples/news/README.cz.md) a
[jak zvolit kritéria](docs/article-methodology.cz.md).
Ukázka měří zvolené textové znaky, nikoli správnost politického názoru.

## Od jedné podmínky dál

Stejné rozhraní podporuje verzované JSON politiky, více kritérií, pevné kontroly
ze skutečných nástrojů, async volání, omezenou opravnou smyčku a JSON CLI.

```python
from sema_jev import Gate, Policy

gate = Gate(Policy.load("policy.json"))
result = gate.check({"article": article_text})
print(result.cost.input_tokens, result.cost.output_tokens)
print(result.cost.billed_usd)  # None means unknown, not free.
```

Viz [integrační příklady](examples/integrations.py), [API](docs/api.cz.md)
a [instrukce pro agenty](docs/agent-integration.cz.md).
Instalace zaregistruje `sema-jev` v aktivním prostředí; systémový PATH se neupravuje.
`python -m sema_jev.cli` přijímá stejné argumenty.

## Ověřování a vývoj

```bash
./dev.sh check    # lint, docs, types, offline tests, build and clean wheel install
./dev.sh demo     # explicitly simulated answers; no key required
```

Zdroj a runtime jsou oddělené. Pro klon v `~/dev` vznikají generované soubory na
stejné relativní cestě v `~/dev-out`; jinde v sousední složce `<checkout>-out`.
Cestu lze změnit přes `SEMA_OUT_DIR`.

CI ověřuje kontrakt knihovny bez skutečných klíčů. Přes OpenRouter proběhly také
živé kontroly; přímý adaptér TypeSafe má offline testy kontraktu, ale není živě
ověřený. Syntetické příklady nejsou nezávislým benchmarkem.
Viz [meze ověření](docs/limitations.cz.md) a [evaluace](evals/README.cz.md).

## Dokumentace

| Začni zde | Pokračuj |
|---|---|
| [API a CLI](docs/api.cz.md) | [Architektura](docs/architecture.cz.md) |
| [API klíče](docs/credentials.cz.md) | [Provoz a vydání](docs/operations.cz.md) |
| [Metodika politik](docs/methodology.cz.md) | [Metodika článků](docs/article-methodology.cz.md) |
| [Integrace agenty](docs/agent-integration.cz.md) | [Přispívání](CONTRIBUTING.cz.md) |
| [Omezení](docs/limitations.cz.md) | [Changelog](CHANGELOG.cz.md) |

Angličtina je primární jazyk veřejného projektu, kódu a komentářů. Česká dokumentace
je dostupná přes jazykové odkazy. Veřejné příklady obsahují pouze fiktivní data.
[MIT licence](LICENSE) pokrývá kód; model vyžaduje vlastní účet u poskytovatele.

## Zapoj se do dalšího vývoje

Pokud tě projekt zaujal nebo ti pomohl při práci, můžeš se podílet na jeho
vylepšování. Poděl se o vlastní využití, upozorni na nečekaný výsledek, vylepši
ukázku nebo přispěj kódem — i drobný příspěvek má smysl.

[Otevři issue](https://github.com/netiqus/sema-jev-framework/issues)
nebo se podívej do [průvodce přispíváním](CONTRIBUTING.cz.md).
