# Implement Memory for store conversation and tool for retrieving

> Ingest the information from this file, implement the Low-level Tasks, and
> generate the code that will satisfy Objectives

## Objectives

- Create a memory service to store conversation with user and assistant
  responses from chat service using ChromaDB
- Use ChromaDB in persistent mode
- ChromaDB embed models only support 200 tokens so we need to cut the
  conversation into chunks with overlap words, start with 200 words each chunks
  and 30 words overlap. Chunks should have linked together
- Create a tool allow LLM models can retrieve memory using keywords
- Create a function for clean-up the memory when starting the chat app. Remove
  conversation that more than 1-month old

## Context

- `modules/memory/tool.py`: Main file for managing tool registrations and
  executions
- `modules/memory/service.py`: New file to be created for Memory implementation
  using Chroma
- `modules/chat/interactive.py`: Interactive chat will store conversation after
  each response cycle
- `main.py`: Add clean-up memory function at beginning of the chat

## Low-level Tasks

1. **Create a new module for Memory implementation**

   - Create `modules/memory/service.py` file
   - Using `chromaDB`
   - Implement the chunks process before store to chromaDB.
   - Implement the retrieve function

2. **Create tool definition and handler for retrieve the memory**

   - Create a new tool call `retrieve_memory` with one required string argument
     is `keywords`
   - Tool should support both Claude and Groq
   - Create handler function

3. **Update chat interactive to store the conversation after every cycles**

   - Update the main loop to store the conversation after every cycles
   - Only store the user input and the assistant_response

4. **Update `main.py` for clean-up memory**

   - Update `main.py` to call memory service to clean-up memory
