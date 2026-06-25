"""Generate a professional Arabic RTL PDF from the system summary — fixed version."""
import os
import re
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Arabic-capable fonts
FONT_DIR = "C:\\Windows\\Fonts"
pdfmetrics.registerFont(TTFont("Arabic", os.path.join(FONT_DIR, "tahoma.ttf")))
pdfmetrics.registerFont(TTFont("ArabicBold", os.path.join(FONT_DIR, "tahomabd.ttf")))
pdfmetrics.registerFont(TTFont("Eng", os.path.join(FONT_DIR, "consola.ttf")))
pdfmetrics.registerFont(TTFont("EngBold", os.path.join(FONT_DIR, "arialbd.ttf")))

# Colors
PRIMARY = HexColor("#1a56db")
DARK = HexColor("#1e293b")
MUTED = HexColor("#64748b")
LIGHT_BG = HexColor("#f1f5f9")
CARD_BG = HexColor("#f8fafc")
BORDER = HexColor("#cbd5e1")
SUCCESS = HexColor("#16a34a")
WARNING = HexColor("#eab308")
DANGER = HexColor("#dc2626")
WHITE = HexColor("#ffffff")
ACCENT_LIGHT = HexColor("#dbeafe")
CODE_BG = HexColor("#f8fafc")

ARABIC_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')


def has_arabic(text: str) -> bool:
    if not text:
        return False
    return bool(ARABIC_RE.search(str(text)))


def ar(text: str) -> str:
    """Reshape pure Arabic text for RTL display."""
    if not text:
        return ""
    text = str(text)
    if not has_arabic(text):
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def cell(text) -> str:
    """Process a table cell — Arabic gets reshaped, English stays as-is."""
    if text is None:
        return ""
    text = str(text)
    if not has_arabic(text):
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def code(text: str) -> str:
    """Code blocks — NEVER reshape, keep as-is LTR."""
    return str(text).replace("\n", "<br/>")


# Styles
def make_styles():
    s = {}
    s["title"] = ParagraphStyle("Title", fontName="ArabicBold", fontSize=26, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=6, leading=32)
    s["subtitle"] = ParagraphStyle("Subtitle", fontName="Arabic", fontSize=13, textColor=MUTED, alignment=TA_CENTER, spaceAfter=4, leading=18)
    s["h1"] = ParagraphStyle("H1", fontName="ArabicBold", fontSize=18, textColor=PRIMARY, alignment=TA_RIGHT, spaceBefore=20, spaceAfter=10, leading=24)
    s["h2"] = ParagraphStyle("H2", fontName="ArabicBold", fontSize=14, textColor=DARK, alignment=TA_RIGHT, spaceBefore=14, spaceAfter=8, leading=20)
    s["body"] = ParagraphStyle("Body", fontName="Arabic", fontSize=10, textColor=DARK, alignment=TA_RIGHT, spaceAfter=4, leading=16)
    s["body_center"] = ParagraphStyle("BodyC", fontName="Arabic", fontSize=10, textColor=DARK, alignment=TA_CENTER, spaceAfter=4, leading=16)
    s["small"] = ParagraphStyle("Small", fontName="Arabic", fontSize=8, textColor=MUTED, alignment=TA_RIGHT, spaceAfter=2, leading=12)
    s["cell_ar"] = ParagraphStyle("CellAr", fontName="Arabic", fontSize=9, textColor=DARK, alignment=TA_RIGHT, leading=14)
    s["cell_en"] = ParagraphStyle("CellEn", fontName="Arabic", fontSize=9, textColor=DARK, alignment=TA_LEFT, leading=14)
    s["cell_bold_ar"] = ParagraphStyle("CellBAr", fontName="ArabicBold", fontSize=9, textColor=DARK, alignment=TA_RIGHT, leading=14)
    s["cell_bold_en"] = ParagraphStyle("CellBEn", fontName="ArabicBold", fontSize=9, textColor=DARK, alignment=TA_LEFT, leading=14)
    s["cell_header"] = ParagraphStyle("CellH", fontName="ArabicBold", fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=14)
    s["cell_center"] = ParagraphStyle("CellC", fontName="Arabic", fontSize=9, textColor=DARK, alignment=TA_CENTER, leading=14)
    s["code"] = ParagraphStyle("Code", fontName="Eng", fontSize=8, textColor=DARK, alignment=TA_LEFT, spaceAfter=3, leading=12, backColor=CODE_BG, borderPadding=6, leftIndent=10, rightIndent=10)
    s["disclaimer"] = ParagraphStyle("Disc", fontName="Arabic", fontSize=10, textColor=DANGER, alignment=TA_CENTER, leading=16)
    return s


S = make_styles()


def P(text, style_key="body"):
    """Create a paragraph with auto Arabic detection."""
    return Paragraph(cell(text), S[style_key])


def section_header(num, title):
    return [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=2, color=PRIMARY),
        Paragraph(ar(f"{num}. {title}" if num else title), S["h1"]),
    ]


