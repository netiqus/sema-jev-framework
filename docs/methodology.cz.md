# Metodika tvorby a ověření politik

[🇬🇧 English](methodology.en.md) · **🇨🇿 Česky**
## Co je hotové a co je návrh

Knihovna poskytuje mechaniku pro aplikování politik. Přibalené otázky jsou
**ilustrační experimentální příklady**, nikoli ověřená univerzální metodika.
Výchozí prahy nejsou certifikát přesnosti. Ověření infrastruktury a ověření úsudku
modelu jsou dvě oddělené činnosti.

## Postup od cíle k otázkám

1. Napiš rozhodnutí, které aplikace potřebuje, a důsledky falešného schválení i zamítnutí.
2. Najdi zavedenou metodiku pro danou doménu; zaznamenej zdroj, verzi a hranice platnosti.
3. Každé její použitelné kritérium převeď na jednu pozorovatelnou otázku a uveď konkrétní
   pole podkladů. Původní význam musí zůstat zachovaný, nic tiše nedoplňuj.
4. Počty, data, oprávnění a výsledky nástrojů vyhodnoť deterministicky.
5. Popiš případy „splněno“, „nesplněno“ a „nedostatek důkazů“.
6. Zmraz formulace i prahy pro jednu verzi politiky a vyhodnoť nezávislou sadu.
7. Změnu modelu, formulace nebo prahu znovu ověř; používej obsahový otisk.

Příklady vhodných zdrojů k dalšímu výběru: recenzní checklist konkrétního projektu,
požadavky příslušného standardu, anotační příručka výzkumného datasetu. Znalost
názvu metodiky ještě neznamená její správné převedení. V této alfě žádný takový
standard neprohlašujeme za implementovaný.

## Praktické kontrolní případy

- Téma faktur a urgence jsou různé otázky. Kritéria urgence musí pojmenovat, co se
  považuje za naléhavost; nelze ji odvodit jen z vysoké jistoty tématu.
- Pravděpodobnost ano u binární otázky není confidence skórovací otázky.
- Změna prahu nenahradí změnu špatně zvolené otázky. Důvody review musí být viditelné.
- Autorův postoj a citovaný výrok je nutné rozlišit přímo v zadání.
- Testy článků potřebují A/B, B/A, A/A, parafrázi, negaci, změnu citace a jazykové varianty.
- Vyhodnocení opírej o konkrétní vstup, výstup a identitu dotazu. Jednotlivý
  úspěšný příklad není benchmark ani důkaz univerzální spolehlivosti.

## Měření kvality

Odděl ladicí a ověřovací sadu. Po zhlédnutí chyby a přizpůsobení otázky už daný
příklad není nezávislým ověřením. Kontroluj i náhodný vzorek vysoce jistých výsledků.

TypeSafe odvozuje `confidence` z tvaru rozdělení odpovědí. Není to nezávislé
ověření ani naměřená pravděpodobnost správnosti. Rozlišuj podporu možností,
confidence a skutečnou správnost. Práh `0.9` nedokládá 90% přesnost a nepřenáší
se automaticky mezi typy otázek, jazyky, modely nebo implementacemi poskytovatelů.

Laď na vývojových datech; na nedotčené ověřovací sadě vykazuj chyby mezi
automaticky přijatými případy společně s pokrytím. Část stejných dotazů opakuj
a testuj změny formulace a pořadí podkladů se zachovaným významem. Stejná fakta
sama nezaručují stabilní rozhodnutí.

Report má ukázat počet příkladů, pokrytí automatickým rozhodnutím, falešné průchody,
falešná odmítnutí, review a chyby API. U nákladů vykazuj známý součet i počet dotazů
s neznámou cenou. Procenta na miniaturním vzorku neprezentuj jako produkční kvalitu.

`evals/` obsahuje malou syntetickou sadu a spouštěč. Je to kouřový test postupu;
rozšíření o nezávislé reálné příklady je podmínkou provozního nasazení.

## Související přístupy

Významové podmínky navazují na existující práci.
[LOTUS](https://github.com/lotus-data/lotus) nabízí sémantické operátory pro hromadné
zpracování dat. [LangChain](https://www.langchain.com/blog/building-a-harness-with-jev)
má vlastní TypeSafe integraci a experimentální agentní middleware. Aplikace, které
tyto frameworky již používají, by měly posoudit jejich nativní možnosti.
Sema Jev se soustředí na malé samostatné rozhraní bran pro existující Python kód.

[jev-align](https://github.com/sutro-sh/jev-align) zkoumá lidskou zpětnou vazbu
a úpravu definic pomocí GEPA. Sema Jev zatím provádí dodané politiky; netrénuje
modely, nedopočítává kalibrační parametry ani automaticky neladí otázky. Jeho
syntetický evaluační spouštěč ověřuje postup, nikoli přesnost v konkrétní doméně.

## Primární zdroje

- [Primitives](https://docs.typesafe.ai/primitives) — otázky, nezávislé odpovědi a skládání.
- [Confidence](https://docs.typesafe.ai/confidence) — rozdíl pravděpodobnosti a confidence.
- [Jev 1.13: známá omezení](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
- [API](https://docs.typesafe.ai/api).

- [Studie stability reprezentace](https://research.prose.md/articles/representation-robustness/)
  popisuje citlivost na uspořádání podkladů v kontrolovaných grafových úlohách;
  nejde o benchmark naší knihovny ani článkové ukázky.

Ověřeno proti dokumentaci dostupné 20. 9. 2026; API a modely se mohou změnit.

[Ukázka článků](../examples/news/README.cz.md) ilustruje návrh znaků a rozlišení citací. Její autorský klíč není nezávislý benchmark.

[Praktický průvodce a editor článkových politik](article-methodology.cz.md) propojuje
tento postup s editací otázek, náhledem celých dotazů a exportem politiky.
