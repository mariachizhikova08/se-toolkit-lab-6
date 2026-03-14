#!/usr/bin/env python3
import subprocess
import json
import os
import sys


def test_agent_output():
    """Проверяет, что agent.py возвращает валидный JSON с нужными полями."""

    # Устанавливаем PYTHONUTF8=1 для корректной обработки Unicode
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        ["uv", "run", "agent.py", "What is 2+2?"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env
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


def test_agent_read_file_tool():
    """
    Проверяет, что агент использует read_file для вопроса о merge conflict.
    Ожидается, что агент прочитает файлы из wiki/ (git-workflow.md, git.md, или git-vscode.md).
    """
    # Устанавливаем PYTHONUTF8=1 для корректной обработки Unicode
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        ["uv", "run", "agent.py", "How do you resolve a merge conflict?"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env
    )

    # Проверяем код выхода
    assert result.returncode == 0, f"Exit code: {result.returncode}, stderr: {result.stderr}"

    # Парсим stdout как JSON
    output = json.loads(result.stdout.strip())

    # Проверяем обязательные поля
    assert "answer" in output, "Missing 'answer' field"
    assert "source" in output, "Missing 'source' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Проверяем, что был вызван read_file
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tool_names, "Expected 'read_file' in tool_calls"

    # Проверяем, что source содержит wiki/ и .md
    source = output["source"].lower()
    assert "wiki/" in source and ".md" in source, \
        f"Expected wiki path in source, got: {output['source']}"

    print("Test test_agent_read_file_tool passed!", file=sys.stderr)


def test_agent_list_files_tool():
    """
    Проверяет, что агент использует list_files для вопроса о файлах в wiki.
    """
    # Устанавливаем PYTHONUTF8=1 для корректной обработки Unicode
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        ["uv", "run", "agent.py", "What files are in the wiki?"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env
    )

    # Проверяем код выхода
    assert result.returncode == 0, f"Exit code: {result.returncode}, stderr: {result.stderr}"

    # Парсим stdout как JSON
    output = json.loads(result.stdout.strip())

    # Проверяем обязательные поля
    assert "answer" in output, "Missing 'answer' field"
    assert "source" in output, "Missing 'source' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Проверяем, что был вызван list_files
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "list_files" in tool_names, "Expected 'list_files' in tool_calls"

    print("Test test_agent_list_files_tool passed!", file=sys.stderr)


if __name__ == "__main__":
    test_agent_output()
    test_agent_read_file_tool()
    test_agent_list_files_tool()
    print("All tests passed!", file=sys.stderr)