def make_table(headers, rows, col_widths=None, row_colors=None):
    """Build a table. headers and rows are lists of strings (Arabic or English)."""
    # Header row — all centered, white text
    header_cells = [Paragraph(cell(h), S["cell_header"]) for h in headers]
    data = [header_cells]

    for row in rows:
        row_cells = []
        for c in row:
            txt = str(c) if c is not None else ""
            if has_arabic(txt):
                row_cells.append(Paragraph(cell(txt), S["cell_ar"]))
            else:
                row_cells.append(Paragraph(txt, S["cell_en"]))
        data.append(row_cells)

    if col_widths is None:
        total = 16 * cm
        n = len(headers)
        col_widths = [total / n] * n

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, CARD_BG]),
    ]
    if row_colors:
        for i, color in enumerate(row_colors):
            if color:
                style.append(("BACKGROUND", (0, i + 1), (-1, i + 1), color))
    t.setStyle(TableStyle(style))
    return t


def info_card(rows):
    """Two-column info card: label (bold) | value."""
    data = []
    for label, value in rows:
        lbl = str(label) if label else ""
        val = str(value) if value else ""
        if has_arabic(lbl):
            lp = Paragraph(cell(lbl), S["cell_bold_ar"])
        else:
            lp = Paragraph(lbl, S["cell_bold_en"])
        if has_arabic(val):
            vp = Paragraph(cell(val), S["cell_ar"])
        else:
            vp = Paragraph(val, S["cell_en"])
        data.append([vp, lp])
    t = Table(data, colWidths=[11 * cm, 5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def arch_diagram():
    """Architecture diagram using nested tables instead of ASCII art."""
    # Row 1: Browser <-> Backend
    r1 = Table([[
        Paragraph("FastAPI Backend<br/>Port 8000", S["cell_center"]),
        Paragraph("&lt;--- REST + WebSocket ---&gt;", S["cell_center"]),
        Paragraph("Browser (Next.js)<br/>Port 3000", S["cell_center"]),
    ]], colWidths=[5 * cm, 6 * cm, 5 * cm])
    r1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), ACCENT_LIGHT),
        ("BACKGROUND", (2, 0), (2, 0), ACCENT_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    arrow = Paragraph("|<br/>| POST /uploads", S["cell_center"])

    # Row 2: Storage
    r2 = Table([[
        Paragraph("Local Storage<br/>(uploads/)", S["cell_center"]),
        Paragraph("PDF / OCR text extraction", S["cell_center"]),
    ]], colWidths=[8 * cm, 8 * cm])
    r2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    arrow2 = Paragraph("|<br/>|", S["cell_center"])

    # Row 3: Three outputs
    r3 = Table([[
        Paragraph("SQLite DB<br/>(Relational)", S["cell_center"]),
        Paragraph("Local ML Model<br/>(Gradient Boosting)", S["cell_center"]),
        Paragraph("OpenAI GPT-4o<br/>(Text + Vision)", S["cell_center"]),
    ]], colWidths=[5.3 * cm, 5.3 * cm, 5.3 * cm])
    r3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), HexColor("#dcfce7")),
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#fef9c3")),
        ("BACKGROUND", (2, 0), (2, 0), HexColor("#dbeafe")),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    arrow3 = Paragraph("|<br/>v", S["cell_center"])

    # Row 4: Result
    r4 = Table([[
        Paragraph(ar("تشخيص شامل منظم (JSON)"), S["cell_center"]),
    ]], colWidths=[16 * cm])
    r4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    # Fix white text on result
    r4 = Table([[
        Paragraph(ar("تشخيص شامل منظم (JSON)"), ParagraphStyle("ResW", fontName="ArabicBold", fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=16)),
    ]], colWidths=[16 * cm])
    r4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    return [r1, arrow, r2, arrow2, r3, arrow3, r4]


