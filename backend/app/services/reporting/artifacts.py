"""Phase 6 Step 5 — report artifact files for HTML/PDF export.

JSON reports stay inline in reports.content (the ReportStore contract). HTML
and PDF reports are rendered once at save time and written as artifact files;
reports.file_path records the real on-disk location so the download endpoint
can serve the persisted artifact verbatim without re-rendering or
re-generating the report.
"""

import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

from app.services.reporting.generator import InvalidReportTypeError
from app.services.reporting.render import ARTIFACT_FORMATS, render_report

ARTIFACT_DIR_ENV_VAR = "LEDGERLENS_REPORT_DIR"

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class ReportArtifactError(Exception):
    """Base class for report artifact file errors."""


class ReportArtifactNotFoundError(ReportArtifactError):
    """Raised when a persisted report artifact cannot be located."""


def default_report_artifact_dir() -> Path:
    """Resolve the artifact directory (env override, else backend/var/reports)."""
    configured = os.environ.get(ARTIFACT_DIR_ENV_VAR)
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / "var" / "reports"


def _safe_label(value: Any, fallback: str) -> str:
    label = _UNSAFE_FILENAME_CHARS.sub("_", str(value or "")).strip("._-")
    return label or fallback


class ReportArtifactStore:
    """Writes and reads rendered report artifact files."""

    def __init__(self, root_dir: Optional[Union[str, Path]] = None) -> None:
        self._root = (
            Path(root_dir).expanduser()
            if root_dir is not None
            else default_report_artifact_dir()
        )

    @property
    def root_dir(self) -> Path:
        return self._root

    def path_for(self, report: Dict[str, Any], report_id: Union[uuid.UUID, str]) -> Path:
        report_format = report.get("format")
        if report_format not in ARTIFACT_FORMATS:
            raise InvalidReportTypeError(
                f"Format {report_format!r} does not produce an artifact file; "
                f"artifact formats are {', '.join(ARTIFACT_FORMATS)}"
            )
        case_label = _safe_label(
            report.get("case_number"),
            f"case-{str(report.get('case_id') or 'unknown')[:8]}",
        )
        return self._root / f"{case_label}_report_{report_id}.{report_format}"

    def write(self, report: Dict[str, Any], report_id: Union[uuid.UUID, str]) -> str:
        """Render and persist an artifact file; returns its absolute path."""
        path = self.path_for(report, report_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(render_report(report, str(report.get("format"))))
        return str(path)

    def read(self, file_path: Union[str, Path]) -> bytes:
        """Read a previously persisted artifact, refusing paths outside the root."""
        try:
            resolved = Path(file_path).expanduser().resolve()
            root = self._root.resolve()
        except OSError as exc:
            raise ReportArtifactNotFoundError(
                f"Report artifact {file_path} could not be resolved"
            ) from exc
        if not resolved.is_relative_to(root):
            raise ReportArtifactNotFoundError(
                f"Report artifact {file_path} is outside the artifact directory"
            )
        if not resolved.is_file():
            raise ReportArtifactNotFoundError(f"Report artifact {file_path} not found")
        return resolved.read_bytes()


def get_report_artifact_store(
    root_dir: Optional[Union[str, Path]] = None,
) -> ReportArtifactStore:
    return ReportArtifactStore(root_dir)
