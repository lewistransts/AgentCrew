### [Streaming a Chat Completion](https://console.groq.com/docs/text-chat\#streaming-a-chat-completion)

To stream a completion, simply set the parameter `stream=True`. Then the completion
function will return an iterator of completion deltas rather than a single, full completion.

```py
1from groq import Groq
2
3client = Groq()
4
5stream = client.chat.completions.create(
6    #
7    # Required parameters
8    #
9    messages=[\
10        # Set an optional system message. This sets the behavior of the\
11        # assistant and can be used to provide specific instructions for\
12        # how it should behave throughout the conversation.\
13        {\
14            "role": "system",\
15            "content": "you are a helpful assistant."\
16        },\
17        # Set a user message for the assistant to respond to.\
18        {\
19            "role": "user",\
20            "content": "Explain the importance of fast language models",\
21        }\
22    ],
23
24    # The language model which will generate the completion.
25    model="llama-3.3-70b-versatile",
26
27    #
28    # Optional parameters
29    #
30
31    # Controls randomness: lowering results in less random completions.
32    # As the temperature approaches zero, the model will become deterministic
33    # and repetitive.
34    temperature=0.5,
35
36    # The maximum number of tokens to generate. Requests can use up to
37    # 2048 tokens shared between prompt and completion.
38    max_completion_tokens=1024,
39
40    # Controls diversity via nucleus sampling: 0.5 means half of all
41    # likelihood-weighted options are considered.
42    top_p=1,
43
44    # A stop sequence is a predefined or user-specified text string that
45    # signals an AI to stop generating content, ensuring its responses
46    # remain focused and concise. Examples include punctuation marks and
47    # markers like "[end]".
48    stop=None,
49
50    # If set, partial message deltas will be sent.
51    stream=True,
52)
53
54# Print the incremental deltas returned by the LLM.
55for chunk in stream:
56    print(chunk.choices[0].delta.content, end="")
```

