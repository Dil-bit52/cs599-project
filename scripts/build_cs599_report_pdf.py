from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "CS599_大作业报告.md"
OUTPUT = ROOT / "docs" / "CS599_大作业报告.pdf"
ASSETS_DIR = ROOT / "docs" / "assets"
CORE_ARCHITECTURE_IMAGE = ASSETS_DIR / "core_architecture.png"
AGENT_WORKFLOW_IMAGE = ASSETS_DIR / "agent_workflow.png"
DATA_FLOW_IMAGE = ASSETS_DIR / "data_flow.png"

BASE_FONT = "STSong-Light"
ACCENT = colors.HexColor("#0F766E")
ACCENT_LIGHT = colors.HexColor("#E6F4F1")
TEXT = colors.HexColor("#111827")
MUTED = colors.HexColor("#4B5563")
BORDER = colors.HexColor("#CBD5E1")


pdfmetrics.registerFont(UnicodeCIDFont(BASE_FONT))


class OutlineDocTemplate(BaseDocTemplate):
    def beforeDocument(self) -> None:
        self._bookmark_seen: dict[str, int] = {}

    def afterFlowable(self, flowable) -> None:  # type: ignore[no-untyped-def]
        title = getattr(flowable, "_bookmark_title", None)
        level = getattr(flowable, "_bookmark_level", None)
        if title is None or level is None:
            return

        base_key = re.sub(r"[^A-Za-z0-9_]+", "_", str(title))[:60] or "section"
        count = self._bookmark_seen.get(base_key, 0) + 1
        self._bookmark_seen[base_key] = count
        key = f"{base_key}_{count}"

        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(str(title), key, int(level), closed=False)
        self.notify("TOCEntry", (int(level), str(title), self.page))


def build_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=styles["Title"],
            fontName=BASE_FONT,
            fontSize=25,
            leading=34,
            alignment=TA_CENTER,
            textColor=ACCENT,
            spaceAfter=18,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=styles["Normal"],
            fontName=BASE_FONT,
            fontSize=12,
            leading=20,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceAfter=22,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=styles["Heading1"],
            fontName=BASE_FONT,
            fontSize=17,
            leading=24,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=styles["Heading2"],
            fontName=BASE_FONT,
            fontSize=13.5,
            leading=20,
            textColor=colors.HexColor("#164E63"),
            spaceBefore=10,
            spaceAfter=7,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=styles["Heading3"],
            fontName=BASE_FONT,
            fontSize=11.5,
            leading=17,
            textColor=TEXT,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body",
            parent=styles["BodyText"],
            fontName=BASE_FONT,
            fontSize=10,
            leading=16,
            alignment=TA_JUSTIFY,
            firstLineIndent=0,
            spaceAfter=5,
            textColor=TEXT,
        ),
        "small": ParagraphStyle(
            "small",
            parent=styles["BodyText"],
            fontName=BASE_FONT,
            fontSize=8.8,
            leading=13,
            alignment=TA_LEFT,
            textColor=TEXT,
        ),
        "table": ParagraphStyle(
            "table",
            parent=styles["BodyText"],
            fontName=BASE_FONT,
            fontSize=8.5,
            leading=12.5,
            alignment=TA_LEFT,
            textColor=TEXT,
        ),
        "code": ParagraphStyle(
            "code",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=7.3,
            leading=10,
            leftIndent=6,
            rightIndent=6,
            spaceBefore=4,
            spaceAfter=8,
            backColor=colors.HexColor("#F8FAFC"),
            borderColor=colors.HexColor("#E2E8F0"),
            borderWidth=0.5,
            borderPadding=6,
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=styles["BodyText"],
            fontName=BASE_FONT,
            fontSize=8.5,
            leading=12.5,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "toc_title": ParagraphStyle(
            "toc_title",
            parent=styles["Heading1"],
            fontName=BASE_FONT,
            fontSize=18,
            leading=26,
            textColor=ACCENT,
            spaceAfter=14,
        ),
    }


STYLES = build_styles()


def inline(text: str) -> str:
    value = html.escape(text)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    return value


