import os
from anthropic import Anthropic
from anthropic.types import TextBlock
from dotenv import load_dotenv
import sys

# Cost constants (USD per million tokens)
INPUT_TOKEN_COST_PER_MILLION = 3.0
OUTPUT_TOKEN_COST_PER_MILLION = 15.0

EXPLAIN_PROMPT = """
Please explain the following markdown content in a way that helps non-experts understand it better.
Break down complex concepts and provide clear explanations.
At the end, add a "Key Takeaways" section that highlights the most important points.

Content to explain:
{content}
"""

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

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_MILLION
        return input_cost + output_cost

    def summarize_content(self, content: str) -> str:
        try:
            message = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": SUMMARIZE_PROMPT.format(content=content),
                    }
                ],
            )

            content_block = message.content[0]
            if not isinstance(content_block, TextBlock):
                raise ValueError(
                    "Unexpected response type: message content is not a TextBlock"
                )

            # Calculate and log token usage and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_cost = self.calculate_cost(input_tokens, output_tokens)

            print(f"\nToken Usage Statistics:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return content_block.text
        except Exception as e:
            raise Exception(f"Failed to summarize content: {str(e)}")

    def explain_content(self, content: str) -> str:
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": EXPLAIN_PROMPT.format(content=content),
                    }
                ],
            )

            content_block = message.content[0]
            if not isinstance(content_block, TextBlock):
                raise ValueError(
                    "Unexpected response type: message content is not a TextBlock"
                )

            # Calculate and log token usage and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_cost = self.calculate_cost(input_tokens, output_tokens)

            print(f"\nToken Usage Statistics:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens: {input_tokens + output_tokens:,}")
            print(f"Estimated cost: ${total_cost:.4f}")

            return content_block.text
        except Exception as e:
            raise Exception(f"Failed to explain content: {str(e)}")
            
    def interactive_chat(self, initial_content=None, files=None):
        """
        Start an interactive chat session with Claude using streaming mode.
        
        Args:
            initial_content (str, optional): Initial message to start the conversation
            files (list, optional): List of file paths to include in the initial message
        """
        messages = []
        import base64
        import mimetypes
        
        # Helper function to read file contents
        def read_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            except Exception as e:
                print(f"❌ Error reading file {file_path}: {str(e)}")
                return None
        
        # Helper function to read binary file and encode as base64
        def read_binary_file(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                return base64.b64encode(content).decode('utf-8')
            except Exception as e:
                print(f"❌ Error reading file {file_path}: {str(e)}")
                return None
        
        # Initialize with files or message if provided
        if files:
            message_content = []
            
            for file_path in files:
                # Determine file type
                mime_type, _ = mimetypes.guess_type(file_path)
                
                if mime_type == 'application/pdf':
                    # Handle PDF as document
                    pdf_data = read_binary_file(file_path)
                    if pdf_data:
                        message_content.append({
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        })
                        print(f"📄 Including PDF document: {file_path}")
                else:
                    # Handle text files as before
                    content = read_file(file_path)
                    if content:
                        message_content.append({
                            "type": "text",
                            "text": f"Content of {file_path}:\n\n{content}"
                        })
                        print(f"📄 Including text file: {file_path}")
            
            # Add initial text if provided
            if initial_content:
                message_content.append({"type": "text", "text": initial_content})
            elif message_content:
                # Add a default message if we have files but no initial content
                message_content.append({"type": "text", "text": "I'm sharing these files with you. Please analyze them."})
            
            if message_content:
                messages.append({"role": "user", "content": message_content})
                print("\n👤 You: [Initial content with files]")
        elif initial_content:
            messages.append({"role": "user", "content": initial_content})
            print("\n👤 You: [Initial content]")
        
        print("\n🎮 Welcome to the interactive chat with Claude! Type 'exit' or 'quit' to end the session.")
        print("💡 Use '/file <file_path>' to include a file in your message.")
        
        # Main chat loop
        while True:
            # If we have an initial message, process it first
            if messages and len(messages) == 1 and (files or initial_content):
                # Skip user input for the first iteration if we have initial content
                pass
            else:
                # Get user input
                user_input = input("\n👤 You: ")
                
                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    print("🎮 Ending chat session. Goodbye!")
                    break
                
                # Check for file command
                if user_input.startswith("/file "):
                    file_path = user_input[6:].strip()
                    
                    # Determine file type
                    mime_type, _ = mimetypes.guess_type(file_path)
                    
                    message_content = []
                    
                    if mime_type == 'application/pdf':
                        # Handle PDF as document
                        pdf_data = read_binary_file(file_path)
                        if pdf_data:
                            message_content.append({
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            })
                            message_content.append({
                                "type": "text",
                                "text": "I'm sharing this PDF file with you. Please analyze it."
                            })
                            print(f"📄 Including PDF document: {file_path}")
                        else:
                            # Skip this iteration if file reading failed
                            continue
                    else:
                        # Handle text files
                        content = read_file(file_path)
                        if content:
                            message_content = [{"type": "text", "text": f"I'm sharing this file with you:\n\nContent of {file_path}:\n\n{content}"}]
                            print(f"📄 Including text file: {file_path}")
                        else:
                            # Skip this iteration if file reading failed
                            continue
                    
                    # Add user message to history
                    messages.append({"role": "user", "content": message_content})
                else:
                    # Add regular text message to history
                    messages.append({"role": "user", "content": user_input})
            
            # Print assistant response with streaming
            print("\n🤖 Claude: ", end="", flush=True)
            
            try:
                # Stream the response
                assistant_response = ""
                input_tokens = 0
                output_tokens = 0
                
                with self.client.messages.stream(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=4096,
                    messages=messages
                ) as stream:
                    # Collect the response
                    for chunk in stream:
                        if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                            print(chunk.delta.text, end="", flush=True)
                            assistant_response += chunk.delta.text
                        elif chunk.type == "message_delta" and hasattr(chunk, "usage") and chunk.usage:
                            # Get token usage when available in the message_delta
                            if hasattr(chunk.usage, "input_tokens"):
                                input_tokens = chunk.usage.input_tokens
                            if hasattr(chunk.usage, "output_tokens"):
                                output_tokens = chunk.usage.output_tokens
                
                # Add assistant's response to message history
                messages.append({"role": "assistant", "content": assistant_response})
                
                # Calculate and log token usage and cost
                total_cost = self.calculate_cost(input_tokens, output_tokens)
                
                print(f"\n\n📊 [Token Usage: Input: {input_tokens:,}, Output: {output_tokens:,}, Cost: ${total_cost:.4f}]")
                    
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                break
