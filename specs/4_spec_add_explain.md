# Add a arguments as an option to explain the content using LLM model

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives

- add an argument in `get-url <url> <output_file> --explain`
  - explain the content the md that help non expert understand
  - Add key take away section at the end
  - using anthropic api with Claude Sonnet latest model
  - use `anthropic` package for integration
- Only allow either `--explain` or `--summarize` not both

## Contexts

- main.py: main python file that use click for command line
- modules/scraping.py: scraping module using Firecrawl
- modules/anthropic.py: new module for integrate with anthropic api

## Low-level Tasks

1. UPDATE main.py to alter `--explain` argument for `get-url`
2. UPDATE main.py to passing scraping content to anthropic module for summarize when `--explain` defined
5. UPDATE anthropic for explain prompt as a constant
4. UPDATE anthropic module to handle the explain content using explain prompt
5. UPDATE main.py to save explained content
