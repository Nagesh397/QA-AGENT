import re
from pathlib import Path


class LocalJiraSource:
    """Reads a story from the local jira/ folder.
    Swap this class for a real Jira client later; keep the same `get_story` signature."""

    def get_story(self, path: str) -> dict:
        text = Path(path).read_text(encoding="utf-8")

        story_id = re.search(r"^Story ID:\s*(.+)$", text, re.M)
        title = re.search(r"^Title:\s*(.+)$", text, re.M)
        desc = re.search(r"^Description:\s*(.+)$", text, re.M)
        acs = re.findall(r"^(AC\d+):\s*(.+)$", text, re.M)

        if not acs:
            raise ValueError(f"No acceptance criteria (lines like 'AC1: ...') found in {path}")

        return {
            "story_id": story_id.group(1).strip() if story_id else Path(path).stem,
            "title": title.group(1).strip() if title else "",
            "description": desc.group(1).strip() if desc else "",
            "acceptance_criteria": [{"id": a, "text": t.strip()} for a, t in acs],
        }


# Later, when you get access (sketch):
# class RealJiraSource:
#     def __init__(self, base_url, email, api_token): ...
#     def get_story(self, issue_key: str) -> dict:
#         # GET {base_url}/rest/api/3/issue/{issue_key}
#         # extract the acceptance criteria field (custom field or description section)
#         # and return the same dict shape as LocalJiraSource
#         ...

