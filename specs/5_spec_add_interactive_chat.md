# Add interactive chat using stream mode of Claude

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives

- Create `chat` cli command for start interactive chat session
- `chat` command should have argument to initial session with file using `--files` or with message ussing `--message`

## Contexts

- main.py: main python file that use click for command line
- modules/anthropic.py: new module for integrate with anthropic api
- ./ai_docs/messages_stream.md: stream message documentation for anthropic

## Low-level Tasks

1. UPDATE main.py to create `chat` command with `--files` and `--message`
3. UPDATE anthropic that handle message stream to anthropic
