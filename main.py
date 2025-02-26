import click
from modules.scraping import Scraper
from modules.anthropic import AnthropicClient


@click.group()
def cli():
    """URL to Markdown conversion tool with Claude AI integration"""
    pass


@cli.command()
@click.argument("url")
@click.argument("output_file")
@click.option("--summarize", is_flag=True, help="Summarize the content using Claude")
@click.option("--explain", is_flag=True, help="Explain the content for non-experts using Claude")
def get_url(url: str, output_file: str, summarize: bool, explain: bool):
    """Fetch URL content and save as markdown"""
    if summarize and explain:
        raise click.UsageError("Cannot use both --summarize and --explain options together")

    try:
        click.echo(f"\n🌐 Fetching content from: {url}")
        scraper = Scraper()
        content = scraper.scrape_url(url)
        click.echo("✅ Content successfully scraped")

        if summarize or explain:
            anthropic_client = AnthropicClient()
            
            if summarize:
                click.echo("\n🤖 Summarizing content using Claude...")
                content = anthropic_client.summarize_content(content)
                click.echo("✅ Content successfully summarized")
            else:  # explain
                click.echo("\n🤖 Explaining content using Claude...")
                content = anthropic_client.explain_content(content)
                click.echo("✅ Content successfully explained")

        click.echo(f"\n💾 Saving content to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        operation = 'explained' if explain else 'summarized' if summarize else ''
        click.echo(
            f"✅ Successfully saved {operation + ' ' if operation else ''}markdown to {output_file}"
        )
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.option("--message", help="Initial message to start the chat")
@click.option("--files", multiple=True, help="Files to include in the initial message")
def chat(message, files):
    """Start an interactive chat session with Claude"""
    try:
        anthropic_client = AnthropicClient()
        anthropic_client.interactive_chat(initial_content=message, files=files)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
