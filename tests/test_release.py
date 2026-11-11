"""Release validation and publication checks without GitHub writes."""

import io
import json
import re
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_release import check_release, release_version
from scripts.publish_release import publish_release, release_notes


@pytest.mark.parametrize("tag", ["0.0.0", "1.2.3", "10.20.30"])
def test_release_version(tag):
    assert release_version(tag) == tag


@pytest.mark.parametrize(
    "tag",
    [
        "latest", "1.2", "1.2.3.4", "v1.2.3", "01.2.3", "1.02.3", "1.2.03",
        "1.2.3a1", "1.2.3b1", "1.2.3rc1", "1.2.3+local", "1..3", "１.2.3",
    ],
)
def test_invalid_release_version(tag):
    with pytest.raises(ValueError):
        release_version(tag)


@pytest.mark.parametrize("version", ["1.2.3", "1.2.4"])
def test_distribution_versions(tmp_path, version):
    metadata = f"Name: mcp-postgresql-ops\nVersion: {version}\n".encode()
    with zipfile.ZipFile(tmp_path / "package.whl", "w") as archive:
        archive.writestr("package.dist-info/METADATA", metadata)
    with tarfile.open(tmp_path / "package.tar.gz", "w:gz") as archive:
        info = tarfile.TarInfo("package/PKG-INFO")
        info.size = len(metadata)
        archive.addfile(info, io.BytesIO(metadata))
    if version == "1.2.3":
        check_release("1.2.3", tmp_path)
    else:
        with pytest.raises(ValueError, match="expected"):
            check_release("1.2.3", tmp_path)


def test_notes_use_previous_release_and_preserve_messages():
    message = "Fix issue\n\n```\n$(touch unwanted)\n```"
    with patch("scripts.publish_release.command") as command:
        command.side_effect = ["new", "old", "", f"abcdef123\0{message}\0"]
        notes = release_notes("owner/repo", "1.2.3", "1.2.2")
    assert message in notes
    assert "````text" in notes
    assert "compare/1.2.2...1.2.3" in notes
    assert command.call_args.args[-2:] == ("old..new", "--")


@pytest.mark.parametrize("draft", [False, True])
def test_existing_release_is_not_overwritten(draft):
    with patch("scripts.publish_release.command") as command:
        command.side_effect = [
            "sha", "sha", "sha",
            json.dumps([[{"tag_name": "1.2.3", "draft": draft}]]),
        ]
        if draft:
            with pytest.raises(ValueError, match="draft"):
                publish_release("owner/repo", "1.2.3")
        else:
            publish_release("owner/repo", "1.2.3")
    assert command.call_count == 4


def test_first_release_creation():
    with patch("scripts.publish_release.command") as command:
        command.side_effect = ["sha", "sha", "sha", "[[]]", "sha", "", ""]
        publish_release("owner/repo", "1.2.3")
    args = command.call_args.args
    assert args[:3] == ("gh", "release", "create")
    assert args[3] == "1.2.3"
    assert "--prerelease" not in args
    assert "--latest=false" not in args


def test_release_creation_attaches_assets(tmp_path):
    bundle = tmp_path / "mcp-postgresql-ops-1.2.3.mcpb"
    bundle.write_bytes(b"bundle")
    with patch("scripts.publish_release.command") as command:
        command.side_effect = ["sha", "sha", "sha", "[[]]", "sha", "", ""]
        publish_release("owner/repo", "1.2.3", (str(bundle),))
    assert command.call_args.args[-1] == str(bundle)


def test_missing_release_asset_stops_publication(tmp_path):
    with patch("scripts.publish_release.command") as command:
        with pytest.raises(ValueError, match="assets not found"):
            publish_release(
                "owner/repo", "1.2.3", (str(tmp_path / "missing.mcpb"),)
            )
    command.assert_not_called()


def test_remote_tag_mismatch_stops_publication():
    with patch("scripts.publish_release.command") as command:
        command.side_effect = ["local", "remote"]
        with pytest.raises(ValueError, match="must match"):
            publish_release("owner/repo", "1.2.3")
    assert command.call_count == 2


@pytest.mark.parametrize("tag", ["v1.2.3", "1.2.3rc1"])
def test_invalid_tag_stops_publication(tag):
    with patch("scripts.publish_release.command") as command:
        with pytest.raises(ValueError):
            publish_release("owner/repo", tag)
    command.assert_not_called()


def test_mcpb_manifest_matches_server_configuration():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "mcpb" / "manifest.json").read_text())
    project = tomllib.loads((root / "pyproject.toml").read_text())
    server = manifest["server"]
    env = server["mcp_config"]["env"]
    config = manifest["user_config"]

    used = {
        match
        for value in env.values()
        for match in re.findall(r"\$\{user_config\.(\w+)\}", value)
    }
    assert used == set(config)
    assert config["postgres_password"]["sensitive"] is True
    assert server["type"] == "uv"
    assert server["entry_point"] == "server.py"
    assert server["mcp_config"]["args"][1:3] == ["--python", "3.12"]
    assert server["mcp_config"]["args"][-1] == "server.py"
    python_requirement = ">=3.12,<3.13"
    assert project["project"]["requires-python"] == python_requirement
    assert manifest["compatibility"]["runtimes"]["python"] == python_requirement
    assert (root / "mcpb" / "server.py").is_file()


def test_release_workflow_builds_and_attaches_mcpb():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/pypi-publish.yml").read_text()
    assert 'scripts/build-mcpb.sh "$RELEASE_TAG" mcpb-dist' in workflow
    assert "python -m pytest -q tests/test_release.py" in workflow
    assert "name: mcpb" in workflow
    assert (
        'python -m scripts.publish_release "$RELEASE_TAG" mcpb-dist/*.mcpb'
        in workflow
    )
