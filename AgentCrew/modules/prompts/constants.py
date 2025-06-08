ANALYSIS_PROMPT = """
<user_context_analysis>
<instruction>
1.  Analyze the <conversation_history> to gather user information.
2.  ONLY INCLUDE information that is related to <user_input>
3.  Format this summary as a JSON object.
4.  MUST enclose the entire JSON object within `<user_context_summary>` tags.
5.  Use the following keys in the JSON object: `explicit_preferences`, `topics_of_interest`, `key_facts_entities`, `inferred_behavior`.
6.  The value for `explicit_preferences`, `topics_of_interest`, `inferred_behavior` MUST be a JSON array of strings `["item1", "item2", ...]`.
7.  the value for `key_facts_entities` MUST be a dictionary with key is a string and value is a array of strings `{"entity1": ["fact about entity1"]}`
8.  If no information has been identified for a category, use an empty array `[]` as its value.
9.  If there are conflicts between conversation_histories, Choose the latest memory by date. 
10. Avoid using ambiguous entity key like "./", "this repo", "this file", choose a meaningful entity key.
11. Only response `<user_context_summary>...</user_context_summary>` block
</instruction>

<output_format_example>
<user_context_summary>
{
  "explicit_preferences": ["Be concise", "Use markdown", "Explain like I'm 5"],
  "topics_of_interest": ["Python", "Machine Learning", "Gardening"],
  "key_facts_entities": {"Project Alpha": ["Deadline: Next Tuesday", "Written in C#"], "Cat's name: Whiskers": ["Favorite food: Fish"]},
  "inferred_behavior": ["Prefers short answers", "Often provides code examples"]
}
</user_context_summary>
</output_format_example>

<empty_value_example>
<user_context_summary>
{
  "explicit_preferences": [],
  "topics_of_interest": ["Photosynthesis"],
  "key_facts_entities": {"User's son": ["Name: Leo"]},
  "inferred_behavior": []
}
</user_context_summary>
</empty_value_example>

</user_context_analysis>

<user_input>
{user_input}
</user_input>

<conversation_history>
{conversation_history}
</conversation_history>
"""

PRE_ANALYZE_PROMPT = """
Enhance this conversation for AI memory storage. Create a single comprehensive text document that includes ALL of the following sections:

    1. ID: keywords from user_message written as snake_case
    2. DATE: {current_date}
    3. SUMMARY: Brief summary of the conversation (1-2 sentences)
    4. CONTEXT: Background information relevant to understanding this exchange
    5. ENTITIES: Important people, organizations, products, or concepts mentioned including essential facts, concepts, or data points discussed about that entity
    6. DOMAIN: The subject domain(s) this conversation relates to
    7. USER PREFERENCES: Any explicit preferences expressed by the user (e.g., "I prefer Python over Java")
    8. BEHAVIORAL INSIGHTS: Observations about user behavior (e.g., "User asks detailed technical questions")

    USER: {user_message}
    ASSISTANT: {assistant_response}

    Format each section with its heading in ALL CAPS followed by the content.
    If a section would be empty, include the heading with "None detected" as the content.
    Focus on extracting factual information rather than making assumptions.
    No explanations or additional text.

    Examples:

    ## ID:
    donald_trump

    ## DATE:
    2025-01-03

    ## SUMMARY:
    A summary about Donald Trump

    Enhanced memory text:
"""