def heading(text: str, level: int) -> Paragraph:
    style = STYLES["h1" if level == 0 else "h2" if level == 1 else "h3"]
    paragraph = Paragraph(inline(text), style)
    paragraph._bookmark_title = text
    paragraph._bookmark_level = level
    return paragraph


def paragraph(text: str, style_name: str = "body") -> Paragraph:
    return Paragraph(inline(text), STYLES[style_name])


def markdown_table(lines: list[str]) -> Table:
    rows: list[list[Paragraph]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append([paragraph(cell, "table") for cell in cells])

    if not rows:
        return Table([[""]])

    col_count = max(len(row) for row in rows)
    for row in rows:
        while len(row) < col_count:
            row.append(paragraph("", "table"))

    available = A4[0] - 4 * cm
    col_widths = [available / col_count] * col_count
    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), BASE_FONT),
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT_LIGHT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#064E3B")),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    max_width: int | None = None,
    line_gap: int = 8,
) -> None:
    lines = wrap_text(draw, text, text_font, max_width or (box[2] - box[0] - 24))
    line_heights = [
        int(draw.textbbox((0, 0), line, font=text_font)[3] - draw.textbbox((0, 0), line, font=text_font)[1])
        for line in lines
    ]
    total_height = sum(line_heights) + max(0, len(lines) - 1) * line_gap
    y = box[1] + (box[3] - box[1] - total_height) // 2
    for line, line_height in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=text_font)
        x = box[0] + (box[2] - box[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=text_font, fill=fill)
        y += line_height + line_gap


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if "\n" in text:
        lines: list[str] = []
        for part in text.splitlines():
            lines.extend(wrap_text(draw, part, text_font, max_width))
        return lines

    if draw.textlength(text, font=text_font) <= max_width:
        return [text]

    lines: list[str] = []
    current = ""
    for char in text:
        candidate = f"{current}{char}"
        if current and draw.textlength(candidate, font=text_font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    radius: int = 24,
    width: int = 3,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int]) -> None:
    draw.line([start, end], fill=color, width=5)
    x1, y1 = start
    x2, y2 = end
    if abs(y2 - y1) >= abs(x2 - x1):
        direction = 1 if y2 > y1 else -1
        points = [(x2, y2), (x2 - 14, y2 - 24 * direction), (x2 + 14, y2 - 24 * direction)]
    else:
        direction = 1 if x2 > x1 else -1
        points = [(x2, y2), (x2 - 24 * direction, y2 - 14), (x2 - 24 * direction, y2 + 14)]
    draw.polygon(points, fill=color)


