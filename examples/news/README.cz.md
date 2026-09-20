# 📰 Stejná návštěva, dvě podání

[🇬🇧 English](README.en.md) · **🇨🇿 Česky** · [← Projekt](../../README.cz.md)

Vzorový příklad používá Sema Jev k rozpoznávání způsobu, jakým autor píše o události.
Čtenář si může vybrat argument, který mu připadá přesvědčivý. Aplikace sleduje
konkrétní znaky textu a podle potřeby jej zařadí do fronty komentářů nebo k prověření.

## Texty připravené ke čtení

| Článek | Anglicky | Česky |
|---|---|---|
| A | [article_a.en.txt](article_a.en.txt) | [article_a.cz.txt](article_a.cz.txt) |
| B | [article_b.en.txt](article_b.en.txt) | [article_b.cz.txt](article_b.cz.txt) |

Lidé, země, média i událost jsou smyšlené. V obou verzích přijme premiérka Mara Vesk
prezidenta Orena Valeka v Eastmere. Jednání trvá 110 minut, má navázat horká linka
a technické rozhovory, posoudí se obilní koridor. Příměří ani energetická smlouva
nevzniknou. Stejné jsou i počty zadržených novinářů, demonstrantů a zdražení energií.
Liší se výběr důrazů, interpretace a vlastní hodnocení autora.

Oba texty jsou delší **komentáře**, oba obsahují argument a oba připouštějí nepohodlná
fakta. Nejde o soutěž, který názor je správný. České protějšky zachovávají jejich
faktický základ a rétorické prostředky; nejsou automaticky ověřeným překladem pro benchmark.

## Prohlédni a uprav hodnoticí zadání

[Praktický průvodce metodikou](../../docs/article-methodology.cz.md) vysvětluje,
proč jsme vybrali jednotlivá kritéria, co se dá přenést na jiné žánry a jak
z neurčité otázky na zaujatost udělat pozorovatelný znak.

```bash
./dev.sh news-lab --lang cz  # local editor; opening it makes no paid request
```

Editor umožňuje nahradit oba články, přidat či odebrat otázky, definovat všechny tři
odpovědi, měnit prahy, zdarma si prohlédnout úplné dotazy a spustit nejvýše dvě
placená posouzení. Nabízí původní předvolbu návštěvy i experimentální obecnou rétoriku.
Politiku exportuj pro `Gate(Policy.load(...))`; importuješ ji vložením jejího JSON.
Každý výsledek uchovává přesnou politiku a otázky dotazu. Zařazování je samostatná
volba aplikace. Poslední dokončené běhy odkazují na uložené výsledky a lze je znovu
otevřít pro úpravu.

Český editor začíná českými otázkami i definicemi odpovědí. Obě předvolby mají
varianty `.en.json` a `.cz.json`; české mají verzi `1-cz`. Pro načtení jiné varianty
vyber **Jazyk otázek načítané předvolby** a stiskni příslušnou předvolbu.
Přepínač rozhraní ani načtení článků vlastní otázky nepřekládá. Starý report
vždy uchovává skutečně použité znění; překlad kritérií vyžaduje nové posouzení.

## Spuštění

Z kořene repozitáře:

```bash
./dev.sh news --lang en       # English article preview; no API calls
./dev.sh news --lang cz       # Czech article preview; no API calls
./dev.sh news-live --lang en  # at most two billable requests; requires a key
./dev.sh news-live --lang cz  # independently assess the Czech originals
```

Klíč patří pouze do prostředí nebo runtime `config/runtime.env`, viz
[provozní návod](../../docs/operations.cz.md). Launcher vše spouští v `dev-out`.
Vznikne `artifacts/news-en-preview/` nebo `news-en-live/` (pro češtinu `news-cz-…`).
Uvnitř otevři výchozí anglické `index.html` nebo české `report.cz.html`. Report má přepínač jazyka
rozhraní, celé články, legendu a samostatně rozbalitelný autorský klíč.
Přepínač HTML nepřekládá podklady ani otázky. `--lang` vybírá články i výchozí předvolbu ve stejném jazyce. Přímé CLI `examples/news_compare.py --policy PATH` umožňuje použít jinou politiku.

Náhled nevymýšlí odpovědi modelu: ukazuje **Neměřeno**, nula pokusů a žádná
pravděpodobnostní čísla. Živý výstup navíc ukládá `report.json`, distribuce odpovědí,
confidence, identitu politiky/modelu, vstupní a výstupní tokeny, výpočet ceny podle
aktuálně dostupného ceníku OR i případnou částku vrácenou API. Neznámé částky se
nesčítají jako nuly. Při chybě prvního poskytovatelského volání se druhé neprovádí.

## Krátká legenda pro laiky

| Otázka | Co hledáme |
|---|---|
| Vítání návštěvy | Autor sám líčí přijetí a jednání jako politický úspěch. |
| Práva a kontrola moci | Autor hájí práva a nezávislý dohled jako omezení politiků. |
| Lid proti elitám | Autor staví autentický lid proti odtržené či sobecké elitě. |
| Lídr před kontrolou | Autor žádá více volnosti pro lídra a dohled líčí jako překážku. |
| Autorské přesvědčování | Autor opakovaně hodnotí, doporučuje nebo používá ironii. |