def page_decorations(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("ArabicBold", 9)
    header_text = ar("نظام المراقبة الطبية الذكي")
    canvas.drawCentredString(A4[0] / 2, A4[1] - 0.75 * cm, header_text)
    canvas.setFont("Arabic", 8)
    canvas.drawString(2 * cm, A4[1] - 0.75 * cm, str(doc.page))
    # Footer
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.2 * cm, A4[0] - 2 * cm, 1.2 * cm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Arabic", 8)
    canvas.drawCentredString(A4[0] / 2, 0.7 * cm, ar("ملخص النظام الفني"))
    canvas.restoreState()


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.6 * cm,
        title="AI Medical Monitor - System Summary",
        author="AI Medical Monitor"
    )
    story = []

    # === COVER ===
    story.append(Spacer(1, 4 * cm))
    story.append(HRFlowable(width="100%", thickness=3, color=PRIMARY))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(ar("نظام المراقبة الطبية الذكي"), S["title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("AI-Powered Medical Monitor System", ParagraphStyle("Eng", fontName="EngBold", fontSize=14, textColor=MUTED, alignment=TA_CENTER, leading=20)))
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="60%", thickness=1, color=BORDER))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(ar("ملخص فني شامل للنظام"), S["subtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("2026-06-23", S["subtitle"]))
    story.append(Spacer(1, 3 * cm))

    cover_info = [
        (ar("التقنية الرئيسية"), "OpenAI GPT-4o + ML Model"),
        (ar("الخادم الخلفي"), "FastAPI + SQLite"),
        (ar("الواجهة الأمامية"), "Next.js 14 + TypeScript"),
        (ar("اللغات"), ar("عربي (RTL) + إنجليزي (LTR)")),
        (ar("دقة النموذج المحلي"), "84% - Gradient Boosting"),
        (ar("عدد ملفات الكود"), "70 files (44 backend + 26 frontend)"),
    ]
    ct_data = []
    for label, value in cover_info:
        if has_arabic(value):
            vp = Paragraph(cell(value), S["cell_ar"])
        else:
            vp = Paragraph(value, S["cell_en"])
        ct_data.append([vp, Paragraph(cell(label), S["cell_bold_ar"])])
    ct = Table(ct_data, colWidths=[9 * cm, 6 * cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, PRIMARY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(ct)
    story.append(PageBreak())

    # === TOC ===
    story.extend(section_header("", "جدول المحتويات"))
    toc_items = [
        ("1", "نظرة عامة"), ("2", "العمارة العامة للنظام"),
        ("3", "التقنيات المستخدمة"), ("4", "هيكل المشروع"),
        ("5", "قاعدة البيانات الحالية"), ("6", "واجهة برمجة التطبيقات (REST API)"),
        ("7", "نظام التشخيص الذكي"), ("8", "النموذج المحلي للتعلم الآلي (ML)"),
        ("9", "الواجهة الأمامية"), ("10", "الأمان والمصادقة"),
        ("11", "التشغيل الحالي والسجلات"), ("12", "البيانات المتاحة للاختبار"),
        ("13", "القيود الحالية والحلول"), ("14", "التطويرات المنجزة"),
        ("15", "الخطوات المقترحة التالية"),
    ]
    toc_data = []
    for num, title in toc_items:
        toc_data.append([
            Paragraph(ar(title), S["cell_ar"]),
            Paragraph(num, S["cell_center"]),
        ])
    toc = Table(toc_data, colWidths=[13 * cm, 2 * cm])
    toc.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, CARD_BG]),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(toc)
    story.append(PageBreak())

    # === 1. OVERVIEW ===
    story.extend(section_header("1", "نظرة عامة"))
    story.append(P("نظام مراقبة وتشخيص طبي متعدد الأسرّة للمستشفيات، يجمع بين الذكاء الاصطناعي السحابي (OpenAI GPT-4o) للتحليل والتفسير الطبي، ونموذج تعلم آلي محلي (Gradient Boosting) للتنبؤ بأمراض القلب، مع واجهة ويب ثنائية اللغة (عربي RTL / إنجليزي LTR)."))
    story.append(Spacer(1, 8))
    story.append(Paragraph(ar("الحالة التشغيلية الحالية"), S["h2"]))
    story.append(make_table(
        [ar("المكوّن"), ar("الحالة"), ar("ملاحظات")],
        [
            ["Backend (FastAPI)", ar("يعمل"), ar("المنفذ 8000")],
            ["Frontend (Next.js)", ar("يعمل"), ar("المنفذ 3000")],
            [ar("قاعدة البيانات (SQLite)"), ar("يعمل"), ar("علائقية + سلاسل زمنية")],
            [ar("نموذج ML"), ar("يعمل"), ar("دقة 84% - محمّل")],
            ["OpenAI GPT-4o", ar("يعمل"), ar("يرد خلال ~4 ثوانٍ")],
            ["WebSocket", ar("يعمل"), ar("بث القراءات الحية")],
            ["MQTT / InfluxDB", ar("غير مشغّل"), ar("يتطلب Docker")],
            ["MinIO / PostgreSQL", ar("غير مشغّل"), ar("تخزين محلي بديل مفعّل")],
        ],
        col_widths=[5 * cm, 3 * cm, 7 * cm],
        row_colors=[None, None, None, None, None, None, HexColor("#fef9c3"), HexColor("#fef9c3")]
    ))
    story.append(PageBreak())

    # === 2. ARCHITECTURE ===
    story.extend(section_header("2", "العمارة العامة للنظام"))
    story.append(Paragraph(ar("تدفق البيانات في النظام"), S["h2"]))
    for elem in arch_diagram():
        story.append(elem)
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 8))
    story.append(P("المسؤول عن التحليل: OpenAI GPT-4o هو المحلل الرئيسي. النموذج المحلي يقدّم إشارة مساعدة (توقع ثنائي + نسبة خطر) تُدمج في سياق OpenAI."))
    story.append(PageBreak())

    # === 3. TECHNOLOGIES ===
    story.extend(section_header("3", "التقنيات المستخدمة"))
    story.append(Paragraph(ar("الخادم الخلفي (Backend)"), S["h2"]))
    story.append(make_table(
        [ar("التقنية"), ar("الإصدار"), ar("الاستخدام")],
        [
            ["Python", "3.9", ar("لغة البرمجة")],
            ["FastAPI", "0.115", ar("إطار الويب")],
            ["SQLAlchemy", "2.0", "ORM"],
            ["SQLite", "-", ar("قاعدة البيانات الحالية")],
            ["Pydantic", "2.9", ar("التحقق من البيانات")],
            ["python-jose", "3.3", "JWT"],
            ["passlib/bcrypt", "1.7", ar("تجزئة كلمات المرور")],
            ["httpx", "0.27", ar("استدعاء OpenAI API")],
            ["pdfplumber", "0.11", ar("استخراج نص من PDF")],
            ["pytesseract", "0.3", "OCR"],
            ["Pillow", "10.4", ar("معالجة الصور")],
            ["scikit-learn", "1.6", ar("نموذج ML المحلي")],
            ["websockets", "13.0", ar("بث القراءات الحية")],
            ["uvicorn", "0.30", ar("خادم ASGI")],
        ],
        col_widths=[4 * cm, 2.5 * cm, 8.5 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("الواجهة الأمامية (Frontend)"), S["h2"]))
    story.append(make_table(
        [ar("التقنية"), ar("الإصدار"), ar("الاستخدام")],
        [
            ["Next.js", "14.2", ar("إطار الواجهة (App Router)")],
            ["React", "18.3", ar("مكتبة الواجهة")],
            ["TypeScript", "5.6", ar("لغة البرمجة")],
            ["Tailwind CSS", "3.4", ar("التنسيق")],
            ["Recharts", "2.12", ar("الرسوم البيانية")],
            ["Zustand", "4.5", ar("إدارة حالة المصادقة")],
            ["WebSocket API", "-", ar("البث اللحظي")],
        ],
        col_widths=[4 * cm, 2.5 * cm, 8.5 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("الذكاء الاصطناعي"), S["h2"]))
    story.append(make_table(
        [ar("المكوّن"), ar("الاستخدام")],
        [
            ["OpenAI GPT-4o", ar("التحليل الطبي الرئيسي (نص + Vision)")],
            ["Function Calling", ar("هيكلة مخرجات التشخيص كـ JSON")],
            ["GradientBoosting", ar("توقع ثنائي لأمراض القلب (84% دقة)")],
        ],
        col_widths=[5 * cm, 10 * cm]
    ))
    story.append(PageBreak())

    # === 4. PROJECT STRUCTURE ===
    story.extend(section_header("4", "هيكل المشروع"))
    story.append(Paragraph(ar("ملفات الخادم الخلفي (44 ملف Python)"), S["h2"]))
    story.append(Paragraph(code(
        "backend/\n"
        "  app/\n"
        "    main.py                  Entry point + seeding\n"
        "    core/config.py           Environment settings\n"
        "    core/security.py         JWT + bcrypt\n"
        "    db/session.py            SQLAlchemy engine\n"
        "    models/ (8 models)       user, patient, bed, alert,\n"
        "                             medical_file, chat, diagnosis, audit_log\n"
        "    schemas/ (7 models)      Pydantic schemas\n"
        "    api/routes/ (8 routes)   auth, patients, beds, uploads,\n"
        "                             diagnosis, alerts, admin, ml\n"
        "    services/ (8 services)   openai, diagnosis_engine, ml_service,\n"
        "                             file_processor, storage, ws_hub, mqtt\n"
        "  ml/                        ML model\n"
        "    train_model.py           Model training\n"
        "    models/heart_model.joblib Trained model (448 KB)\n"
        "  medical_monitor.db         SQLite database"
    ), S["code"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(ar("ملفات الواجهة الأمامية (26 ملف TypeScript)"), S["h2"]))
    story.append(Paragraph(code(
        "frontend/src/\n"
        "  app/ (11 pages)\n"
        "    login/                   Login page\n"
        "    diagnosis/               AI diagnosis (Chat + card)\n"
        "    ml/                      ML prediction page\n"
        "    dashboard/               Beds dashboard\n"
        "    beds/[id]/               Bed details\n"
        "    patients/                Patients + patient file\n"
        "    alerts/                  Alerts log\n"
        "    admin/                   User management\n"
        "  components/ (9)            DiagnosisCard, FileUploader,\n"
        "                             VitalsChart, Navbar, UI components\n"
        "  lib/                       api.ts, auth.ts, socket.ts, vitals.ts\n"
        "  i18n/                      ar/common.json, en/common.json"
    ), S["code"]))
    story.append(PageBreak())

    # === 5. DATABASE ===
    story.extend(section_header("5", "قاعدة البيانات الحالية (SQLite)"))
    story.append(make_table(
        [ar("الجدول"), ar("عدد الصفوف"), ar("الوصف")],
        [
            ["users", "3", ar("admin / doctor / nurse")],
            ["patients", "1", ar("Test Patient (45 سنة، ذكر)")],
            ["beds", "0", ar("غير معرفة (تتطلب MQTT)")],
            ["medical_files", "8", ar("4 ملفات × نسختان من الاختبار")],
            ["chat_sessions", "17", ar("جلسات تشخيص")],
            ["chat_messages", "26", ar("رسائل بين المستخدم و AI")],
            ["alerts", "0", ar("لا توجد تنبيهات")],
            ["audit_log", "28", ar("سجل عمليات الدخول")],
        ],
        col_widths=[4 * cm, 3 * cm, 8 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("حسابات الدخول الافتراضية"), S["h2"]))
    story.append(make_table(
        [ar("المستخدم"), ar("كلمة المرور"), ar("الدور")],
        [
            ["admin", "admin123", ar("مدير")],
            ["doctor", "doctor123", ar("طبيب")],
            ["nurse", "nurse123", ar("ممرض")],
        ],
        col_widths=[5 * cm, 5 * cm, 5 * cm]
    ))
    story.append(PageBreak())

    # === 6. API ===
    story.extend(section_header("6", "واجهة برمجة التطبيقات (REST API)"))
    story.append(P("23 مسار REST + WebSocket"))
    story.append(Spacer(1, 6))
    story.append(Paragraph(ar("المصادقة والمرضى"), S["h2"]))
    story.append(make_table(
        [ar("الطريقة"), ar("المسار"), ar("الدور المطلوب")],
        [
            ["POST", "/api/auth/login", ar("عام")],
            ["GET", "/api/patients", "doctor/nurse/admin"],
            ["POST", "/api/patients", "doctor/admin"],
            ["GET", "/api/patients/{id}", "doctor/nurse/admin"],
        ],
        col_widths=[2 * cm, 8 * cm, 5 * cm]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(ar("التشخيص الذكي و ML"), S["h2"]))
    story.append(make_table(
        [ar("الطريقة"), ar("المسار"), ar("الدور المطلوب")],
        [
            ["POST", "/api/diagnosis/sessions", "doctor/admin"],
            ["GET", "/api/diagnosis/sessions", "doctor/nurse/admin"],
            ["POST", "/api/diagnosis/sessions/{id}/messages", "doctor/admin"],
            ["GET", "/api/diagnosis/sessions/{id}/diagnosis", "doctor/nurse/admin"],
            ["POST", "/api/diagnosis/sessions/{id}/stream", "doctor/admin"],
            ["GET", "/api/ml/status", "doctor/nurse/admin"],
            ["POST", "/api/ml/predict/heart", "doctor/nurse/admin"],
        ],
        col_widths=[2 * cm, 8 * cm, 5 * cm]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(ar("الملفات الطبية والتنبيهات"), S["h2"]))
    story.append(make_table(
        [ar("الطريقة"), ar("المسار"), ar("الدور المطلوب")],
        [
            ["POST", "/api/patients/{id}/uploads", "doctor/admin"],
            ["GET", "/api/patients/{id}/uploads", "doctor/nurse/admin"],
            ["GET", "/api/uploads/{id}", "doctor/nurse/admin"],
            ["DELETE", "/api/uploads/{id}", "doctor/admin"],
            ["POST", "/api/uploads/{id}/extract", "doctor/admin"],
            ["GET", "/api/alerts", "doctor/nurse/admin"],
            ["POST", "/api/alerts/{id}/ack", "doctor/nurse/admin"],
            ["WS", "/api/beds/ws/stream", ar("مصادق")],
        ],
        col_widths=[2 * cm, 8 * cm, 5 * cm]
    ))
    story.append(PageBreak())

    # === 7. DIAGNOSIS ===
    story.extend(section_header("7", "نظام التشخيص الذكي"))
    story.append(Paragraph(ar("تدفق التشخيص"), S["h2"]))
    story.append(P("عند بدء جلسة تشخيص، يقوم محرك التشخيص (diagnosis_engine) بتجميع السياق التالي:"))
    story.append(Spacer(1, 4))
    for item in [
        "1. بيانات المريض (الاسم، العمر، الجنس، التشخيص الحالي)",
        "2. العلامات الحيوية (من InfluxDB - غير متاحة حالياً)",
        "3. الملفات المرفوعة: PDF -> استخراج نص، صورة -> OCR، صورة طبية -> Vision",
        "4. توقع النموذج المحلي ML (مرض قلبي + نسبة الخطر)",
    ]:
        story.append(P(item))
    story.append(Spacer(1, 8))
    story.append(P("ثم يُرسل السياق كاملاً إلى OpenAI GPT-4o مع:"))
    story.append(Spacer(1, 4))
    for item in [
        "System prompt طبي بالعربية (تشخيص فوري بدون تأجيل)",
        "الصور الطبية -> image_url لـ Vision (تحليل بصري مباشر)",
        "Function Calling: provide_diagnosis (هيكلة JSON)",
        "النموذج: gpt-4o | الحرارة: 0.3 | max_tokens: 2000",
    ]:
        story.append(P(item))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("مخرجات التشخيص (JSON منظم)"), S["h2"]))
    story.append(make_table(
        [ar("الحقل"), ar("الوصف")],
        [
            ["primary_diagnosis", ar("التشخيص الرئيسي الأكثر احتمالاً")],
            ["differential_diagnoses", ar("تشخيصات تفريقية محتملة")],
            ["severity", "low / moderate / high / critical"],
            ["confidence", "low / medium / high"],
            ["findings", ar("النتائج الملاحظة من الفحوصات")],
            ["possible_causes", ar("الأسباب المحتملة")],
            ["recommendations", ar("التوصيات والخطوات التالية")],
            ["additional_tests", ar("فحوصات إضافية موصى بها")],
            ["red_flags", ar("علامات تحذيرية تستدعي تدخلاً فورياً")],
            ["follow_up_questions", ar("أسئلة متابعة")],
        ],
        col_widths=[5 * cm, 10 * cm]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(ar("معالجة الملفات المرفوعة"), S["h2"]))
    story.append(make_table(
        [ar("نوع الملف"), ar("التقنية"), ar("ما يصل لـ OpenAI")],
        [
            ["PDF", "pdfplumber", ar("نص مستخرج")],
            [ar("صورة (نص مكتوب)"), "pytesseract OCR", ar("نص مستخرج")],
            [ar("صورة طبية (أشعة)"), "Vision prep", ar("صورة -> Vision بصرياً")],
            ["ECG (PDF)", "pdfplumber", ar("نص الوصف فقط (لا يرى الموجة)")],
        ],
        col_widths=[4 * cm, 4 * cm, 7 * cm]
    ))
    story.append(PageBreak())

    # === 8. ML MODEL ===
    story.extend(section_header("8", "النموذج المحلي للتعلم الآلي (ML)"))
    story.append(info_card([
        (ar("النوع"), "GradientBoostingClassifier"),
        (ar("بيانات التدريب"), ar("1,220 مريض (29 ملف CSV مدمج)")),
        (ar("الدقة"), "84% (test) / 80% (cross-validation)"),
        (ar("الميزات"), ar("13 متغير طبي")),
        (ar("المخرجات"), ar("توقع ثنائي + نسبة خطر + مستوى الخطر")),
        (ar("التكامل"), ar("يُرسل توقعه كجزء من سياق OpenAI")),
        (ar("حجم النموذج"), "448 KB (heart_model.joblib)"),
    ]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("أهم الميزات المساهمة في التنبؤ"), S["h2"]))
    story.append(make_table(
        [ar("#"), ar("الميزة"), ar("الأهمية")],
        [
            ["1", ar("نوع ألم الصدر (cp)"), "24.2%"],
            ["2", ar("الثلاسيميا (thal)"), "15.8%"],
            ["3", ar("ميل ST (slope)"), "15.2%"],
            ["4", "Oldpeak", "10.7%"],
            ["5", ar("الكوليسترول (chol)"), "8.6%"],
            ["6", ar("أقصى ضربات قلب (thalach)"), "6.8%"],
            ["7", ar("العمر (age)"), "4.0%"],
            ["8", ar("ضغط الدم (trestbps)"), "3.5%"],
        ],
        col_widths=[1.5 * cm, 9 * cm, 4.5 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("الميزات الـ 13 المطلوبة للتنبؤ"), S["h2"]))
    story.append(Paragraph(code("age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal"), S["code"]))
    story.append(PageBreak())

    # === 9. FRONTEND ===
    story.extend(section_header("9", "الواجهة الأمامية - الصفحات والميزات"))
    story.append(make_table(
        [ar("الصفحة"), ar("المسار"), ar("الوصف")],
        [
            [ar("تسجيل الدخول"), "/login", ar("مصادقة JWT (بدون Demo Mode)")],
            [ar("التشخيص الذكي"), "/diagnosis", ar("Chat مع AI + رفع ملفات + بطاقة تشخيص")],
            [ar("التنبؤ ML"), "/ml", ar("إدخال 13 متغير -> توقع فوري")],
            [ar("لوحة الأسرّة"), "/dashboard", ar("شبكة الأسرّة + علامات حيوية حية")],
            [ar("تفاصيل السرير"), "/beds/[id]", ar("رسوم بيانية لحظية (WebSocket)")],
            [ar("المرضى"), "/patients", ar("قائمة + إضافة مريض")],
            [ar("ملف المريض"), "/patients/[id]", ar("رفع ملفات + قائمة الملفات")],
            [ar("التنبيهات"), "/alerts", ar("سجل + تأكيد يدوي")],
            [ar("الإدارة"), "/admin", ar("إدارة المستخدمين (admin فقط)")],
        ],
        col_widths=[3.5 * cm, 4 * cm, 7.5 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("الميزات الرئيسية"), S["h2"]))
    for f in [
        "ثنائية اللغة (عربي RTL / إنجليزي LTR) مع تبديل فوري",
        "بث لحظي للعلامات الحيوية عبر WebSocket",
        "رفع ملفات Drag & Drop (PDF / صور)",
        "بطاقة تشخيص منظمة مع مستوى الخطورة والثقة",
        "رسوم بيانية حية (Recharts)",
        "مؤشرات حالة بالألوان (أخضر / أصفر / أحمر)",
        "تحليل تلقائي عند بدء الجلسة",
        "تنبؤ ML فوري بدون استدعاء OpenAI",
        "محادثة تفاعلية مع AI (أسئلة ومتابعة)",
    ]:
        story.append(P(f"->  {f}"))
    story.append(PageBreak())

    # === 10. SECURITY ===
    story.extend(section_header("10", "الأمان والمصادقة"))
    story.append(make_table(
        [ar("المجال"), ar("الإجراء المتخذ")],
        [
            [ar("المصادقة"), ar("JWT (HS256) مع انتهاء صلاحية 60 دقيقة")],
            [ar("كلمات المرور"), "bcrypt (12 rounds)"],
            [ar("الأدوار (RBAC)"), ar("3 أدوار: admin / doctor / nurse")],
            [ar("سجل التدقيق"), ar("كل عملية دخول تُسجّل في audit_log")],
            ["CORS", ar("مفعّل للواجهة الأمامية")],
            [ar("API Key"), ar("OpenAI key في .env (يجب تدويره)")],
        ],
        col_widths=[4 * cm, 11 * cm]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(ar("تنبيه أمني"), S["h2"]))
    story.append(P("مفتاح OpenAI API مكشوف في ملف .env. يُنصح بشدة بإنشاء مفتاح جديد، حذف القديم من لوحة OpenAI، ووضع المفتاح في متغير بيئة النظام بدلاً من ملف."))
    story.append(PageBreak())

    # === 11. OPERATIONS ===
    story.extend(section_header("11", "التشغيل الحالي والسجلات"))
    story.append(Paragraph(ar("الخدمات النشطة"), S["h2"]))
    story.append(make_table(
        [ar("الخدمة"), ar("المنفذ"), ar("العملية")],
        [
            ["Backend (FastAPI)", "8000", "python"],
            ["Frontend (Next.js)", "3000", "node"],
        ],
        col_widths=[6 * cm, 3 * cm, 6 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("أوامر التشغيل"), S["h2"]))
    story.append(P(ar("الخادم الخلفي:")))
    story.append(Paragraph(code("cd D:\\Desktop\\bbbb\\backend\npython -m uvicorn app.main:app --host 0.0.0.0 --port 8000"), S["code"]))
    story.append(P(ar("الواجهة الأمامية:")))
    story.append(Paragraph(code("cd D:\\Desktop\\bbbb\\frontend\nnpm run dev"), S["code"]))
    story.append(P(ar("إعادة تدريب النموذج:")))
    story.append(Paragraph(code("cd D:\\Desktop\\bbbb\\backend\npython ml\\train_model.py"), S["code"]))
    story.append(PageBreak())

    # === 12. TEST DATA ===
    story.extend(section_header("12", "البيانات المتاحة للاختبار"))
    story.append(Paragraph(ar("ملفات طبية جاهزة في dataset/test_files/"), S["h2"]))
    story.append(make_table(
        [ar("الملف"), ar("النوع"), ar("المحتوى")],
        [
            ["blood_test_lab.pdf", ar("تحاليل مخبرية"), ar("CBC + كيمياء (WBC مرتفع، CRP مرتفع، كوليسترول مرتفع)")],
            ["ecg_report.pdf", ar("تقرير طبي"), ar("تخطيط قلب (ST depression، T wave inversion)")],
            ["chest_xray_report.png", ar("صورة طبية"), ar("أشعة صدر (consolidation في الفص السفلي الأيمن)")],
            ["urinalysis_report.pdf", ar("تحاليل مخبرية"), ar("تحليل بول (UTI - بكتيريا، nitrite إيجابي)")],
        ],
        col_widths=[5 * cm, 3 * cm, 7 * cm]
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(ar("نتيجة اختبار التشخيص الشامل"), S["h2"]))
    story.append(info_card([
        (ar("التشخيص الرئيسي"), "Pneumonia with UTI"),
        (ar("مستوى الخطورة"), "high (عالية)"),
        (ar("مستوى الثقة"), "high (عالية)"),
        (ar("النتائج"), ar("WBC/CRP مرتفع، consolidation، مؤشرات UTI")),
        (ar("التوصيات"), ar("مضاد حيوي، تخطيط قلب، مراقبة فقر الدم")),
        (ar("العلامات التحذيرية"), ar("consolidation، نقص تروية ECG، CRP/WBC مرتفع")),
    ]))
    story.append(PageBreak())

    # === 13. LIMITATIONS ===
    story.extend(section_header("13", "القيود الحالية والحلول"))
    story.append(make_table(
        [ar("القيد"), ar("السبب"), ar("الحل المقترح")],
        [
            [ar("لا توجد علامات حيوية لحظية"), ar("MQTT/InfluxDB غير مشغّلة"), "docker compose up mosquitto influxdb"],
            [ar("ECG يُحلل كنص"), ar("pdfplumber يستخرج النص المكتوب فقط"), ar("رفع ECG كصورة (PNG screenshot)")],
            [ar("النموذج يتنبأ بالقلب فقط"), ar("مدرب على بيانات القلب"), ar("إضافة بيانات لأمراض أخرى")],
            [ar("API Key مكشوف"), ar("مفتاح حقيقي في .env"), ar("تدوير المفتاح + متغيرات بيئة النظام")],
            [ar("تخزين محلي"), ar("MinIO غير مشغّل"), "docker compose up minio"],
            [ar("لا توجد أسرّة"), ar("تعتمد على MQTT"), ar("إضافة أسرّة يدوياً أو تشغيل Docker")],
        ],
        col_widths=[4.5 * cm, 4.5 * cm, 6 * cm]
    ))
    story.append(PageBreak())

    # === 14. DEVELOPMENTS ===
    story.extend(section_header("14", "التطويرات المنجزة"))
    story.append(make_table(
        [ar("#"), ar("التطوير"), ar("الملفات المتأثرة")],
        [
            ["1", ar("إزالة وضع Demo بالكامل"), "api.ts, login, diagnosis, dashboard, beds"],
            ["2", ar("إظهار الأخطاء الحقيقية"), "login/page.tsx, diagnosis/page.tsx"],
            ["3", ar("إصلاح دعم WebSocket"), "websockets==13.0.1"],
            ["4", ar("تحليل تلقائي عند بدء الجلسة"), "diagnosis/page.tsx"],
            ["5", ar("تحسين System Prompt"), "openai_service.py"],
            ["6", ar("دمج 29 ملف CSV (1,220 مريض)"), "ml/train_model.py"],
            ["7", ar("تدريب نموذج GradientBoosting (84%)"), "ml/models/"],
            ["8", ar("خدمة التنبؤ المحلي"), "ml_service.py"],
            ["9", ar("تكامل ML مع محرك التشخيص"), "diagnosis_engine.py, openai_service.py"],
            ["10", ar("API للتنبؤ بـ ML"), "api/routes/ml.py, main.py"],
            ["11", ar("صفحة التنبؤ ML في الواجهة"), "app/ml/page.tsx, Navbar.tsx"],
            ["12", ar("تخزين محلي بديل عن MinIO"), "storage.py"],
            ["13", ar("إصلاح has_extracted_text property"), "models/medical_file.py"],
            ["14", ar("ملفات اختبار طبية واقعية"), "dataset/test_files/"],
            ["15", ar("اختبار شامل للرفع والتشخيص"), "test_upload_and_diagnose.py"],
        ],
        col_widths=[1 * cm, 6 * cm, 8 * cm]
    ))
    story.append(PageBreak())

    # === 15. NEXT STEPS ===
    story.extend(section_header("15", "الخطوات المقترحة التالية"))
    story.append(make_table(
        [ar("الأولوية"), ar("المهمة"), ar("الوصف")],
        [
            [ar("عالية"), ar("تشغيل Docker services"), ar("تفعيل البث اللحظي + MinIO + PostgreSQL")],
            [ar("عالية"), ar("تدوير OpenAI API Key"), ar("مفتاح جديد + متغير بيئة النظام")],
            [ar("متوسطة"), ar("رفع ECG كصورة"), ar("تحويل تقارير ECG إلى صور لـ Vision")],
            [ar("متوسطة"), ar("تدريب نماذج إضافية"), ar("التهاب رئوي، سكري، إلخ")],
            [ar("متوسطة"), ar("إضافة مرضى وأسرّة تجريبية"), ar("بيانات لاختبار لوحة التحكم")],
            [ar("منخفضة"), ar("RAG لقاعدة المعرفة"), "embeddings + ChromaDB"],
            [ar("منخفضة"), ar("كشف الشذوذ"), ar("مقارنة القراءات بالاتجاه التاريخي")],
            [ar("منخفضة"), ar("تقارير PDF قابلة للمشاركة"), "ReportLab"],
        ],
        col_widths=[2.5 * cm, 5 * cm, 7.5 * cm],
        row_colors=[HexColor("#fee2e3"), HexColor("#fee2e3"), HexColor("#fef9c3"), HexColor("#fef9c3"), HexColor("#fef9c3"), HexColor("#dcfce7"), HexColor("#dcfce7"), HexColor("#dcfce7")]
    ))

    # === FOOTER PAGE ===
    story.append(PageBreak())
    story.append(Spacer(1, 6 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(ar("نظام المراقبة الطبية الذكي"), S["title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(ar("ملخص فني شامل للنظام"), S["subtitle"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("2026-06-23", S["subtitle"]))
    story.append(Spacer(1, 2 * cm))
    story.append(HRFlowable(width="40%", thickness=1, color=BORDER))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(ar("هذا النظام أداة مساعدة للمراقبة وتقديم رأي ثانٍ - وليس بديلاً عن التشخيص الطبي أو قرار الطبيب المختص."), S["disclaimer"]))

    doc.build(story, onFirstPage=page_decorations, onLaterPages=page_decorations)
    print(f"PDF generated: {output_path}")
    print(f"Size: {os.path.getsize(output_path) // 1024} KB")


if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "SYSTEM_SUMMARY.pdf")
    build_pdf(output)
