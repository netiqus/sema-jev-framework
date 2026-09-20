# Použití knihovny

[🇬🇧 English](api.en.md) · **🇨🇿 Česky**
## Jedna podmínka

```python
from sema_jev import Gate, Status

gate = Gate("Does `message` explicitly request a refund?")
result = gate.check({"message": "Please refund the duplicate payment."})
if result.status == Status.PASS:
    print("Continue")
elif result.status == Status.FAIL:
    print("Return for correction", result.failed_checks)
else:
    print("Request evidence or review manually", result.review_checks)
```

Default je OpenRouter a `OPENROUTER_API_KEY`. Knihovna sama nehledá `.env`.
Klíč můžeš také předat `OpenRouter(api_key=...)`; nesmí být literálem ve zdrojáku.
Doplňování klíče do prostředí je odpovědnost hostitelské aplikace.

## Více pravidel a pevné kontroly

```python
from sema_jev import Gate, Policy, Rule

policy = Policy(
    "completion",
    version="1",
    rules=(
        Rule.require(
            "scope",
            "Does `diff` implement the requirement in `task`?",
            guidance="Implement the missing part of the requirement.",
        ),
        Rule.require("evidence", "Does `test_output` demonstrate the requested behavior?"),
    ),
    required_fields=("task", "diff", "test_output"),
    required_checks=("build",),
)
gate = Gate(policy)
result = gate.check(
    {"task": "...", "diff": "...", "test_output": "..."},
    checks={"build": True},
)
```

Hodnota `build` pochází ze skutečného nástroje, nikoli z tvrzení agenta.
Chybějící povinný klíč nebo `None` vrací review bez dotazu. Prázdný text je přítomná
hodnota; pokud jej chceš zakázat, vytvoř vlastní pevnou kontrolu.

`Policy.load(path)` načte verzi JSON schématu 1. Ukázky jsou v `policies/`.
Neznámá pole jsou chyba; nedochází k tichému ignorování překlepů.

## Typy pravidel

| Konstruktor | Kdy použít |
|---|---|
| `Rule.require(id, instructions)` | Výchozí volba s explicitním nedostatkem důkazů. |
| `Rule.boolean(id, instructions, expected=True)` | Jednoznačná binární vlastnost; bez zvláštní confidence. |
| `Rule.choose(..., options={...}, accept=(...), reject=(...))` | Vlastní uzavřené kategorie. Nezařazené možnosti vedou k review. |
| `Rule.rate(..., levels=(...), accept=(2,3), reject=(0,1))` | Stupnice s popsanými úrovněmi. Posuzuje se pravděpodobnost příslušnosti k povoleným stupňům. |

Výchozí `min_probability=0.85` a `min_confidence=0.60` jsou pouze startovní nastavení.
U boolean není samostatná confidence. U ostatních musí projít oba limity.
`CheckResult.probability` vždy vyjadřuje podporu přijatelných výsledků, nikoli
pravděpodobnost zvolené kategorie či globální přesnost celého rozhodnutí.
`guidance` je tebou napsaný pokyn k opravě; model žádné vysvětlení negeneruje.

## Adaptéry a async

```python
from sema_jev import Gate, TypeSafe

gate = Gate("Does the evidence support the claim?", provider=TypeSafe())
# Reads TYPESAFE_API_KEY only when check() is called.
```
Přímý adaptér TypeSafe má offline testy kontraktu; živé ověření zatím používá OpenRouter.


V asynchronní aplikaci použij `await gate.acheck(data)`.
Implementace deleguje synchronní přenos do threadu. Po zrušení čekající coroutine
může vzdálený dotaz dokončit a být účtován. Omezení souběžnosti nastav v aplikaci.
Jeden request má timeout; dotazy se automaticky neopakují ani nepřepínají na jiného providera.

## Opravná smyčka

```python
from sema_jev import Gate, run_until_pass

gate = Gate("Does the text contain an explicit greeting?")
result = run_until_pass(
    gate,
    produce=lambda: "Draft text",
    revise=lambda text, decision: "Hello! " + text,
    max_attempts=3,
)
```

`fail` vyvolá opravný callback, `review` okamžitě zastaví smyčku. Po vyčerpání limitu
je `stop_reason=attempt_limit`. Callbacky si aplikace dodá sama; knihovna nevolá
programovací LLM ani shell. Parametr `evidence` mapuje výstup na podklady pro Jev,
`checks` po každé opravě znovu získá deterministické kontroly.

## Cena a audit

`result.cost.billed_usd` je částka vrácená API. `input_usd` a `output_usd` jsou
výpočty podle tokenů a ceníku, `calculated_usd` jejich součet. Částky jsou `Decimal`,
v JSON řetězce. Nedostupná hodnota je `None`, nikdy automaticky nula.
Ceník OR se drží v paměti nejvýše 5 minut; obsahuje URL a čas načtení. Jeho výpadek
neznemožní použít výsledek modelu. Cena přímého TypeSafe není odhadována z ceníku OR.

`JsonlAudit(path)` je volitelný. Nepíše texty ani klíče. Při problému se zápisem
zůstane původní výsledek, ale `audit_error=audit_write_failed`; aplikace může podle
svých požadavků zastavit další krok. Audit nefunguje jako bezpečnostní důkaz.

## CLI pro jiné aplikace

```bash
printf '%s' '{"state":{"message":"Please refund the duplicate payment."}}' |   sema-jev policies/refund.json
```

Na stdout jde JSON rozhodnutí. Exit kódy: 0 pass, 1 fail, 2 review, 3 chyba
konfigurace/vstupu. CLI nespouští žádný návazný příkaz. Live volání je placené.

Přesné pořadí zdrojů, načtení runtime souboru a příklady pro autory aplikací popisuje [předání API klíče](credentials.cz.md).
