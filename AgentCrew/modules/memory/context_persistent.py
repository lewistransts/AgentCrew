import json
import os
import uuid
import datetime
from typing import Dict, Any, List, Optional


class ContextPersistenceService:
    """
    Manages persistence for user context (summary + rankings) and conversation
    histories for a single-user application, using JSON files.
    Handles nested structure for key_facts_entities.
    Persistence directory is determined by PERSISTENCE_DIR environment variable,
    defaulting to the current directory.
    Uses print for output and raises exceptions on critical errors.
    """

    CONTEXT_FILENAME = "context.json"
    CONVERSATIONS_SUBDIR = "conversations"
    DEFAULT_CONTEXT_STRUCTURE = {"latest_summary": {}, "_rankings": {}}
    KEY_FACTS_CATEGORY_NAME = "key_facts_entities"
    ENTITY_ITSELF_COUNT_KEY = (
        "_entity_itself_count"  # Key to store entity's own frequency
    )

    def __init__(self, persistence_dir_override: Optional[str] = None):
        """
        Initializes the service, setting up paths and ensuring directories exist.

        The base directory is determined in the following order:
        1. `persistence_dir_override` argument (if provided).
        2. `PERSISTENCE_DIR` environment variable (if set and not empty).
        3. Current working directory (`.`) as the final default.

        Args:
            persistence_dir_override: Optional explicit path to the persistence directory,
                                      bypassing environment variable lookup.

        Raises:
            OSError: If the persistence directories cannot be created.
        """
        # Removed: self.logger initialization

        if persistence_dir_override:
            persistence_dir = persistence_dir_override
            # print(
            #     f"INFO: Using provided persistence directory override: {persistence_dir}"
            # )
        else:
            env_dir = os.getenv("PERSISTENCE_DIR")
            if env_dir:
                persistence_dir = env_dir
                # print(
                #     f"INFO: Using persistence directory from PERSISTENCE_DIR environment variable: {persistence_dir}"
                # )
            else:
                persistence_dir = "./persistents"  # Default to current directory
                # print(
                #     "INFO: PERSISTENCE_DIR environment variable not set. Defaulting persistence directory to current directory ('.')"
                # )

        # Expand user path (~) if present, and get absolute path for clarity
        self.base_dir = os.path.abspath(os.path.expanduser(persistence_dir))
        self.context_file_path = os.path.join(self.base_dir, self.CONTEXT_FILENAME)
        self.conversations_dir = os.path.join(self.base_dir, self.CONVERSATIONS_SUBDIR)

        # _ensure_dir already raises OSError on failure
        self._ensure_dir(self.base_dir)
        self._ensure_dir(self.conversations_dir)
        print(
            f"INFO: Persistence service initialized. Absolute base directory: {self.base_dir}"
        )

    def _ensure_dir(self, dir_path: str):
        """Ensures a directory exists, creating it if necessary."""
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as e:
            # Removed: self.logger.error(...)
            print(f"ERROR: Failed to create directory {dir_path}: {e}")
            raise  # Re-raise after printing

    def _read_json_file(self, file_path: str, default_value: Any = None) -> Any:
        """
        Safely reads a JSON file. Returns default value on expected errors.

        Args:
            file_path: Path to the JSON file.
            default_value: Value to return if the file doesn't exist or is invalid.

        Returns:
            Parsed JSON content or the default value.
        """
        if not os.path.exists(file_path):
            return default_value
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    # Treat empty file same as invalid JSON for consistency
                    print(f"WARNING: File {file_path} is empty. Returning default.")
                    return default_value
                return json.loads(content)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            # Removed: self.logger.warning(...)
            print(
                f"WARNING: Could not read or parse {file_path}: {e}. Returning default."
            )
            return default_value
        except Exception as e:
            # Catch unexpected errors during read/parse
            print(f"ERROR: Unexpected error reading {file_path}: {e}")
            # Decide if unexpected errors should raise or return default.
            # Returning default might hide issues, raising might be better.
            # Let's raise for unexpected errors.
            raise

    def _write_json_file(self, file_path: str, data: Any):
        """
        Safely writes data to a JSON file. Raises exceptions on failure.

        Args:
            file_path: Path to the JSON file.
            data: Python object to serialize and write.

        Raises:
            IOError: If writing to the file fails.
            TypeError: If the data cannot be serialized to JSON.
            OSError: If the directory cannot be created.
        """
        try:
            # Ensure directory exists before writing (raises OSError on failure)
            self._ensure_dir(os.path.dirname(file_path))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, TypeError, OSError) as e:
            print(f"ERROR: Could not write to {file_path}: {e}")
            raise  # Re-raise the caught exception
        except Exception as e:
            # Catch unexpected errors during write/dump
            print(f"ERROR: Unexpected error writing {file_path}: {e}")
            raise

    def _update_rankings(self, current_rankings: dict, new_summary: dict) -> dict:
        """
        Updates ranking counts based on a new context summary.
        Maintains nested structure for 'key_facts_entities' ranking.

        Args:
            current_rankings: The existing rankings dictionary.
            new_summary: The new user context summary dictionary.

        Returns:
            The dictionary with updated ranking counts.
        """
        updated_rankings = {}
        # Ensure all categories from current_rankings are carried over safely
        for category, items in current_rankings.items():
            # Ensure the copied item is a dictionary, especially for nested ones
            if isinstance(items, dict):
                # Deep copy might be safer for nested structures if modification is complex,
                # but simple assignment should be okay if we only modify counts.
                # Let's stick with shallow copy for now for simplicity. If issues arise, use copy.deepcopy.
                updated_rankings[category] = items.copy()
            else:
                print(
                    f"WARNING: Malformed ranking category found: {category}. Resetting."
                )
                updated_rankings[category] = {}

        # Iterate through the categories and items in the *new* summary
        for category, items in new_summary.items():
            # Ensure the category exists in rankings, initialize if not
            if category not in updated_rankings:
                updated_rankings[category] = {}

            # --- Handle the special 'key_facts_entities' category ---
            if category == self.KEY_FACTS_CATEGORY_NAME:
                if isinstance(items, dict):
                    # Ensure the ranking category itself is a dict
                    if not isinstance(updated_rankings[category], dict):
                        print(
                            f"WARNING: Resetting ranking for {category} as it wasn't a dict."
                        )
                        updated_rankings[category] = {}

                    for entity_key, facts_list in items.items():
                        if not isinstance(entity_key, str):
                            # print(f"DEBUG: Skipping non-string entity key in ranking: {entity_key}")
                            continue  # Skip non-string keys

                        # Ensure the entity key exists in the ranking dict for this category
                        if entity_key not in updated_rankings[category]:
                            updated_rankings[category][
                                entity_key
                            ] = {}  # Value is now a dict for facts

                        # Ensure the value is a dictionary (might be needed if loaded from corrupt file)
                        if not isinstance(updated_rankings[category][entity_key], dict):
                            print(
                                f"WARNING: Resetting ranking for entity '{entity_key}' as its value wasn't a dict."
                            )
                            updated_rankings[category][entity_key] = {}

                        # Increment the count for the entity key itself
                        entity_count = updated_rankings[category][entity_key].get(
                            self.ENTITY_ITSELF_COUNT_KEY, 0
                        )
                        updated_rankings[category][entity_key][
                            self.ENTITY_ITSELF_COUNT_KEY
                        ] = entity_count + 1

                        # Rank the associated facts within the entity's dictionary
                        if isinstance(facts_list, list):
                            for fact in facts_list:
                                if isinstance(fact, str):
                                    # Increment count for this fact *within this entity's dict*
                                    fact_count = updated_rankings[category][
                                        entity_key
                                    ].get(fact, 0)
                                    updated_rankings[category][entity_key][fact] = (
                                        fact_count + 1
                                    )
                                else:
                                    # print(f"DEBUG: Skipping non-string fact in ranking: {fact}")
                                    pass
                        else:
                            # print(f"DEBUG: Facts list for entity '{entity_key}' is not a list: {facts_list}")
                            pass
                else:
                    # print(f"DEBUG: Expected a dict for '{self.KEY_FACTS_CATEGORY_NAME}', but got {type(items)}")
                    pass

            # --- Handle other categories (assumed to be List[str]) ---
            else:
                # Ensure the ranking category itself is a dict
                if not isinstance(updated_rankings[category], dict):
                    print(
                        f"WARNING: Resetting ranking for {category} as it wasn't a dict."
                    )
                    updated_rankings[category] = {}

                if isinstance(items, list):
                    for item in items:
                        # Only rank strings for simplicity
                        if isinstance(item, str):
                            current_count = updated_rankings[category].get(item, 0)
                            updated_rankings[category][item] = current_count + 1
                        else:
                            # print(f"DEBUG: Skipping non-string item in ranking category '{category}': {item}")
                            pass
                else:
                    # print(f"DEBUG: Expected a list for category '{category}', but got {type(items)}")
                    pass

        return updated_rankings

    # --- User Context Management ---

    def store_user_context(self, context_summary: dict):
        """
        Stores the latest user context summary and updates the rankings.

        Args:
            context_summary: The new user context summary dictionary.

        Raises:
            ValueError: If context_summary is not a dictionary.
            IOError, TypeError, OSError: If writing to the context file fails.
        """
        if not isinstance(context_summary, dict):
            # Raise error instead of just logging
            raise ValueError(
                "Invalid context_summary provided (must be a dict). Aborting store."
            )

        full_data = self._read_json_file(
            self.context_file_path, default_value=self.DEFAULT_CONTEXT_STRUCTURE.copy()
        )
        # Ensure the structure read from file is valid before proceeding
        if not isinstance(full_data.get("_rankings"), dict):
            print(
                f"WARNING: Invalid rankings structure in {self.context_file_path}. Resetting rankings."
            )
            full_data["_rankings"] = {}
        if not isinstance(full_data.get("latest_summary"), dict):
            full_data["latest_summary"] = {}  # Ensure latest_summary exists

        current_rankings = full_data["_rankings"]

        # Call the updated ranking logic
        updated_rankings = self._update_rankings(current_rankings, context_summary)

        data_to_save = {
            "latest_summary": context_summary,
            "_rankings": updated_rankings,
        }

        # _write_json_file now raises exceptions on failure
        self._write_json_file(self.context_file_path, data_to_save)
        # print(f"INFO: User context stored successfully at {self.context_file_path}")

    def get_user_context(self) -> Dict[str, Any] | None:
        """
        Retrieves the stored user context including latest summary and rankings.

        Returns:
            The dictionary containing 'latest_summary' and '_rankings',
            or None if the file doesn't exist or is invalid/empty.
        """
        data = self._read_json_file(self.context_file_path, default_value=None)

        # Basic validation after reading
        if (
            data is None
            or not isinstance(data.get("latest_summary"), dict)
            or not isinstance(data.get("_rankings"), dict)
        ):
            print(
                f"WARNING: Stored context file {self.context_file_path} is missing or invalid."
            )
            return None  # Return None if invalid or missing

        # Check if it's just the default empty structure
        if not data["latest_summary"] and not data["_rankings"]:
            # print(f"INFO: Stored context file {self.context_file_path} is empty.")
            return None  # Return None if empty

        return data

    def get_user_context_json(
        self, min_count_threshold: int = 3, limit_count_threshold: int = 10
    ) -> str:
        """
        Formats the ranking data into a JSON string suitable for prompt injection.

        Includes only items/entities with a count >= min_count_threshold.
        Limits the number of items/entities per category to limit_count_threshold,
        selecting the ones with the highest counts.
        Counts are used for filtering/limiting but are *not* included in the output JSON.

        Args:
            min_count_threshold: The minimum count an item/entity must have to be considered.
            limit_count_threshold: The maximum number of items/entities to include per category,
                                sorted by count descending. For key_facts_entities,
                                this limits the number of entities shown.

        Returns:
            A JSON formatted string summarizing the high-frequency, limited context,
            or an empty JSON object string "{}" if no items meet the criteria.
        """
        context_data = self.get_user_context()
        if not context_data or not isinstance(context_data.get("_rankings"), dict):
            return "{}"  # Return empty JSON object string

        rankings = context_data["_rankings"]
        filtered_data_for_json = {}  # Build a dict containing filtered items

        # --- Filter and Limit the data ---
        for category, category_rankings in rankings.items():
            if not isinstance(category_rankings, dict):
                continue  # Skip malformed

            # --- Special handling for key_facts_entities ---
            if category == self.KEY_FACTS_CATEGORY_NAME:
                potentially_includable_entities = []
                # First pass: identify entities meeting min_threshold and get their count
                for entity_key, entity_data in category_rankings.items():
                    if not isinstance(entity_data, dict):
                        continue  # Skip malformed entity

                    entity_itself_count = entity_data.get(
                        self.ENTITY_ITSELF_COUNT_KEY, 0
                    )
                    include_entity = entity_itself_count >= min_count_threshold

                    # Also check facts to see if entity should be considered even if its own count is low
                    if not include_entity:
                        for fact, count in entity_data.items():
                            if fact == self.ENTITY_ITSELF_COUNT_KEY:
                                continue
                            if count >= min_count_threshold:
                                include_entity = True
                                break  # Found one fact meeting threshold, entity is potentially includable

                    if include_entity:
                        # Store entity key and its own count for sorting/limiting
                        potentially_includable_entities.append(
                            (entity_key, entity_itself_count)
                        )

                # Sort potential entities by their own count (descending)
                potentially_includable_entities.sort(key=lambda x: x[1], reverse=True)

                # Limit the number of entities
                limited_entities = potentially_includable_entities[
                    :limit_count_threshold
                ]

                # Second pass: build the output dict for the limited entities
                filtered_entities_dict = {}
                if limited_entities:
                    # Get just the keys of the top entities
                    top_entity_keys = [key for key, count in limited_entities]
                    # Sort keys alphabetically for final output consistency
                    top_entity_keys.sort()

                    for entity_key in top_entity_keys:
                        entity_data = category_rankings.get(
                            entity_key, {}
                        )  # Should exist, but default defensively
                        filtered_facts_list = []
                        # Collect facts meeting min_threshold for this top entity
                        for fact, count in entity_data.items():
                            if fact == self.ENTITY_ITSELF_COUNT_KEY:
                                continue
                            if count >= min_count_threshold:
                                filtered_facts_list.append(fact)

                        # Add entity to output dict, even if facts list is empty (if entity itself met threshold)
                        # Sort facts alphabetically
                        filtered_entities_dict[entity_key] = sorted(filtered_facts_list)

                # Add the category to the final dict only if it has filtered entities
                if filtered_entities_dict:
                    filtered_data_for_json[category] = filtered_entities_dict

            # --- Handling for regular (flat) categories ---
            else:
                items_meeting_min_threshold = []
                for item, count in category_rankings.items():
                    if count >= min_count_threshold:
                        items_meeting_min_threshold.append((item, count))

                # Sort by count descending
                items_meeting_min_threshold.sort(key=lambda x: x[1], reverse=True)

                # Limit the number of items
                if category not in ["explicit_preferences", "inferred_behavior"]:
                    limited_items = items_meeting_min_threshold[:limit_count_threshold]
                else:
                    limited_items = items_meeting_min_threshold

                # Extract just the item names from the limited list
                final_item_list = [item for item, count in limited_items]

                # Add the category to the final dict only if it has filtered items
                if final_item_list:
                    # Sort items alphabetically for final output consistency
                    filtered_data_for_json[category] = sorted(final_item_list)

        # --- Generate JSON string ---
        if not filtered_data_for_json:
            return "{}"  # Return empty JSON object string

        # Use separators=(',', ':') for compact JSON, sort_keys=True for consistency
        try:
            json_string = json.dumps(
                filtered_data_for_json, separators=(",", ":"), sort_keys=True
            )
            return json_string
        except TypeError as e:
            print(f"ERROR: Failed to serialize filtered data to JSON: {e}")
            return "{}"  # Fallback on serialization error

    # --- Conversation History Management ---

    def start_conversation(self) -> str:
        """
        Generates a unique conversation ID. Does not create a file immediately.

        Returns:
            The unique conversation ID (UUID string).
        """
        conversation_id = str(uuid.uuid4())
        # Removed file creation: File will be created on first append.
        # file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        # self._write_json_file(file_path, []) # REMOVED
        # print(f"INFO: Generated new conversation ID: {conversation_id}")
        return conversation_id

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Deletes a conversation JSON file from the filesystem.

        Args:
            conversation_id: The ID of the conversation to delete.

        Returns:
            True if the file was deleted or did not exist, False on error.
        """
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"INFO: Deleted conversation file: {file_path}")
            else:
                print(f"INFO: Conversation file not found (already deleted?): {file_path}")
            return True
        except OSError as e:
            print(f"ERROR: Failed to delete conversation file {file_path}: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error deleting conversation file {file_path}: {e}")
            return False

    def append_conversation_messages(
        self, conversation_id: str, new_messages: List[Dict[str, Any]], force=False
    ):
        """
        Appends a list of new message dictionaries to a conversation history file.

        Args:
            conversation_id: The ID of the conversation to update.
            new_messages: The list of new message dictionaries to append.
                          Typically contains a user message and an assistant message.

        Raises:
            ValueError: If new_messages format is invalid.
            IOError, TypeError, OSError: If reading or writing the conversation file fails.
        """
        if not isinstance(new_messages, list) or not all(
            isinstance(msg, dict) for msg in new_messages
        ):
            raise ValueError(
                f"Invalid new_messages format for {conversation_id} (must be a list of dicts). Aborting append."
            )

        if not new_messages and not force:
            # print(
            #     f"INFO: No new messages provided for {conversation_id}. Nothing to append."
            # )
            return  # Nothing to do

        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")

        history = []  # Initialize history as empty list
        if os.path.exists(file_path):
            # File exists, read its content
            history = self._read_json_file(file_path, default_value=[])
            if not isinstance(history, list):
                print(
                    f"WARNING: Conversation file {file_path} was not a list. Resetting history before append."
                )
                history = []
        # else: File doesn't exist, history remains [], file will be created by _write_json_file

        if force:
            history = new_messages
        else:
            # Append the new messages
            history.extend(new_messages)

        self._write_json_file(file_path, history)
        # print(
        #     f"INFO: Appended {len(new_messages)} message(s) to conversation: {conversation_id}"
        # )

    def get_conversation_history(
        self, conversation_id: str
    ) -> List[Dict[str, Any]] | None:
        """
        Loads and returns the message list for a specific conversation.

        Args:
            conversation_id: The ID of the conversation to retrieve.

        Returns:
            A list of message dictionaries, or None if the conversation file
            doesn't exist or is invalid.
        """
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        history = self._read_json_file(file_path, default_value=None)

        if history is None or not isinstance(history, list):
            print(
                f"WARNING: Conversation history for {conversation_id} not found or invalid."
            )
            return None

        return history

    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        Scans the conversations directory and returns metadata for available conversations.

        Returns:
            A list of dictionaries, each containing 'id', 'timestamp' (of last modification),
            and 'preview' (first few words of the first user message).
            Sorted by timestamp descending (most recent first).

        Raises:
            OSError: If the conversations directory cannot be listed.
        """
        conversations = []
        try:
            # listdir raises OSError if the directory is invalid
            filenames = os.listdir(self.conversations_dir)
            for filename in filenames:
                if filename.endswith(".json"):
                    conversation_id = filename[:-5]  # Remove .json extension
                    file_path = os.path.join(self.conversations_dir, filename)
                    try:
                        # getmtime raises OSError if file not found or inaccessible
                        mtime = os.path.getmtime(file_path)
                        timestamp = datetime.datetime.fromtimestamp(mtime).isoformat()

                        # _read_json_file handles its own errors internally
                        history = self._read_json_file(file_path, default_value=[])
                        preview = "Empty Conversation"
                        if isinstance(history, list) and len(history) > 0:
                            user_msgs = (
                                msg
                                for msg in history
                                if isinstance(msg, dict) and msg.get("role") == "user"
                            )
                            while True:
                                first_user_msg = next(
                                    user_msgs,
                                    None,
                                )
                                if first_user_msg:
                                    content = first_user_msg.get("content", "")
                                    if isinstance(content, str) and content:
                                        preview = (
                                            (content[:50] + "...")
                                            if len(content) > 50
                                            else content
                                        )
                                    elif isinstance(content, list):
                                        first_text_block = next(
                                            (
                                                block.get("text", "")
                                                for block in content
                                                if isinstance(block, dict)
                                                and block.get("type") == "text"
                                            ),
                                            "",
                                        )
                                        if first_text_block:
                                            preview = (
                                                (first_text_block[:50] + "...")
                                                if len(first_text_block) > 50
                                                else first_text_block
                                            )
                                        else:
                                            preview = "[Image/Tool Data]"
                                    else:
                                        preview = "[Non-text Content]"
                                else:
                                    preview = "[No User Message Found]"

                                if not preview.startswith(
                                    "Context from your memory:"
                                ) and not preview.startswith("Content of "):
                                    break

                        conversations.append(
                            {
                                "id": conversation_id,
                                "timestamp": timestamp,
                                "preview": preview,
                            }
                        )
                    except OSError as e:
                        # Log specific file access errors but continue listing others
                        print(f"WARNING: Could not access metadata for {filename}: {e}")
                    except (
                        Exception
                    ) as e:  # Catch other potential errors during preview generation
                        print(f"WARNING: Error processing {filename} for listing: {e}")

            # Sort by timestamp descending (most recent first)
            conversations.sort(key=lambda x: x["timestamp"], reverse=True)

        except FileNotFoundError:
            # This case might be less likely now due to __init__ checks, but keep for robustness
            print(
                f"WARNING: Conversations directory not found during listing: {self.conversations_dir}"
            )
        except OSError as e:
            # Raise error if listing the directory itself fails
            print(
                f"ERROR: Could not list conversations directory {self.conversations_dir}: {e}"
            )
            raise

        return conversations
