# API klíče a integrace do aplikace

[🇬🇧 English](credentials.en.md) · **🇨🇿 Česky**

Rozhraní pro předání klíče určuje knihovna. Hostitelská aplikace si volí, odkud
klíč získá: z prostředí, správce tajemství, systémové klíčenky nebo vlastního
nastavení. Konkrétní úložiště ani framework uživatelského rozhraní nejsou předepsané.

## Nainstalovaná knihovna

| Poskytovatel | Explicitní parametr | Náhradní zdroj v prostředí |
|---|---|---|
| `OpenRouter` | `OpenRouter(api_key=key)` | `OPENROUTER_API_KEY` |
| `TypeSafe` | `TypeSafe(api_key=key)` | `TYPESAFE_API_KEY` |

Priorita je **explicitní `api_key` → prostředí**. Pouze `api_key=None` vybírá
načtení z prostředí. Explicitně prázdný klíč je chyba, nikoli pokyn použít jiný
klíč. Bílé znaky na okrajích se odstraní. Prostředí se čte při dotazu, nikoli
při importu nebo konstrukci adaptéru.

Pro aplikaci, která už spravuje své klíče:

```python
from sema_jev import Gate, OpenRouter


def make_gate(runtime_key: str) -> Gate:
    return Gate(
        "Does `message` explicitly request a refund?",
        provider=OpenRouter(api_key=runtime_key),
    )
```

Aplikace zavolá `make_gate` s klíčem ze svého zvoleného zdroje. Pro oddělené
uživatelské klíče vytvoří odpovídající adaptéry s explicitním klíčem; nebude mezi
souběžnými požadavky přepisovat společnou proměnnou prostředí procesu.

Knihovna nezobrazuje dialog, nehledá soubory `.env`, nečte klíčenku ani klíč
neukládá na disk. Předaný klíč zůstává v paměti objektu poskytovatele a odesílá
se v autentizační hlavičce tomuto poskytovateli. Veřejné dotazy na ceník OpenRouteru
ho neobsahují. Není součástí JSON politiky, běžného JSON rozhodnutí, vestavěného
auditu ani HTML reportu příkladu.

Chybějící či prázdný klíč znamená při `Gate.check` výsledek `review` s chybou
`missing_api_key`, ještě před jakýmkoli síťovým dotazem. Ukázka zpráv kontroluje
chybějící klíč už na začátku a skončí s vysvětlením. Nedosazuje simulované odpovědi.
HTML report zpráv je statický: neobsahuje políčko pro klíč ani klienta živého API.

## Vývojový launcher tohoto repozitáře

`dev.sh` přidává pohodlnou možnost mimo samotnou nainstalovanou knihovnu:

1. Převezme prostředí procesu.
2. Volitelně přečte `config/runtime.env` **v běhovém adresáři**.
3. Soubor doplní pouze chybějící proměnné. Existující proměnná prostředí má
   přednost, i pokud je prázdná.
4. S tímto prostředím spustí příklad. Soubor přijímá jen dva výše uvedené názvy klíčů.

Ve standardním uspořádání jde o soubor
`~/dev-out/sema-jev-framework/config/runtime.env`. Vytvoř jej ze vzoru
[`runtime.env.example`](../examples/runtime.env.example) a na Linuxu nastav
práva `0600`. Vyplň ho lokálně editorem. Vyplněný soubor nepatří do `dev`, gitu
ani cloudem synchronizovaného zdroje. Skutečný klíč nepatří do příkladu ani argumentu příkazu.

Přímé spuštění Python příkladu tento loader obchází: prostředí musíš připravit
sám. Živé CI vyhodnocení bere klíč z GitHub Actions secrets; běžné CI používá
offline odpovědi a skutečný klíč nepotřebuje.

## Co rozhoduje autor aplikace

Volí získání klíče, přístupy jednotlivých účtů, ukládání a obměnu klíčů. Framework
určuje způsob předání poskytovateli a chování při chybějícím klíči. MIT licence
tohoto kódu nezajišťuje API klíč; pro živé dotazy je stále potřeba účet u poskytovatele.

[API](api.cz.md) · [Provoz](operations.cz.md) · [Projekt](../README.cz.md)
