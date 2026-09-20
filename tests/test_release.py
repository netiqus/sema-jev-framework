"""Regression checks for publication boundaries and exact release identity."""

import runpy
import shutil
import subprocess

import pytest


@pytest.fixture
def exporter():
    return runpy.run_path("scripts/public_export.py")


@pytest.fixture
def export_source_tree(tmp_path, exporter):
    source = tmp_path / "source"
    source.mkdir()
    for directory in exporter["PUBLIC_DIRS"]:
        (source / directory).mkdir()
    for name in exporter["PUBLIC_FILES"]:
        (source / name).write_text("synthetic public fixture\n")
    workflows = source / ".github/workflows"
    workflows.mkdir(parents=True)
    for name in exporter["PUBLIC_WORKFLOWS"]:
        (workflows / name).write_text("name: Synthetic workflow\n")
    shutil.copy2("scripts/check_source.py", source / "scripts/check_source.py")
    (source / "src/example.py").write_text("VALUE = 1\n")
    return source


def test_public_export_excludes_private_paths_and_unselected_workflows(
    exporter, export_source_tree, tmp_path
):
    source = export_source_tree
    for relative in (
        ".claude/notes.md",
        ".git/history",
        "AGENTS.md",
        "CLAUDE.md",
        ".github/workflows/private.yml",
    ):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("private fixture, never export\n")
    target = tmp_path / "public"
    count = exporter["export_source"](source, target)
    files = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()}
    assert count == len(files)
    assert "src/example.py" in files
    assert {p.name for p in (target / ".github/workflows").iterdir()} == set(
        exporter["PUBLIC_WORKFLOWS"]
    )
    assert not any(".claude" in name or ".git/" in name for name in files)
    assert not (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()
    with pytest.raises(ValueError, match="never overwritten"):
        exporter["export_source"](source, target)


@pytest.mark.parametrize(
    "relative",
    ["examples/runtime.env", "docs/.claude/notes.md", "src/CLAUDE.md", "examples/input.bin"],
)
def test_export_rejects_unapproved_files_before_creating_target(
    exporter, export_source_tree, tmp_path, relative
):
    path = export_source_tree / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic fixture")
    target = tmp_path / "public"
    with pytest.raises(ValueError):
        exporter["export_source"](export_source_tree, target)
    assert not target.exists()


def test_export_rejects_symlink_to_unapproved_content(exporter, export_source_tree, tmp_path):
    extra = tmp_path / "not-public.txt"
    extra.write_text("synthetic private fixture")
    (export_source_tree / "examples/link.txt").symlink_to(extra)
    target = tmp_path / "public"
    with pytest.raises(ValueError, match="symlink"):
        exporter["export_source"](export_source_tree, target)
    assert not target.exists()


def test_release_verifies_alpha_tag_commit_and_both_versions(tmp_path):
    verify = runpy.run_path("scripts/verify_release.py")["verify_release"]
    (tmp_path / "src/sema_jev").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.2.0a1"\n')
    module = tmp_path / "src/sema_jev/__init__.py"
    module.write_text('__version__ = "0.2.0a1"\n')

    def git(*args):
        subprocess.run(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "user.name=Release Test",
                "-c",
                "user.email=release@example.invalid",
                "-c",
                "commit.gpgsign=false",
                *args,
            ],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    git("init", "--initial-branch=main")
    git("add", ".")
    git("commit", "-m", "Synthetic release fixture")
    git("tag", "v0.2.0a1")
    verify(tmp_path, "v0.2.0a1")
    module.write_text('__version__ = "0.2.0a2"\n')
    with pytest.raises(ValueError, match="versions must match"):
        verify(tmp_path, "v0.2.0a1")
    git("add", ".")
    git("commit", "-m", "Synthetic next revision")
    with pytest.raises(ValueError, match="exact tagged ref"):
        verify(tmp_path, "v0.2.0a1")


@pytest.mark.parametrize("tag", ["--help", "v0.2.0;echo", "main", "v0.2.0a", "v0.2.0/other"])
def test_release_rejects_non_version_refs(tmp_path, tag):
    verify = runpy.run_path("scripts/verify_release.py")["verify_release"]
    with pytest.raises(ValueError, match="version tag"):
        verify(tmp_path, tag)
