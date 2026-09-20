# Přispívání

[🇬🇧 English](CONTRIBUTING.en.md) · **🇨🇿 Česky** · [Projekt](README.cz.md)

Začni issue s popisem pozorovatelného problému nebo integrační potřeby.
Změny drž zaměřené na daný problém. Projekt patří pod organizaci **netiqus**
na GitHubu a používá [licenci MIT](LICENSE).

## Místní kontroly

Nainstaluj Python 3.11+ a uv, pak spusť `./dev.sh check`. Launcher drží virtuální
prostředí, cache, buildy a reporty mimo zdroj. Běžné testy jsou offline a nepotřebují
API klíč. `./dev.sh demo` spouští příklad se simulovanými odpověďmi.
Cesty výstupů popisuje [provozní dokumentace](docs/operations.cz.md).

Kód, identifikátory, komentáře, chyby a výchozí texty UI jsou anglicky. Veřejné MD
příručky mají protějšky `.en.md` / `.cz.md` se vzájemnými odkazy. Výchozí soubory
README/CHANGELOG/CONTRIBUTING odpovídají anglické verzi. Česká data v jazykových
testech a českých překladech jsou záměrná.

Zachovej výslovné pass/fail/review, časové limity, absenci automatických opakování
a přesné vykazování nákladů. Ke změně chování přidej cílený regresní test. Při změně
politiky verzuj kritéria a zvlášť ověř reprezentativní příklady. Simulované testy
nevydávej za přesnost živého modelu.

## Pull requesty

Popiš problém, výsledné chování a provedené kontroly. Klíče, skutečné články,
běhové reporty a interní pracovní poznámky nepatří do změn. Používej syntetické
reprodukce. Tokeny nepatří do logů ani textu issue.

Veřejné API a [integrační instrukce agentům](docs/agent-integration.cz.md) jsou
součástí kontraktu; při změně chování je aktualizuj. Primární jazyk review je
angličtina. Windows zůstává neověřený; testovanou platformou je Linux.