POST_RETRIEVE_MEMORY = """
<INPUT_KEYWORDS>
{keywords}
</INPUT_KEYWORDS>
<MEMORY_LIST>
{memory_list}
</MEMORY_LIST>

**Task:** As an AI data processor, filter and clean timestamped conversation memory snippets based on `INPUT_KEYWORDS`.

**Goal:** Output a cleaned list of memory snippets that are:
1.  **Relevant:** Directly relevant to the provided `INPUT_KEYWORDS`.
2.  **Current & Accurate:** Resolve conflicts using the `DATE` field, prioritizing newer entries.
3.  **Noise-Free:** Eliminate irrelevant or only vaguely related snippets.

**Input Provided:**
1.  `INPUT_KEYWORDS`: A string of keywords defining the topic of interest.
2.  `MEMORY_LIST`: A list of memory snippet objects. Each object includes:
    *   `ID`: Unique identifier.
    *   `DATE`: "YYYY-MM-DD" format.
    *   `SUMMARY`: Brief summary.
    *   `CONTEXT`: Background information.
    *   `ENTITIES`: Key people, orgs, products, concepts, facts.
    *   `DOMAIN`: Subject domain(s).
    *   `USER_PREFERENCES`: Explicit user preferences.
    *   `BEHAVIORAL_INSIGHTS`: User behavior observations.

**Processing Instructions:**
1.  **Relevance Filtering:**
    *   Keep a snippet only if its `SUMMARY`, `CONTEXT`, or `ENTITIES` fields demonstrate clear and direct relevance to `INPUT_KEYWORDS`.
    *   Discard snippets that are off-topic, tangentially related, or lack substantial information regarding `INPUT_KEYWORDS`.
2.  **Recency and Conflict Resolution (Prioritize Newer):**
    *   When multiple relevant snippets address the *exact same specific fact/entity* related to `INPUT_KEYWORDS`: Retain the snippet with the most recent `DATE` and discard older ones if they present outdated or directly conflicting information on that specific point.
    *   If relevant snippets discuss *different aspects* or details related to `INPUT_KEYWORDS` and do not directly conflict, they can all be kept if they pass relevance. Do not discard older snippets if they offer unique, still-relevant information not in newer ones.
3.  **Noise Reduction:**
    *   After the above filters, review and discard any remaining snippets that technically match keywords but add no real value or insight (e.g., a mere mention without substance).

**Output Format:**
*   Return a Markdown result containing only the filtered and cleaned memory snippets.
*   Snippets in the output should retain their original structure.
*   Maintain the original relative order or order chronologically by `DATE` (oldest relevant to newest relevant).

**Example Scenario:**
If `INPUT_KEYWORDS` = "Qwen3 model capabilities" and `MEMORY_LIST` contains:
*   A (`DATE`: "2024-05-01", `SUMMARY`: "Qwen3's context window size.")
*   B (`DATE`: "2025-03-10", `SUMMARY`: "Qwen3's updated context window.")
*   C (`DATE`: "2025-01-15", `SUMMARY`: "General LLM context, Qwen2 mentioned.")
*   D (`DATE`: "2025-03-11", `SUMMARY`: "Qwen3 coding abilities.")

Processing: Snippet C might be discarded (tangential). Snippet A is older; if B supersedes A's info on the *same point* (context window), A is discarded. Snippet D discusses a different capability and is relevant, so B and D would likely be kept.

**Primary Objective:** Distill `MEMORY_LIST` into a concise, relevant, and up-to-date set of information based on `INPUT_KEYWORDS`.
"""

SEMANTIC_EXTRACTING = """
Extract the core information from the user's message and generate a short sentence or phrase summarizing the main idea or context with key entities. No explanations or additional text
User input: {user_input}"""

# Prompt templates
EXPLAIN_PROMPT = """
Please explain the following markdown content in a way that helps non-experts understand it better.
Break down complex concepts and provide clear explanations.
At the end, add a "Key Takeaways" section that highlights the most important points.

Content to explain:
{content}
"""

SUMMARIZE_PROMPT = """
# Web Content Extraction and Compression

I'll provide you with raw HTML or text content from a web page. Your task is to process this content to extract and preserve only the essential information while significantly reducing the token count. Follow these steps:

## 1. Content Analysis
- Identify the main content sections of the page (articles, key information blocks)
- Distinguish between primary content and supplementary elements (navigation, ads, footers, sidebars)
- Recognize important structural elements (headings, lists, tables, key paragraphs)
- Identify code blocks and code examples that are relevant to the content

## 2. Extraction Process
- Remove all navigation menus, ads, footers, and sidebar content
- Eliminate redundant headers, copyright notices, and boilerplate text
- Preserve headings (H1, H2, H3) as they provide structural context
- Keep lists and tables but format them concisely
- Maintain critical metadata (publication date, author) if present
- Preserve ALL code blocks and programming examples in their entirety

## 3. Content Compression
- Remove unnecessary adjectives and filler words while preserving meaning
- Condense long paragraphs to their essential points
- Convert verbose explanations to concise statements
- Eliminate redundant examples while keeping the most illustrative ones
- Merge similar points into unified statements
- NEVER compress or modify code blocks - maintain them exactly as they appear

## 4. Special Content Handling
- For educational/technical content: preserve definitions, formulas, and key examples
- For news articles: maintain the 5W1H elements (Who, What, When, Where, Why, How)
- For product pages: keep specifications, pricing, and unique features
- For documentation: retain procedure steps, warnings, and important notes
- For technical/programming content: keep ALL code snippets, syntax examples, and command-line instructions intact

## 5. Output Format
- Present content in a structured, hierarchical format
- Use markdown for formatting to maintain readability with minimal tokens
- Include section headers to maintain document organization
- Preserve numerical data, statistics, and quantitative information exactly
- Maintain code blocks with proper markdown formatting (```language ... ```)
- Ensure inline code is preserved with backtick formatting (`code`)

Return ONLY the processed content without explanations about your extraction process. Focus on maximizing information retention while minimizing token usage.

WEB CONTENT: {content}
"""
