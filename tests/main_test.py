import os
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_scraper():
    with patch("main.Scraper") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.scrape_url.return_value = "# Test Content"
        yield mock_instance


@pytest.fixture
def mock_anthropic():
    with patch("main.AnthropicClient") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.summarize_content.return_value = "# Summarized Content"
        mock_instance.explain_content.return_value = "# Explained Content"
        yield mock_instance


def test_get_url_basic(runner, mock_scraper, tmp_path):
    # Arrange
    output_file = os.path.join(tmp_path, "output.md")
    test_url = "https://example.com"

    # Act
    result = runner.invoke(cli, ["get-url", test_url, output_file])

    # Assert
    assert result.exit_code == 0
    assert "🌐 Fetching content from:" in result.output
    assert "✅ Content successfully scraped" in result.output
    assert "💾 Saving content to:" in result.output

    mock_scraper.scrape_url.assert_called_once_with(test_url)

    with open(output_file, "r") as f:
        content = f.read()
        assert content == "# Test Content"


def test_get_url_with_summarize(runner, mock_scraper, mock_anthropic, tmp_path):
    # Arrange
    output_file = os.path.join(tmp_path, "output.md")
    test_url = "https://example.com"

    # Act
    result = runner.invoke(cli, ["get-url", test_url, output_file, "--summarize"])

    # Assert
    assert result.exit_code == 0
    assert "🌐 Fetching content from:" in result.output
    assert "✅ Content successfully scraped" in result.output
    assert "🤖 Summarizing content using Claude..." in result.output
    assert "✅ Content successfully summarized" in result.output
    assert "💾 Saving content to:" in result.output

    mock_scraper.scrape_url.assert_called_once_with(test_url)
    mock_anthropic.summarize_content.assert_called_once_with("# Test Content")

    with open(output_file, "r") as f:
        content = f.read()
        assert content == "# Summarized Content"


def test_get_url_with_explain(runner, mock_scraper, mock_anthropic, tmp_path):
    # Arrange
    output_file = os.path.join(tmp_path, "output.md")
    test_url = "https://example.com"

    # Act
    result = runner.invoke(cli, ["get-url", test_url, output_file, "--explain"])

    # Assert
    assert result.exit_code == 0
    assert "🌐 Fetching content from:" in result.output
    assert "✅ Content successfully scraped" in result.output
    assert "🤖 Explaining content using Claude..." in result.output
    assert "✅ Content successfully explained" in result.output
    assert "💾 Saving content to:" in result.output

    mock_scraper.scrape_url.assert_called_once_with(test_url)
    mock_anthropic.explain_content.assert_called_once_with("# Test Content")

    with open(output_file, "r") as f:
        content = f.read()
        assert content == "# Explained Content"


def test_get_url_both_flags_error(runner):
    # Act
    result = runner.invoke(
        cli, ["get-url", "https://example.com", "output.md", "--summarize", "--explain"]
    )

    # Assert
    assert result.exit_code != 0
    assert "Cannot use both --summarize and --explain options together" in result.output


def test_get_url_scraper_error(runner, mock_scraper):
    # Arrange
    mock_scraper.scrape_url.side_effect = Exception("Scraper error")

    # Act
    result = runner.invoke(cli, ["get-url", "https://example.com", "output.md"])

    # Assert
    assert result.exit_code == 0  # Click catches exceptions and prints them
    assert "❌ Error: Scraper error" in result.output


def test_get_url_anthropic_error(runner, mock_scraper, mock_anthropic):
    # Arrange
    mock_anthropic.summarize_content.side_effect = Exception("Anthropic error")

    # Act
    result = runner.invoke(
        cli, ["get-url", "https://example.com", "output.md", "--summarize"]
    )

    # Assert
    assert result.exit_code == 0  # Click catches exceptions and prints them
    assert "❌ Error: Anthropic error" in result.output
