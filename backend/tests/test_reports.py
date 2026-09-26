import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.dashboard import AlertSeverityCounts, DashboardSummary
from app.schemas.machine import MachineDetail
from app.services import reports
from app.services.reports import build_executive_report_pdf, build_machine_report_pdf


@pytest.fixture(autouse=True)
def clean_database():
    """No database needed for report generation tests."""
    pass


def test_build_machine_report_pdf_escapes_xml_tags_in_hostname(monkeypatch):
    captured_story = []
    orig_build_pdf = reports._build_pdf

    def capture_build(story):
        captured_story.extend(story)
        return orig_build_pdf(story)

    monkeypatch.setattr(reports, "_build_pdf", capture_build)

    machine = MachineDetail(
        id=1,
        hostname="PC-CORP<script>alert(1)</script>&<b>test</b>",
        status="online",
        last_seen=None,
    )

    pdf_bytes = build_machine_report_pdf(
        machine=machine,
        metrics=[],
        programs=[],
        admins=[],
        alerts=[],
        events=[],
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")

    heading_paragraph = next(
        p for p in captured_story if hasattr(p, "text") and "Relatorio da maquina" in p.text
    )
    assert "PC-CORP&lt;script&gt;alert(1)&lt;/script&gt;&amp;&lt;b&gt;test&lt;/b&gt;" in heading_paragraph.text


def test_build_machine_report_pdf_with_malformed_xml_does_not_crash():
    machine = MachineDetail(
        id=1,
        hostname="PC-CORP<unclosed",
        status="online",
        last_seen=None,
    )

    pdf_bytes = build_machine_report_pdf(
        machine=machine,
        metrics=[],
        programs=[],
        admins=[],
        alerts=[],
        events=[],
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")


def test_build_executive_report_pdf_returns_valid_pdf():
    summary = DashboardSummary(
        machines_total=10,
        machines_online=8,
        machines_offline=2,
        alerts_open_total=3,
        alerts_open_by_severity=AlertSeverityCounts(low=1, medium=1, high=1, critical=0),
        recent_events=[],
    )

    pdf_bytes = build_executive_report_pdf(summary=summary)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
