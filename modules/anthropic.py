import os
from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv

SUMMARIZE_PROMPT = """
Please provide a clear and concise summary of the following markdown content, starting directly with the content summary WITHOUT any introductory phrases or sentences.
Focus on the main points and key takeaways while maintaining the essential information, code snippets and examples.
Keep the summary well-structured and easy to understand.

Content to summarize:
{content}
"""


class AnthropicClient:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)

    def summarize_content(self, content: str) -> str:
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": SUMMARIZE_PROMPT.format(content=content),
                    }
                ],
            )
            content_block = message.content[0]
            if isinstance(content_block, TextBlock):
                return content_block.text
            raise ValueError(
                "Unexpected response type: message content is not a TextBlock"
            )
        except Exception as e:
            raise Exception(f"Failed to summarize content: {str(e)}")
