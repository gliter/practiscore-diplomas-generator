import base64
from pathlib import Path
import struct

import pytest

from practiscore_diplomas import help_viewer


@pytest.mark.parametrize("language", ["pl", "en"])
def test_help_displays_the_exact_readme_outside_project(monkeypatch, tmp_path, language):
    source = Path(__file__).resolve().parents[1] / "docs" / f"README.{language}.md"
    monkeypatch.chdir(tmp_path)

    assert help_viewer._load_help(language) == source.read_text(encoding="utf-8")


def test_help_falls_back_to_english_for_unknown_language():
    assert help_viewer._load_help("de") == help_viewer._load_help("en")


@pytest.mark.parametrize("language", ["pl", "en"])
def test_frozen_app_reads_the_documentation_beside_executable(monkeypatch, tmp_path, language):
    docs = tmp_path / "docs"
    docs.mkdir()
    expected = f"# Current external README ({language})"
    (docs / f"README.{language}.md").write_text(expected, encoding="utf-8")
    monkeypatch.setattr(help_viewer.sys, "frozen", True, raising=False)
    monkeypatch.setattr(help_viewer.sys, "executable", str(tmp_path / "app.exe"))

    assert help_viewer._load_help(language) == expected


def test_help_uses_bundled_readme_when_external_documentation_is_absent(monkeypatch, tmp_path):
    bundled = tmp_path / "package"
    (bundled / "docs").mkdir(parents=True)
    expected = "# Bundled user guide"
    (bundled / "docs" / "README.pl.md").write_text(expected, encoding="utf-8")
    monkeypatch.setattr(help_viewer.sys, "frozen", True, raising=False)
    monkeypatch.setattr(help_viewer.sys, "executable", str(tmp_path / "app.exe"))
    monkeypatch.setattr(help_viewer, "files", lambda package: bundled)

    assert help_viewer._load_help("pl") == expected


@pytest.mark.parametrize("language", ["pl", "en"])
def test_readme_images_are_rendered_from_documentation_directory(monkeypatch, tmp_path, language):
    expected_directory = Path(__file__).resolve().parents[1] / "docs"
    image_data = []

    class Picture:
        def __init__(self, master, data):
            raw = base64.b64decode(data)
            image_data.append(raw)
            self.size = struct.unpack(">II", raw[16:24])

        def width(self):
            return self.size[0]

        def subsample(self, scale):
            self.size = tuple(value // scale for value in self.size)
            return self

    class Text:
        def __init__(self):
            self.images = []
            self.lines = []

        def image_create(self, index, image):
            self.images.append(image)

        def insert(self, index, value, *tags):
            self.lines.append(value)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(help_viewer.tk, "PhotoImage", Picture)
    text = Text()

    retained_images = help_viewer._populate_help(text, help_viewer._load_help(language), language, 600)

    assert image_data == [(expected_directory / name).read_bytes() for name in ("psc-1.png", "psc-2.png")]
    assert retained_images == text.images
    assert len(retained_images) == 2
    assert all(image.width() <= 600 for image in retained_images)
    assert not any("![" in line for line in text.lines)


def test_images_are_read_from_bundled_documentation_in_standalone_executable(monkeypatch, tmp_path):
    directory = Path(__file__).resolve().parents[1] / "docs"
    bundled = tmp_path / "package"
    (bundled / "docs").mkdir(parents=True)
    expected = (directory / "psc-1.png").read_bytes()
    (bundled / "docs" / "psc-1.png").write_bytes(expected)
    monkeypatch.setattr(help_viewer.sys, "frozen", True, raising=False)
    monkeypatch.setattr(help_viewer.sys, "executable", str(tmp_path / "app.exe"))
    monkeypatch.setattr(help_viewer, "files", lambda package: bundled)
    received = []

    class Picture:
        def __init__(self, master, data):
            received.append(base64.b64decode(data))

        def width(self):
            return 400

    monkeypatch.setattr(help_viewer.tk, "PhotoImage", Picture)

    image = help_viewer._help_photo(object(), "pl", "psc-1.png", 600)

    assert isinstance(image, Picture)
    assert received == [expected]
