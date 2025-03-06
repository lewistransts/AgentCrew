# ChromaDB for LLM Memory Implementation with Anthropic Claude

## What is ChromaDB?

ChromaDB is an open-source embedding database that makes it easy to store,
retrieve, and search vector embeddings for AI applications. It's particularly
well-suited for implementing memory systems for Large Language Models (LLMs) by
storing and retrieving relevant context.

## Key Features

- **Simple API**: Only 4 core functions for easy implementation (add, get,
  update, query)
- **Embeddings Support**: Automatic handling of embeddings or custom embedding
  functions
- **Persistence**: In-memory for prototyping or persistent storage for
  production
- **Metadata Filtering**: Store and filter by metadata alongside embeddings
- **Scalability**: Scale from local development to production environments
- **Multi-modal**: Support for various data types (text, images, etc.)
- **Integration**: Works with popular frameworks like LangChain and LlamaIndex

## Installation

```bash
pip install chromadb anthropic
```

## Basic Usage

```python
import chromadb

# In-memory client (for prototyping)
client = chromadb.Client()

# Persistent client (for production)
# client = chromadb.Client(Settings(
#     chroma_db_impl="duckdb+parquet",
#     persist_directory="path/to/persist"
# ))

# Create a collection for storing conversations or knowledge
collection = client.create_collection("llm_memory")

# Add documents/memories to the collection
collection.add(
    documents=["User asked about Python performance optimization",
               "User mentioned they work in healthcare sector"],
    metadatas=[
        {"source": "conversation", "timestamp": "2025-02-15T14:22:00", "topic": "programming"},
        {"source": "user_info", "timestamp": "2025-02-10T09:15:00", "topic": "background"}
    ],
    ids=["memory1", "memory2"]
)

# Query relevant memories
query_result = collection.query(
    query_texts=["User is asking about data security regulations in healthcare"],
    n_results=2
)

relevant_contexts = query_result["documents"][0]  # List of relevant documents
```

## Integration with Anthropic Claude

Here's a complete implementation showing how to use ChromaDB with Anthropic
Claude:

```python
import chromadb
import anthropic
import os
import uuid
import datetime
from typing import List, Dict, Any, Tuple

class ClaudeMemory:
    def __init__(self, collection_name="claude_memory", persist_directory="./claude_memory_db"):
        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(chromadb.config.Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))

        # Initialize Anthropic client
        self.anthropic = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        # Create or get collection for storing memories
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            # Optionally use Anthropic's embeddings via API
            # embedding_function=YourCustomEmbeddingFunction()
        )

    def store_interaction(self, user_message: str, assistant_response: str,
                          metadata: Dict[str, Any] = None) -> str:
        """Store a user-assistant interaction in memory"""
        memory_id = str(uuid.uuid4())

        # Create the memory document by combining user message and response
        memory_text = f"User: {user_message}\nAssistant: {assistant_response}"

        # Default metadata if none provided
        if metadata is None:
            metadata = {}

        # Add timestamp and interaction type to metadata
        metadata.update({
            "timestamp": datetime.datetime.now().isoformat(),
            "interaction_type": "conversation"
        })

        # Add to ChromaDB collection
        self.collection.add(
            documents=[memory_text],
            metadatas=[metadata],
            ids=[memory_id]
        )

        return memory_id

    def retrieve_relevant_context(self, current_message: str, n_results: int = 5) -> str:
        """Retrieve relevant past interactions based on the current message"""
        results = self.collection.query(
            query_texts=[current_message],
            n_results=n_results
        )

        # Format the retrieved memories as context
        if results["documents"] and results["documents"][0]:
            context = "\n\nPrevious relevant interactions:\n"
            for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                # Add timestamp in a more readable format if available
                timestamp = ""
                if "timestamp" in metadata:
                    try:
                        dt = datetime.datetime.fromisoformat(metadata["timestamp"])
                        timestamp = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        timestamp = metadata["timestamp"]

                context += f"--- Memory {i+1} ({timestamp}) ---\n{doc}\n\n"

            return context

        return ""

    def generate_response(self, user_message: str, system_prompt: str = None) -> Tuple[str, str]:
        """Generate a response from Claude using relevant memory context"""
        # Get relevant context from memory
        memory_context = self.retrieve_relevant_context(user_message)

        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = "You are Claude, a helpful AI assistant with memory of past conversations."

        # If we have relevant context, add it to the system prompt
        if memory_context:
            system_prompt = f"{system_prompt}\n\n{memory_context}"

        # Get response from Claude
        response = self.anthropic.messages.create(
            model="claude-3-opus-20240229",  # or choose another Claude model
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000
        )

        assistant_response = response.content[0].text

        # Store this interaction in memory
        self.store_interaction(user_message, assistant_response)

        return assistant_response, system_prompt
```

## Usage Example

Here's how to use the `ClaudeMemory` class in a conversation loop:

```python
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

def main():
    # Initialize the Claude memory system
    claude_memory = ClaudeMemory(
        collection_name="personal_assistant",
        persist_directory="./claude_memory_db"
    )

    # Example: pre-seed some information about the user
    claude_memory.store_interaction(
        "My name is Alex and I work as a software engineer.",
        "Thank you for sharing that information, Alex. I'll remember that you're a software engineer.",
        metadata={"category": "user_info", "topic": "personal_background"}
    )

    claude_memory.store_interaction(
        "I'm working on a project using React and TypeScript.",
        "That sounds interesting! React and TypeScript make a powerful combination for frontend development.",
        metadata={"category": "user_info", "topic": "current_projects"}
    )

    # Interactive chat loop
    print("Chat with Claude (type 'exit' to quit):")

    system_prompt = """
    You are Claude, a helpful AI assistant with memory of past conversations.
    Always be respectful, helpful, and remember details about the user.
    If referring to information from past conversations, briefly mention that you're
    recalling it to help the user understand your context awareness.
    """

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Get response from Claude with memory
        response, enhanced_prompt = claude_memory.generate_response(
            user_input,
            system_prompt=system_prompt
        )

        print(f"\nClaude: {response}")

if __name__ == "__main__":
    main()
```

## Advanced Features

### Using Custom Embeddings

```python
from chromadb.utils import embedding_functions

# Using OpenAI embeddings for higher quality
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-ada-002"
)

# Create collection with custom embedding function
collection = client.create_collection(
    name="enhanced_memory",
    embedding_function=openai_ef
)
```

### Filtering by Metadata

```python
# Retrieve only memories related to a specific topic
results = collection.query(
    query_texts=["Tell me about data security"],
    where={"topic": "data_security"}
)

# Time-based filtering - get only recent memories
results = collection.query(
    query_texts=["What were we discussing recently?"],
    where={"timestamp": {"$gt": "2025-03-01"}}
)
```

## Best Practices

1. **Proper Chunking**: Break large texts into appropriate chunks before storing
2. **Meaningful Metadata**: Use detailed metadata to help with filtering
3. **Regular Maintenance**: Periodically clean or archive old memories
4. **Optimized Queries**: Combine vector search with metadata filtering
5. **Persistence Setup**: Use persistent storage for production applications
6. **Back Up Your Database**: Regularly back up your ChromaDB persistence
   directory
