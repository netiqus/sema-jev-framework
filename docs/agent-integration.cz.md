# Integrační instrukce pro agenty

[🇬🇧 English](agent-integration.en.md) · **🇨🇿 Česky** · [Projekt](../README.cz.md)

Tento návod předej programovacímu agentovi při začleňování Sema do aplikace.
Popisuje veřejný kontrakt bez interních pracovních pravidel správců.
Za oprávnění, klíče a následné akce odpovídá hostitelská aplikace.

## Text pro integrační úkol

> Začleň `sema_jev` do vybraného rozhodovacího bodu. Použij `Gate`, `Policy`,
> `Rule` a `Status`; nepiš další HTTP klient Jev ani parser pravděpodobností.
> Přesnou validaci a autorizaci ponech aplikaci. Definuj jednu verzovanou politiku
> s konkrétními požadavky a rozlišením nedostatku podkladů. Gate používej opakovaně,
> volej `check` nebo `await acheck` a zvlášť obsluž PASS, FAIL a REVIEW.
> Nepoužívej `if decision`, neopakuj dotazy do náhodného úspěchu a nepovažuj API
> chybu za schválení. Čti tento návod a `docs/api.en.md`; implementaci studuj až
> podle potřeby. Větve ověř přes `FakeProvider`, živý test proveď až se samostatným
> oprávněním. Při předání rozliš simulované kontroly od živých.

## Minimální integrace

Balíček instaluj do prostředí aplikace podle [návodu](../README.cz.md#rychlý-start).
Klíče pocházejí z prostředí či správce tajemství aplikace, ne z JSON politiky nebo kódu.

```python
from sema_jev import Gate, Status

refund_gate = Gate("Does `message` explicitly request a refund?")


def route_message(message: str) -> str:
    decision = refund_gate.check({"message": message})
    if decision.status == Status.PASS:
        return "refund_queue"
    if decision.status == Status.FAIL:
        return "general_queue"
    return "review_queue"
```

Výchozí provider čte `OPENROUTER_API_KEY` až při dotazu. Klíč již spravovaný aplikací
předej do Gate přes `provider=OpenRouter(api_key=runtime_key)`. Explicitní klíč má
přednost; explicitně prázdný klíč nepoužije náhradní hodnotu z prostředí.
Instalovaná knihovna žádný konfigurační soubor s klíči nevyhledává.

## Politika a výsledky

- `Rule.require(id, instructions)` rozlišuje podporu, rozpor a nedostatek podkladů.
  Odkazuj na skutečné názvy vstupních polí a definuj, co se počítá. Nezávislé požadavky
  rozděl na otázky; neurčité „je vše správně?“ není metodika.
- `Policy(..., required_fields=(...), required_checks=(...))` deklaruje podklady
  a pevné kontroly. Skutečné výsledky nástrojů předej přes `gate.check(data, checks=...)`.
  Selhané či chybějící pevné kontroly zabrání dotazu na model.
- `pass` vyžaduje úspěch všech kontrol. Doložené nesplnění znamená `fail` i při
  nejistotě jiné kontroly. Jinak nejistota vede k `review`.
- `decision.checks` obsahuje jednotlivé výsledky; `failed_checks` a `review_checks`
  jejich podmnožiny. `decision.error` je kód chyby poskytovatele. Neplatná lokální
  politika vyvolá `ConfigurationError`.
- `guidance` je předem zadaný text opravy, nikoli vysvětlení vytvořené modelem.
  `run_until_pass` opravuje po fail, zastaví na review a má omezený počet pokusů.
- Confidence není pravděpodobnost „ano“. `CheckResult.probability` je podpora
  přijatelných možností. Výchozí prahy vyžadují ověření na doménových datech.
- Náklady používají `Decimal`; `None` znamená neznámou hodnotu. Zachovej počty
  neznámých účtů. `decision.to_dict()` lze serializovat do JSON a obsahuje hash
  politiky i identitu modelu.
- `acheck` používá thread; zrušení čekání nezaručí zrušené účtování. Aplikace omezuje
  souběh a nastavuje timeout poskytovatele.

## Offline ověření

Větve aplikace ověř simulovanými odpověďmi. Tento příklad výslovně simuluje
nedostatek podkladů a nevolá model:

```python
from sema_jev import FakeProvider, Gate, Status

provider = FakeProvider({
    "requirement": {
        "type": "choice",
        "choice": "insufficient",
        "probabilities": {"supported": 0.01, "contradicted": 0.01, "insufficient": 0.98},
        "confidence": 0.98,
    }
})
result = Gate("Does the evidence establish completion?", provider=provider).check({})
assert result.status == Status.REVIEW
assert not result.passed
```

Pokryj také pass, fail, chybu poskytovatele a selhanou pevnou kontrolu. Poslední
případ nesmí zavolat provider. Tyto testy neprokazují významovou přesnost Jev.
Před nasazením vyhodnoť verzovanou politiku na nezávisle označených doménových příkladech.

## Politika z editoru článků

Exportované JSON načti přes `Policy.load(path)` a předej `{"article": text}`.
Export obsahuje skutečná kritéria; nevymýšlej další skrytý prompt. Framework přidává
svůj zdokumentovaný pokyn zacházet se vstupem jako s podklady.

Používej jednotlivé výsledky znaků. Souhrnné pass/fail není známka kvality článku.
`routing_rule` ukázky je samostatná aplikační logika a nepatří do exportu politiky.
Následné větve hostitelské aplikace zvol výslovně.

[API](api.cz.md) · [Klíče](credentials.cz.md) · [Metodika](methodology.cz.md) · [Příklady](../examples/integrations.py)
