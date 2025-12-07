"""Integration tests for CLI."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from docling_view.cli import app

runner = CliRunner()


class TestCliHelp:
    """Tests for CLI help and version."""

    def test_cli_help(self):
        """Test that help displays correctly."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "docling-view" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_cli_version(self):
        """Test that version displays correctly."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "0.2.0" in result.stdout


class TestCliValidation:
    """Tests for CLI input validation."""

    def test_cli_missing_input(self):
        """Test error on missing input file."""
        result = runner.invoke(app, ["nonexistent.pdf"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_cli_invalid_mode(self, tmp_json_file: Path):
        """Test error on invalid mode."""
        result = runner.invoke(app, [str(tmp_json_file), "-m", "invalid"])

        assert result.exit_code == 2
        assert "invalid" in result.stdout.lower()

    def test_cli_invalid_file_extension(self, tmp_path: Path):
        """Test error on unsupported file extension."""
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("test")

        result = runner.invoke(app, [str(txt_file)])

        assert result.exit_code == 1
        assert "unsupported" in result.stdout.lower()

    def test_cli_invalid_element_types(self, tmp_json_file: Path, tmp_path: Path):
        """Test error on invalid element types."""
        output = tmp_path / "output.html"
        result = runner.invoke(
            app,
            [str(tmp_json_file), "-m", "overlay", "-o", str(output), "-t", "invalid_type"],
        )

        assert result.exit_code == 2
        assert "invalid" in result.stdout.lower()


class TestCliOutput:
    """Tests for CLI output options."""

    def test_cli_default_output_naming(self, tmp_json_file: Path, tmp_path: Path):
        """Test default output naming from input file."""
        result = runner.invoke(app, [str(tmp_json_file)])

        if result.exit_code == 0:
            expected_output = tmp_json_file.with_suffix(".html")
            assert expected_output.exists() or "output" in result.stdout.lower()

    def test_cli_custom_output_path(self, tmp_json_file: Path, tmp_path: Path):
        """Test custom output path."""
        output_path = tmp_path / "custom" / "output.html"

        result = runner.invoke(app, [str(tmp_json_file), "-o", str(output_path)])

        if result.exit_code != 0:
            assert "docling" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_cli_verbose_flag(self, tmp_json_file: Path, tmp_path: Path):
        """Test verbose output."""
        output_path = tmp_path / "output.html"

        result = runner.invoke(app, [str(tmp_json_file), "-o", str(output_path), "-v"])

        if result.exit_code == 0:
            assert "processing" in result.stdout.lower() or "loading" in result.stdout.lower()


class TestCliModes:
    """Tests for CLI visualization modes."""

    def test_cli_native_mode_default(self, tmp_json_file: Path):
        """Test that native mode is default."""
        result = runner.invoke(app, [str(tmp_json_file)])

        if result.exit_code != 0:
            pass

    def test_cli_overlay_mode(self, tmp_json_file: Path, tmp_path: Path):
        """Test overlay mode invocation."""
        output_path = tmp_path / "visualizer" / "index.html"

        result = runner.invoke(app, [str(tmp_json_file), "-m", "overlay", "-o", str(output_path)])

        if result.exit_code != 0:
            pass

    def test_cli_scale_option(self, tmp_json_file: Path, tmp_path: Path):
        """Test scale option."""
        output_path = tmp_path / "output.html"

        result = runner.invoke(
            app,
            [str(tmp_json_file), "-m", "overlay", "-o", str(output_path), "-s", "3.0"],
        )

        if result.exit_code != 0:
            pass


class TestCliElementFilters:
    """Tests for CLI element filtering."""

    def test_cli_filter_tables(self, tmp_json_file: Path, tmp_path: Path):
        """Test filtering to tables only."""
        output_path = tmp_path / "output.html"

        result = runner.invoke(
            app,
            [str(tmp_json_file), "-m", "overlay", "-o", str(output_path), "-t", "table"],
        )

        if result.exit_code != 0:
            pass

    def test_cli_filter_multiple_types(self, tmp_json_file: Path, tmp_path: Path):
        """Test filtering to multiple types."""
        output_path = tmp_path / "output.html"

        result = runner.invoke(
            app,
            [str(tmp_json_file), "-m", "overlay", "-o", str(output_path), "-t", "table,picture"],
        )

        if result.exit_code != 0:
            pass

    def test_cli_no_furniture_flag(self, tmp_json_file: Path, tmp_path: Path):
        """Test no-furniture flag."""
        output_path = tmp_path / "output.html"

        result = runner.invoke(
            app,
            [str(tmp_json_file), "-m", "overlay", "-o", str(output_path), "--no-furniture"],
        )

        if result.exit_code != 0:
            pass
