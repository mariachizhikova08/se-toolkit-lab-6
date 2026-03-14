# Plan for Task 2: The Documentation Agent

## Overview
Build an agentic loop that allows the LLM to call tools (`read_file`, `list_files`) to navigate the project wiki and find answers with source references.

## Tool Definitions

### read_file
**Purpose**: Read contents of a file from the project repository.

**Schema**:
```json
{
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
```

**Implementation**:
- Accept `path` parameter (relative to project root)
- Security: Reject paths with `..` traversal or absolute paths
- Resolve full path: `project_root / path`
- Verify resolved path is within project directory
- Return file contents or error message

### list_files
**Purpose**: List files and directories at a given path.

**Schema**:
```json
{
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
```

**Implementation**:
- Accept `path` parameter (relative to project root)
- Security: Reject paths with `..` traversal or absolute paths
- Resolve full path: `project_root / path`
- Verify resolved path is within project directory and is a directory
- Return newline-separated listing of entries

## Path Security Strategy

1. **Normalize input**: Use `os.path.normpath()` to normalize the path
2. **Reject absolute paths**: Check `os.path.isabs()` - reject if absolute
3. **Reject traversal**: Check for `..` in normalized path
4. **Resolve full path**: `os.path.join(project_root, relative_path)`
5. **Verify containment**: Ensure resolved path starts with `project_root`
6. **Handle errors gracefully**: Return error message instead of raising exception

## Agentic Loop Implementation

### Flow
```
1. Initialize messages with system prompt + user question
2. Loop (max 10 iterations):
   a. Call LLM with messages + tool definitions
   b. If LLM returns tool_calls:
      - Execute each tool
      - Append tool results as 'tool' role messages
      - Continue loop
   c. If LLM returns text answer (no tool_calls):
      - Extract answer and source
      - Break loop with final answer
3. Return JSON with answer, source, tool_calls
```

### System Prompt Strategy
The system prompt will instruct the LLM to:
1. Use `list_files` to discover wiki files when needed
2. Use `read_file` to read specific wiki files and find answers
3. Always include a source reference (file path + section anchor) in the final answer
4. Stop calling tools once the answer is found
5. Never call more than 10 tools total

### Message Format
```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": question}
]

# After tool calls:
messages.append({
    "role": "assistant",
    "content": None,
    "tool_calls": [...]
})
messages.append({
    "role": "tool",
    "tool_call_id": "...",
    "content": tool_result
})
```

## Output Format
```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "git-workflow.md\n..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}
```

## Source Extraction Strategy
- Parse LLM answer for file path references (e.g., `wiki/git-workflow.md`)
- Look for section anchors (e.g., `#resolving-merge-conflicts`)
- If no explicit source, infer from last `read_file` call
- Format: `{file_path}#{section_anchor}` or just `{file_path}`

## Error Handling
- Tool errors: Return error message as tool result, continue loop
- LLM errors: Log to stderr, return error JSON
- Max iterations reached: Use whatever answer is available
- Path security violations: Return error message, don't execute

## Testing Strategy
1. Test `read_file` tool with valid path
2. Test `read_file` with path traversal (security)
3. Test `list_files` tool with valid directory
4. Test agentic loop with question requiring file discovery
5. Test source extraction from answer
