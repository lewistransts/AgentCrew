# AI Multi-Agent Interactive System

A sophisticated command-line tool that provides an enhanced interactive AI experience through a multi-agent architecture and support for multiple LLM providers, featuring specialized agents, intelligent handoffs, file integration, web capabilities, and a modular extension system.

## Core Architecture

### Multi-Agent System

This system implements a multi-agent architecture with specialized agents for different domains:

- **Documentation Agent**: Expert in creating clear technical documentation, user guides, and explanations
- **Architect Agent**: Specializes in software architecture design, system planning, and technical decision-making
- **Tech Lead Agent**: Focuses on code implementation, debugging, and programming tasks

The system intelligently routes tasks to the appropriate agent and features seamless **agent handoffs** when a conversation requires different expertise. This allows for:

- Domain-specialized reasoning and responses
- Continuity of context during complex multi-domain tasks
- Improved problem-solving through agent collaboration

### Multi-Provider LLM Integration

The system supports multiple LLM providers through a unified interface:

- **Anthropic's Claude**: State-of-the-art reasoning and task execution
- **OpenAI's GPT Models**: Advanced language understanding and generation
- **Groq's LLMs**: High-performance inference options

Key multi-model capabilities:

- Dynamic model switching during sessions with the `/model` command
- Provider-specific optimizations and features
- Standardized message transformation between providers
- Consistent tool integration across all models

## Key Features

- **Interactive Chat**: Rich conversation interface with various AI models
- **File Integration**: Include PDFs and text files directly in conversations
- **Web Capabilities**: Fetch content, perform searches, and extract information from the web
- **Tool Ecosystem**: Extensible set of tools for specialized tasks
- **Keyboard Shortcuts**: Efficient message editing and response management
- **Persistent Memory**: Cross-conversation knowledge retention and retrieval
- **Code Analysis**: Deep analysis of code structure in repositories

## Agent System Details

### Agent Manager

The system employs a centralized Agent Manager that:

- Maintains the registry of available specialized agents
- Handles selection of the appropriate agent for each task
- Manages the handoff process between agents
- Ensures context preservation during transitions

### Agent Handoff Mechanism

The intelligent handoff system allows seamless transitions between specialized agents:

1. The current agent identifies when a different expertise is required
2. A handoff request is initiated with context preservation
3. The appropriate specialized agent is activated
4. Conversation continues with maintained context but specialized capabilities

### Agent Activation

Each agent features:

- A specialized system prompt optimized for its domain
- Specific tools relevant to its expertise
- Custom reasoning patterns suited to its specialty

## LLM Provider Integration

The system implements a unified service layer that:

- Standardizes interactions across different LLM providers
- Transforms messages between provider-specific formats
- Handles provider-specific authentication and API interactions
- Manages tool registration and execution for each provider

### Provider-Specific Features

- **Claude (Anthropic)**: Extended thinking mode for complex reasoning
- **GPT (OpenAI)**: Advanced tool use and function calling
- **Groq**: High-performance inference for faster responses

## Additional Capabilities

- **Web Content Processing**: Fetch and process web content as markdown
- **Web Search**: Search the internet for current information
- **Web Content Extraction**: Extract and analyze content from specific URLs
- **YouTube Integration**: Extract subtitles and chapter information
- **Model Context Protocol (MCP)**: Connect to MCP-compatible servers to extend AI capabilities
- **AI Summarization & Explanation**: Process complex content into summaries or explanations
- **Memory System**: Store, retrieve, and manage conversation history
- **Code Structure Analysis**: Generate structural maps of source code

## Chat Features

- **File Integration**: Include files in your conversation
- **Web Integration**: Ask the AI to scrape URLs or search the web directly
- **Copy Responses**: Easily copy AI responses to your clipboard with Alt+C
- **Multiline Input**: Write complex messages with proper formatting
- **Code Analysis**: Analyze and understand the structure of code repositories

## Extended Thinking Mode

The system supports extended thinking capability (currently only with Claude), which allows the AI to:

- Work through complex problems step-by-step
- Show its reasoning process before providing a final answer
- Allocate a specific token budget for the thinking process

Enable thinking mode during chat with `/think <budget>` command, where budget is the token allocation (minimum 1024 tokens).

## Chat Commands

During an interactive chat session, you can use these commands:

