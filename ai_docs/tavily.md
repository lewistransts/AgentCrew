[Tavily Docs home page![light logo](https://mintlify.s3.us-west-1.amazonaws.com/tavilyai/logo/light.svg)![dark logo](https://mintlify.s3.us-west-1.amazonaws.com/tavilyai/logo/dark.svg)](https://docs.tavily.com/)

Search or ask...

Ctrl K

Search...

Navigation

Python

Get Started

[Home](https://docs.tavily.com/welcome) [Guides](https://docs.tavily.com/guides/introduction) [API Reference](https://docs.tavily.com/api-reference/introduction) [SDKs](https://docs.tavily.com/sdk/introduction) [Integrations](https://docs.tavily.com/integrations/langchain)

Looking for the Python SDK Reference? Head to our [Python SDK Reference](https://docs.tavily.com/sdk/python/reference) and learn how to use `tavily-python`.

## [​](https://docs.tavily.com/sdk/python/get-started\#introduction)  Introduction

The Python SDK allows for easy interaction with the Tavily API, offering the full range of our search functionality directly from your Python programs. Easily integrate smart search capabilities into your applications, harnessing Tavily’s powerful search features.

[**GitHub**\\
\\
`/tavily-ai/tavily-python`\\
\\
![GitHub Repo stars](https://img.shields.io/github/stars/tavily-ai/tavily-python?style=social)](https://github.com/tavily-ai/tavily-python) [**PyPI** \\
\\
`tavily-python`\\
\\
![PyPI downloads](https://img.shields.io/pypi/dm/tavily-python)](https://pypi.org/project/tavily-python)

## [​](https://docs.tavily.com/sdk/python/get-started\#quickstart)  Quickstart

Get started with our Python SDK in less than 5 minutes!

[**Get your free API key** \\
\\
You get 1,000 free API Credits every month. **No credit card required.**](https://app.tavily.com/)

### [​](https://docs.tavily.com/sdk/python/get-started\#installation)  Installation

You can install the Tavily Python SDK using the following:

Copy

```bash
pip install tavily-python

```

### [​](https://docs.tavily.com/sdk/python/get-started\#usage)  Usage

With Tavily’s Python SDK, you can search the web in only 4 lines of code:

Copy

```python
from tavily import TavilyClient

tavily_client = TavilyClient(api_key="tvly-YOUR_API_KEY")
response = tavily_client.search("Who is Leo Messi?")

print(response)

```

You can also easily extract content from URLs:

Copy

```python
from tavily import TavilyClient

tavily_client = TavilyClient(api_key="tvly-YOUR_API_KEY")
response = tavily_client.extract("https://en.wikipedia.org/wiki/Lionel_Messi")

print(response)

```

These examples are very simple, and you can do so much more with Tavily!

## [​](https://docs.tavily.com/sdk/python/get-started\#features)  Features

Our Python SDK supports the full feature range of our [REST API](https://docs.tavily.com/api-reference), and more. We offer both a synchronous and an asynchronous client, for increased flexibility.

- The `search` function lets you harness the full power of Tavily Search.
- The `extract` function allows you to easily retrieve web content with Tavily Extract.

For more details, head to the [Python SDK Reference](https://docs.tavily.com/sdk/python/reference).

[Introduction](https://docs.tavily.com/sdk/introduction) [SDK Reference](https://docs.tavily.com/sdk/python/reference)

On this page

- [Introduction](https://docs.tavily.com/sdk/python/get-started#introduction)
- [Quickstart](https://docs.tavily.com/sdk/python/get-started#quickstart)
- [Installation](https://docs.tavily.com/sdk/python/get-started#installation)
- [Usage](https://docs.tavily.com/sdk/python/get-started#usage)
- [Features](https://docs.tavily.com/sdk/python/get-started#features)