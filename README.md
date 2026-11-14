# QA Test Case Agent

An agent that reads acceptance criteria from a Jira story and generates test cases in Excel format. It is built with LangGraph and LangChain and uses Google Gemini for test case generation.

Until Jira access is available, stories are read from local text files in the `jira/` folder.

## How it works

The agent is a LangGraph workflow with four steps:

1. **read_criteria**: reads the story file and parses the story ID, title, description and acceptance criteria (lines like `AC1: ...`).
2. **generate_tests**: sends the acceptance criteria to Gemini and gets back structured test cases (title, linked AC, type, priority, preconditions, steps, test data, expected result).
3. **review_coverage**: checks that every acceptance criterion has at least one test case. If any are missing, it loops back to step 2 for only the missing criteria (up to 2 retries).
4. **write_excel**: writes the test cases to an `.xlsx` file.

```
START -> read_criteria -> generate_tests -> review_coverage -> write_excel -> END
                               ^                   |
                               |___ (gaps found) __|
```

## Project structure

```
QA AGENT/
├── .env                  # GEMINI_API_KEY (see Setup)
├── requirements.txt
├── main.py               # command-line entry point
├── README.md
├── jira/
│   └── PROJ-101.txt      # sample story with acceptance criteria
├── agent/
│   ├── __init__.py
│   ├── graph.py          # LangGraph workflow and Gemini prompt
│   ├── jira_source.py    # reads stories (local file now, real Jira later)
│   ├── models.py         # Pydantic schema for test cases
│   └── excel_writer.py   # builds the Excel workbook
└── output/               # generated Excel files
```

## Setup

1. **Create and activate a virtual environment** (Python 3.10 or newer):

   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```
   pip install -r requirements.txt
   ```

3. **Add your Gemini API key** to a file named `.env` in the project root:

   ```
   GEMINI_API_KEY=your_key_here
   ```

   Optional: choose a different model with `GEMINI_MODEL=<model name>`. The default is `gemini-3.8-flash`.

   On Windows, make sure the file is really named `.env` and not `.env.txt`. The code also falls back to `.env.txt`, but `.env` is the standard name.

## Usage

Run with the sample story:

```
python main.py
```

Run with another story or a custom output path:

```
python main.py --file jira/PROJ-102.txt --out output/custom.xlsx
```

| Option   | Default                              | Description                      |
|----------|--------------------------------------|----------------------------------|
| `--file` | `jira/PROJ-101.txt`                  | Story file to read               |
| `--out`  | `output/<story file name>_test_cases.xlsx` | Where to save the Excel file |

## Story file format

Create one text file per story in the `jira/` folder:

```
Story ID: PROJ-101
Title: User Login
Description: As a registered user, I want to log in with my email and password so that I can access my account.

Acceptance Criteria:
AC1: User can log in with a valid registered email and correct password and is redirected to the dashboard.
AC2: Login fails with an error message "Invalid email or password" when the email or password is incorrect.
```

Each acceptance criterion must be on its own line and start with `AC` followed by a number and a colon. `Story ID`, `Title` and `Description` are optional; if `Story ID` is missing, the file name is used.

## Output

The Excel file has two sheets:

- **Test Cases**: one row per test case with the columns TC ID, Story ID, Linked AC, Title, Type, Priority, Preconditions, Steps, Test Data and Expected Result. The header row is frozen and filterable.
- **Traceability**: each acceptance criterion with the test cases that cover it and a count, so coverage gaps are easy to spot.

## Moving to real Jira

Only `agent/jira_source.py` needs to change. Add a `RealJiraSource` class with the same `get_story(...)` method that fetches the issue from the Jira REST API and returns the same dictionary shape:

```python
{
    "story_id": "PROJ-101",
    "title": "...",
    "description": "...",
    "acceptance_criteria": [{"id": "AC1", "text": "..."}, ...],
}
```

Then use it in `read_criteria` in `agent/graph.py`. The rest of the workflow stays the same. You will need your Jira base URL, account email and an API token.

## Troubleshooting

- **404 NOT_FOUND for a Gemini model**: the model name is retired or not available to your key. Set `GEMINI_MODEL` in `.env` to a model your key can use.
- **`KeyError: 'GEMINI_API_KEY'`**: the key was not loaded. Check that `.env` is in the project root and the variable name is spelled exactly `GEMINI_API_KEY`.
- **"No acceptance criteria found"**: the story file has no lines starting with `AC1:`, `AC2:` and so on.
- **Some criteria have no test cases**: the agent retries up to 2 times. If gaps remain, they show as a count of 0 on the Traceability sheet.
