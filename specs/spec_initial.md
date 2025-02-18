# Build a command line application to fetch a url and convert to markdown file

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satify Objectives

## Objective

- Create the command `get-url <url> <output_file>`
- using `uv` for package manager with `pyproject.toml`
- can be expanded with other commands later on, for example, `sumarize-file`, `get-transcript`, etc...

## Context

Create new files when needed

## Low-level Tasks

1. Create the command `get-url <url> <output_file>`

```aider
CREATE modules/scraping.py

# Her is an example crawl website using Firecrawl
    from firecrawl import FirecrawlApp
    app = FirecrawlApp(api_key="FC-YOUR_API_KEY") //FC-YOUR_API_KEY should be from env
    scrape_result = app.scrape_url('firecrawl.dev', params={'formats': ['markdown', 'html']})
    print(scrape_result)

CREATE tests/scraping_test.py
    Create a test with https://raw.githubusercontent.com/ivanbicalho/python-docx-replace/refs/heads/main/README.md

CREATE main.py
      
    Should be able to expanded with other commands  

    CREATE get_url(url, file_path)
```
