import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import database as db

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(_BASE_DIR, "reports")
CREATOR = "Favour Maina"
SCHOOL_NAME = "ELROI FAVOURED SCHOOL"
PO_BOX = "P.O. BOX 5527"

NAVY   = colors.HexColor("#1a2e4a")
GOLD   = colors.HexColor("#c9a84c")
LIGHT  = colors.HexColor("#f5f0e8")
WHITE  = colors.white
GREY   = colors.HexColor("#666666")
RED    = colors.HexColor("#c0392b")
GREEN  = colors.HexColor("#1e7e34")
MID    = colors.HexColor("#d0c9b8")


def fmt(n):
    """Format number as whole number with comma, e.g. 1,000"""
    try:
        return f"{int(round(float(n))):,}"
    except:
        return str(n)


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # ── Header ──
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 55*mm, w, 55*mm, fill=1, stroke=0)

    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 58*mm, w, 4*mm, fill=1, stroke=0)

    canvas.setFont("Helvetica-Bold", 20)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(w/2, h - 20*mm, SCHOOL_NAME)

    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(GOLD)
    canvas.drawCentredString(w/2, h - 29*mm, PO_BOX)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(MID)
    canvas.drawCentredString(w/2, h - 37*mm, f"Generated: {datetime.now().strftime('%d %B %Y  %H:%M')}")

    # ── Footer ──
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 14*mm, w, 1.5*mm, fill=1, stroke=0)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(15*mm, 5*mm, f"Created by: {CREATOR}")
    canvas.drawCentredString(w/2, 5*mm, SCHOOL_NAME)
    canvas.drawRightString(w - 15*mm, 5*mm, f"Page {doc.page}")

    canvas.restoreState()


def _build_doc(filename):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=62*mm, bottomMargin=22*mm,
        leftMargin=15*mm, rightMargin=15*mm
    )
    return doc, path


def _styles():
    s = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=s["Title"],
        fontSize=14, textColor=NAVY, spaceAfter=4, alignment=TA_CENTER,
        fontName="Helvetica-Bold")
    sub = ParagraphStyle("Sub", parent=s["Normal"],
        fontSize=10, textColor=GREY, alignment=TA_CENTER, spaceAfter=8)
    section = ParagraphStyle("Section", parent=s["Normal"],
        fontSize=12, textColor=WHITE, backColor=NAVY,
        fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=10,
        leftIndent=4, rightIndent=4, leading=18)
    normal = ParagraphStyle("Body", parent=s["Normal"], fontSize=9, textColor=NAVY)
    return title, sub, section, normal


# ════════════════════════════════════════════════════════════
#  STUDENT REGISTER — per class or whole school
# ════════════════════════════════════════════════════════════

