# Plan for Task 1: Call an LLM from Code

## LLM Provider
- Provider: Qwen Code API (self-hosted on VM)
- Model: qwen3-coder-plus
- API Base: http://10.93.25.242:42005/v1

## Agent Structure
1. Parse command-line argument (user question)
2. Load API config from .env.agent.secret
3. Send request to LLM via OpenAI-compatible API
4. Parse response and format as JSON
5. Output JSON to stdout, logs to stderr

## Output Format
{"answer": "...", "tool_calls": []}