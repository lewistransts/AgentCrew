import click
from modules.scraping import Scraper
from modules.anthropic import AnthropicClient


@click.group()
def cli():
    """URL to Markdown conversion tool"""
    pass


@cli.command()
@click.argument("url")
@click.argument("output_file")
@click.option("--summarize", is_flag=True, help="Summarize the content using Claude")
def get_url(url: str, output_file: str, summarize: bool):
    """Fetch URL content and save as markdown"""
    try:
        click.echo(f"\n🌐 Fetching content from: {url}")
        scraper = Scraper()
        content = scraper.scrape_url(url)
        click.echo("✅ Content successfully scraped")

        if summarize:
            click.echo("\n🤖 Summarizing content using Claude...")
            anthropic_client = AnthropicClient()
            content = anthropic_client.summarize_content(content)
            click.echo("✅ Content successfully summarized")

        click.echo(f"\n💾 Saving content to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        click.echo(
            f"✅ Successfully saved {'summarized ' if summarize else ''}markdown to {output_file}"
        )
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
