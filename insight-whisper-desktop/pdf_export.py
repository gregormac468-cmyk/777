"""
Модуль экспорта анализа звонка в PDF (через ReportLab).
"""
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import sys


def _register_fonts():
    """Регистрируем шрифт с поддержкой кириллицы."""
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/ARIAL.TTF",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("CyrFont", path))
                bold = path.replace("arial.ttf", "arialbd.ttf").replace("ARIAL.TTF", "ARIALBD.TTF")
                bold = bold.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
                bold = bold.replace("Arial.ttf", "Arial Bold.ttf")
                if os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont("CyrFont-Bold", bold))
                else:
                    pdfmetrics.registerFont(TTFont("CyrFont-Bold", path))
                return "CyrFont"
            except Exception:
                continue
    return "Helvetica"


_FONT = None


def get_font():
    global _FONT
    if _FONT is None:
        _FONT = _register_fonts()
    return _FONT



def _score_color(score):
    if score is None:
        return colors.grey
    if score >= 7:
        return colors.HexColor("#16a34a")
    if score >= 4:
        return colors.HexColor("#d97706")
    return colors.HexColor("#dc2626")


def _make_styles(font: str):
    bold = f"{font}-Bold" if font == "CyrFont" else "Helvetica-Bold"
    if font == "Helvetica":
        bold = "Helvetica-Bold"
    return {
        "title": ParagraphStyle("Title", fontName=bold, fontSize=20,
                                textColor=colors.HexColor("#1e40af"),
                                spaceAfter=12, alignment=1),
        "h2": ParagraphStyle("H2", fontName=bold, fontSize=14,
                             textColor=colors.HexColor("#1e293b"),
                             spaceBefore=12, spaceAfter=6),
        "h3": ParagraphStyle("H3", fontName=bold, fontSize=11,
                             textColor=colors.HexColor("#334155"),
                             spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName=font, fontSize=10,
                               textColor=colors.HexColor("#0f172a"),
                               leading=14, spaceAfter=4),
        "small": ParagraphStyle("Small", fontName=font, fontSize=9,
                                textColor=colors.HexColor("#64748b"),
                                leading=12),
        "score_big": ParagraphStyle("Score", fontName=bold, fontSize=28,
                                    alignment=1, leading=32),
    }


def _safe(text):
    if text is None:
        return ""
    s = str(text)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))



def export_call_to_pdf(call: dict, output_path: str):
    """Экспортирует один звонок в PDF."""
    font = get_font()
    styles = _make_styles(font)

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    # Заголовок
    story.append(Paragraph("Анализ звонка", styles["title"]))
    story.append(Spacer(1, 0.3*cm))

    # Метаданные
    a = call.get("analysis") or {}
    score = a.get("overall_score")
    call_type = a.get("call_type", "—")
    created = call.get("created_at", "")
    if isinstance(created, str) and "T" in created:
        try:
            created = datetime.fromisoformat(created).strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass

    meta_data = [
        ["Файл:", _safe(call.get("file_name", ""))],
        ["Менеджер:", _safe(call.get("manager_name", "—"))],
        ["Дата:", _safe(created)],
        ["Тип звонка:", _safe(call_type)],
        ["Инструкция:", _safe(call.get("instruction_name", "—"))],
    ]
    meta = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), f"{font}-Bold" if font == "CyrFont" else "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta)
    story.append(Spacer(1, 0.5*cm))

    # Общая оценка
    if score is not None:
        score_style = ParagraphStyle("ScoreColored",
            parent=styles["score_big"],
            textColor=_score_color(score))
        story.append(Paragraph(f"Общая оценка: {score:.1f} / 10", score_style))
        story.append(Spacer(1, 0.4*cm))



    # Резюме
    if a.get("summary"):
        story.append(Paragraph("Резюме", styles["h2"]))
        story.append(Paragraph(_safe(a["summary"]), styles["body"]))

    # Критерии
    criteria = a.get("criteria") or []
    if criteria:
        story.append(Paragraph("Критерии оценки", styles["h2"]))
        rows = [["Критерий", "Оценка", "Комментарий"]]
        for c in criteria:
            rows.append([
                _safe(c.get("name", "")),
                f"{c.get('score', '—')}/10",
                _safe(c.get("comment", "")),
            ])
        tbl = Table(rows, colWidths=[5*cm, 2*cm, 9*cm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0),
             f"{font}-Bold" if font == "CyrFont" else "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8fafc")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.4*cm))

    # Сильные/слабые стороны/рекомендации
    for title, key, color in [
        ("Сильные стороны", "strengths", "#16a34a"),
        ("Слабые стороны", "weaknesses", "#dc2626"),
        ("Рекомендации", "recommendations", "#2563eb"),
    ]:
        items = a.get(key) or []
        if items:
            h = ParagraphStyle(f"H_{key}", parent=styles["h2"],
                               textColor=colors.HexColor(color))
            story.append(Paragraph(title, h))
            for item in items:
                story.append(Paragraph(f"• {_safe(item)}", styles["body"]))
            story.append(Spacer(1, 0.2*cm))



    # Транскрипт на новой странице
    transcript = call.get("transcript", "")
    if transcript:
        story.append(PageBreak())
        story.append(Paragraph("Транскрипт", styles["h2"]))
        for line in transcript.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(_safe(line), styles["body"]))

    # Подвал
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Отчёт сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        styles["small"]
    ))

    doc.build(story)


def export_calls_summary_to_pdf(calls: list[dict], output_path: str,
                                 title: str = "Сводный отчёт"):
    """Экспорт сводного отчёта по нескольким звонкам."""
    font = get_font()
    styles = _make_styles(font)
    bold = f"{font}-Bold" if font == "CyrFont" else "Helvetica-Bold"

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    story.append(Paragraph(title, styles["title"]))
    story.append(Paragraph(
        f"Всего звонков: {len(calls)} | "
        f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        styles["small"]
    ))
    story.append(Spacer(1, 0.5*cm))

    # Статистика
    scores = [c.get("overall_score") for c in calls if c.get("overall_score") is not None]
    if scores:
        avg = sum(scores) / len(scores)
        good = sum(1 for s in scores if s >= 7)
        mid = sum(1 for s in scores if 4 <= s < 7)
        bad = sum(1 for s in scores if s < 4)
        stats_data = [
            ["Средняя оценка", f"{avg:.2f} / 10"],
            ["Хорошие (≥7)", f"{good} ({good*100//len(scores)}%)"],
            ["Средние (4-7)", f"{mid} ({mid*100//len(scores)}%)"],
            ["Низкие (<4)", f"{bad} ({bad*100//len(scores)}%)"],
        ]
        stbl = Table(stats_data, colWidths=[5*cm, 4*cm])
        stbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), bold),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(stbl)
        story.append(Spacer(1, 0.5*cm))



    # Таблица звонков
    rows = [["Дата", "Файл", "Менеджер", "Тип", "Оценка"]]
    for c in calls:
        created = c.get("created_at", "")
        if isinstance(created, str) and "T" in created:
            try:
                created = datetime.fromisoformat(created).strftime("%d.%m %H:%M")
            except Exception:
                pass
        score = c.get("overall_score")
        score_str = f"{score:.1f}" if score is not None else "—"
        rows.append([
            _safe(created)[:16],
            _safe(c.get("file_name", ""))[:30],
            _safe(c.get("manager_name", "—"))[:20],
            _safe(c.get("call_type", "—"))[:20],
            score_str,
        ])

    tbl = Table(rows, colWidths=[2.5*cm, 6*cm, 4*cm, 4*cm, 1.5*cm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)

    doc.build(story)
