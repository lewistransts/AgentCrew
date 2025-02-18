# Add a arguments as an option to summarize the content using LLM model

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives

- add an argument in `get-url <url> <output_file> --summarize`
  - summarize the md that specified for LLM model
  - using anthropic api with Claude Sonnet latest model
  - use `anthropic` package for integration

## Contexts

- main.py: main python file that use click for command line
- modules/scraping.py: scraping module using Firecrawl
- modules/anthropic.py: new module for integrate with anthropic api

## Low-level Tasks

1. UPDATE main.py to alter `--summarize` argument for `get-url`
2. UPDATE main.py to passing scraping content to anthropic module for summarize when `--summarize` defined
3. CREATE anthropic that handle api call to anthropic
5. UPDATE anthropic for summarize prompt as a constant
4. UPDATE anthropic module to handle the summarize content using summarize prompt
5. UPDATE main.py to save summarized content
