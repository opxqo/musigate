import re
from pathlib import Path

import musigate


def test_pyproject_uses_module_version_as_single_source_of_truth():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")

    project_section_match = re.search(
        r"^\[project\]\n(?P<section>.*?)(?:^\[|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    assert project_section_match is not None

    project_section = project_section_match.group("section")
    assert 'dynamic = ["version"]' in project_section
    assert not re.search(r"^\s*version\s*=", project_section, re.MULTILINE)
    assert 'version = { attr = "musigate.__version__" }' in content
    assert musigate.__version__
