# Add a check when scrapping for getting file

> Ingest the information from this file, implement the Low-level Tasks, and generate the code that will satisfy Objectives

## Problems

- When scrapping a file url with extensions like `.md` or `.txt`, etc... The scrapper is wrapping the content in a code block

## Objectives

- When scrapping a file url, the content should return as raw format.

## Contexts

- modules/scrapping.py: Scrapping modules usig Firecrawl

## Low-level Tasks

- UPDATE modules/scrapping.py to check if the url is actually a file. If it a file then scrap it as raw format, otherwises scrap as markdown
