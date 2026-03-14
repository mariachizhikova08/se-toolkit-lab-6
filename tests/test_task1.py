#!/usr/bin/env python3
import subprocess
import json
import sys

def test_agent_output():
    """Проверяет, что agent.py возвращает валидный JSON с нужными полями."""
    
    result = subprocess.run(
        ["uv", "run", "agent.py", "What is 2+2?"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Проверяем код выхода
    assert result.returncode == 0, f"Exit code: {result.returncode}, stderr: {result.stderr}"
    
    # Парсим stdout как JSON
    output = json.loads(result.stdout.strip())
    
    # Проверяем обязательные поля
    assert "answer" in output, "Missing 'answer' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"
    
    print("Test passed!", file=sys.stderr)

if __name__ == "__main__":
    test_agent_output()