from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

HEADERS = [
    "TC ID", "Story ID", "Linked AC", "Title", "Type", "Priority",
    "Preconditions", "Steps", "Test Data", "Expected Result",
]
WIDTHS = [10, 12, 11, 40, 11, 10, 35, 55, 35, 45]


def write_excel(story: dict, test_cases: list[dict], path: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"

    thin = Side(style="thin", color="BBBBBB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill("solid", fgColor="1F4E78")

    ws.append(HEADERS)
    for col, w in enumerate(WIDTHS, start=1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[cell.column_letter].width = w

    trace = defaultdict(list)
    for i, tc in enumerate(test_cases, start=1):
        tc_id = f"TC_{i:03d}"
        trace[tc["linked_ac"]].append(tc_id)
        steps = "\n".join(f"{n}. {s}" for n, s in enumerate(tc["steps"], start=1))
        ws.append([
            tc_id, story["story_id"], tc["linked_ac"], tc["title"], tc["test_type"],
            tc["priority"], tc["preconditions"], steps, tc["test_data"], tc["expected_result"],
        ])

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # Traceability sheet: AC -> test cases
    tr = wb.create_sheet("Traceability")
    tr.append(["AC ID", "Acceptance Criterion", "Test Cases", "Count"])
    for cell in tr[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
    for ac in story["acceptance_criteria"]:
        ids = trace.get(ac["id"], [])
        tr.append([ac["id"], ac["text"], ", ".join(ids), len(ids)])
    for letter, w in zip("ABCD", [9, 80, 40, 8]):
        tr.column_dimensions[letter].width = w
    for row in tr.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    wb.save(path)
    return path
