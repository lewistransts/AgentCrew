# Add interactive chat using stream mode of Claude

> Ingest the information from this file, implement the Low-level Tasks, and
> generate the code that will satisfy Objectives

## Objectives

- include tools to llm anthropic call to allow claude call the tools
- tools should be injected to llm service with a list of tool definition and
  handler
- handle stream message for `stop_reason` is `tool_use` for processing with
  tools
- continue the conversation with a user message contains `tool_result`
- Use scraping service as a first tool

## Contexts

- main.py: main python file that use click for command line
- modules/anthropic/service.py: Main service for process with anthropic api
- modules/chat/interactive.py: interactive chat service implementation
- ./ai_docs/tool-use.md: document for how implement tool_use

## Low-level Tasks

1. UPDATE anthropic/service.py that handle message stream to anthropic with
   tool-use
2. UPDATE main.py to injected scraping service as a tool with this definition

```json
{
  "name": "scrap_url",
  "description": "Scrap the content on given URL",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "the url that will be scraped"
      }
    },
    "required": ["url"]
  }
}
```
