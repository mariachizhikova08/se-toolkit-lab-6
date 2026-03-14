\# Agent Documentation — Task 1



\## Overview

Simple CLI agent that calls an LLM and returns JSON answers.



\## Architecture

```

User Input → agent.py → LLM API (OpenAI-compatible) → JSON Output

```



\## LLM Provider

\- \*\*Provider\*\*: Qwen Code API (self-hosted on VM)

\- \*\*Model\*\*: `qwen3-coder-plus`

\- \*\*API Endpoint\*\*: `http://10.93.25.242:42005/v1`



\## Configuration

\- API key and settings stored in `.env.agent.secret`

\- Required variables: `LLM\_API\_KEY`, `LLM\_API\_BASE`, `LLM\_MODEL`



\## Usage

```bash

uv run agent.py "Your question here"

```



\## Output Format

```json

{"answer": "...", "tool\_calls": \[]}

```

\- `answer`: текст ответа от LLM

\- `tool\_calls`: пустой массив (заполняется в Task 2)



\## Error Handling

\- All errors logged to stderr

\- Exit code 1 on failure, 0 on success

\- 60-second timeout for API calls

```

