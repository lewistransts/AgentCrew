import os
import chromadb
import uuid
import numpy as np
import queue
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from threading import Thread, Event
from AgentCrew.modules import logger

from AgentCrew.modules.llm.base import BaseLLMService

from .base_service import BaseMemoryService
from .voyageai_ef import VoyageEmbeddingFunction
from AgentCrew.modules.prompts.constants import (
    SEMANTIC_EXTRACTING,
    PRE_ANALYZE_PROMPT,
    POST_RETRIEVE_MEMORY,
)
from .github_copilot_ef import GithubCopilotEmbeddingFunction
import chromadb.utils.embedding_functions as embedding_functions

# Configuration constants
DEFAULT_CHUNK_SIZE = 200  # words per chunk
DEFAULT_CHUNK_OVERLAP = 40  # words overlap between chunks
DEFAULT_QUEUE_TIMEOUT = 5.0  # seconds
MAX_QUEUE_SIZE = 1000  # maximum pending operations
WORKER_THREAD_NAME = "ChromaMemoryWorker"
MEMORY_DB_PATH = "./memory_db"


class ChromaMemoryService(BaseMemoryService):
    """Service for storing and retrieving conversation memory using ChromaDB."""

    def __init__(
        self,
        collection_name="conversation",
        llm_service: Optional[BaseLLMService] = None,
    ):
        """
        Initialize the memory service with ChromaDB.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the ChromaDB data
        """
        # Ensure the persist directory exists
        self.db_path = os.getenv("MEMORYDB_PATH", MEMORY_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.db_path)

        self.llm_service = llm_service
        ## set to groq if key available
        if self.llm_service:
            if self.llm_service.provider_name == "google":
                self.llm_service.model = "gemini-2.5-flash-lite-preview-06-17"
            elif self.llm_service.provider_name == "claude":
                self.llm_service.model = "claude-3-5-haiku-latest"
            elif self.llm_service.provider_name == "openai":
                self.llm_service.model = "gpt-4.1-nano"
            elif self.llm_service.provider_name == "groq":
                self.llm_service.model = "llama-3.3-70b-versatile"
            elif self.llm_service.provider_name == "deepinfra":
                self.llm_service.model = "google/gemma-3-27b-it"
            elif self.llm_service.provider_name == "github_copilot":
                self.llm_service.model = "gpt-4o-mini"

        # Create or get collection for storing memories
        if os.getenv("VOYAGE_API_KEY"):
            voyage_ef = VoyageEmbeddingFunction(
                api_key=os.getenv("VOYAGE_API_KEY"),
                model_name="voyage-3.5",
            )
            self.embedding_function = voyage_ef
        elif os.getenv("GITHUB_COPILOT_API_KEY"):
            github_copilot_ef = GithubCopilotEmbeddingFunction(
                api_key=os.getenv("GITHUB_COPILOT_API_KEY"),
                model_name="text-embedding-3-small",
            )
            self.embedding_function = github_copilot_ef
        elif os.getenv("OPENAI_API_KEY"):
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small"
            )
            self.embedding_function = openai_ef
        else:
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedding_function
        )
        # Configuration for chunking
        self.chunk_size = DEFAULT_CHUNK_SIZE
        self.chunk_overlap = DEFAULT_CHUNK_OVERLAP
        self.current_embedding_context = None

        self.context_embedding = []

        # Memory queue infrastructure
        self._conversation_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self._memory_thread = None
        self._memory_stop_event = Event()

        # Start worker thread
        self._start_memory_worker()

    def _create_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: The text to split into chunks

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        if len(words) <= self.chunk_size:
            return [text]

        i = 0
        while i < len(words):
            chunk_end = min(i + self.chunk_size, len(words))
            chunk = " ".join(words[i:chunk_end])
            chunks.append(chunk)
            i += self.chunk_size - self.chunk_overlap

        return chunks

    def _memory_worker_thread(self):
        """Worker thread for processing conversation storage operations."""
        while not self._memory_stop_event.is_set():
            try:
                # Get operation from queue with timeout
                operation_data = self._conversation_queue.get(
                    timeout=DEFAULT_QUEUE_TIMEOUT
                )

                if operation_data.get("type") == "shutdown":
                    break

                # Process conversation storage
                self._store_conversation_internal(operation_data)
                self._conversation_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Memory worker error: {e}")

    def _start_memory_worker(self):
        """Start the memory worker thread."""
        if self._memory_thread is None or not self._memory_thread.is_alive():
            self._memory_stop_event.clear()
            self._memory_thread = Thread(
                target=self._memory_worker_thread, name=WORKER_THREAD_NAME, daemon=True
            )
            self._memory_thread.start()

    def _stop_memory_worker(self):
        """Stop the memory worker thread gracefully."""
        if self._memory_thread and self._memory_thread.is_alive():
            # Signal shutdown
            try:
                self._conversation_queue.put({"type": "shutdown"}, timeout=1.0)
                self._memory_thread.join(timeout=10.0)
            except queue.Full:
                logger.warning("Could not send shutdown signal to memory worker")

    async def store_conversation(
        self, user_message: str, assistant_response: str, agent_name: str = "None"
    ) -> List[str]:
        """
        Store a conversation exchange in memory.

        Args:
            user_message: The user's message
            assistant_response: The assistant's response
            agent_name: Name of the agent

        Returns:
            List with operation ID for tracking, or empty list if queue is full
        """
        operation_id = str(uuid.uuid4())

        operation_data = {
            "type": "store_conversation",
            "operation_id": operation_id,
            "user_message": user_message,
            "assistant_response": assistant_response,
            "agent_name": agent_name,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            self._conversation_queue.put(operation_data, timeout=1.0)
            logger.debug(f"Queued conversation storage: {operation_id}")
            return [operation_id]
        except queue.Full:
            logger.warning("Memory queue full, dropping conversation storage")
            return []

    def _store_conversation_internal(self, operation_data: Dict[str, Any]):
        """Internal method to actually store conversation (runs in worker thread)."""
        try:
            user_message = operation_data["user_message"]
            assistant_response = operation_data["assistant_response"]
            agent_name = operation_data["agent_name"]
            session_id = operation_data["session_id"]

            # Use the existing storage logic but make it synchronous
            ids = []
            if self.llm_service:
                try:
                    # Process with LLM using asyncio.run to handle async call in worker thread
                    conversation_text = asyncio.run(
                        self.llm_service.process_message(
                            PRE_ANALYZE_PROMPT.replace(
                                "{current_date}", datetime.today().strftime("%Y-%m-%d")
                            )
                            .replace("{user_message}", user_message)
                            .replace("{assistant_response}", assistant_response)
                        )
                    )
                    lines = conversation_text.split("\n")
                    for i, line in enumerate(lines):
                        if line == "## ID:":
                            ids.append(lines[i + 1])
                except Exception as e:
                    logger.warning(f"Error processing conversation with LLM: {e}")
                    # Fallback to simple concatenation if LLM fails
                    conversation_text = f"Date: {datetime.today().strftime('%Y-%m-%d')}.\n\n User: {user_message}.\n\nAssistant: {assistant_response}"
            else:
                # Create the memory document by combining user message and response
                conversation_text = f"Date: {datetime.today().strftime('%Y-%m-%d')}.\n\n User: {user_message}.\n\nAssistant: {assistant_response}"

            # Store in ChromaDB (existing logic)
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            conversation_embedding = self.embedding_function([conversation_text])
            self.context_embedding.append(conversation_embedding)
            if len(self.context_embedding) > 5:
                self.context_embedding.pop(0)

            # Add to ChromaDB collection (existing logic)
            if ids:
                self.collection.upsert(
                    ids=[ids[0]],
                    documents=[conversation_text],
                    embeddings=conversation_embedding,
                    metadatas=[
                        {
                            "timestamp": timestamp,
                            "conversation_id": memory_id,
                            "session_id": session_id,
                            "agent": agent_name,
                            "type": "conversation",
                            "user_message": user_message,
                            "assistant_messsage": assistant_response,
                        }
                    ],
                )
            else:
                self.collection.add(
                    documents=[conversation_text],
                    embeddings=conversation_embedding,
                    metadatas=[
                        {
                            "timestamp": timestamp,
                            "conversation_id": memory_id,
                            "session_id": session_id,
                            "agent": agent_name,
                            "type": "conversation",
                            "user_message": user_message,
                            "assistant_messsage": assistant_response,
                        }
                    ],
                    ids=[memory_id],
                )

            logger.debug(f"Stored conversation: {operation_data['operation_id']}")

        except Exception as e:
            logger.error(
                f"Failed to store conversation {operation_data['operation_id']}: {e}"
            )

    async def need_generate_user_context(self, user_input: str) -> bool:
        keywords = await self._semantic_extracting(user_input)
        if not self.loaded_conversation and self.current_embedding_context is None:
            self.current_embedding_context = self.embedding_function([keywords])
            return True

        self.current_embedding_context = self.embedding_function([keywords])
        # Cannot Calculate similarity
        if len(self.context_embedding) == 0:
            return False
        avg_conversation = np.mean(self.context_embedding, axis=0)

        similarity = self._cosine_similarity(
            self.current_embedding_context, avg_conversation
        )
        return similarity < 0.31

    def clear_conversation_context(self):
        self.current_embedding_context = None
        self.context_embedding = []

    async def generate_user_context(
        self, user_input: str, agent_name: str = "None"
    ) -> str:
        """
        Generate context based on user input by retrieving relevant memories.

        Args:
            user_input: The current user message to generate context for

        Returns:
            Formatted string containing relevant context from past conversations
        """
        return await self.retrieve_memory(user_input, 3, agent_name=agent_name)

    async def _semantic_extracting(self, input: str) -> str:
        if self.llm_service:
            try:
                keywords = await self.llm_service.process_message(
                    SEMANTIC_EXTRACTING.replace("{user_input}", input)
                )
                return keywords
            except Exception as e:
                logger.warning(f"Error extracting keywords with LLM: {e}")
                return input
        else:
            return input

    async def retrieve_memory(
        self, keywords: str, limit: int = 5, agent_name: str = "None"
    ) -> str:
        """
        Retrieve relevant memories based on keywords.

        Args:
            keywords: Keywords to search for
            limit: Maximum number of results to return

        Returns:
            Formatted string of relevant memories
        """

        results = self.collection.query(
            query_texts=[keywords],
            n_results=limit,
            where={
                "$and": [
                    {"session_id": {"$ne": self.session_id}},
                    {"agent": agent_name},
                ]
            },
        )

        if not results["documents"] or not results["documents"][0]:
            return "No relevant memories found."

        # Group chunks by conversation_id
        conversation_chunks = {}
        for i, (doc, metadata) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            conv_id = metadata.get("conversation_id", "unknown")
            if conv_id not in conversation_chunks:
                conversation_chunks[conv_id] = {
                    "chunks": [],
                    "timestamp": metadata.get("timestamp", "unknown"),
                    "relevance": len(results["documents"][0])
                    - i,  # Higher relevance for earlier results
                }
            conversation_chunks[conv_id]["chunks"].append(
                (metadata.get("chunk_index", 0), doc)
            )

        # Sort conversations by relevance
        sorted_conversations = sorted(
            conversation_chunks.items(), key=lambda x: x[1]["relevance"], reverse=True
        )

        # Format the output
        output = []
        for conv_id, conv_data in sorted_conversations:
            # Sort chunks by index
            sorted_chunks = sorted(conv_data["chunks"], key=lambda x: x[0])
            conversation_text = "\n".join([chunk for _, chunk in sorted_chunks])

            # Format timestamp
            timestamp = "Unknown time"
            if conv_data["timestamp"] != "unknown":
                try:
                    dt = datetime.fromisoformat(conv_data["timestamp"])
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    timestamp = conv_data["timestamp"]

            output.append(f"--- Memory from {timestamp} ---\n{conversation_text}\n---")

        memories = "\n\n".join(output)
        if self.llm_service:
            try:
                return await self.llm_service.process_message(
                    POST_RETRIEVE_MEMORY.replace("{keywords}", keywords).replace(
                        "{memory_list}", memories
                    )
                )
            except Exception as e:
                logger.warning(f"Error processing retrieved memories with LLM: {e}")
                # Fallback to returning raw memories if LLM processing fails
                return memories
        else:
            return memories

    def _cosine_similarity(self, vec_a, vec_b):
        """Calculate cosine similarity between vectors"""

        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        # Flatten 2D arrays (e.g., shape (1,1536) -> (1536,))
        a = a.flatten() if a.ndim > 1 else a
        b = b.flatten() if b.ndim > 1 else b
        dot_product = np.dot(a, b)
        magnitude_a = np.linalg.norm(a)
        magnitude_b = np.linalg.norm(b)
        if magnitude_a == 0 or magnitude_b == 0:
            return 0
        return dot_product / (magnitude_a * magnitude_b)

    def cleanup_old_memories(self, months: int = 1) -> int:
        """
        Remove memories older than the specified number of months.

        Args:
            months: Number of months to keep

        Returns:
            Number of memories removed
        """
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=30 * months)

        # Get all memories
        all_memories = self.collection.get()

        # Find IDs to remove
        ids_to_remove = []
        if all_memories["metadatas"]:
            for i, metadata in enumerate(all_memories["metadatas"]):
                # Parse timestamp string to datetime object for proper comparison
                timestamp_str = str(
                    metadata.get("timestamp", datetime.now().isoformat())
                )
                try:
                    timestamp_dt = datetime.fromisoformat(timestamp_str)
                    if timestamp_dt < cutoff_date:
                        ids_to_remove.append(all_memories["ids"][i])
                except ValueError:
                    # If timestamp can't be parsed, consider it as old and remove it
                    ids_to_remove.append(all_memories["ids"][i])
                    ids_to_remove.append(all_memories["ids"][i])

        # Remove the old memories
        if ids_to_remove:
            self.collection.delete(ids=ids_to_remove)

        return len(ids_to_remove)

    def forget_topic(self, topic: str, agent_name: str = "None") -> Dict[str, Any]:
        """
        Remove memories related to a specific topic based on keyword search.

        Args:
            topic: Keywords describing the topic to forget

        Returns:
            Dict with success status and information about the operation
        """
        try:
            # Query for memories related to the topic
            results = self.collection.query(
                query_texts=[topic], n_results=100, where={"agent": agent_name}
            )

            if not results["documents"] or not results["documents"][0]:
                return {
                    "success": False,
                    "message": f"No memories found related to '{topic}'",
                    "count": 0,
                }

            # Collect all conversation IDs related to the topic
            conversation_ids = set()
            if results["metadatas"] and results["metadatas"][0]:
                for metadata in results["metadatas"][0]:
                    conv_id = metadata.get("conversation_id")
                    if conv_id:
                        conversation_ids.add(conv_id)

            # Get all memories to find those with matching conversation IDs
            all_memories = self.collection.get()

            # Find IDs to remove
            ids_to_remove = []
            if all_memories["metadatas"]:
                for i, metadata in enumerate(all_memories["metadatas"]):
                    if metadata.get("conversation_id") in conversation_ids:
                        ids_to_remove.append(all_memories["ids"][i])

            # Remove the memories
            if ids_to_remove:
                self.collection.delete(ids=ids_to_remove)

            return {
                "success": True,
                "message": f"Successfully removed {len(ids_to_remove)} memory chunks related to '{topic}'",
                "count": len(ids_to_remove),
                "conversations_affected": len(conversation_ids),
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error forgetting topic: {str(e)}",
                "count": 0,
            }

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status for monitoring."""
        return {
            "queue_size": self._conversation_queue.qsize(),
            "worker_alive": self._memory_thread.is_alive()
            if self._memory_thread
            else False,
            "max_queue_size": MAX_QUEUE_SIZE,
        }

    def shutdown(self):
        """Gracefully shutdown the memory service."""
        logger.info("Shutting down memory service...")
        self._stop_memory_worker()
        logger.info("Memory service shutdown complete")

    def __del__(self):
        """Ensure cleanup on object destruction."""
        try:
            self.shutdown()
        except Exception:
            pass
