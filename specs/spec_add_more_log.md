# Add more logs

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Objectives

- Add log for each step like scrapping, summarizing
- Add input token, output token and total cost for anthropic called
  - use a constant for token cost of input token = 3$/Million Tokens and output token = 15$/Million Tokens

## Contexts

- main.py: main python file that use click for command line
- modules/scraping.py: scraping module using Firecrawl
- modules/anthropic.py: new module for integrate with anthropic api

## Low-level Tasks

- UPDATE main.py for each step logs
- UPDATE modules/anthropic.py for const constant
- UPDATE modules/anthropic.py for token and cost logs