def generate_student_register(class_filter=None):
    label = class_filter.replace(" ", "_") if class_filter else "WholeSchool"
    filename = f"StudentRegister_{label}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc, path = _build_doc(filename)
    title_style, sub_style, section_style, normal_style = _styles()

    story = []
    report_title = f"Student Register — {class_filter}" if class_filter else "Student Register — All Classes"
    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(f"Academic Year 2026", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8))

    classes = [class_filter] if class_filter else db.CLASSES

    for cls in classes:
        students = db.get_students_by_class(cls)
        # Teacher name (all students in class share teacher)
        teacher = students[0]["teacher"] if students and students[0]["teacher"] else "—"

        story.append(Paragraph(f"  {cls}", section_style))
        story.append(Paragraph(f"Class Teacher: {teacher}", ParagraphStyle(
            "teacher", fontSize=9, textColor=GREY, spaceAfter=4,
            fontName="Helvetica-Oblique"
        )))

        if not students:
            story.append(Paragraph("No students enrolled in this class.", normal_style))
            story.append(Spacer(1, 6))
            continue

        table_data = [["#", "Student ID", "Name", "Date of Birth", "Join Term"]]
        for i, st in enumerate(students, 1):
            dob = st["dob"] if st["dob"] else "—"
            join = st["join_term"] if st["is_new_student"] else "Term I"
            table_data.append([str(i), st["student_id"], st["name"], dob, join])

        col_widths = [10*mm, 30*mm, 70*mm, 35*mm, 25*mm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",    (0,0), (-1,0), WHITE),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 9),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("ALIGN",        (2,1), (2,-1), "LEFT"),
            ("FONTSIZE",     (0,1), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT]),
            ("GRID",         (0,0), (-1,-1), 0.4, MID),
            ("TOPPADDING",   (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Paragraph(f"Total Students: {len(students)}", ParagraphStyle(
            "count", fontSize=8, textColor=GREY, alignment=TA_RIGHT, spaceAfter=4,
            fontName="Helvetica-Bold"
        )))
        story.append(Spacer(1, 6))

        if not class_filter and cls != classes[-1]:
            story.append(PageBreak())

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return path


# ════════════════════════════════════════════════════════════
#  PAYMENT REPORT — single student, per class, or whole school
# ════════════════════════════════════════════════════════════

def _student_payment_block(student, story, section_style, normal_style, terms_filter=None):
    fees = db.get_student_fees(student["student_id"])
    if not fees:
        return

    active_terms = terms_filter if terms_filter else db.TERMS

    by_term = {}
    for f in fees:
        by_term.setdefault(f["term"], []).append(f)

    grand_owed = 0
    grand_paid = 0

    for term in active_terms:
        rows = by_term.get(term)
        if not rows:
            continue

        total_owed = sum(r["total_owed"] for r in rows)
        total_paid = sum(r["total_paid"] for r in rows)
        balance    = total_owed - total_paid
        grand_owed += total_owed
        grand_paid += total_paid

        # Main fee table
        table_data = [["Fee Category", "Total Owed", "Total Paid", "Balance", "Status"]]
        for r in rows:
            b = r["total_owed"] - r["total_paid"]
            status = "PAID" if b <= 0 else ("PARTIAL" if r["total_paid"] > 0 else "UNPAID")
            table_data.append([
                r["category"], fmt(r["total_owed"]), fmt(r["total_paid"]), fmt(b), status
            ])
        table_data.append(["TOTAL", fmt(total_owed), fmt(total_paid), fmt(balance), ""])

        col_widths = [55*mm, 28*mm, 28*mm, 28*mm, 22*mm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        status_colors = {"PAID": GREEN, "PARTIAL": colors.orange, "UNPAID": RED}
        style = TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 8),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("ALIGN",         (0,1), (0,-1), "LEFT"),
            ("FONTSIZE",      (0,1), (-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1), (-1,-2), [WHITE, LIGHT]),
            ("BACKGROUND",    (0,-1), (-1,-1), MID),
            ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
            ("GRID",          (0,0), (-1,-1), 0.4, MID),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ])
        for i, row in enumerate(table_data[1:-1], 1):
            sc = status_colors.get(row[4], GREY)
            style.add("TEXTCOLOR", (4,i), (4,i), sc)
            style.add("FONTNAME",  (4,i), (4,i), "Helvetica-Bold")
        t.setStyle(style)

        story.append(Paragraph(f"    {term}", ParagraphStyle(
            "termhead", fontSize=9, textColor=NAVY, fontName="Helvetica-Bold",
            spaceBefore=4, spaceAfter=2)))
        story.append(t)

        # Payment transactions sub-table per term
        all_payments = db.get_payment_history(student["student_id"], term=term)
        if all_payments:
            pay_data = [["Date", "Category", "Amount Paid", "Notes"]]
            for p in all_payments:
                d = p["paid_date"] or (p["paid_at"][:10] if p["paid_at"] else "—")
                pay_data.append([d, p["category"], f"Ksh {fmt(p['amount'])}", p["notes"] or ""])
            pt = Table(pay_data, colWidths=[25*mm, 55*mm, 30*mm, 51*mm], repeatRows=1)
            pt.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), GOLD),
                ("TEXTCOLOR",     (0,0), (-1,0), NAVY),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,0), 7),
                ("FONTSIZE",      (0,1), (-1,-1), 7),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("ALIGN",         (1,1), (1,-1), "LEFT"),
                ("ALIGN",         (3,1), (3,-1), "LEFT"),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT]),
                ("GRID",          (0,0), (-1,-1), 0.3, MID),
                ("TOPPADDING",    (0,0), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ]))
            story.append(Paragraph("    Payment Transactions:", ParagraphStyle(
                "payhead", fontSize=7, textColor=GREY, fontName="Helvetica-Oblique",
                spaceBefore=2, spaceAfter=1)))
            story.append(pt)

        bal_color = "green" if balance <= 0 else "red"
        story.append(Paragraph(
            f'<font color="{bal_color}"><b>Balance for {term}: Ksh {fmt(balance)}</b></font>',
            ParagraphStyle("bal", fontSize=8, alignment=TA_RIGHT, spaceAfter=3)))

    # Grand total (shown when more than one term selected)
    if len(active_terms) > 1:
        grand_balance = grand_owed - grand_paid
        grand_color = "green" if grand_balance <= 0 else "red"
        summary_data = [
            ["", "Total Owed", "Total Paid", "Total Balance", ""],
            ["ALL SELECTED TERMS", fmt(grand_owed), fmt(grand_paid), fmt(grand_balance), ""],
        ]
        gt = Table(summary_data, colWidths=[55*mm, 28*mm, 28*mm, 28*mm, 22*mm])
        gt.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",    (0,0), (-1,0), WHITE),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 8),
            ("BACKGROUND",   (0,1), (-1,1), GOLD),
            ("TEXTCOLOR",    (0,1), (-1,1), NAVY),
            ("FONTNAME",     (0,1), (-1,1), "Helvetica-Bold"),
            ("FONTSIZE",     (0,1), (-1,1), 9),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("ALIGN",        (0,1), (0,1), "LEFT"),
            ("GRID",         (0,0), (-1,-1), 0.6, NAVY),
            ("TOPPADDING",   (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(Spacer(1, 4))
        story.append(gt)
        story.append(Paragraph(
            f'<font color="{grand_color}"><b>GRAND BALANCE: Ksh {fmt(grand_balance)}</b></font>',
            ParagraphStyle("grand", fontSize=10, alignment=TA_RIGHT,
                           spaceBefore=2, spaceAfter=6, fontName="Helvetica-Bold")))


def _student_requirements_block(student, story, section_style, normal_style):
    """Flat requirements table — no terms, just what the student has brought."""
    reqs = db.get_student_requirements(student["student_id"])
    if not reqs:
        return

    story.append(Spacer(1, 8))
    story.append(Paragraph("  Requirements", ParagraphStyle(
        "reqhead", fontSize=11, textColor=WHITE, backColor=GOLD,
        fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=6,
        leftIndent=4, leading=16
    )))

    table_data = [["Requirement", "Required", "Brought", "Status"]]
    for r in reqs:
        brought  = r["brought"]
        required = r["required"]
        if brought >= required:
            status = "Complete"
        elif brought > 0:
            status = f"Partial ({brought}/{required})"
        else:
            status = "Missing"
        table_data.append([r["name"], str(required), str(brought), status])

    col_widths = [90*mm, 28*mm, 28*mm, 15*mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("ALIGN",         (0,1), (0,-1), "LEFT"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT]),
        ("GRID",          (0,0), (-1,-1), 0.4, MID),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ])
    for i, row in enumerate(table_data[1:], 1):
        color = GREEN if row[3] == "Complete" else (RED if row[3] == "Missing" else colors.orange)
        style.add("TEXTCOLOR", (3,i), (3,i), color)
        style.add("FONTNAME",  (3,i), (3,i), "Helvetica-Bold")
    t.setStyle(style)
    story.append(t)
    story.append(Spacer(1, 4))


