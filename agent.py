import sys
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.agent.secret')

def call_llm(question: str) -> dict:
    
    api_key = os.getenv('LLM_API_KEY')
    api_base = os.getenv('LLM_API_BASE')
    model = os.getenv('LLM_MODEL')
    
    url = f"{api_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question}
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    
    return {
        "answer": answer,
        "tool_calls": []
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: agent.py \"Your question here\"", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    
    try:
        result = call_llm(question)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()