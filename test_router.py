import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Model router: which questions go to the cheap model and which to the strong one, and why."""
import router


def tier(q):
    return router.classify(q)[0]


def names(q):
    return [name for name, _, _ in router.signals(q)]


# 1. short lookups and small talk stay on the cheap model
for q in ("hi", "thanks!", "When is spring break?", "What is your return policy?", "How do I reset my password?",
          "Do I need a permit to park?", "How much is the application fee?", "Where can I eat on campus?",
          "How many organizations from the Dallas area have tables?"):
    assert tier(q) == "cheap", (q, router.classify(q))
print("cheap OK: lookups and greetings stay on the cheap model")

# 2. each signal is found on its own, and explained
assert names("Compare the two shipping options.") == ["reasoning"]
assert names("expalin the refund rules") == ["reasoning"], "typos in reasoning words are tolerated"
assert names("What are the prizes, and can I use slides?") == ["several"]
assert names("I graduated last year. Which system do I use?") == ["situation", "specifics"] or \
    names("I graduated last year. Which system do I use?") == ["situation"]
assert names("If I order a $40 tent at 1 PM, when will it ship?") == ["situation", "specifics"]
assert names("How many days after classes begin is the census date?") == ["working out"]
assert names("Do I need a permit to park?") == [], "a question that contains 'I need' is not a situation"
print("signals OK: reasoning, several requests, situation, specifics, working out")

# 3. the signals add up: one weak signal is not enough, two are
assert tier("I live off campus. Where is the library?") == "cheap"          # situation only (1 point)
assert tier("I have a 2.8 GPA. Could I still be considered?") == "strong"   # situation + specifics
assert tier("I'm presenting at the AI Expo and want to win. What are the prizes, and can I use slides?") == "strong"
assert tier("If I order a $40 tent on a Tuesday at 1 PM with express shipping, how much is shipping and when will it ship?") == "strong"
t, why = router.classify("I missed my appointment and didn't cancel. What is the rule, and how do I reschedule?")
assert t == "strong" and "asks 2 things" in why and "situation" in why, why
print("scoring OK:", why)

# 4. long messages and code always go to the strong model; forced modes ignore the signals
assert tier("word " * 60) == "strong" and tier("```\nprint(1)\n```") == "strong"
assert router.pick_tier("Compare A and B", "cheap")[0] == "cheap"
assert router.pick_tier("hi", "strong")[0] == "strong"
assert router.pick_tier("Compare A and B", "auto")[0] == "strong"
print("overrides OK: long text, code, and forced cheap/strong")

print("ALL ROUTER TESTS PASSED")
