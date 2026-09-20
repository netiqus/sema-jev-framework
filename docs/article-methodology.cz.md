# Od „je to zaujaté?“ k hodnoticímu zadání

[🇬🇧 English](article-methodology.en.md) · **🇨🇿 Česky** · [Ukázka zpráv](../examples/news/README.cz.md)

Politické články v ukázce vysvětlují fungování. Přenositelné je sestavení
pozorovatelných otázek, definic odpovědí a rozhodnutí, co s nimi aplikace udělá.
Rozsah platnosti výsledku určují samotné otázky.

## Vyzkoušej celý postup

```bash
./dev.sh news-lab --lang cz
```

Otevři vypsanou místní adresu. Launcher načte klíč z runtime; prohlížeč ho nikdy
nedostane. Editace, načtení ukázek, validace a export politiky nevolají model.
**Posoudit oba články** provede nejvýše dva placené dotazy. Chyba API zastaví druhý
dotaz. Počty tokenů a dostupné ceny jsou uvedené zvlášť pro každý článek.

1. Načti ukázky nebo vlož vlastní texty. Změna jazyka rozhraní zachová články
   a otázky; načtení ukázkových článků nahradí textová pole.
2. Zvol jazyk předvolby (čeština/angličtina), načti ji a rozbal kritéria. Český
   editor začíná českými otázkami i definicemi; existující běhy zachovávají původní jazyk. Uprav přesné zadání a význam možností
   `present`, `absent`, `unclear`. Kritéria podle potřeby přidávej či odebírej.
3. Nastav prahy podpory odpovědi a confidence. Uplatňuje je aplikace až po odpovědi;
   nejsou to další instrukce posílané modelu.
4. Zvol **Pouze porovnat znaky**, nebo výslovně vyber otázku na přesvědčování pro
   zařazení mezi komentáře a zprávy. Nejistá odpověď nebo chyba API vede k prověření.
5. Bezplatně zadání ověř. Prohlédni úplné otázky včetně společného pokynu frameworku
   nebo celý dotaz pro každý článek. Neobsahuje autorský klíč, druhý článek, název
   souboru ani API klíč. Identifikátory API a společný bezpečnostní pokyn knihovny
   zůstávají anglicky; vlastní otázky a definice se odesílají beze změny.
6. Spusť posouzení. Report uchová texty, politiku, přesné otázky, prahy, otisk,
   skutečný model a náklady. Odkaz **Upravit tyto texty a kritéria** vytvoří nové
   zadání; nepřepíše podklady ani výsledek předchozího běhu.

## Co jsme vybrali v původní ukázce?

| Kritérium | Co pozoruje | Rozsah |
|---|---|---|
| `welcomes_visit` | Autor vítá právě toto přijetí jako úspěch. | Konkrétní událost; pro jiné téma nahradit. |
| `rights_and_oversight` | Autor obhajuje práva a nezávislý dohled. | Politický rámec, nikoli verdikt o zaujatosti. |
| `people_vs_elites` | Autor přijímá morální protiklad lidu a elit. | Určitý rétorický rámec. |
| `leader_over_scrutiny` | Autor žádá větší volnost lídra před kontrolou. | Určitý politický argument. |
| `authorial_persuasion` | Autor vlastním hlasem opakovaně hodnotí či přesvědčuje. | Obecněji použitelný znak; ověřit na zamýšleném žánru. |

Jev si tyto dimenze nevybírá sám. Oba články dostávají samostatně stejné otázky.
Odlišný profil nedokazuje, že jeden autor píše pravdivěji nebo že se autoři
rozcházejí v samotných faktech události.

## Nahraď vágní cíl viditelným znakem

„Je autor zaujatý?“ nechává definici na modelu. U článku o fiktivním dopravním
návrhu může konkrétní otázka vypadat takto:

> Obhajuje autor v `article` vlastním hlasem návrh bezplatné městské autobusové dopravy?
> Převyprávění citátu zastánce bez autorova souhlasu se nepočítá.

| Odpověď | Definice |
|---|---|
| `present` | Autor vlastním hlasem výslovně doporučuje či podporuje návrh. |
| `absent` | Text návrh neobhajuje; může jej odmítat, neutrálně popisovat nebo podporu pouze někomu přisuzovat. |
| `unclear` | Smíšené postoje či nejasné připsání výroku brání rozhodnutí. |

`absent` zde **neznamená odpor**. Pokud potřebuješ rozlišit podporu a odpor,
definuj další otázku na odmítání, případně v knihovně použij odpovídající
vícemožnostní `Rule.choose`. Tento učební editor záměrně používá otázky na znaky
s odpověďmi přítomno/nepřítomno/nejasné.

Předvolba **obecné znaky rétoriky** odstraňuje otázky vázané na návštěvu. Hledá
autorské přesvědčování, hodnotící nálepky, shazování oponentů a přijatou rétoriku
my versus oni. Jde o experimentální výchozí návrh, nikoli standard či univerzálně
kalibrovaný detektor. Automaticky neurčuje cíl autorovy podpory, neprokazuje úmysl
ani bez srovnávacích zdrojů neověřuje zamlčená fakta. Silný názor a faktická
správnost jsou samostatné věci.

## Přenes politiku do vlastní aplikace

Stáhni ověřený `policy.json`, ulož jej do runtime konfigurace cílové aplikace
a použij stejné rozhraní knihovny:

```python
from sema_jev import Gate, Policy

gate = Gate(Policy.load("config/article-policy.json"))
decision = gate.check({"article": article_text})
for feature in decision.checks:
    print(feature.id, feature.status, feature.probabilities, feature.confidence)
```

Politika exportuje otázky a prahy. Volitelné zařazování z ukázky je aplikační
logika, uložená zvlášť jako `routing_rule` v `report.json`; ve vlastní aplikaci
si zvol odpovídající akci. Souhrnné `decision.passed` nevykládej jako známku
kvality či nezaujatosti článku.

Začni jasným pozitivním případem, neutrální zprávou, odmítnutou citací, ironií
a nejasným případem. Označ je ručně před prohlédnutím odpovědí modelu. Odděl
ladicí a ověřovací sadu a kontroluj i sebejisté chyby. Změna otázky, jazyka,
modelu či prahů potřebuje nové ověření. Viz [metodika politik](methodology.cz.md)
a [předání klíče](credentials.cz.md).
