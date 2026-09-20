# Ověřování chování modelu

[🇬🇧 English](README.en.md) · **🇨🇿 Česky** · [Projekt](../README.cz.md)

`cases.json` obsahuje 12 ručně napsaných syntetických případů: kladný a záporný požadavek,
negaci, citaci, podmínku, chybějící kontext, pokyn uvnitř dat a dvojice čeština/angličtina.
Očekávání jsou návrh anotací autora ukázky, nikoli nezávisle ověřený benchmark.

`./dev.sh evaluate` výslovně spustí **placené** vyhodnocení přes OpenRouter.
Klíč patří do runtime konfigurace; výsledný report do runtime `artifacts/evaluation.json`.
Při první provozní chybě se série zastaví. Přehled obsahuje pokrytí automatickým
rozhodnutím, záměny tříd, chybná schválení/zamítnutí a známé i neznámé náklady.
Tyto případy slouží k odhalení základních problémů, ne k odvození produkčních prahů.

Před nasazením doplň reprezentativní lokální data, nezávislé anotace, oddělenou
kalibrační a testovací sadu a kontrolu změny modelu. Ostrá data drž výhradně v dev-out.
Změna promptu vyžaduje nové vyhodnocení; verze a hash pravidel jsou v každém výsledku.
