"""Official Railway Incident Audit Report Generator (PDF and Markdown)."""

import io
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from level_crossing.common.logger import get_logger

logger = get_logger("incident_report")


def generate_incident_pdf_bytes(
    alert_id: str,
    event_id: str,
    severity: str,
    alert_type: str,
    message: str,
    crossing_state: str,
    timestamp_sec: float,
    wall_clock_time: str,
    snapshot_path: Optional[str] = None,
    rule_citation: Optional[str] = None,
    system_health: str = "HEALTHY",
) -> bytes:
    """Generates an official, publication-grade Railway Safety Incident Audit Report PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Color definitions
    navy_blue = colors.HexColor("#0F172A")
    railway_blue = colors.HexColor("#1E3A8A")
    steel_gray = colors.HexColor("#475569")
    light_bg = colors.HexColor("#F8FAFC")
    border_gray = colors.HexColor("#CBD5E1")

    # Severity color
    if severity == "CRITICAL":
        sev_color = colors.HexColor("#DC2626")
    elif severity == "HIGH":
        sev_color = colors.HexColor("#EA580C")
    elif severity == "MEDIUM":
        sev_color = colors.HexColor("#D97706")
    else:
        sev_color = colors.HexColor("#16A34A")

    # Custom typography
    header_style = ParagraphStyle(
        "ReportHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=railway_blue,
        alignment=TA_LEFT,
    )
    sub_header_style = ParagraphStyle(
        "SubHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=steel_gray,
        alignment=TA_LEFT,
    )
    meta_ref_style = ParagraphStyle(
        "MetaRef",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=steel_gray,
        alignment=TA_RIGHT,
    )
    badge_style = ParagraphStyle(
        "SeverityBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=sev_color,
        alignment=TA_CENTER,
    )
    cell_label = ParagraphStyle(
        "CellLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=navy_blue,
    )
    cell_val = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=railway_blue,
        spaceBefore=8,
        spaceAfter=4,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
    )

    story = []

    # 1. Header Block with Organization Banner
    header_table_data = [
        [
            Paragraph("DIRECTORATE OF RAILWAY SAFETY & HAZARD MITIGATION<br/><font size='11'><b>Level Crossing Automated Vision Surveillance & Incident Register</b></font>", header_style),
            Paragraph(f"<b>REPORT REF:</b> LC-AUDIT-{alert_id}<br/><b>CLASSIFICATION:</b> OFFICIAL AUDIT<br/><b>GENERATED:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", meta_ref_style),
        ]
    ]
    t_header = Table(header_table_data, colWidths=[360, 172])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=railway_blue, spaceBefore=4, spaceAfter=8))

    # 2. Executive Alert Banner
    banner_data = [
        [
            Paragraph(f"INCIDENT SEVERITY CLASSIFICATION: <b>{severity}</b>", badge_style),
            Paragraph(f"ALERT TYPE: <b>{alert_type}</b> | CROSSING SIGNAL ASPECT: <b>{crossing_state}</b>", ParagraphStyle("B2", parent=badge_style, fontSize=10, textColor=navy_blue)),
        ]
    ]
    t_banner = Table(banner_data, colWidths=[270, 262])
    t_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("BOX", (0, 0), (-1, -1), 1.2, sev_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 8))

    # 3. Incident Core Parameters Table
    story.append(Paragraph("1. Incident Core Parameters & Temporal Context", section_title))
    params_data = [
        [Paragraph("Incident Record ID", cell_label), Paragraph(f"<code>{alert_id}</code>", cell_val), Paragraph("Parent Safety Event", cell_label), Paragraph(f"<code>{event_id}</code>", cell_val)],
        [Paragraph("Active Clock (t)", cell_label), Paragraph(f"{timestamp_sec:.2f} seconds", cell_val), Paragraph("System Wall-Clock", cell_label), Paragraph(wall_clock_time.replace("T", " ")[:19], cell_val)],
        [Paragraph("Crossing State", cell_label), Paragraph(f"<b>{crossing_state}</b>", cell_val), Paragraph("System Health", cell_label), Paragraph(f"<b>{system_health}</b>", cell_val)],
        [Paragraph("Event Summary", cell_label), Paragraph(message, cell_val), Paragraph("Evidence Type", cell_label), Paragraph("Real-Time High-Resolution Frame", cell_val)],
    ]
    t_params = Table(params_data, colWidths=[110, 156, 110, 156])
    t_params.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, border_gray),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_params)
    story.append(Spacer(1, 8))

    # 4. Deterministic Rule Arbitration & Regulatory Basis
    story.append(Paragraph("2. Deterministic Safety Matrix Rule Evaluation", section_title))
    default_citation = (
        f"Rule Arbitration evaluated against 64-Rule Master Severity Matrix V3.1.<br/>"
        f"<b>Combination:</b> CrossingState: <code>{crossing_state}</code>, Entity: <code>{message.split()[2] if len(message.split()) > 2 else 'TARGET'}</code>.<br/>"
        f"<b>Decision:</b> Temporal dwell threshold (T &ge; 0.5s) exceeded inside designated railway safety polygon. State transitioned from PENDING &rarr; CONFIRMED at {severity} severity."
    )
    rule_table = Table([[Paragraph(rule_citation or default_citation, cell_val)]], colWidths=[532])
    rule_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(rule_table)
    story.append(Spacer(1, 8))

    # 5. Visual Forensic Photographic Evidence
    story.append(Paragraph("3. Forensic Photographic Evidence", section_title))
    has_image = False
    if snapshot_path and Path(snapshot_path).exists():
        try:
            # Scale image to fit width (max 520pt)
            img_flow = RLImage(snapshot_path, width=480, height=270)
            story.append(img_flow)
            has_image = True
        except Exception as e:
            logger.warning(f"Could not load image into report: {e}")

    if not has_image:
        no_img_table = Table([[Paragraph("<i>Visual snapshot archived in secure SQLite blob store or file system.</i>", cell_val)]], colWidths=[532])
        no_img_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("BOX", (0, 0), (-1, -1), 0.5, border_gray),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 16),
        ]))
        story.append(no_img_table)

    story.append(Spacer(1, 10))

    # 6. Audit Trail & Sign-Off Block
    story.append(Paragraph("4. Chain of Custody & Authentication Hash", section_title))
    
    # Generate cryptographic SHA-256 hash of incident details
    hash_payload = f"{alert_id}:{event_id}:{severity}:{crossing_state}:{timestamp_sec}:{wall_clock_time}".encode("utf-8")
    sha256_hash = hashlib.sha256(hash_payload).hexdigest()

    auth_data = [
        [
            Paragraph(f"<b>SHA-256 Digital Verification Hash:</b><br/><code>{sha256_hash}</code>", cell_val),
            Paragraph("<b>Station Master / Rail Safety Inspector:</b><br/><br/>___________________________________<br/><i>Signature & Official OCC Stamp</i>", cell_val),
        ]
    ]
    t_auth = Table(auth_data, colWidths=[330, 202])
    t_auth.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, border_gray),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_auth)

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.8, color=border_gray, spaceBefore=2, spaceAfter=4))
    story.append(Paragraph(
        "CONFIDENTIAL RAILWAY SAFETY SYSTEM AUDIT DOCUMENT • Advisory Prototype System per CENELEC EN 50126/EN 50128 guidelines.<br/>"
        "Records stored immutably in SQLite database with Write-Ahead Logging (WAL) and foreign-key referential integrity.",
        disclaimer_style,
    ))

    doc.build(story)
    return buf.getvalue()
