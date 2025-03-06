## IMPLEMENTATION NOTES AND BEST PRACTICES

""" IMPLEMENTATION NOTES

1. EXTENDED THINKING MODE

   - Claude 3.7 Sonnet's extended thinking gives the model enhanced reasoning
     capabilities
   - Creates 'thinking' content blocks with step-by-step reasoning before
     responding
   - Thinking blocks are cryptographically signed to verify authenticity
   - Occasionally, some thinking may be redacted for safety (as
     'redacted_thinking' blocks)
   - Budget control: Set 'budget_tokens' parameter to control thinking depth
     (1,024 to 32K+)
   - The thinking budget is a target rather than a strict limit

2. STREAM HANDLING

   - Each streaming event has a specific type that must be handled differently
   - Main event types: message_start, content_block_start, content_block_delta,
     content_block_stop, message_delta, message_stop
   - Delta types include: thinking_delta, text_delta, tool_use_delta,
     signature_delta
   - Thinking content may arrive in "chunky" delivery patterns (alternating
     large chunks with smaller, token-by-token delivery)
   - Stream processing should be robust to connection issues and timeout
     considerations

3. TOOL USE WITH THINKING

   - The first user request will typically result in thinking blocks followed by
     tool use
   - Tool results must be sent back with the original thinking blocks preserved
   - After receiving tool results, Claude won't generate new thinking blocks in
     that turn
   - Claude will not output another thinking block until after the next
     non-tool_result user turn
   - Preserving thinking blocks during tool use is CRITICAL for maintaining
     reasoning flow

4. REDACTED THINKING

   - When Claude's internal reasoning is flagged by safety systems, some
     thinking may be encrypted
   - These appear as 'redacted_thinking' blocks with a 'data' field containing
     encrypted content
   - Must be passed back unchanged to Claude in multi-turn conversations
   - Your application should handle these blocks gracefully without breaking the
     UI

5. TOKEN MANAGEMENT
   - Extended thinking tokens count towards output tokens and are billed
     accordingly
   - Previous thinking blocks from earlier turns don't count toward input token
     limits
   - The API automatically strips thinking blocks from previous turns when
     calculating context usage
   - max_tokens (which includes thinking budget) is enforced as a strict limit
     in Claude 3.7

## BEST PRACTICES

1. THINKING BUDGET OPTIMIZATION

   - Start with minimum budget (1,024 tokens) and increase incrementally based
     on task complexity
   - For complex reasoning tasks, consider budgets of 8K-16K tokens
   - For very complex problems (math, coding, analysis), consider 16K-32K
     budgets
   - For budgets above 32K, use batch processing to avoid networking issues
   - Be mindful that higher budgets increase response time and token usage

2. TOOL DEFINITION QUALITY

   - Provide detailed descriptions for each tool to help Claude decide when to
     use it
   - Include clear parameter descriptions and proper JSON schema validation
   - Consider Claude 3.7 Sonnet or Claude 3 Opus for complex tools and ambiguous
     queries
   - For Sonnet, explicit prompting for step-by-step reasoning can improve tool
     selection

3. ERROR HANDLING

   - Implement robust error handling for network issues and API errors
   - Handle partial JSON in streaming tool arguments by accumulating fragments
   - Handle redacted thinking blocks gracefully in your UI
   - Consider implementing timeouts and retries for long-running operations
   - Add proper error handling for tool execution failures

4. USER EXPERIENCE

   - Consider showing thinking content in a collapsible UI element
   - Provide clear indications when Claude is "thinking" vs. using tools
   - For redacted thinking blocks, display a simple explanation: "Some reasoning
     has been automatically encrypted for safety reasons"
   - Implement proper loading states during tool execution
   - Consider connection keep-alive for multiple requests

5. PERFORMANCE CONSIDERATIONS

   - For tasks requiring large thinking budgets (>32K), use batch processing
   - Be aware that streaming with thinking enabled may result in "chunky"
     delivery patterns
   - Consider using a connection pool for high-volume applications
   - Implement backpressure handling for slow consumers
   - Buffer output appropriately for smooth UI rendering

6. TOKEN EFFICIENCY

   - Only enable extended thinking when needed for complex tasks
   - Use the token counting API to monitor usage
   - Consider caching frequent responses
   - Be aware that tool definitions add to input token counts
   - System prompts with extended thinking have an additional ~28-29 token
     overhead

7. SECURITY CONSIDERATIONS

   - Never modify thinking or redacted_thinking blocks
   - Always pass cryptographic signatures back unchanged
   - Validate tool inputs before execution to prevent injection attacks
   - Consider implementing rate limiting for tool calls
   - Add proper authentication and authorization for sensitive tools

8. TESTING AND MONITORING
   - Implement comprehensive logging for debugging
   - Test with a variety of thinking budgets to find optimal settings
   - Monitor token usage and costs
   - Consider implementing A/B testing for different thinking budget
     configurations
   - Create test cases for different types of queries and tool combinations """

## Implementations Example

