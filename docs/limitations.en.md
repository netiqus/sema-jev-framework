# Limitations and boundaries

**🇬🇧 English** · [🇨🇿 Česky](limitations.cz.md)
- A model can make an incorrect judgement with high confidence. Type-correct
  output does not guarantee correct meaning.
- Jev is not a proof system, compiler or code execution sandbox. Permissions and
  enforced security boundaries must remain outside it.
- Instructions inside evidence can influence results. A data-only instruction
  is not guaranteed prompt-injection protection. Do not use it alone to authorise sensitive actions.
- Input size is measured in JSON bytes, not by an exact tokenizer. A provider
  may reject smaller inputs because of its context limit. The library never silently truncates text.
- Questions in a batch are independent; if one needs another's result, use another step.
- Boolean rules do not explicitly distinguish missing evidence. Use three-option
  `Rule.require` for such tasks.
- `acheck` uses a thread; cancellation does not cancel remote billing. Loop
  callbacks are synchronous and their exceptions propagate to the caller.
- There is no durable queue, transactional write or automatic interrupted-loop recovery.
- Evidence is not implicitly stored. The optional audit includes metadata;
  even rule names may be sensitive. The application manages retention, access
  and concurrent writes from multiple processes. An example may explicitly save
  a local report containing evidence, as the news demo does.
- Adapter and rule tests verify the contract. Live domain benchmarks are not
  part of the library's demonstrated quality.
- Linux with Python 3.11–3.14 is verified. Windows remains unverified.
- Live checks have used OpenRouter. The direct TypeSafe adapter is covered by
  offline contract tests but has not been verified against the live service.
