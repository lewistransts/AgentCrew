# Implement CodeAssistant with Aider subprocess integration

> Integrate CodeAssistant service to execute aider CLI with spec prompts in target repositories

## Objectives
- Create CodeAssistant service to execute aider commands via subprocess
- Implement implement_spec_prompt tool to trigger code generation
- Ensure secure execution with proper CWD and env vars
- Handle temp files and error conditions

## Contexts
- modules/coder/service.py: New service class location
- modules/coder/tool.py: Tool registration
- modules/coder/__init__.py: Module initialization
- modules/llm/service_manager.py: LLM service dependencies
- modules/tools/registry.py: Tool registry

## Low-level Tasks
1. UPDATE modules/coder/service.py:
```python
class CodeAssistant:
    def generate_implementation(self, spec_prompt: str, repo_path: str) -> str:
        sanitized_path = self._sanitize_repo_path(repo_path)
        with tempfile.NamedTemporaryFile(suffix='.spec', delete=False) as tf:
            tf.write(spec_prompt.encode())
            spec_path = tf.name
            
        aider_exec = os.getenv('AIDER_PATH', 'aider')
        command = [
            aider_exec,
            "generate",
            "--no-auto-commits",
            "--architect",
            "--dark-mode",
            "--model", "claude-3-7-sonnet-latest",
            "--yes-always",
            "--message-file", spec_path
        ]

        try:
            result = subprocess.run(
                command,
                cwd=str(sanitized_path),
                capture_output=True,
                text=True,
                timeout=120,
                check=True
            return result.stdout
        finally:
            Path(spec_path).unlink(missing_ok=True)
```

2. Add modules/coder/tool.py:
```python
def get_implement_spec_prompt_tool_definition():
    return {
        "name": "implement_spec_prompt",
        "description": "Generate code via aider using spec prompt",
        "args": {
            "type": "object",
            "properties": {
                "spec_prompt": {"type": "string"},
                "repo_path": {"type": "string"}
            },
            "required": ["spec_prompt", "repo_path"]
        }
    }

def handle_implement_spec_prompt(params):
    ca = CodeAssistant()
    return ca.generate_implementation(
    # ... (full implementation)
```

3. Add security checks in modules/coder/service.py:
```python
def _sanitize_repo_path(self, repo_path: str) -> Path:
    base_dir = Path(__file__).resolve().parent.parent  # Project root
    provided_path = Path(repo_path).resolve())
    
    if not provided_path.is_relative_to(base_dir):
        raise SecurityException("Path traversal detected")
        
    if not provided_path.is_dir():
        raise NotADirectoryError
```

4. Add unit test in tests/coder/test_code_assistant.py:
```python
def test_aider_env_var_overide(monkeypatch):
    monkeypatch.setenv('AIDER_PATH', '/usr/local/bin/aider_custom')
    ca = CodeAssistant()
    with patch('subprocess.run') as mock_run:
        ca.generate_implementation("test spec", "/tmp")
        mock_run.assert_called_with(
            ["/usr/local/bin/aider_custom", ...],  # Verify custom path used
            ...
```

## Critical Implementation Notes
- Use `os.environ.get('AIDER_PATH', 'aider')` for executable path
- Add `timeout=120` to `subprocess.run`
- Ensure `cwd` is always the sanitized repo path
- Add `missing_ok=True` when deleting temp files
