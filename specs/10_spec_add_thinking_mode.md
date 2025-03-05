# Implement Dynamic Thinking mode for Claude

> Ingest the information from this file, implement the Low-level Tasks, and
> generate the code that will satisfy Objectives

## Objectives

- Add thinking config to stream call
- Update process chunk to include redacted thinking block when using tool_use
- Update process chunk to print out thinking data
- Update chat interactive to show thinking data
- Thinking data should also show for reasoner model of openai and groq
- Add `/think <budget_token>` for switch to thinking mode for claude.
  `budget_token` must higher than 1024. If user set below 1024, change it to
  1024 with a warning
- Disable think mode with `/think 0`
- For Groq and OpenAI, print "Not Supported" when call `/think`

## Context

- `./modules/anthropic/service.py:` anthropic implementation
- `./modules/llm/base.py:` Abstract class for anthropic, groq, OpenAI
- `./modules/openai/service.py:` OpenAI implementation
- `./modules/groq/service.py:` Groq Implementation
- `modules/chat/interactive.py`: Interactive chat will store conversation after
  each response cycle

## Low-level Tasks

1. Update `./modules/chat/interactive.py`:

```aider
UPDATE main chat loop to include new command /think
UPDATE _stream_assistant_response to process thinking data returned from llm service
UPDATE _stream_assistant_response to include thinking_data when tool_use call

```

2. UPDATE `./modules/llm/base.py`:

```aider
ADD set_think(budget_token) function that will be called when user type command /think
UPDATE process_stream_chunk(message) to return think_content
```

3. UPDATE `./modules/anthropic/service.py`:

```aider
ADD set_think(budget_token) function to add "thinking" option to stream params
UPDATE process_stream_chunk(message) to return think_content
```

3. UPDATE `./modules/openai/service.py`:

```aider
ADD set_think(budget_token) function print not supported
UPDATE process_stream_chunk(message) to return think_content
```

4. UPDATE `./modules/groq/service.py`:

```aider
ADD set_think(budget_token) function print not supported
UPDATE process_stream_chunk(message) to return think_content
```
