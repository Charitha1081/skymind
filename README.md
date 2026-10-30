# SkyMind

**An AI orchestration platform that deploys and scales LLM chatbots from a simple spec.**

> 🚧 In progress. Follow along as I build it.

## What it does

Describe what you need, and SkyMind handles the rest:

```yaml
bot_name: support-bot
expected_concurrent_users: 500
latency_target_p95: 2s
memory: summary + long_term
model: auto
monthly_budget: $50
```

SkyMind will:

1. **Plan capacity:** estimate replicas and monthly cost from your spec
2. **Deploy** the chatbot to Kubernetes automatically
3. **Manage memory:** short-term (Redis) and long-term (pgvector), configurable per bot
4. **Route models:** a cheaper model for simple questions, a stronger model for hard ones
5. **Autoscale** with load, and track latency, tokens, and cost per user
6. **Prove it works:** load tests at 100, 500, and 1,000 concurrent users

## Architecture

```
User spec ──► Control plane (FastAPI)
               ├─ capacity planner
               └─ deployer ──► Kubernetes
                                ├─ Chatbot service (LLM gateway + model router)
                                ├─ Redis (short-term memory)
                                ├─ Postgres + pgvector (long-term memory)
                                ├─ Autoscaler
                                └─ Prometheus + Grafana
```

## Roadmap

- [ ] Chatbot service with FastAPI + LLM API
- [ ] Conversation memory in Redis, packaged with Docker
- [ ] Long-term memory with pgvector
- [ ] Model routing
- [ ] Control plane: spec → capacity plan → Kubernetes deploy
- [ ] Autoscaling + metrics dashboards
- [ ] Load tests and results
- [ ] Evaluation pipeline for answer quality

## Tech

Python · FastAPI · LLM APIs · Redis · pgvector · Docker · Kubernetes · Prometheus · Grafana

---

Built by [Charithasri Ande](https://charitha1081.github.io)
