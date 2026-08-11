import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.alert import AlertSummary
from app.schemas.dashboard import DashboardSummary
from app.schemas.machine import MachineDetail, MachineLocalAdmin, MachineMetric, MachineProgram
from app.schemas.security_event import SecurityEventSummary

_STYLES = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle("ReportTitle", parent=_STYLES["Title"], fontSize=18)
_SECTION_STYLE = ParagraphStyle("ReportSection", parent=_STYLES["Heading2"], spaceBefore=12)

_TABLE_STYLE = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
)


def _generated_at_label() -> str:
    return f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"


def _table(headers: list[str], rows: list[list[str]], column_widths: list[float] | None = None) -> Table:
    table = Table([headers] + rows, colWidths=column_widths, repeatRows=1)
    table.setStyle(_TABLE_STYLE)
    return table


def _format_datetime(value: datetime | None) -> str:
    return value.strftime("%d/%m/%Y %H:%M") if value else "-"


def _build_pdf(story: list) -> bytes:
    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    ).build(story)
    return buffer.getvalue()


def build_executive_report_pdf(*, summary: DashboardSummary) -> bytes:
    story: list = [
        Paragraph("IT Center Security Cloud", _TITLE_STYLE),
        Paragraph("Relatorio Executivo", _STYLES["Heading3"]),
        Paragraph(_generated_at_label(), _STYLES["Normal"]),
        Spacer(1, 0.5 * cm),
        _table(
            ["Indicador", "Valor"],
            [
                ["Maquinas monitoradas", str(summary.machines_total)],
                ["Maquinas online", str(summary.machines_online)],
                ["Maquinas offline", str(summary.machines_offline)],
                ["Alertas abertos", str(summary.alerts_open_total)],
                ["Alertas baixa severidade", str(summary.alerts_open_by_severity.low)],
                ["Alertas media severidade", str(summary.alerts_open_by_severity.medium)],
                ["Alertas alta severidade", str(summary.alerts_open_by_severity.high)],
                ["Alertas criticos", str(summary.alerts_open_by_severity.critical)],
            ],
        ),
        Spacer(1, 0.8 * cm),
        Paragraph("Eventos de seguranca recentes", _SECTION_STYLE),
    ]

    if summary.recent_events:
        story.append(
            _table(
                ["Data", "Maquina", "Tipo", "Severidade", "Descricao"],
                [
                    [
                        _format_datetime(event.created_at),
                        str(event.machine_id) if event.machine_id is not None else "-",
                        event.event_type,
                        event.severity,
                        event.description[:120],
                    ]
                    for event in summary.recent_events
                ],
                column_widths=[3 * cm, 2 * cm, 3.5 * cm, 2.5 * cm, 6 * cm],
            )
        )
    else:
        story.append(Paragraph("Nenhum evento registrado.", _STYLES["Normal"]))

    return _build_pdf(story)


def build_machine_report_pdf(
    *,
    machine: MachineDetail,
    metrics: list[MachineMetric],
    programs: list[MachineProgram],
    admins: list[MachineLocalAdmin],
    alerts: list[AlertSummary],
    events: list[SecurityEventSummary],
) -> bytes:
    latest_metric = metrics[0] if metrics else None
    operating_system = f"{machine.operating_system or '-'} {machine.os_version or ''}".strip()

    story: list = [
        Paragraph("IT Center Security Cloud", _TITLE_STYLE),
        Paragraph(f"Relatorio da maquina {machine.hostname}", _STYLES["Heading3"]),
        Paragraph(_generated_at_label(), _STYLES["Normal"]),
        Spacer(1, 0.5 * cm),
        _table(
            ["Campo", "Valor"],
            [
                ["Hostname", machine.hostname],
                ["Usuario", machine.username or "-"],
                ["IP", machine.ip_address or "-"],
                ["Sistema operacional", operating_system],
                ["Status", machine.status],
                ["Ultimo check-in", _format_datetime(machine.last_seen)],
                ["CPU (ultima coleta)", f"{latest_metric.cpu_usage:.1f}%" if latest_metric else "-"],
                ["RAM (ultima coleta)", f"{latest_metric.ram_usage:.1f}%" if latest_metric else "-"],
                ["Disco (ultima coleta)", f"{latest_metric.disk_usage:.1f}%" if latest_metric else "-"],
            ],
        ),
        Spacer(1, 0.8 * cm),
        Paragraph("Alertas", _SECTION_STYLE),
    ]

    if alerts:
        story.append(
            _table(
                ["Data", "Tipo", "Severidade", "Status", "Titulo"],
                [
                    [
                        _format_datetime(alert.created_at),
                        alert.alert_type,
                        alert.severity,
                        alert.status,
                        alert.title,
                    ]
                    for alert in alerts
                ],
            )
        )
    else:
        story.append(Paragraph("Nenhum alerta registrado para esta maquina.", _STYLES["Normal"]))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("Eventos de seguranca", _SECTION_STYLE))

    if events:
        story.append(
            _table(
                ["Data", "Tipo", "Severidade", "Descricao"],
                [
                    [
                        _format_datetime(event.created_at),
                        event.event_type,
                        event.severity,
                        event.description[:150],
                    ]
                    for event in events[:20]
                ],
                column_widths=[3 * cm, 4 * cm, 2.5 * cm, 8 * cm],
            )
        )
    else:
        story.append(Paragraph("Nenhum evento registrado para esta maquina.", _STYLES["Normal"]))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("Programas instalados", _SECTION_STYLE))

    if programs:
        story.append(
            _table(
                ["Nome", "Versao", "Publicador"],
                [[program.name, program.version or "-", program.publisher or "-"] for program in programs[:200]],
            )
        )
    else:
        story.append(Paragraph("Nenhum programa registrado.", _STYLES["Normal"]))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("Administradores locais", _SECTION_STYLE))

    if admins:
        story.append(
            _table(
                ["Conta", "Primeira deteccao", "Ultima deteccao"],
                [
                    [
                        admin.admin_name,
                        _format_datetime(admin.first_seen_at),
                        _format_datetime(admin.last_seen_at),
                    ]
                    for admin in admins
                ],
            )
        )
    else:
        story.append(Paragraph("Nenhum administrador local registrado.", _STYLES["Normal"]))

    return _build_pdf(story)
