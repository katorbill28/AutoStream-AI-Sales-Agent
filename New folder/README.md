# AutoStream Lead Agent

This project implements an end-to-end conversational lead generation agent for the AutoStream assignment. It covers:

- Intent identification for pricing, features, policies, greetings, and sales intent
- Local knowledge retrieval over pricing/features and company policies
- Stateful lead qualification across multiple turns
- A mock lead-capture tool that writes qualified leads to `data/leads.jsonl`
- A FastAPI interface for running the agent as a simple backend service
- Optional Groq-backed intent classification and grounded response generation

## Project Structure

```text
app/
  agent.py
  config.py
  knowledge_base.py
  lead_store.py
  main.py
  models.py
data/
  knowledge_base/
    pricing_features.md
    company_policies.md
  leads.jsonl
tests/
  test_agent.py
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If you want to enable Groq:

```bash
copy .env.example .env
```

Then put your Groq key inside `.env`:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

## API Usage

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Chat with the agent:

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"demo-1\",\"message\":\"What are your pricing plans?\"}"
```

Lead capture example:

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"lead-1\",\"message\":\"I'm interested in booking a demo\"}"
```

Continue with the same `session_id` to complete qualification.

## How It Maps to the Assignment

Intent identification:

- Rule-based classification routes user questions into pricing, policy, feature, greeting, or lead-capture paths.

RAG-powered retrieval:

- The agent searches local markdown documents inside `data/knowledge_base/` and returns the most relevant chunks as grounded context.

Tool execution:

- Once the lead has provided enough information, the agent triggers a mock tool that persists the lead in `data/leads.jsonl`.

Conversation workflow:

- The agent first understands the user request, retrieves relevant knowledge when needed, and moves into discovery mode when buying intent appears.

## Testing

```bash
pytest
```

## Notes

- The implementation is intentionally lightweight and dependency-friendly so it can run locally without external APIs.
- If `GROQ_API_KEY` is set, the app will try Groq first for intent classification and grounded answer synthesis, then fall back to local rules if the API or package is unavailable.
