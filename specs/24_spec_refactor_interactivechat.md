# Extract Message Handling Logic from InteractiveChat

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives
- Reduce complexity of the InteractiveChat class by extracting message handling logic
- Create a MessageHandler class to process messages and responses
- Create a CommandHandler class to handle chat commands
- Maintain all existing functionality while improving code organization
- Ensure backward compatibility with the rest of the codebase

## Contexts
- modules/chat/interactive.py: Contains the InteractiveChat class that needs refactoring
- modules/llm/base.py: Contains the BaseLLMService class used by the message handler
- modules/agents/manager.py: Contains the AgentManager class used by the command handler
- modules/chat/constants.py: Contains color constants and other shared values

## Low-level Tasks
1. CREATE modules/chat/message_handler.py:
   - Create a MessageHandler class that handles processing user messages and assistant responses
   - Implement methods for processing file commands, user messages, and assistant responses
   - Extract streaming response logic from InteractiveChat._stream_assistant_response
   - Include proper error handling and token tracking

2. CREATE modules/chat/command_handler.py:
   - Create a CommandHandler class that processes all commands (e.g., /clear, /copy, /think)
   - Extract command handling logic from InteractiveChat methods
   - Implement methods for each command type
   - Ensure command handler returns appropriate status flags

3. UPDATE modules/chat/interactive.py:
   - Modify InteractiveChat to use the new MessageHandler and CommandHandler classes
   - Update _process_user_input to delegate to CommandHandler
   - Update _stream_assistant_response to delegate to MessageHandler
   - Maintain backward compatibility with existing method signatures
   - Ensure all existing functionality continues to work

4. CREATE modules/chat/types.py:
   - Define common types and data structures used across chat modules
   - Create a CommandResult class to standardize command handling results
   - Define enums for command types and message types

5. CREATE tests/chat/test_message_handler.py:
   - Implement unit tests for the MessageHandler class
   - Test processing of different message types
   - Test error handling scenarios

6. CREATE tests/chat/test_command_handler.py:
   - Implement unit tests for the CommandHandler class
   - Test handling of different command types
   - Test command result flags
