import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Whoever deploys a bot picks its budget, but whoever runs the server pays the model bill.

Found while checking SkyMind against a list of common attacks (November 2026): any visitor could deploy a bot
with a $99,999,999,999 budget and chat on the server owner's model credits, and a negative budget was accepted.
Now: every bot not deployed with the admin token, sample bots included, gets at most MAX_BOT_LLM_BUDGET of model
spending a month; all bots together stop at MAX_FLEET_LLM_BUDGET (admins exempt); nonsense budgets are refused.
"""
import json
import fakeredis
from fastapi.testclient import TestClient
import examples, main, settings, store

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
R = fakeredis.FakeRedis(server=srv, decode_responses=True)
CAP = settings.MAX_BOT_LLM_BUDGET
body = {k: v for k, v in next(e for e in examples.EXAMPLES if e["key"] == "acme").items() if k != "key"}
body["provider"] = "mock"

with TestClient(main.app) as c:
    ADMIN = {"X-Admin-Token": main.app.state.admin_token}
    llm = lambda bid: json.loads(R.get(f"bot:{bid}"))["llm_budget"]

    # visitors: capped, and told so; admins (evaluation runs): the budget they asked for
    v = c.post("/bots", json=dict(body, bot_name="Visitor", monthly_budget="$99999999999")).json()
    assert llm(v["bot_id"]) == CAP and any(f"capped at ${CAP:g}" in n for n in v["notes"]), v["notes"]
    adm = c.post("/bots", json=dict(body, bot_name="Eval", monthly_budget="$100000"), headers=ADMIN).json()
    assert llm(adm["bot_id"]) > CAP
    tiny = c.post("/bots", json=dict(body, bot_name="Tiny", monthly_budget="$46")).json()  # just above the $45 of servers
    assert llm(tiny["bot_id"]) < CAP and not any("capped" in n for n in tiny["notes"]), "a budget under the cap is kept as is"
    print(f"per-bot cap OK: visitor bots at most ${CAP:g} a month, admin bots as asked")

    # nonsense budgets and sizes are refused
    for bad in ({"monthly_budget": "-$100"}, {"monthly_budget": "$0"}, {"expected_concurrent_users": 10**9}):
        r = c.post("/bots", json=dict(body, bot_name="Bad", **bad))
        assert r.status_code == 422, (bad, r.status_code, r.text)
    print("validation OK: negative or zero budgets and absurd user counts refused")

    # sample bots stored before the cap existed are capped on the next start
    async def old_sample():
        main.settings.SEED_EXAMPLES = True
        await store.seed_examples()
        sample_id = store.slugify(next(e for e in examples.EXAMPLES if e["key"] in examples.DEPLOY_KEYS)["bot_name"])
        raw = json.loads(await main.app.state.redis.get(store.bot_key(sample_id)))
        assert raw["llm_budget"] <= CAP, raw["llm_budget"]
        raw["llm_budget"] = 333.0  # as stored by the old code
        await main.app.state.redis.set(store.bot_key(sample_id), json.dumps(raw))
        await main.app.state.redis.delete("seed_lock")
        await store.seed_examples()
        raw = json.loads(await main.app.state.redis.get(store.bot_key(sample_id)))
        assert raw["llm_budget"] == CAP, raw["llm_budget"]
    c.portal.call(old_sample)
    print("sample bots OK: capped when created, and old ones capped on the next start")

    # every answer's cost also counts toward the whole server's month
    before = float(R.get(store.month_cost_key(store.FLEET)) or 0)
    c.post(f"/bots/{v['bot_id']}/chat", json={"session_id": "f1", "message": "What is the return policy?"})
    assert float(R.get(store.month_cost_key(store.FLEET)) or 0) > before
    R.set(store.month_cost_key(store.FLEET), settings.MAX_FLEET_LLM_BUDGET + 1)
    assert c.post(f"/bots/{v['bot_id']}/chat", json={"session_id": "f2", "message": "hi"}).status_code == 429
    assert c.post(f"/bots/{v['bot_id']}/chat", json={"session_id": "f3", "message": "hi"}, headers=ADMIN).status_code == 200
    c.delete("/admin/stats", headers=ADMIN)
    assert R.get(store.month_cost_key(store.FLEET)) is None, "resetting stats clears the server's month too"
    print("server-wide cap OK: counted per answer, stops visitors, not admins; cleared by a stats reset")
print("ALL BUDGET-CAP TESTS PASSED")
