# Tool Use with Claude

Claude can interact with client-side tools and functions, expanding its
capabilities to perform various tasks. Tools are specified by developers in API
requests and executed on the client side.

## Tool Use Process

1. **Provide tools and prompt**: Define tools with names, descriptions, and
   input schemas in your API request
2. **Claude decides to use a tool**: Returns a response with
   `stop_reason: "tool_use"` and a formatted tool use request
3. **Execute the tool**: Extract tool name and input, run the corresponding code
   on your side
4. **Return results**: Continue conversation with a new `user` message
   containing `tool_result`

## Implementation Details

### Choosing a Model

- **Best for complex tools**: Claude 3.7 Sonnet, Claude 3.5 Sonnet, Claude 3
  Opus
- **For straightforward tools**: Claude 3.5 Haiku, Claude 3 Haiku

### Tool Specification

Each tool requires:

- `name`: Must match regex `^[a-zA-Z0-9_-]{1,64}$`
- `description`: Detailed explanation of the tool's purpose
- `input_schema`: JSON Schema object defining parameters

### Best Practices

- Provide extremely detailed descriptions (3-4 sentences minimum)
- Explain what the tool does, when to use it, parameter meanings, and
  limitations
- Prioritize descriptions over examples

### Controlling Claude's Output

- **Force tool use**: Set `tool_choice` to
  `{"type": "tool", "name": "tool_name"}`
- **JSON mode**: Use tools to get JSON output following a schema
- **Chain of thought**: Claude can show reasoning process before using tools
- **Disable parallel tool use**: Set `disable_parallel_tool_use=true`

### Handling Responses

When Claude uses a tool, you'll receive:

- `id`: Unique identifier for the tool use
- `name`: Name of the tool
- `input`: Object with parameters for the tool

Return results in a `tool_result` content block with:

- `tool_use_id`: Matching the original tool use ID
- `content`: The result (string or content blocks)
- `is_error` (optional): Set to `true` if execution failed

## Pricing

Tool use is priced based on total tokens, including:

- `tools` parameter (names, descriptions, schemas)
- `tool_use` content blocks
- `tool_result` content blocks
- Tool use system prompt (varies by model, ~159-530 tokens)

## Common Patterns

- Single tool usage
- Multiple tools
- Sequential tool chains
- JSON schema enforcement
- Chain-of-thought reasoning

For best results, provide comprehensive tool descriptions and ensure all
required parameters are available in the user's request or can be reasonably
inferred.