def generate_payment_report(class_filter=None, student_id=None, terms_filter=None):
    """
    terms_filter: list of term strings to include, e.g. ['Term I', 'Term II'].
                  None means all terms.
    """
    active_terms = terms_filter if terms_filter else db.TERMS
    terms_label  = "_".join(t.replace(" ", "") for t in active_terms)

    if student_id:
        label = student_id.replace("/", "-").replace("\\", "-")
    elif class_filter:
        label = class_filter.replace(" ", "_")
    else:
        label = "WholeSchool"

    filename = f"PaymentReport_{label}_{terms_label}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc, path = _build_doc(filename)
    title_style, sub_style, section_style, normal_style = _styles()

    story = []
    if student_id:
        report_title = f"Payment Report — Student {student_id}"
    elif class_filter:
        report_title = f"Payment Report — {class_filter}"
    else:
        report_title = "Payment Report — All Classes"

    terms_display = "  |  ".join(active_terms)
    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(f"Academic Year 2026   ·   {terms_display}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8))

    if student_id:
        student = db.get_student(student_id)
        if not student:
            story.append(Paragraph("Student not found.", normal_style))
        else:
            story.append(Paragraph(
                f"  {student['name']}  |  {student['class']}  |  ID: {student['student_id']}",
                section_style
            ))
            _student_payment_block(student, story, section_style, normal_style, active_terms)
            # Requirements section — only for single student reports
            _student_requirements_block(student, story, section_style, normal_style)
    else:
        classes = [class_filter] if class_filter else db.CLASSES
        for cls in classes:
            students = db.get_students_by_class(cls)
            story.append(Paragraph(f"  {cls}", section_style))
            if not students:
                story.append(Paragraph("No students.", normal_style))
                continue
            for student in students:
                story.append(Paragraph(
                    f"Student: {student['name']}  (ID: {student['student_id']})",
                    ParagraphStyle("sname", fontSize=9, textColor=NAVY,
                                   fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2)
                ))
                _student_payment_block(student, story, section_style, normal_style, active_terms)
                story.append(HRFlowable(width="100%", thickness=0.5, color=MID, spaceAfter=4))

            if not class_filter and cls != classes[-1]:
                story.append(PageBreak())

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return path


# ════════════════════════════════════════════════════════════
#  PENDING BALANCES REPORT — cumulative across all terms
# ════════════════════════════════════════════════════════════

def generate_balances_report(class_filter=None):
    """
    Report every student who has any outstanding balance across ALL terms.
    Only terms that have fee data are included — so mid-year this naturally
    covers Term I + II (or whichever terms have been set up).
    class_filter=None means all classes.
    """
    label_part = class_filter.replace(" ", "_") if class_filter else "AllClasses"
    filename   = f"BalancesReport_{label_part}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    doc, path  = _build_doc(filename)
    title_style, sub_style, section_style, normal_style = _styles()

    story = []
    report_title = "Pending Balances Report"
    if class_filter:
        report_title += f"  |  {class_filter}"
    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(
        "Academic Year 2026  ·  Cumulative outstanding balances across all terms",
        sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8))

    classes = [class_filter] if class_filter else db.CLASSES
    grand_balance_total = 0
    any_data = False

    for cls in classes:
        students = db.get_students_by_class(cls)
        pending = []

        for student in students:
            fees = db.get_student_fees(student["student_id"])
            if not fees:
                continue

            # Group fees by term, only include terms that have data
            by_term = {}
            for f in fees:
                by_term.setdefault(f["term"], []).append(f)

            # Build per-term breakdown, keep only terms with a balance
            term_rows = []
            total_owed_all = 0
            total_paid_all = 0
            for term in db.TERMS:               # preserves Term I → II → III order
                if term not in by_term:
                    continue
                t_owed = sum(f["total_owed"] for f in by_term[term])
                t_paid = sum(f["total_paid"] for f in by_term[term])
                t_bal  = t_owed - t_paid
                total_owed_all += t_owed
                total_paid_all += t_paid
                if t_bal > 0:
                    term_rows.append({
                        "term":  term,
                        "owed":  t_owed,
                        "paid":  t_paid,
                        "bal":   t_bal,
                        "fees":  by_term[term],
                    })

            total_balance = total_owed_all - total_paid_all
            if total_balance > 0:
                pending.append({
                    "student":     student,
                    "term_rows":   term_rows,
                    "total_owed":  total_owed_all,
                    "total_paid":  total_paid_all,
                    "balance":     total_balance,
                })

        if not pending:
            continue

        any_data = True
        story.append(Paragraph(f"  {cls}", section_style))

        # ── Class summary table ────────────────────────────────────────────
        table_data = [["#", "Student ID", "Name", "Total Owed", "Total Paid", "Balance"]]
        class_balance = 0
        for i, row in enumerate(pending, 1):
            s = row["student"]
            table_data.append([
                str(i),
                s["student_id"],
                s["name"],
                f"Ksh {fmt(row['total_owed'])}",
                f"Ksh {fmt(row['total_paid'])}",
                f"Ksh {fmt(row['balance'])}",
            ])
            class_balance += row["balance"]
        table_data.append(["", "", "CLASS TOTAL", "", "", f"Ksh {fmt(class_balance)}"])
        grand_balance_total += class_balance

        col_widths = [10*mm, 30*mm, 55*mm, 28*mm, 28*mm, 28*mm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0,  0), (-1,  0), NAVY),
            ("TEXTCOLOR",      (0,  0), (-1,  0), WHITE),
            ("FONTNAME",       (0,  0), (-1,  0), "Helvetica-Bold"),
            ("FONTSIZE",       (0,  0), (-1,  0), 9),
            ("ALIGN",          (0,  0), (-1, -1), "CENTER"),
            ("ALIGN",          (2,  1), ( 2, -1), "LEFT"),
            ("FONTSIZE",       (0,  1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0,  1), (-1, -2), [WHITE, LIGHT]),
            ("BACKGROUND",     (0, -1), (-1, -1), MID),
            ("FONTNAME",       (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR",      (5,  1), ( 5, -2), RED),
            ("FONTNAME",       (5,  1), ( 5, -2), "Helvetica-Bold"),
            ("GRID",           (0,  0), (-1, -1), 0.4, MID),
            ("TOPPADDING",     (0,  0), (-1, -1), 4),
            ("BOTTOMPADDING",  (0,  0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

        # ── Per-student term breakdown ─────────────────────────────────────
        for row in pending:
            s = row["student"]
            story.append(Paragraph(
                f"    {s['name']}  (ID: {s['student_id']})",
                ParagraphStyle("sname2", fontSize=8, textColor=NAVY,
                               fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2)
            ))

            for tr in row["term_rows"]:
                # Term sub-heading
                story.append(Paragraph(
                    f"        {tr['term']}  —  Balance: Ksh {fmt(tr['bal'])}",
                    ParagraphStyle("termbal", fontSize=7, textColor=NAVY,
                                   fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=1)
                ))
                # Category rows for this term (only those with a balance)
                detail_data = [["Fee Category", "Owed", "Paid", "Balance"]]
                for f in tr["fees"]:
                    b = f["total_owed"] - f["total_paid"]
                    if b > 0:
                        detail_data.append([
                            f["category"],
                            fmt(f["total_owed"]),
                            fmt(f["total_paid"]),
                            fmt(b),
                        ])
                if len(detail_data) > 1:
                    dt = Table(detail_data, colWidths=[80*mm, 28*mm, 28*mm, 28*mm],
                               repeatRows=1)
                    dt.setStyle(TableStyle([
                        ("BACKGROUND",     (0, 0), (-1,  0), GOLD),
                        ("TEXTCOLOR",      (0, 0), (-1,  0), NAVY),
                        ("FONTNAME",       (0, 0), (-1,  0), "Helvetica-Bold"),
                        ("FONTSIZE",       (0, 0), (-1,  0), 7),
                        ("FONTSIZE",       (0, 1), (-1, -1), 7),
                        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
                        ("ALIGN",          (0, 1), ( 0, -1), "LEFT"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                        ("TEXTCOLOR",      (3, 1), ( 3, -1), RED),
                        ("FONTNAME",       (3, 1), ( 3, -1), "Helvetica-Bold"),
                        ("GRID",           (0, 0), (-1, -1), 0.3, MID),
                        ("TOPPADDING",     (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING",  (0, 0), (-1, -1), 2),
                    ]))
                    story.append(dt)

            # Student total
            story.append(Paragraph(
                f'<font color="red"><b>Total Balance:  Ksh {fmt(row["balance"])}</b></font>',
                ParagraphStyle("stubal", fontSize=8, alignment=TA_RIGHT,
                               spaceBefore=2, spaceAfter=4)
            ))
            story.append(HRFlowable(width="100%", thickness=0.4, color=MID, spaceAfter=2))

        if not class_filter and cls != classes[-1]:
            story.append(PageBreak())

    if not any_data:
        story.append(Paragraph(
            "No students with pending balances.",
            ParagraphStyle("none", fontSize=11, textColor=GREY,
                           alignment=TA_CENTER, spaceBefore=20)
        ))
    else:
        story.append(HRFlowable(width="100%", thickness=1, color=GOLD,
                                spaceBefore=8, spaceAfter=4))
        story.append(Paragraph(
            f'<b>GRAND TOTAL PENDING:  '
            f'<font color="red">Ksh {fmt(grand_balance_total)}</font></b>',
            ParagraphStyle("grandbal", fontSize=11, alignment=TA_RIGHT,
                           textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)
        ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return path
