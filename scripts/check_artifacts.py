"""Inspect distribution manifests, not only Git ignore rules."""

import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

license_text = (Path(__file__).resolve().parents[1] / "LICENSE").read_bytes()
root = Path(sys.argv[1])
archives = list(root.glob("*.whl")) + list(root.glob("*.tar.gz"))
assert len(archives) == 2, "Expected one wheel and one source archive"
for archive in archives:
    if archive.suffix == ".whl":
        with zipfile.ZipFile(archive) as item:
            names = item.namelist()
            licences = [n for n in names if n.endswith(".dist-info/licenses/LICENSE")]
            assert len(licences) == 1, "Wheel must include the MIT licence"
            assert item.read(licences[0]) == license_text, "Wheel licence differs from source"
            metadata = next(n for n in names if n.endswith(".dist-info/METADATA"))
            assert BytesParser().parsebytes(item.read(metadata))["License-Expression"] == "MIT"
    else:
        with tarfile.open(archive) as item:
            names = item.getnames()
            licences = [n for n in names if n.endswith("/LICENSE")]
            assert len(licences) == 1, "Source distribution must include the MIT licence"
            licence = item.extractfile(licences[0])
            assert licence is not None and licence.read() == license_text
            metadata = next(n for n in names if n.endswith("/PKG-INFO"))
            metadata_file = item.extractfile(metadata)
            assert metadata_file is not None
            assert BytesParser().parsebytes(metadata_file.read())["License-Expression"] == "MIT"
    for name in names:
        parts = Path(name).parts
        assert not set(parts) & {
            ".claude",
            ".git",
            ".github",
            ".venv",
            "__pycache__",
            "AGENTS.md",
            "CLAUDE.md",
        }, name
        assert not any(p.startswith(".env") and not p.endswith(".example") for p in parts), name
        assert not name.endswith((".pyc", ".log", ".key", ".pem")), name
    print(f"Archive clean: {archive.name} ({len(names)} entries)")
