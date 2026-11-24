# Reversals

Things we believed, the evidence that changed our minds, and what we did. Keep adding to this. A record of being wrong and fixing it is worth more than a list of things that worked.

Each entry: **what we believed → what showed it was wrong → what we changed → how we know it's fixed.**

---

## The router looked accurate until it met new questions

- **Believed:** the first router, which only looked for reasoning words ("explain", "compare"), worked. It agreed with the easy/hard labels on 97% of the original questions.
- **Evidence:** those were the questions it had been written against. On new questions it scored 45% and 61%.
- **Changed:** rebuilt it around five signals (reasoning, several requests at once, the person's own situation, specific numbers, arithmetic). It scored 89% on a set it was never tuned to.
- **Also learned:** judged by results instead of labels, the cheap model answered almost every "hard" document question correctly, so routing by guessed difficulty cost more for no gain. The recommended setting became the cheap model plus the second look.
- **Caveat:** these numbers were measured on the earlier university sample, which has since been replaced. They need re-measuring on the new samples (TODO.md, Phase 1).

## Source chips under "I don't have that" (the refusal-chip bug)

- **Believed:** showing the sections search returned under every answer was honest citation.
- **Evidence:** an off-topic question still scrapes a weak match (for example, "return policy for hiking boots" matched an unrelated section). The bot correctly refused, but a clickable source chip sat under the refusal, which looked like a citation for an answer that was never written.
- **Changed:** a refusal now cites nothing. Other answers name only the sections whose wording actually appears in the answer (`orchestrator.py`, `shown_sources`).
- **Guarded by:** `tests/test_orchestrator.py`, the sources tests.

## The coverage guard

- **Believed:** _(fill in)_
- **Evidence:** _(fill in)_
- **Changed:** _(fill in)_
- **Guarded by:** _(fill in)_

## The budget belonged to the wrong person

- **Believed:** the budget guard and hard stop protected the money.
- **Evidence:** checking SkyMind against a public list of common attacks showed that whoever *deploys* a bot picks its budget, while whoever *runs the server* pays the model bill. A visitor could set a $99,999,999,999 budget, and a negative one was accepted. The guard protected the visitor's number, not the owner's credits. The sample bots on the live site had about $330 a month of model budget, open to anyone.
- **Changed:** a per-bot cap on model spending for every bot not deployed with the admin token (sample bots included, existing ones capped on the next start), a server-wide monthly cap, and refusal of zero, negative or absurd values.
- **Guarded by:** `guard_check.py` (11 of 14 blocked before, 14 of 14 after; it fails CI if any attack gets through) and `tests/test_budget_caps.py`.

## The monthly budget never reset

- **Believed:** the budget guard and the hard stop enforced a *monthly* budget.
- **Evidence:** a code review found they compared the *lifetime* spending counter with the monthly budget. Once a bot overspent, it stayed blocked in every later month.
- **Changed:** spending is now also counted per calendar month (`monthcost:{bot}:{YYYY-MM}`), and the guard, the hard stop, the usage endpoint and the admin page all read that.
- **Guarded by:** `tests/test_review_fixes.py`.

## Visitors could fake their address to get around rate limits

- **Believed:** trusting the proxy's `X-Forwarded-For` header (`FORWARDED_ALLOW_IPS="*"`) gave each visitor's real address.
- **Evidence:** with everything trusted, the server used the *left-most* entry, which the visitor writes themselves. Sending a new fake address on each request avoided every per-address limit.
- **Changed:** the address is read from the right (`TRUSTED_PROXY_HOPS`). On Render the header had 3 entries, and the log line showed that hop 3 is the visitor (checked against a known address).
- **Guarded by:** `tests/test_review_fixes.py`; the server logs the header layout once per start.

## The fix for one security hole caused a regression

- **Believed:** connecting to the address that passed the private-address check would block DNS rebinding.
- **Evidence:** a second review found it always used the first address in a sorted list, which is often IPv6. On hosts without IPv6, every website import would fail.
- **Changed:** IPv4 addresses come first, and if one can't be reached, the next checked address is tried.
- **Lesson:** review the fix, not just the original code.

## A test only passed without internet

- **Believed:** the test suite ran offline.
- **Evidence:** on a laptop with internet, one platform test reached the real website through the website lookup and got a real answer, so the "I don't have that" check failed. It had only passed in an environment with no internet access.
- **Changed:** that test now blocks website fetching explicitly.
