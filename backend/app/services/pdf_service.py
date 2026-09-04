import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_inspection_pdf(inspection_data: dict) -> bytes:
    """Generate an institutional PDF Inspection Report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles matching government design
    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0B192C'),
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'GovSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_LEFT
    )

    section_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0B192C'),
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'GovBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("GOVERNMENT OF INDIA", ParagraphStyle('GovTop', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#475569'))))
    story.append(Paragraph("Department of Legal Metrology", title_style))
    story.append(Paragraph("Ministry of Consumer Affairs, Food & Public Distribution | Compliance Checker System", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0B192C'), spaceBefore=2, spaceAfter=12))

    # 2. Inspection Metadata Box
    insp_id = inspection_data.get("inspection_id", "N/A")
    created_at = str(inspection_data.get("created_at", "N/A"))[:19]
    score = inspection_data.get("compliance_score")
    status = inspection_data.get("status") or inspection_data.get("overall_status", "NEEDS_REVIEW")
    officer_name = inspection_data.get("officer_name") or inspection_data.get("reviewed_by_name", "Inspector")
    notes = inspection_data.get("officer_review_notes", "")
    reviewed_at = str(inspection_data.get("reviewed_at", ""))[:19]

    if status in ["COMPLIANT", "RESOLVED"]:
        status_color = colors.HexColor('#16A34A')
    elif status == "NEEDS_REVIEW":
        status_color = colors.HexColor('#D97706')
    else:
        status_color = colors.HexColor('#DC2626')

    score_text = f"{score}%" if score is not None else "N/A"

    meta_table_data = [
        [
            Paragraph(f"<b>INSPECTION ID:</b> #{insp_id}", body_style),
            Paragraph(f"<b>OFFICER:</b> {officer_name}", body_style),
            Paragraph(f"<b>STATUS:</b> <font color='{status_color.hexval()}'><b>{status}</b></font>", body_style),
            Paragraph(f"<b>SCORE:</b> <font color='{status_color.hexval()}'><b>{score_text}</b></font>", body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[150, 150, 130, 110])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 3. Product Details Section
    story.append(Paragraph("Product Information", section_heading))
    p_info = inspection_data.get("product_information", {})
    prod_data = [
        [Paragraph("<b>Product Name:</b>", body_style), Paragraph(p_info.get("product_name", "N/A"), body_style),
         Paragraph("<b>Net Quantity:</b>", body_style), Paragraph(p_info.get("net_quantity", "N/A"), body_style)],
        [Paragraph("<b>Commodity:</b>", body_style), Paragraph(p_info.get("commodity", "N/A"), body_style),
         Paragraph("<b>MRP (Incl. taxes):</b>", body_style), Paragraph(p_info.get("mrp", "N/A"), body_style)],
        [Paragraph("<b>Mfg / Pack Date:</b>", body_style), Paragraph(p_info.get("mfg_date", "N/A"), body_style),
         Paragraph("<b>Country of Origin:</b>", body_style), Paragraph(p_info.get("country_of_origin", "India"), body_style)],
        [Paragraph("<b>Manufacturer:</b>", body_style), Paragraph(p_info.get("manufacturer", "N/A"), body_style),
         Paragraph("<b>Consumer Care:</b>", body_style), Paragraph(p_info.get("consumer_care", "N/A"), body_style)],
    ]
    prod_table = Table(prod_data, colWidths=[100, 170, 100, 170])
    prod_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(prod_table)
    story.append(Spacer(1, 14))

    # 4. Compliance Checks Ledger Table
    story.append(Paragraph("Compliance Checks Ledger (PCR 2011)", section_heading))
    checks = inspection_data.get("compliance_checks", [])
    ledger_data = [[
        Paragraph("REQUIREMENT", table_header_style),
        Paragraph("EXTRACTED VALUE", table_header_style),
        Paragraph("RULE REF", table_header_style),
        Paragraph("STATUS", table_header_style)
    ]]

    for c in checks:
        st = c.get("status", "PASS")
        st_color = "#16A34A" if st == "PASS" else ("#DC2626" if st == "FAIL" else "#F59E0B")
        ledger_data.append([
            Paragraph(c.get("requirement", ""), body_style),
            Paragraph(c.get("extracted_value", ""), body_style),
            Paragraph(c.get("source_reference", "") or c.get("rule_id", ""), body_style),
            Paragraph(f"<font color='{st_color}'><b>{st}</b></font>", body_style)
        ])

    ledger_table = Table(ledger_data, colWidths=[170, 170, 110, 90])
    ledger_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(ledger_table)
    story.append(Spacer(1, 14))

    # 5. Manual Review Resolution Section (if resolved)
    if status == "RESOLVED" or inspection_data.get("review_status") == "RESOLVED":
        story.append(Paragraph("Manual Verification & Officer Resolution", section_heading))
        res_data = [
            [Paragraph("<b>Verification Status:</b>", body_style), Paragraph("<font color='#16A34A'><b>Manual Review Completed</b></font>", body_style)],
            [Paragraph("<b>Reviewing Officer:</b>", body_style), Paragraph(officer_name, body_style)],
            [Paragraph("<b>Resolution Timestamp:</b>", body_style), Paragraph(reviewed_at or created_at, body_style)],
            [Paragraph("<b>Officer Review Notes:</b>", body_style), Paragraph(notes or "Physical package manually inspected and verified.", body_style)]
        ]
        res_table = Table(res_data, colWidths=[140, 400])
        res_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8FAFC')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 14))
    elif status == "NEEDS_REVIEW":
        story.append(Paragraph("Officer Verification Note", section_heading))
        note_table = Table([[Paragraph("<b>MANUAL VERIFICATION REQUIRED:</b> Automated analysis detected low-confidence or missing evidence. Physical package inspection is required before statutory enforcement.", body_style)]], colWidths=[540])
        note_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF3C7')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#F59E0B')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(note_table)
        story.append(Spacer(1, 14))

    # 6. Legal Disclaimer
    disc_text = (
        "<b>LEGAL DISCLAIMER:</b> This inspection report is generated automatically by the Legal Metrology "
        "Compliance Checker screening system based on OCR data extractions and rule algorithms. "
        "It serves as an assistive preliminary verification tool for authorized Legal Metrology Officers. "
        "Final legal determination and enforcement decisions remain with the statutory authority under the Legal Metrology Act, 2009."
    )
    disc_table = Table([[Paragraph(disc_text, ParagraphStyle('Disc', fontName='Helvetica-Oblique', fontSize=7.5, leading=10, textColor=colors.HexColor('#475569')))]], colWidths=[540])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(disc_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