**Přítomno** znamená rozpoznaný znak, **Nepřítomno** jeho nepřítomnost v autorském
podání, **Prověřit** nejistotu nebo chybu. Jsou to popisy, ne známky kvality.
Každá otázka má vlastní výsledek. `pass/fail` celého objektu `Decision` se zde
nepoužívá jako verdikt nad článkem, protože smíšený profil je normální.

Výchozí politika vyžaduje pravděpodobnost dané možnosti ≥ 0.85 a confidence ≥ 0.60.
Confidence není procento správnosti změřené na článcích. Tato startovní nastavení
nejsou kalibrovaná. Všech pět otázek se posílá najednou pro každý článek zvlášť.
V původním jazykovém pokusu byly pro EN i CZ použity stejné anglické otázky,
takže se měnil pouze vstupní text. Nová česká předvolba překládá také otázky;
její výsledky proto nelze bez dalšího přisoudit jen jazyku článku. Původní
`policy.json` zůstává anglickým protějškem `policy.en.json`. Jev neposkytuje slovní vysvětlení; ukázky níže jsme napsali my.

## Praktický výstup do aplikace

Při spolehlivě rozpoznaném autorském přesvědčování jde článek do `commentary_queue`,
při jeho spolehlivé absenci do `reporting_queue`. Jakákoli nejistá dílčí odpověď
nebo chyba znamená `review_queue`. To je zdejší konzervativní pravidlo aplikace,
které je viditelné ve funkci `route` v [příkladu](../news_compare.py).
Další použití může vybírat jednotlivé znaky bez nálepkování politické identity autora.

<details>
<summary>Autorský klíč — nejprve zkus posoudit texty sám</summary>

A je záměrně liberálně institucionální komentář; B záměrně populistický komentář.
Tyto rámce nejsou obecně neslučitelné a pět zdejších znaků je nedefinuje univerzálně.

| Znak | A | B |
|---|---|---|
| Vítání návštěvy | nepřítomno | přítomno |
| Práva a kontrola moci | přítomno | nepřítomno |
| Lid proti elitám | nepřítomno | přítomno |
| Lídr před kontrolou | nepřítomno | přítomno |
| Autorské přesvědčování | přítomno | přítomno |

Oba citují Pellův stejný slogan. A jej odmítá, B se s ním ztotožňuje. Detekce slov
„obyčejní lidé“ sama o sobě tudíž nestačí. B zároveň zmiňuje parlament i novináře;
samotný výskyt těchto slov není obhajobou nezávislého dohledu.

[reference.json](reference.json) obsahuje očekávání a přesné úryvky. Jsou to
autorské anotace, nikoli naměřené odpovědi Jev. Do modelu se neposílají. Ukázkový
úryvek nemůže sám dokázat nepřítomnost znaku v celém textu.

</details>

## Vlastní texty a kontrolní pokusy

Po `./dev.sh sync` pracuj v runtime s jeho Pythonem:

```bash
cd ~/dev-out/sema-jev-framework
.venv/bin/python examples/news_compare.py --article-a /cesta/a.txt --article-b /cesta/b.txt
.venv/bin/python examples/news_compare.py --article-b examples/news/article_a.en.txt
```

První příkaz vytvoří náhled vlastních textů, druhý kontrolu A/A. `--live` je změní
na placené vyhodnocení; při přímém spuštění musí být klíč v prostředí, protože
`config/runtime.env` načítá pouze launcher. `--output` určí jiný výstup mimo `dev`.
Při vlastních vstupech se přibalený autorský klíč nezobrazuje.

Pro další testy vyměň A/B za B/A, nahraď citaci vlastním souhlasem nebo změň jazyk.
Texty se neposílají společně, názvy souborů ani očekávání nejsou součástí dotazu.
Shoda A/A nebo CZ/EN se nevnucuje kódem — její případné selhání je výsledek k prozkoumání.
Tato dvojice je učební pomůcka. Neprokazuje přesnost, skrytou koordinaci, pravdivost
zprávy ani úmysly skutečných osob.

## Zajímavost na závěr: překlad jako další vrstva rámování

Ukázka vznikla pro vysvětlení integrace a porovnání stylů psaní. Při samostatném posouzení anglických a českých textů se nabídl další možný způsob využití: porovnat originál s volným překladem a hledat posun důrazu, hodnocení nebo toho, čí názor text vyjadřuje.

Při prvním samostatném EN/CZ běhu 19. září 2026 dostal model
`typesafe/jev-1.13-20260917` pro každý článek stejných pět anglických otázek.
Všech deset rozhodnutí o znacích se mezi jazyky shodovalo a odpovídalo autorskému
klíči. Čísla totožná nebyla: u vítání návštěvy v článku B byla podpora „přítomno“
99 % v EN a 92 % v CZ; confidence 99 % a 88 %. Tento běh neprokázal, že překlad
změnil rámování.

Rozdíl může upozornit na pasáže, které stojí za kontrolu. Sám ale nedokazuje, že překlad změnil rámování: hodnoty může ovlivnit i citlivost modelu na jazyk a proměnlivost mezi běhy. Jde o vedlejší námět z učebního experimentu, nikoli ověřenou kontrolu překladu.