def generate_core_architecture_image() -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 1800, 1120
    image = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(image)

    title_font = font(54, bold=True)
    layer_font = font(34, bold=True)
    box_title_font = font(30, bold=True)
    box_text_font = font(24)
    small_font = font(22)

    teal = (15, 118, 110)
    teal_dark = (19, 78, 74)
    slate = (51, 65, 85)
    border = (148, 163, 184)
    pale = (236, 253, 245)
    blue_pale = (239, 246, 255)
    amber_pale = (255, 251, 235)
    violet_pale = (245, 243, 255)
    white = (255, 255, 255)

    draw_centered_text(draw, (0, 35, width, 105), "ResearchPilot 核心架构图", title_font, teal_dark)
    draw_centered_text(
        draw,
        (0, 95, width, 145),
        "Next.js 前端 + FastAPI 接口 + 多 Agent 工作流 + MCP/RAG/SQLite 工具与记忆层",
        small_font,
        slate,
    )

    layers = [
        ("前端展示层", 165, 310, pale, "Next.js Web Console", "任务创建 / 执行轨迹 / 论文卡片 / 报告预览 / 质量评估 / 知识库问答"),
        ("业务接口层", 345, 490, blue_pale, "FastAPI REST API", "Research Task API / Report API / Chat API / Delete Task API"),
        ("智能体编排层", 525, 730, amber_pale, "ResearchWorkflow", "Planner -> Search -> Reader -> RAG Store -> Synthesis -> Writer -> Evaluator"),
        ("数据与工具层", 780, 1035, violet_pale, "Task Memory + Tool Layer", "SQLite / Chroma or JSON / OpenAlex / arXiv / MCP Server / Markdown Reports"),
    ]

    for label, top, bottom, fill, title, desc in layers:
        rounded_box(draw, (80, top, 1720, bottom), fill, border, radius=28, width=3)
        rounded_box(draw, (105, top + 24, 355, bottom - 24), teal, teal, radius=20, width=2)
        draw_centered_text(draw, (105, top + 24, 355, bottom - 24), label, layer_font, white)
        draw_centered_text(draw, (410, top + 28, 1650, top + 74), title, box_title_font, teal_dark)
        if label in {"前端展示层", "业务接口层"}:
            draw_centered_text(draw, (410, top + 76, 1650, bottom - 24), desc, box_text_font, slate)

    for y1, y2 in [(310, 345), (490, 525), (730, 780)]:
        arrow(draw, (900, y1 + 8), (900, y2 - 8), teal)

    agent_top, agent_bottom = 620, 705
    agent_names = ["Planner", "Search", "Reader", "RAG Store", "Synthesis", "Writer", "Evaluator"]
    start_x, gap, box_w = 395, 35, 155
    for idx, name in enumerate(agent_names):
        x = start_x + idx * (box_w + gap)
        rounded_box(draw, (x, agent_top, x + box_w, agent_bottom), white, (203, 213, 225), radius=18, width=3)
        draw_centered_text(draw, (x + 8, agent_top + 8, x + box_w - 8, agent_bottom - 8), name, small_font, teal_dark)
        if idx < len(agent_names) - 1:
            draw_centered_text(
                draw,
                (x + box_w, agent_top, x + box_w + gap, agent_bottom),
                "→",
                font(28, bold=True),
                teal,
            )

    tool_boxes = [
        ("SQLite", "任务状态 / 日志\n论文 / 评分"),
        ("RAG Index", "Chroma 优先\nJSON 回退"),
        ("Paper APIs", "OpenAlex + arXiv"),
        ("MCP Tools", "search / retrieve\nreport / evaluate"),
        ("Reports", "Markdown 文件下载"),
    ]
    tool_top, tool_bottom = 905, 1000
    start_x, gap, box_w = 410, 24, 225
    for idx, (title, desc) in enumerate(tool_boxes):
        x = start_x + idx * (box_w + gap)
        rounded_box(draw, (x, tool_top, x + box_w, tool_bottom), white, (203, 213, 225), radius=18, width=3)
        draw_centered_text(draw, (x + 8, tool_top + 8, x + box_w - 8, tool_top + 44), title, small_font, teal_dark)
        draw_centered_text(draw, (x + 8, tool_top + 45, x + box_w - 8, tool_bottom - 6), desc, font(18), slate)

    image.save(CORE_ARCHITECTURE_IMAGE, quality=95)
    return CORE_ARCHITECTURE_IMAGE


def architecture_image_flowables() -> list:
    image_path = generate_core_architecture_image()
    return image_flowables(image_path, 1800, 1120)


def image_flowables(image_path: Path, image_width: int, image_height: int) -> list:
    available_width = A4[0] - 4 * cm
    rendered_height = available_width * image_height / image_width
    return [RLImage(str(image_path), width=available_width, height=rendered_height), Spacer(1, 9)]


def screenshot_flowables(image_name: str, caption: str) -> list:
    image_path = ASSETS_DIR / f"{image_name}.png"
    if not image_path.exists():
        return [paragraph(f"截图缺失：{image_name}", "body")]

    with Image.open(image_path) as opened:
        image_width, image_height = opened.size

    available_width = A4[0] - 4 * cm
    max_height = A4[1] - 7.2 * cm
    scale = min(available_width / image_width, max_height / image_height)
    rendered_width = image_width * scale
    rendered_height = image_height * scale

    image = RLImage(str(image_path), width=rendered_width, height=rendered_height)
    image.hAlign = "CENTER"
    return [
        KeepTogether(
            [
                image,
                Paragraph(inline(caption), STYLES["caption"]),
            ]
        ),
        Spacer(1, 8),
    ]


