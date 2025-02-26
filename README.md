# URL Scraper with Claude AI Integration

A command-line tool that scrapes web content and integrates with Claude AI to summarize, explain, or chat about the content.

## Features

- **Web Scraping**: Fetch content from any URL and save it as markdown
- **AI Summarization**: Use Claude AI to create concise summaries of web content
- **AI Explanation**: Have Claude AI explain complex content in simpler terms
- **Interactive Chat**: Start a conversation with Claude AI, with the ability to include files

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) for package manager
- An Anthropic API key (for Claude AI features)
- A Firecrawl API key (for web scraping features)

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
   FC_API_KEY=your_firecrawl_api_key
   ```

## Usage

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

## Chat Commands

During an interactive chat session, you can use these commands:

- `/file <file_path>` - Include a file in your message
- `/clear` - Clear the conversation history
- `exit` or `quit` - End the chat session
- Press `Enter` for a new line, `Ctrl+S` to submit your message

## License

[MIT License](LICENSE)
