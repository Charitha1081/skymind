import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""The grader judges facts, not spelling.

The Kestrel held-out run (November 2026) marked two right answers wrong: "100%" and "4%" against a
required "100 percent" and "4 percent", and "doesn't need advance notice" against "does not need advance
notice". Both sides are now rewritten the same way before comparing. The held-out figures in the README stay
as first measured; this fixes the measuring tool for the next run.
"""
import evaluate as e

g = lambda must, answer: e.grade({"must": must}, answer)

# the two held-out answers, word for word in their key parts
assert g(["100 percent", "4 percent", "2 years"],
         "If you contribute 4% of your pay, Kestrel matches 100% of that. The company match vests fully after 2 years.")
assert g(["does not need advance notice", "bereavement leave"],
         "Bereavement leave doesn't need advance notice, so you don't have to notify your manager beforehand.")

# and the reverse direction: the question says "%", the answer says "percent"
assert g(["20%"], "Partners get a 20 percent revenue share.")
assert g(["cannot"], "You can't carry over more than 5 days.") and g(["can not"], "You cannot do that.")

# no new false passes
assert not g(["4 percent"], "Kestrel matches 40% of pay.")
assert not g(["does not need advance notice"], "Bereavement leave needs advance notice.")
assert not g(["is not"], "It is now available.")

# numbers with thousands separators still match either way
assert g(["3,200"], "more than 3200 customer teams") and g(["5250"], "up to $5,250 a year")

# refusals are graded as before, in either spelling
for reply in ("I don't have that information.", "I do not have that.", "That isn't covered.", "I can't find that."):
    assert e.grade({"refuse": True}, reply), reply
assert not e.grade({"refuse": True}, "You get 5 paid days off.")
print("ALL GRADER TESTS PASSED")
