from pathlib import Path

from backend.ai import prompts as prompt_module


def test_prompt_files_are_available(prompt_dir):
    expected = ["agentic_ai.md", "cyber.md", "executive.md", "iam.md", "regulations.md", "research.md", "vendors.md"]
    for name in expected:
        assert (prompt_dir / name).exists()


def test_prompt_module_can_load_prompt_files(prompt_dir):
    markdown_files = sorted(p.name for p in prompt_dir.glob("*.md"))
    assert markdown_files
    assert "executive.md" in markdown_files
