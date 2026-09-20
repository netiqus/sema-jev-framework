# Omezení a hranice použití

[🇬🇧 English](limitations.en.md) · **🇨🇿 Česky**
- Model může udělat chybný úsudek i s vysokou confidence. Typová správnost výsledku
  nezaručuje správnost jeho významu.
- Jev není důkazový systém, kompilátor ani izolované prostředí pro spouštění kódu.
  Pravidla pro oprávnění a vynucené bezpečnostní hranice musí zůstat mimo něj.
- Instrukce v posuzovaných datech mohou ovlivnit výsledek. Přidaná formulace o datech
  není garantovaná ochrana proti prompt injection. Neschvaluj podle ní sama citlivé operace.
- Limit velikosti je v bajtech JSON; nejde o přesný tokenizer. Poskytovatel může
  menší vstup odmítnout kvůli kontextovému limitu. Knihovna nikdy text tiše nezkracuje.
- Otázky v jedné dávce jsou nezávislé; potřebuje-li jedna výstup druhé, udělej další krok.
- Výchozí boolean prahy neposkytují explicitní rozlišení chybějícího důkazu; pro takové
  úlohy použij `Rule.require` se třemi možnostmi.
- `acheck` využívá thread; zrušení čekání neruší vzdálený účet. Callbacky smyčky jsou
  synchronní a jejich výjimky se propagují volajícímu.
- Není zde durable queue, transakční zápis ani automatické obnovení rozpracované smyčky.
- Žádné implicitní ukládání podkladů. Volitelný audit obsahuje metadata; citlivé mohou
  být i názvy pravidel. Retenci, přístup a souběžné zápisy více procesů řeší aplikace.
- API adaptéry a pravidla ověřují kontrakt. Živé benchmarky jednotlivých domén zatím
  nejsou součástí prokázané kvality knihovny.

- Ověřená platforma je Linux Python 3.11–3.14. Windows zůstává neověřený.
- Živé kontroly proběhly přes OpenRouter. Přímý TypeSafe adaptér má offline testy
  kontraktu, ale nebyl ověřen proti živé službě.
- Příklad zpráv výslovně ukládá vstupní texty do lokálního reportu v runtime;
  nejde o implicitní audit jádra.
