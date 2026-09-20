# Sema Jev Framework 0.2.0a3

[🇬🇧 English](release-notes.en.md) · **🇨🇿 Česky**

První veřejná experimentální alfa projektu pod **netiqus**. Vydání balí významové
kontroly, praktický editor článků a primárně anglický integrační návod pod licencí
MIT. Python 3.11+, bez běhových závislostí. Na PyPI zatím nepublikováno.

## Obsah

- Typované pass/fail/review, verzované politiky, pevné kontroly, async volání,
  omezená opravná smyčka, JSON CLI, auditní metadata a účtování.
- Lokální editor článků a kritérií, bezplatný náhled dotazů, explicitní placené běhy,
  neměnné výsledky a export politiky. Fiktivní články a předvolby v EN/CZ.
- Výchozí anglické README, evaluační a přispěvatelské příručky s českými protějšky.
- Veřejné integrační instrukce pro agenty bez nutnosti znát přenosový formát Jev.
- Export povolených souborů s Linux CI a ručními workflow pro draft a evaluaci.
  Pipeline ověřuje čistý export i instalovaný wheel.

## Rozsah ověření

Offline CI ověřuje Linux Python 3.11–3.14. Živé kontroly proběhly přes OpenRouter.
Přímý TypeSafe adaptér má offline testy kontraktu, ale není ověřen živě.
Windows zůstává neověřený. Výchozí prahy a politiky ukázek nejsou kalibrované
produkční metodiky; viz [omezení](limitations.cz.md).

Instaluj ze zdroje nebo odpovídajícího wheelu podle [README](../README.cz.md).
Vydávací workflow připravuje draft ke kontrole správcem. Jeho zveřejnění je
samostatný krok; workflow nepublikuje na PyPI.