```python
import json
import asyncio
from anthropic import Anthropic

# Create Anthropic client
client = Anthropic()

# Tool definitions
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or location"},
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    }
]

# Tool implementations
async def get_weather(location, unit="celsius"):
    # In a real app, this would call a weather API
    weather_data = {
        "Paris": {"temp": 22, "condition": "Sunny"},
        "London": {"temp": 18, "condition": "Cloudy"},
        "New York": {"temp": 25, "condition": "Partly cloudy"}
    }

    if location not in weather_data:
        return f"Weather data for {location} not available"

    temp = weather_data[location]["temp"]
    if unit == "fahrenheit":
        temp = (temp * 9/5) + 32

    return f"{temp}° {unit}, {weather_data[location]['condition']}"

async def process_streaming_with_thinking_and_tools():
    # Initial request
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=20000,
        stream=True,
        thinking={
            "type": "enabled",
            "budget_tokens": 16000
        },
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather in Paris and London?"}
        ]
    )

    # Process the streaming response
    thinking_blocks = []
    tool_use_blocks = []
    text_blocks = []
    current_block = None
    current_block_index = None
    current_block_type = None

    thinking_content = ""
    assistant_response = ""
    tool_calls = []

    for event in response:
        event_type = getattr(event, 'type', None)

        # Handle message start
        if event_type == 'message_start':
            print("Assistant is responding...")

        # Handle content block start
        elif event_type == 'content_block_start':
            current_block_index = event.index
            current_block_type = event.content_block.type

            if current_block_type == 'thinking':
                current_block = {"type": "thinking", "thinking": "", "signature": ""}
                print("\n[Thinking started]")
            elif current_block_type == 'redacted_thinking':
                current_block = {"type": "redacted_thinking", "data": event.content_block.data}
                thinking_blocks.append(current_block)
                current_block = None
                print("\n[Redacted thinking block received]")
            elif current_block_type == 'tool_use':
                current_block = {
                    "type": "tool_use",
                    "id": getattr(event.content_block, 'id', None),
                    "name": getattr(event.content_block, 'name', None),
                    "input": {}
                }
                print("\n[Tool use started]")
            elif current_block_type == 'text':
                current_block = {"type": "text", "text": ""}
                print("\n[Response started]")

        # Handle content deltas
        elif event_type == 'content_block_delta':
            delta_type = getattr(event.delta, 'type', None)

            if delta_type == 'thinking_delta' and current_block and current_block_type == 'thinking':
                thinking_part = event.delta.thinking
                current_block["thinking"] += thinking_part
                thinking_content += thinking_part
                print(f"{thinking_part}", end="")

            elif delta_type == 'signature_delta' and current_block and current_block_type == 'thinking':
                current_block["signature"] = event.delta.signature

            elif delta_type == 'tool_use_delta' and current_block and current_block_type == 'tool_use':
                if hasattr(event.delta, 'id') and event.delta.id:
                    current_block["id"] = event.delta.id
                if hasattr(event.delta, 'name') and event.delta.name:
                    current_block["name"] = event.delta.name
                if hasattr(event.delta, 'input') and event.delta.input:
                    # Handle potentially partial JSON
                    for key, value in event.delta.input.items():
                        if key in current_block["input"]:
                            current_block["input"][key] += value
                        else:
                            current_block["input"][key] = value

            elif delta_type == 'text_delta' and current_block and current_block_type == 'text':
                content = event.delta.text
                current_block["text"] += content
                assistant_response += content
                print(f"{content}", end="")

        # Handle block stop - finalize current block
        elif event_type == 'content_block_stop':
            if current_block:
                if current_block_type == 'thinking':
                    thinking_blocks.append(current_block)
                    print("\n[Thinking complete]")
                elif current_block_type == 'tool_use':
                    tool_use_blocks.append(current_block)
                    tool_calls.append({
                        "id": current_block["id"],
                        "name": current_block["name"],
                        "input": current_block["input"]
                    })
                    print(f"\n[Tool call completed: {current_block['name']}]")
                elif current_block_type == 'text':
                    text_blocks.append(current_block)
                    print("\n[Response block complete]")

                current_block = None
                current_block_type = None

        # Handle message completion
        elif event_type == 'message_stop':
            print("\n\n[Response complete]")

    # Execute any tool calls
    if tool_calls:
        print(f"\nExecuting {len(tool_calls)} tool call(s)...")
        tool_results = []

        for tool_call in tool_calls:
            try:
                if tool_call["name"] == "get_weather":
                    result = await get_weather(**tool_call["input"])
                else:
                    result = f"Unknown tool: {tool_call['name']}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": result
                })
                print(f"Tool result for {tool_call['name']}: {result}")
            except Exception as e:
                error_message = f"Error executing tool {tool_call['name']}: {str(e)}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": error_message,
                    "is_error": True
                })
                print(error_message)

        # Continue conversation with tool results
        # CRITICAL: Include original thinking blocks when providing tool results
        print("\nContinuing conversation with tool results...")
        continuation = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=20000,
            stream=True,
            thinking={
                "type": "enabled",
                "budget_tokens": 16000
            },
            tools=tools,
            messages=[
                {"role": "user", "content": "What's the weather in Paris and London?"},
                {"role": "assistant", "content": thinking_blocks + tool_use_blocks},
                {"role": "user", "content": tool_results}
            ]
        )

        # Process continuation response
        final_response = ""
        for chunk in continuation:
            if hasattr(chunk, 'type') and chunk.type == 'content_block_delta':
                if chunk.delta.type == 'text_delta':
                    content = chunk.delta.text
                    final_response += content
                    print(content, end="")

        print("\n\n[Final response complete]")
        return final_response

    return assistant_response

# Run the example
async def main():
    result = await process_streaming_with_thinking_and_tools()
    print(f"\nFinal result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```
