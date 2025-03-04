# Claude AI Interactive Chat Tool

A command-line tool that provides an enhanced interactive chat experience with Claude AI or Groq LLMs, featuring file integration, web scraping capabilities, and convenient keyboard shortcuts.

## Key Features

- **Interactive Chat**: Rich conversation interface with Claude AI or Groq LLMs
- **Multiple LLM Providers**: Choose between Anthropic's Claude or Groq's models
- **File Integration**: Include PDFs and text files directly in your conversation
- **Web Scraping & Search**: Ask Claude to fetch web content and search the internet in real-time
- **Keyboard Shortcuts**: Efficient message editing and response management
- **Multiline Input**: Write complex messages with proper formatting
- **Response Copying**: Easily copy Claude's responses to your clipboard
- **Conversation Memory**: Persistent memory of past conversations that can be retrieved by the AI

## Additional Capabilities

- **Web Content Processing**: Fetch content from any URL and save it as markdown
- **Web Search**: Search the internet for current information on any topic
- **Web Content Extraction**: Extract and analyze content from specific URLs
- **YouTube Subtitles**: Extract and analyze subtitles from YouTube videos
- **YouTube Chapters**: Get chapter information from YouTube videos
- **AI Summarization**: Create concise summaries of web content
- **AI Explanation**: Explain complex content in simpler terms
- **Memory Retrieval**: Access relevant past conversations based on keywords
- **Memory Forgetting**: Remove specific topics or conversations from memory

## Chat Features

- **File Integration**: Include files in your conversation
- **Web Integration**: Ask Claude to scrape URLs or search the web directly in chat
- **YouTube Integration**: Extract subtitles and chapters from YouTube videos
- **Copy Responses**: Easily copy Claude's responses to your clipboard with Alt+C
- **Multiline Input**: Write complex messages with proper formatting
- **Conversation Memory**: The AI can recall and reference past conversations

## Chat Commands

During an interactive chat session, you can use these commands:

- `/file <file_path>` - Include a file in your message
- `/clear` - Clear the conversation history
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

- [x] **Web Search Integration**: Allow Claude to search the web for real-time information
- [x] **YouTube Integration**: Extract subtitles and chapters from YouTube videos
- [x] **Conversation Memory**: Store and retrieve past conversations
- [ ] **Bash Command Execution**: Enable running system commands directly from the chat
- [ ] **File Manipulation**: Create, edit, and manage files through chat commands

### Advanced Personalization

- [ ] **Multiple Personalities**: Switch between different assistant personas tailored for specific tasks
- [ ] **Custom Instructions**: Save and load different instruction sets for various use cases
- [ ] **Enhanced Memory Management**: Configure memory retention periods and retrieval preferences

### Technical Improvements

- [ ] **Model Context Protocol (MCP) Support**: Implement MCP for improved context management
- [ ] **Streaming Optimizations**: Enhance response speed and token efficiency
- [ ] **Local Model Support**: Add compatibility with locally-hosted models
- [ ] **Advanced Memory Indexing**: Improve memory retrieval accuracy and performance

### User Experience

- [ ] **Session Management**: Save, resume, and manage multiple conversation threads
- [ ] **UI Improvements**: Enhanced terminal interface with better visualization options
- [ ] **Configuration Profiles**: Create and switch between different tool configurations
- [ ] **Memory Visualization**: Browse and manage stored conversations

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) for package manager
- An Anthropic API key (for Claude AI features)
- A Groq API key (optional, for Groq LLM features)
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
   GROQ_API_KEY=your_groq_api_key
   FC_API_KEY=your_firecrawl_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

## Usage

### Start an Interactive Chat with Claude

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

### Start a Chat with Groq Provider

```bash
uv run main.py chat --provider groq
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
