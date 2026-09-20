# Provoz, CI/CD a vydání

[🇬🇧 English](operations.en.md) · **🇨🇿 Česky**
## Zdroj versus běh

`~/dev/sema-jev-framework` obsahuje zdroj, příklady a dokumentaci.
`~/dev-out/sema-jev-framework` obsahuje spustitelnou kopii, `.venv`, `cache/`,
`config/runtime.env` a `artifacts/`. `dev.sh` před každým během zkontroluje zdroj a
obnoví v runtime jen spravované zdrojové adresáře. `config/` a `artifacts/` zachová.
Vlastní data nedávej do runtime `src/`, `tests/` ani jiných synchronizovaných adresářů.

Proměnná `SEMA_OUT_DIR` může změnit runtime; nesmí ukazovat dovnitř zdroje ani do
`~/dev/`. Při klonu mimo `~/dev` je default sousední adresář `<název>-out`.
`uv.lock` je verzovaný, závislosti v CI se instalují přes `--locked`.

Ostrý konfigurační soubor je volitelný a patří pouze do runtime:

```bash
cp examples/runtime.env.example ~/dev-out/sema-jev-framework/config/runtime.env
chmod 600 ~/dev-out/sema-jev-framework/config/runtime.env
```

Vyplň ho lokálně editorem. Nikdy nevkládej klíč do argumentu shellu, příkladu nebo commitu.
Samotná instalovaná knihovna tento soubor nenačítá; dělá to jen vývojový launcher.

## Kontrolní pipeline

1. Kontrola, že zdroj neobsahuje runtime artefakty a známé vzory credentials.
2. Ruff lint/formát, kontrola místních odkazů a jazykových dvojic, mypy veřejných typů.
3. Offline testy: význam rozhodnutí, hranice prahů, lokální HTTP chyby, účtování a smyčka.
4. Build wheel a sdist, kontrola obsahu archivů, `twine check`.
5. Instalace wheelu v prázdném prostředí a import mimo repozitář.
6. Povinné CI Linux Python 3.11–3.14 a kompletní ověření z čistého veřejného exportu.
   Windows není součástí ověřené platformy alfy.

Kontrola vzorů není univerzální detektor tajemství. Základem je nikdy je do zdroje
nevkládat a publikovat jen povolené soubory. PR workflow nemá API klíče a nepoužívá
`pull_request_target`. Placený live test se spouští odděleně a výslovně.

## CD

Ručně spuštěné workflow `release` přijme tag `vX.Y.Z` nebo předběžné verze jako `v0.2.0a1`, ověří soulad tagu s verzí
balíčku, spustí stejné kontroly a připraví **koncept předběžného vydání** se sestavenými archivy.
Tag musí předem existovat a při ručním spuštění vyber přesně tento tag jako ref. Workflow nikdy nepublikuje na PyPI ani nemění viditelnost repa.
Privátní release lze využít k instalaci do vlastních aplikací bez veřejného indexu.

Kód používá [licenci MIT](../LICENSE), která je přibalena do wheelu, sdist i čistého
exportu. Zveřejnění repozitáře, publikace na PyPI a případný trusted publisher
zůstávají samostatnými rozhodnutími před vydáním.

## Čistý export zdroje

Wheel obsahuje Python balíček; sdist veřejný zdroj, příklady a dokumentaci.
`scripts/check_artifacts.py` kontroluje jejich obsah. Z úplného klonu vytvoř
nový zdrojový snapshot:

```bash
./dev.sh export --export-dir /path/outside/source/public-source
```

Exportér kontroluje čistotu zdroje, odmítá symlinky a nepovolené soubory.
Kopíruje pouze veřejné adresáře, vyjmenované kořenové soubory a workflow `ci.yml`,
`release.yml` a `live-evaluation.yml`. Vynechá interní podklady a historii Gitu.
Nic nepublikuje a nepřepisuje existující export. CI ověřuje kompletní projekt
přímo z tohoto samostatného snapshotu.

Interní vývojová historie zůstává soukromá. Při zveřejnění interního projektu
založ novou historii z ověřeného exportu. [Integrační instrukce agentům](agent-integration.cz.md)
jsou veřejná dokumentace pro uživatele knihovny.

## Volitelné živé vyhodnocení

`./dev.sh evaluate` provede až 12 placených syntetických kontrol a uloží report do
runtime. CI varianta `Optional paid evaluation` se spouští ručně pouze z main,
s výslovně zaškrtnutou volbou nákladů a klíčem `OPENROUTER_API_KEY` v prostředí
GitHub Actions `live-evaluation`. Klíč se nastavuje pouze v UI/secret store, nikdy v YAML.
Provozní selhání zastaví sérii. Běžný push ani pull request živé API nevolá.

## Ukázka zpráv a jazykové verze

`./dev.sh news --lang en` připraví náhled bez API. `./dev.sh news-live --lang en`
provede nejvýše dva placené dotazy. Volba `cz` posuzuje přímo české texty.
Viz [průvodce ukázkou](../examples/news/README.cz.md).

Kořenové README zobrazuje přímo anglickou příručku. Angličtina je primární, čeština druhý jazyk. Veřejné příručky a poznámky k vydání mají
protějšky `.cz.md` / `.en.md`, články `.cz.txt` / `.en.txt`. Každý průvodce odkazuje
na druhý jazyk. Původní nesufixované odkazy dokumentace zůstávají malými rozcestníky s angličtinou na prvním místě.
`.cz` je konvence názvů souborů; HTML správně používá jazykový kód `cs`.
Kód, identifikátory, komentáře a výchozí UI jsou anglicky. České předvolby mají
české otázky; změna jazyka rozhraní nepřekládá vlastní kritéria.

Kontrakt autentizace popisuje [předání API klíče](credentials.cz.md).

## Lokální editor politik

`./dev.sh news-lab --lang cz --port 8770` spustí HTTP editor ze standardní knihovny
pouze na `127.0.0.1`. Klíč bere ze stejného prostředí/configu launcheru; po změně
klíče jej restartuj. Prohlížeč klíč nedostává. Server přijímá jen vlastní Host a Origin
s tokenem formuláře; zpřístupňuje vyjmenované reporty, nikoli runtime adresář nebo
config. Model se nevolá automaticky a placené POST dotazy se automaticky neopakují.

Běhy jsou v `artifacts/news-lab/runs/<id>/`. Před dotazem se uloží značka odeslání;
opakování stejného dokončeného zadání vrátí jeho výsledek. Přerušené zadání se
automaticky neopakuje. Výslovně nové odeslání může být znovu účtováno. Každý běh ukládá
`policy.json`, `questions.json`, `report.json`, kopie článků a dvojjazyčné HTML.
Samotný výsledkový report API nevolá. Editor importuje/exportuje politiku znaků pro
`Gate` (v této ukázce 1–10 třímožnostních otázek). Viz [průvodce metodikou](article-methodology.cz.md).