- `/file <file_path>` - Include a file in your message
- `/clear` - Clear the conversation history
- `/think <budget>` - Enable extended thinking mode with specified token budget (min 1024)
- `/think 0` - Disable thinking mode
- `/model <model_id>` - Switch to a different AI model during your chat session
- `/models` - List all available models you can switch to
- `/agent <agent_name>` - Switch to a different specialized agent
- `/agents` - List all available specialized agents
- `exit` or `quit` - End the chat session
- Press `Enter` for a new line, `Ctrl+S` to submit your message
- Press `Alt+C` to copy the latest assistant response to clipboard

## Memory System

The tool includes a persistent memory system that:

- Automatically stores all conversations
- Allows the AI to retrieve relevant past conversations using the `retrieve_memory` tool
- Automatically cleans up conversations older than one month
- Intelligently chunks and stores conversations for efficient retrieval

## Roadmap

The following features are planned for future releases:

### Enhanced Assistant Capabilities

- [x] **Web Search Integration**: Allow AI to search the web for real-time information
- [x] **YouTube Integration**: Extract subtitles and chapters from YouTube videos
- [x] **Conversation Memory**: Store and retrieve past conversations
- [x] **Code Analysis**: Analyze code structure in git repositories
- [ ] **Bash Command Execution**: Enable running system commands directly from the chat
- [ ] **File Manipulation**: Create, edit, and manage files through chat commands
- [ ] **Enhanced Agent Specialization**: More domain-specific agents with deeper expertise

### Advanced Personalization

- [ ] **Custom Instructions**: Save and load different instruction sets for various use cases
- [ ] **Enhanced Memory Management**: Configure memory retention periods and retrieval preferences
- [ ] **Agent Customization**: Create and configure custom specialized agents

### Technical Improvements

- [x] **Model Context Protocol (MCP) Support**: Implement MCP for improved context management
- [x] **Command-line Thinking Mode Options**: Enable and configure thinking mode with the `/think` command
- [ ] **Streaming Optimizations**: Enhance response speed and token efficiency
- [ ] **Local Model Support**: Add compatibility with locally-hosted models
- [ ] **Advanced Memory Indexing**: Improve memory retrieval accuracy and performance
- [ ] **Multi-Agent Collaboration**: Enable multiple agents to work together on complex tasks

### User Experience

- [ ] **Session Management**: Save, resume, and manage multiple conversation threads
- [ ] **UI Improvements**: Enhanced terminal interface with better visualization options
- [ ] **Configuration Profiles**: Create and switch between different tool configurations
- [ ] **Memory Visualization**: Browse and manage stored conversations
- [ ] **Agent Performance Metrics**: Track and analyze agent effectiveness

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) for package manager
- An Anthropic API key (for Claude AI features)
- A Groq API key (optional, for Groq LLM features)
- An OpenAI API key (optional, for GPT features)
- A Firecrawl API key (for web scraping features)
- A Tavily API key (for web search features)

### Setup

1. Clone this repository:

   ```
   git clone https://github.com/daltonnyx/swissknife.git
   cd swissknife
   ```

2. Install the package:

   ```
   uv sync
   ```

3. Create a `.env` file in the project root with your API keys:

   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   OPENAI_API_KEY=your_openai_api_key(optional)
   GROQ_API_KEY=your_groq_api_key(optional)
   FC_API_KEY=your_firecrawl_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

## Usage

### Start an Interactive Chat

```bash
uv run main.py chat
```

### Start a Chat with an Initial Message

```bash
uv run main.py chat --message "Hello, I need help with software architecture"
```

### Include Files in Your Chat

```bash
uv run main.py chat --files document.pdf --files code.py
```

### Start a Chat with Different Providers

```bash
# Use Claude models from Anthropic
uv run main.py chat --provider claude

# Use LLM models from Groq
uv run main.py chat --provider groq

# Use GPT models from OpenAI
uv run main.py chat --provider openai
```

### Start with a Specific Agent

```bash
# Start with the Architect agent for system design tasks
uv run main.py chat --agent architect

# Start with the Code Assistant agent for programming tasks
uv run main.py chat --agent code_assistant

# Start with the Documentation agent for documentation tasks
uv run main.py chat --agent documentation
```

### Scrape a URL and Save as Markdown

```bash
uv run main.py get-url https://example.com output.md
```

### Scrape and Summarize Content

```bash
uv run main.py get-url https://example.com output.md --summarize
```

### Scrape and Explain Content

```bash
uv run main.py get-url https://example.com output.md --explain
```

## License

[MIT License](LICENSE)
