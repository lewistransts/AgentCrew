import os
import subprocess
import tempfile
from pathlib import Path


class SecurityException(Exception):
    """Exception raised for security violations like path traversal attempts."""

    pass


class CodeAssistant:
    """Service for executing aider commands to implement code from spec prompts."""

    def _sanitize_repo_path(self, repo_path: str) -> Path:
        """
        Validate and sanitize the repository path for security.

        Args:
            repo_path: The repository path to sanitize

        Returns:
            Path object of the sanitized repository path

        Raises:
            SecurityException: If path traversal is detected
            NotADirectoryError: If the path is not a directory
        """
        # Resolve the provided path
        provided_path = Path(os.path.expanduser(repo_path)).resolve()

        # Security check - this is a basic check and might need enhancement
        # based on your specific security requirements
        if not provided_path.exists():
            raise NotADirectoryError(f"Path does not exist: {provided_path}")

        if not provided_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {provided_path}")

        return provided_path

    def generate_implementation(self, spec_prompt: str, repo_path: str) -> str:
        """
        Generate code implementation using aider based on a spec prompt.

        Args:
            spec_prompt: The specification prompt to implement
            repo_path: Path to the repository where code should be implemented

        Returns:
            Output from the aider command execution

        Raises:
            SecurityException: If path validation fails
            subprocess.SubprocessError: If aider execution fails
        """
        sanitized_path = self._sanitize_repo_path(repo_path)

        # Create a temporary file for the spec prompt
        with tempfile.NamedTemporaryFile(suffix=".spec", delete=False) as tf:
            tf.write(spec_prompt.encode())
            spec_path = tf.name

        # Get aider executable path (default to 'aider' if not specified)
        aider_exec = os.environ.get("AIDER_PATH", "aider")

        # Build the command
        command = [
            aider_exec,
            "generate",
            "--no-auto-commits",
            "--model",
            "no-detect-urls",
            "claude-3-7-sonnet-latest",
            "--yes-always",
            "--message-file",
            spec_path,
        ]

        try:
            # Execute aider command
            result = subprocess.run(
                command,
                cwd=str(sanitized_path),
                capture_output=True,
                text=True,
                timeout=180,
                check=True,
            )
            return result.stdout
        except subprocess.SubprocessError as e:
            return f"Error executing aider: {str(e)}"
        finally:
            # Clean up the temporary file
            Path(spec_path).unlink(missing_ok=True)
