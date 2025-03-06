Based on the information I've gathered, I can now provide a guide on implementing the Model Context Protocol client in an existing LLM interactive chat project.

# Implementing Model Context Protocol Client in an Existing LLM Chat Project

The Model Context Protocol (MCP) allows your LLM chat application to connect with external tools, data sources, and capabilities. Here's how to implement it in your existing project:

## 1. Install the MCP Python SDK

```bash
pip install mcp
# or using uv
uv pip install mcp
```

## 2. Create a Client Implementation

Here's a step-by-step approach to integrate MCP into your chat application:

```python
import asyncio
import sys
from contextlib import AsyncExitStack
from typing import Optional, List, Dict, Any

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp.shared.stdio_params import StdioParams


class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None

    async def connect_to_server(self, server_script_path: str):
        # Create server process parameters
        server_params = StdioParams(
            command=[sys.executable, server_script_path],
            cwd=None  # You can specify working directory if needed
        )
        
        # Connect to the server via stdio
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        # Create a session
        self.session = ClientSession(stdio_transport)
        
        # Initialize the session
        await self.session.initialize({})
        
        # List available tools (optional, but useful for discovery)
        tools_response = await self.session.list_tools()
        print(f"Available tools: {tools_response.tools}")
        
        return self.session
    
    async def process_message(self, user_message: str):
        if not self.session:
            raise RuntimeError("Not connected to an MCP server")
        
        # This is where you'd integrate with your LLM
        # When the LLM returns a response with tool calls:
        tool_calls = self._extract_tool_calls_from_llm_response(llm_response)
        
        # Execute each tool call via MCP
        for tool_call in tool_calls:
            tool_result = await self.session.execute_tool(
                tool_id=tool_call["tool_id"],
                parameters=tool_call["parameters"]
            )
            
            # Pass tool results back to LLM for final response
            final_response = self._get_llm_response_with_tool_results(tool_result)
            
        return final_response
    
    def _extract_tool_calls_from_llm_response(self, llm_response):
        # Implement based on your LLM response format
        # Example with Anthropic Claude format:
        tool_calls = []
        if "<tool>" in llm_response:
            # Parse the tool call from the response
            # This is a simplified example
            tool_sections = llm_response.split("<tool>")[1:]
            for section in tool_sections:
                if "</tool>" in section:
                    tool_content = section.split("</tool>")[0]
                    # Parse the tool content into id and parameters
                    # This depends on your LLM's format
                    tool_id = "example_tool"  # Extract from response
                    parameters = {}  # Extract from response
                    tool_calls.append({
                        "tool_id": tool_id,
                        "parameters": parameters
                    })
        return tool_calls
    
    def _get_llm_response_with_tool_results(self, tool_result):
        # Implement based on your LLM integration
        # Send the tool results back to the LLM for processing
        pass

    async def close(self):
        if self.session:
            await self.session.shutdown()
        await self.exit_stack.aclose()


# Example usage
async def main():
    client = MCPClient()
    try:
        # Connect to an MCP server
        await client.connect_to_server("path/to/your/server.py")
        
        # Process a user message
        response = await client.process_message("Can you check the weather in San Francisco?")
        print(response)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 3. Integrate with Your Existing Chat Application

To integrate this into your existing chat application:

1. **Initialize the MCP Client**: Start the MCP client when your application starts.

2. **Connect to MCP Servers**: Add functionality to discover and connect to MCP servers.

3. **Process Messages Through MCP**: Modify your message processing pipeline to route tool calls through MCP:

```python
# In your existing chat application
async def handle_user_message(user_message):
    # 1. Get initial LLM response
    llm_response = await get_llm_response(user_message)
    
    # 2. Check if response contains tool calls
    if has_tool_calls(llm_response):
        # 3. Process tool calls through MCP
        mcp_response = await mcp_client.process_message(llm_response)
        
        # 4. Return the final response with tool results
        return mcp_response
    else:
        # No tool calls, return the original response
        return llm_response
```

## 4. Managing MCP Server Communication

The MCP client communicates with servers using a standard protocol. You can:

1. **Connect to Built-in Servers**: Include MCP servers with your application

2. **Connect to User-Selected Servers**: Allow users to specify server paths

3. **Support Multiple Servers**: Connect to multiple MCP servers for different capabilities

## 5. Handling Tool Calls From Different LLMs

Different LLMs format tool calls differently. Implement parsers for your specific LLM:

- **Anthropic Claude**: Uses `<tool>...</tool>` tags
- **OpenAI**: Uses JSON function calling format 
- **Other LLMs**: Implement according to their specific formats

## 6. Error Handling and Session Management

Add proper error handling for MCP communication:

```python
try:
    response = await mcp_client.session.execute_tool(tool_id, parameters)
except Exception as e:
    # Handle MCP errors appropriately
    print(f"MCP tool execution error: {e}")
    # Provide fallback or error message to user
```

## 7. Testing Your Integration

Test your MCP integration with simple servers:

```bash
# Run your chat application with a test MCP server
python your_chat_app.py --mcp-server=example_mcp_server.py
```

## Resources

- Official MCP Python SDK: [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- MCP Specification: [spec.modelcontextprotocol.io](https://spec.modelcontextprotocol.io)
- Example MCP Servers: [modelcontextprotocol.io/servers](https://modelcontextprotocol.io/servers)

By following this guide, you'll be able to enhance your LLM chat application with MCP capabilities, allowing it to securely access external tools and data sources in a standardized way.
