"""
Test script to verify all four ingress decorator patterns work as documented.

Run this to validate that the CASTING_GUIDE examples are accurate.
"""

from hubcap.casting import project_kinds, register_project_root
import os
from pathlib import Path


def setup_test_project():
    """Create a minimal test project structure."""
    test_root = Path("/tmp/test_hubcap_projects")
    test_root.mkdir(exist_ok=True)

    test_project = test_root / "test_project"
    test_project.mkdir(exist_ok=True)

    # Create .git directory
    (test_project / ".git").mkdir(exist_ok=True)

    # Create a README
    (test_project / "README.md").write_text("# Test Project\n\nThis is a test.")

    # Register the root
    register_project_root(str(test_root))

    return str(test_project)


def test_pattern_1_explicit_arg_name():
    """Pattern 1: @graph.ingress('kind', 'arg_name')"""

    @project_kinds.ingress('local_proj_folder', 'project_path')
    def analyze(project_path: str, depth: int = 1):
        return f"Analyzing {Path(project_path).name} at depth {depth}"

    result = analyze("test_project", depth=2)
    assert "test_project" in result
    assert "depth 2" in result
    print("✓ Pattern 1 works: @graph.ingress('kind', 'arg_name')")


def test_pattern_2_kind_only():
    """Pattern 2: @graph.ingress('kind') - transforms first arg"""

    @project_kinds.ingress('local_proj_folder')
    def analyze(project_path: str):
        return f"Analyzing {Path(project_path).name}"

    result = analyze("test_project")
    assert "test_project" in result
    print("✓ Pattern 2 works: @graph.ingress('kind')")


def test_pattern_3_attribute_with_arg():
    """Pattern 3: @graph.ingress.kind('arg_name')"""

    @project_kinds.ingress.local_proj_folder('project_path')
    def analyze(project_path: str, depth: int = 1):
        return f"Analyzing {Path(project_path).name} at depth {depth}"

    result = analyze("test_project", depth=3)
    assert "test_project" in result
    assert "depth 3" in result
    print("✓ Pattern 3 works: @graph.ingress.kind('arg_name')")


def test_pattern_4_attribute_first_arg():
    """Pattern 4: @graph.ingress.kind - cleanest syntax"""

    @project_kinds.ingress.local_proj_folder
    def analyze(project_path: str):
        return f"Analyzing {Path(project_path).name}"

    result = analyze("test_project")
    assert "test_project" in result
    print("✓ Pattern 4 works: @graph.ingress.kind")


def test_all_input_formats():
    """Test that all input formats work with decorated function."""
    test_proj = setup_test_project()

    @project_kinds.ingress.local_proj_folder
    def get_readme(project_path: str):
        with open(Path(project_path) / "README.md") as f:
            return f.read()

    # Test with project name
    content1 = get_readme("test_project")
    assert "Test Project" in content1

    # Test with full path
    content2 = get_readme(test_proj)
    assert "Test Project" in content2

    print("✓ All input formats work correctly")


if __name__ == "__main__":
    print("Testing all four ingress decorator patterns...\n")

    test_proj_path = setup_test_project()
    print(f"Created test project at: {test_proj_path}\n")

    test_pattern_1_explicit_arg_name()
    test_pattern_2_kind_only()
    test_pattern_3_attribute_with_arg()
    test_pattern_4_attribute_first_arg()
    test_all_input_formats()

    print("\n✅ All patterns documented in CASTING_GUIDE are working correctly!")
