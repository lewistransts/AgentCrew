PDF Support in Claude - Key Points:

Requirements & Compatibility:

- Max request size: 32MB
- Max pages per request: 100
- Format: Standard PDF (no passwords/encryption)
- Available on Claude 3.5 Sonnet models via API and Google Vertex AI

How It Works:

1. Document contents extraction (text and images)
2. Analysis of both textual and visual elements
3. Response generation referencing PDF contents

Cost Estimation:

- Text: 1,500-3,000 tokens per page
- Images: Standard vision-based cost calculations
- No additional PDF processing fees

Best Practices:

- Place PDFs before text in requests
- Use standard fonts and clear text
- Ensure proper page orientation
- Reference logical page numbers
- Split large PDFs when needed

Scaling Options:

1. Prompt Caching:

   - Cache PDFs for repeated queries
   - Use cache_control with "type": "ephemeral"

2. Batch Processing:
   - Use Message Batches API for high volume
   - Submit multiple requests simultaneously

Implementation Examples:

- Code snippets provided for shell, Python, and TypeScript

```python
import anthropic
import base64
import httpx

# Load and encode the PDF
pdf_url = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
pdf_data = base64.standard_b64encode(httpx.get(pdf_url).content).decode("utf-8")

# Send to Claude
client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": "What are the key findings in this document?"
                }
            ]
        }
    ],
)

print(message.content)
```

- Examples show basic requests, caching, and batch processing

  - prompt caching

  ```python
  message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    },
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": "Analyze this document."
                }
            ]
        }
    ],
  )
  ```

- API endpoints: /v1/messages and /v1/messages/batches

Sample Use Cases:

- Financial report analysis
- Legal document extraction
- Document translation
- Converting documents to structured formats
