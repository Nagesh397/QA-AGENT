import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load the key from .env; also fall back to .env.txt (Windows can hide the .txt extension)
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.txt")

from agent.graph import build_graph  # noqa: E402  (after load_dotenv)


def main():
    parser = argparse.ArgumentParser(description="Generate test cases from Jira acceptance criteria")
    parser.add_argument("--file", default="jira/PROJ-101.txt", help="Story file in the jira/ folder")
    parser.add_argument("--out", default=None, help="Output .xlsx path")
    args = parser.parse_args()

    out = args.out or f"output/{Path(args.file).stem}_test_cases.xlsx"
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    app = build_graph()
    app.invoke({"story_file": args.file, "output_path": out})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
