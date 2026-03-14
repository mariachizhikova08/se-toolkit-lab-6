#!/usr/bin/env python3
import json
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv('.env.agent.secret')

# Project root directory (where agent.py is located)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Maximum tool calls per question
MAX_TOOL_CALLS = 10

# System prompt for the documentation agent
SYSTEM_PROMPT = """You are a documentation assistant for a software engineering toolkit.
You have access to a project wiki with documentation files.

Your task is to answer user questions by searching the wiki files.

Available tools:
1. list_files - List files and directories at a given path
2. read_file - Read contents of a specific file

Strategy:
1. Use list_files to discover what files exist in the wiki directory
2. For Git-related questions, check these files in order: git.md, git-vscode.md, git-workflow.md, github.md
3. Use read_file to read specific files and find the answer
4. If you don't find the answer in the first file, try reading other related files
5. Once you find the answer, provide it with a source reference

Source reference format:
- Include the file path and section anchor (e.g., wiki/git-workflow.md#resolving-merge-conflicts)
- If no specific section, just use the file path (e.g., wiki/git-workflow.md)

Important rules:
- Always include a source field in your final answer
- The source should point to the exact file (and section if applicable) where the answer was found
- Stop calling tools once you have found the answer
- Do not make up information - only use information from the wiki files
- If the first file you read doesn't contain the answer, try other related files

When providing your final answer, structure it like this:
ANSWER: <your answer here>
SOURCE: <file_path>#<section_anchor> or <file_path>
"""

# Tool definitions for LLM function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki')"
                    }
                },
                "required": ["path"]
            }
        }
    }
]


def is_path_safe(relative_path: str) -> bool:
    """
    Check if a relative path is safe (no traversal outside project root).
    
    Args:
        relative_path: The relative path to check
        
    Returns:
        True if path is safe, False otherwise
    """
    # Reject absolute paths
    if os.path.isabs(relative_path):
        return False
    
    # Normalize the path
    normalized = os.path.normpath(relative_path)
    
    # Reject paths with .. traversal
    if '..' in normalized:
        return False
    
    # Resolve the full path
    full_path = os.path.join(PROJECT_ROOT, normalized)
    resolved = os.path.realpath(full_path)
    
    # Ensure the resolved path is within project root
    project_root_resolved = os.path.realpath(PROJECT_ROOT)
    if not resolved.startswith(project_root_resolved):
        return False
    
    return True


def read_file(path: str) -> str:
    """
    Read a file from the project repository.

    Args:
        path: Relative path from project root

    Returns:
        File contents or error message
    """
    if not is_path_safe(path):
        return f"Error: Access denied - path '{path}' is not allowed (security violation)"

    full_path = os.path.join(PROJECT_ROOT, path)

    try:
        if not os.path.exists(full_path):
            return f"Error: File '{path}' does not exist"

        if not os.path.isfile(full_path):
            return f"Error: '{path}' is not a file"

        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str) -> str:
    """
    List files and directories at a given path.

    Args:
        path: Relative directory path from project root

    Returns:
        Newline-separated listing or error message
    """
    if not is_path_safe(path):
        return f"Error: Access denied - path '{path}' is not allowed (security violation)"

    full_path = os.path.join(PROJECT_ROOT, path)

    try:
        if not os.path.exists(full_path):
            return f"Error: Directory '{path}' does not exist"

        if not os.path.isdir(full_path):
            return f"Error: '{path}' is not a directory"

        entries = os.listdir(full_path)
        # Sort entries: directories first, then files
        sorted_entries = sorted(entries, key=lambda x: (not os.path.isdir(os.path.join(full_path, x)), x.lower()))
        return '\n'.join(sorted_entries)

    except Exception as e:
        return f"Error listing directory: {e}"


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    """
    Execute a tool and return the result.
    
    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool
        
    Returns:
        Tool result as string
    """
    if tool_name == "read_file":
        return read_file(args.get("path", ""))
    elif tool_name == "list_files":
        return list_files(args.get("path", ""))
    else:
        return f"Error: Unknown tool '{tool_name}'"


def call_llm(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Call the LLM API with messages and tool definitions.

    Args:
        messages: List of message dictionaries

    Returns:
        LLM response JSON
    """
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
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto"
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    return response.json()


def extract_source_from_answer(answer: str, tool_calls: list[dict[str, Any]]) -> str:
    """
    Extract source reference from the LLM answer or infer from tool calls.

    Args:
        answer: The LLM's text answer
        tool_calls: List of tool calls made

    Returns:
        Source reference string
    """
    # Try to find SOURCE: line in the answer
    lines = answer.split('\n')
    for line in lines:
        if line.strip().startswith('SOURCE:'):
            source = line.replace('SOURCE:', '').strip()
            return source
    
    # Try to find file path patterns in the answer
    import re
    # Look for patterns like wiki/something.md or wiki/something.md#anchor
    pattern = r'(wiki/[\w\-/]+\.md(?:#[\w\-]+)?)'
    matches = re.findall(pattern, answer)
    if matches:
        return matches[0]
    
    # Infer from last read_file tool call
    for tc in reversed(tool_calls):
        if tc.get("tool") == "read_file":
            path = tc.get("args", {}).get("path", "")
            if path:
                return path
    
    return "unknown"


def run_agentic_loop(question: str) -> dict[str, Any]:
    """
    Run the agentic loop to answer a question using tools.

    Args:
        question: User's question

    Returns:
        Result dictionary with answer, source, and tool_calls
    """
    # Initialize messages with system prompt and user question
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    tool_calls_log: list[dict[str, Any]] = []
    tool_call_count = 0

    while tool_call_count < MAX_TOOL_CALLS:
        # Call LLM
        response = call_llm(messages)
        assistant_message = response["choices"][0]["message"]

        # Check for tool calls
        tool_calls: list[dict[str, Any]] = assistant_message.get("tool_calls", [])

        if not tool_calls:
            # No tool calls - this is the final answer
            answer_text = assistant_message.get("content", "")
            source = extract_source_from_answer(answer_text, tool_calls_log)

            return {
                "answer": answer_text,
                "source": source,
                "tool_calls": tool_calls_log
            }

        # Add assistant message with tool calls
        messages.append(assistant_message)

        # Execute each tool call
        for tc in tool_calls:
            tool_call_id = tc.get("id", "")
            function = tc.get("function", {})
            tool_name = function.get("name", "")

            try:
                args: dict[str, Any] = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}

            # Execute the tool
            result = execute_tool(tool_name, args)

            # Log the tool call
            tool_calls_log.append({
                "tool": tool_name,
                "args": args,
                "result": result
            })
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result
            })
            
            tool_call_count += 1
            
            if tool_call_count >= MAX_TOOL_CALLS:
                break
    
    # Max tool calls reached - extract whatever answer we have
    # Make one final LLM call to get a summary answer
    messages.append({
        "role": "system",
        "content": "Maximum tool calls reached. Please provide the best answer you can based on the information gathered so far. Include SOURCE: line with file reference."
    })
    
    try:
        response = call_llm(messages)
        answer_text = response["choices"][0]["message"].get("content", "")
    except Exception:
        answer_text = "Maximum tool calls reached. Partial results available in tool_calls."
    
    source = extract_source_from_answer(answer_text, tool_calls_log)
    
    return {
        "answer": answer_text,
        "source": source,
        "tool_calls": tool_calls_log
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: agent.py \"Your question here\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    try:
        result = run_agentic_loop(question)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