def generate_agent_workflow_image() -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 1800, 820
    image = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(image)

    teal = (15, 118, 110)
    teal_dark = (19, 78, 74)
    slate = (51, 65, 85)
    border = (148, 163, 184)
    pale = (236, 253, 245)
    blue_pale = (239, 246, 255)
    amber_pale = (255, 251, 235)
    white = (255, 255, 255)

    draw_centered_text(draw, (0, 40, width, 105), "Agent 交互流程图", font(52, bold=True), teal_dark)
    draw_centered_text(draw, (0, 105, width, 145), "从用户主题到报告评估，每个节点独立完成职责并写入可观测日志", font(23), slate)

    top_boxes = [
        ("用户输入", "topic / language / max_papers"),
        ("FastAPI", "创建任务并启动后台工作流"),
        ("ResearchWorkflow", "维护状态、进度和节点顺序"),
    ]
    top_y1, top_y2 = 180, 300
    box_w, gap, start_x = 410, 95, 180
    for idx, (title, desc) in enumerate(top_boxes):
        x = start_x + idx * (box_w + gap)
        rounded_box(draw, (x, top_y1, x + box_w, top_y2), blue_pale if idx != 2 else pale, border, radius=22, width=3)
        draw_centered_text(draw, (x + 20, top_y1 + 18, x + box_w - 20, top_y1 + 55), title, font(28, bold=True), teal_dark)
        draw_centered_text(draw, (x + 20, top_y1 + 56, x + box_w - 20, top_y2 - 12), desc, font(21), slate)
        if idx < len(top_boxes) - 1:
            arrow(draw, (x + box_w + 15, (top_y1 + top_y2) // 2), (x + box_w + gap - 15, (top_y1 + top_y2) // 2), teal)

    arrow(draw, (900, top_y2 + 20), (900, 355), teal)

    rounded_box(draw, (90, 360, 1710, 610), amber_pale, border, radius=28, width=3)
    draw_centered_text(draw, (0, 378, width, 420), "多 Agent 协作链路", font(31, bold=True), teal_dark)

    agents = [
        ("Planner", "关键词\n问题\n大纲"),
        ("Search", "OpenAlex\narXiv"),
        ("Reader", "论文摘要\n贡献局限"),
        ("RAG Store", "任务级\n知识库"),
        ("Synthesis", "方法对比\n趋势局限"),
        ("Writer", "Markdown\n报告"),
        ("Evaluator", "质量评分\n改进建议"),
    ]
    agent_y1, agent_y2 = 450, 560
    agent_w, agent_gap, agent_x = 185, 35, 170
    for idx, (title, desc) in enumerate(agents):
        x = agent_x + idx * (agent_w + agent_gap)
        rounded_box(draw, (x, agent_y1, x + agent_w, agent_y2), white, (203, 213, 225), radius=20, width=3)
        draw_centered_text(draw, (x + 10, agent_y1 + 8, x + agent_w - 10, agent_y1 + 42), title, font(23, bold=True), teal_dark)
        draw_centered_text(draw, (x + 10, agent_y1 + 45, x + agent_w - 10, agent_y2 - 10), desc, font(19), slate, line_gap=4)
        if idx < len(agents) - 1:
            draw_centered_text(draw, (x + agent_w, agent_y1, x + agent_w + agent_gap, agent_y2), "→", font(28, bold=True), teal)

    rounded_box(draw, (280, 660, 1520, 750), pale, border, radius=22, width=3)
    draw_centered_text(draw, (300, 670, 1510, 708), "SQLite Agent Logs + Task Status", font(28, bold=True), teal_dark)
    draw_centered_text(draw, (300, 710, 1510, 742), "每个节点写入 current_step、progress、payload 和错误信息，前端时间线持续轮询展示", font(21), slate)
    arrow(draw, (900, 610), (900, 655), teal)

    image.save(AGENT_WORKFLOW_IMAGE, quality=95)
    return AGENT_WORKFLOW_IMAGE


def workflow_image_flowables() -> list:
    return image_flowables(generate_agent_workflow_image(), 1800, 820)


def generate_data_flow_image() -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 1800, 760
    image = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(image)

    teal = (15, 118, 110)
    teal_dark = (19, 78, 74)
    slate = (51, 65, 85)
    border = (148, 163, 184)
    blue_pale = (239, 246, 255)
    green_pale = (236, 253, 245)
    amber_pale = (255, 251, 235)
    red_pale = (254, 242, 242)
    white = (255, 255, 255)

    draw_centered_text(draw, (0, 35, width, 100), "数据流设计图", font(52, bold=True), teal_dark)
    draw_centered_text(draw, (0, 98, width, 138), "任务数据、论文证据、RAG 索引、报告文件和前端展示形成闭环", font(23), slate)

    nodes = [
        ("用户输入", "topic\nlanguage\nmax_papers", green_pale),
        ("任务记忆", "SQLite\ntasks / logs", blue_pale),
        ("论文检索", "OpenAlex\narXiv", amber_pale),
        ("论文证据", "papers\nsummaries", white),
        ("RAG 索引", "Chroma\nJSON fallback", blue_pale),
        ("报告评估", "Markdown\nscores", amber_pale),
        ("前端展示", "timeline\nreport / chat", green_pale),
    ]

    y1, y2 = 250, 405
    node_w, gap, start_x = 205, 34, 95
    centers: list[tuple[int, int]] = []
    for idx, (title, desc, fill) in enumerate(nodes):
        x = start_x + idx * (node_w + gap)
        centers.append((x + node_w // 2, (y1 + y2) // 2))
        rounded_box(draw, (x, y1, x + node_w, y2), fill, border, radius=22, width=3)
        draw_centered_text(draw, (x + 8, y1 + 14, x + node_w - 8, y1 + 52), title, font(26, bold=True), teal_dark)
        draw_centered_text(draw, (x + 8, y1 + 58, x + node_w - 8, y2 - 14), desc, font(20), slate, line_gap=4)
        if idx < len(nodes) - 1:
            arrow(draw, (x + node_w + 4, (y1 + y2) // 2), (x + node_w + gap - 6, (y1 + y2) // 2), teal)

    side_boxes = [
        ((260, 500, 620, 610), "SQLite 持久化", "tasks / papers\nagent_logs / evaluations"),
        ((720, 500, 1080, 610), "RAG 文档索引", "Chroma 优先\nJSON fallback"),
        ((1180, 500, 1540, 610), "报告文件", "data/reports/{task_id}.md"),
    ]
    for box, title, desc in side_boxes:
        rounded_box(draw, box, white, border, radius=20, width=3)
        draw_centered_text(draw, (box[0] + 10, box[1] + 12, box[2] - 10, box[1] + 48), title, font(24, bold=True), teal_dark)
        draw_centered_text(draw, (box[0] + 10, box[1] + 52, box[2] - 10, box[3] - 10), desc, font(19), slate, line_gap=4)

    arrow(draw, (centers[1][0], y2 + 8), (440, 492), teal)
    arrow(draw, (centers[4][0], y2 + 8), (900, 492), teal)
    arrow(draw, (centers[5][0], y2 + 8), (1360, 492), teal)

    rounded_box(draw, (330, 650, 1470, 720), red_pale, border, radius=22, width=3)
    draw_centered_text(draw, (350, 660, 1450, 710), "DELETE 任务时同步清理 SQLite 记录、RAG 索引和报告文件", font(24, bold=True), teal_dark)

    image.save(DATA_FLOW_IMAGE, quality=95)
    return DATA_FLOW_IMAGE


def data_flow_image_flowables() -> list:
    return image_flowables(generate_data_flow_image(), 1800, 760)


def diagram_table(kind: str) -> list:
    if kind == "technology_route":
        data = [
            ["用户主题", "Planner", "Search", "Reader/RAG", "Writer", "Evaluator"],
            ["研究意图", "关键词/问题/大纲", "论文检索", "论文总结与知识库", "Markdown 报告", "质量评分"],
        ]
        widths = [2.55 * cm, 2.55 * cm, 2.55 * cm, 3 * cm, 2.55 * cm, 2.55 * cm]
    elif kind == "architecture":
        return architecture_image_flowables()
    elif kind == "workflow":
        return workflow_image_flowables()
    elif kind == "dataflow":
        return data_flow_image_flowables()
    elif kind == "evaluation":
        data = [
            ["相关性", "引用完整性", "结构清晰度", "事实一致性", "综合评分"],
            ["是否围绕主题", "是否保留论文来源", "章节是否合理", "是否受证据约束", "0-10 分汇总"],
        ]
        widths = [3.05 * cm] * 5
    else:
        return []

    rows = [[paragraph(str(cell), "table") for cell in row] for row in data]
    table = Table(rows, colWidths=widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [table, Spacer(1, 9)]


def parse_markdown(text: str) -> list:
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith("## 一、"))
    except StopIteration:
        start = 0
    lines = lines[start:]

    story: list = []
    paragraph_buffer: list[str] = []
    bullet_buffer: list[str] = []
    table_buffer: list[str] = []
    in_code = False
    code_buffer: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        if paragraph_buffer:
            story.append(paragraph(" ".join(item.strip() for item in paragraph_buffer)))
            paragraph_buffer = []

    def flush_bullets() -> None:
        nonlocal bullet_buffer
        if bullet_buffer:
            items = [ListItem(paragraph(item, "body"), leftIndent=12) for item in bullet_buffer]
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=16, bulletFontName=BASE_FONT))
            story.append(Spacer(1, 4))
            bullet_buffer = []

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            story.append(markdown_table(table_buffer))
            story.append(Spacer(1, 7))
            table_buffer = []

    def flush_code() -> None:
        nonlocal code_buffer
        if code_buffer:
            story.append(Preformatted("\n".join(code_buffer), STYLES["code"]))
            code_buffer = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                flush_bullets()
                flush_table()
                in_code = True
                code_buffer = []
            continue

        if in_code:
            code_buffer.append(line)
            continue

        marker = re.fullmatch(r"<!--\s*diagram:([a-z_]+)\s*-->", line.strip())
        if marker:
            flush_paragraph()
            flush_bullets()
            flush_table()
            story.extend(diagram_table(marker.group(1)))
            continue

        image_marker = re.fullmatch(r"<!--\s*image:([a-zA-Z0-9_-]+)\|(.*?)\s*-->", line.strip())
        if image_marker:
            flush_paragraph()
            flush_bullets()
            flush_table()
            story.extend(screenshot_flowables(image_marker.group(1), image_marker.group(2).strip()))
            continue

        if not line.strip():
            flush_paragraph()
            flush_bullets()
            flush_table()
            continue

        if line.startswith("|"):
            flush_paragraph()
            flush_bullets()
            table_buffer.append(line)
            continue
        elif table_buffer:
            flush_table()

        if line.startswith("### "):
            flush_paragraph()
            flush_bullets()
            story.append(heading(line[4:].strip(), 1))
        elif line.startswith("#### "):
            flush_paragraph()
            flush_bullets()
            story.append(heading(line[5:].strip(), 2))
        elif line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            story.append(heading(line[3:].strip(), 0))
        elif line.startswith("- "):
            flush_paragraph()
            bullet_buffer.append(line[2:].strip())
        elif re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            bullet_buffer.append(re.sub(r"^\d+\.\s+", "", line).strip())
        else:
            paragraph_buffer.append(line)

    flush_paragraph()
    flush_bullets()
    flush_table()
    flush_code()
    return story


def cover_story() -> list:
    metadata = [
        ["课程名称", "企业级应用软件设计与开发"],
        ["项目名称", "ResearchPilot: Agentic AI Research Assistant"],
        ["方向", "方向一：Agentic AI 原生开发"],
        ["学号", "2025303065"],
        ["姓名", "刘迪"],
        ["专业", "软件工程"],
        ["指导教师", "戚欣"],
        ["提交日期", "2026 年 6 月 22 日"],
        ["部署地址", "http://60.205.203.170:3000"],
    ]
    table = Table(
        [[paragraph(k, "table"), paragraph(v, "table")] for k, v in metadata],
        colWidths=[4 * cm, 10.7 * cm],
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), ACCENT_LIGHT),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#064E3B")),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [
        Spacer(1, 3.2 * cm),
        Paragraph("CS599 期末大作业报告", STYLES["cover_title"]),
        Paragraph("企业级应用软件设计与开发（AI 驱动的软件开发与 Agentic AI）", STYLES["cover_subtitle"]),
        table,
        Spacer(1, 1.2 * cm),
        Paragraph(
            "本报告根据课程要求整理项目背景、SDD 规格、系统架构、关键实现、测试评估、扩展计划与课程总结。",
            STYLES["cover_subtitle"],
        ),
    ]


def on_page(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont(BASE_FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.15 * cm, "ResearchPilot CS599 Final Report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.15 * cm, f"第 {doc.page} 页")
    canvas.restoreState()


def build_pdf() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    frame = Frame(2 * cm, 1.8 * cm, A4[0] - 4 * cm, A4[1] - 3.6 * cm, id="normal")
    doc = OutlineDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOCLevel0", fontName=BASE_FONT, fontSize=10.5, leading=16, leftIndent=0, firstLineIndent=0),
        ParagraphStyle("TOCLevel1", fontName=BASE_FONT, fontSize=9.5, leading=14, leftIndent=14, firstLineIndent=0),
        ParagraphStyle("TOCLevel2", fontName=BASE_FONT, fontSize=9, leading=13, leftIndent=28, firstLineIndent=0),
    ]

    toc_title = Paragraph("目录", STYLES["toc_title"])
    toc_title._bookmark_title = "目录"
    toc_title._bookmark_level = 0

    story = []
    story.extend(cover_story())
    story.append(PageBreak())
    story.append(toc_title)
    story.append(toc)
    story.append(PageBreak())
    story.extend(parse_markdown(source_text))
    doc.multiBuild(story)
    rewrite_unicode_outline(source_text)


def collect_expected_outline(source_text: str) -> list[tuple[str, int]]:
    entries: list[tuple[str, int]] = [("目录", 0)]
    lines = source_text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith("## 一、"))
    except StopIteration:
        start = 0
    for line in lines[start:]:
        if line.startswith("#### "):
            entries.append((line[5:].strip(), 2))
        elif line.startswith("### "):
            entries.append((line[4:].strip(), 1))
        elif line.startswith("## "):
            entries.append((line[3:].strip(), 0))
    return entries


def flatten_pdf_outline(reader: PdfReader) -> list[tuple[int, int]]:
    entries: list[tuple[int, int]] = []

    def walk(items, level: int = 0) -> None:  # type: ignore[no-untyped-def]
        for item in items:
            if isinstance(item, list):
                walk(item, level + 1)
            else:
                entries.append((reader.get_destination_page_number(item), level))

    walk(reader.outline)
    return entries


def rewrite_unicode_outline(source_text: str) -> None:
    reader = PdfReader(str(OUTPUT))
    destination_entries = flatten_pdf_outline(reader)
    expected_entries = collect_expected_outline(source_text)
    if not destination_entries:
        return

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    parents: dict[int, object] = {}
    for (title, expected_level), (page_number, fallback_level) in zip(expected_entries, destination_entries):
        level = expected_level if expected_level is not None else fallback_level
        parent = parents.get(level - 1) if level > 0 else None
        outline_item = writer.add_outline_item(title, page_number=page_number, parent=parent)
        parents[level] = outline_item
        for stale_level in [key for key in parents if key > level]:
            del parents[stale_level]

    temp_path = OUTPUT.with_suffix(".tmp.pdf")
    with temp_path.open("wb") as file:
        writer.write(file)
    temp_path.replace(OUTPUT)


if __name__ == "__main__":
    build_pdf()
