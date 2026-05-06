from utils import run_lark_command, AGENT_CONFIG
from pathlib import Path
from config import DEFAULT_BOT_SCOPE
import json
import os
import httpx

SKILL_DOCS_DIR = Path(__file__).parent / "lark-doc"

TOOLS = []


def read_skill_file(relative_path: str) -> str:
    file_path = SKILL_DOCS_DIR / relative_path
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    return ""


def get_all_skill_docs() -> dict:
    docs = {}
    if SKILL_DOCS_DIR.exists():
        for root, dirs, files in os.walk(SKILL_DOCS_DIR):
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(SKILL_DOCS_DIR))
                    docs[rel_path] = read_skill_file(rel_path)
    return docs


def get_skill_summary() -> str:
    summary = """This agent can access Feishu/Lark OpenAPI through lark-cli tool.

Available lark-cli modules and commands (read SKILL.md for details):
- lark-doc: Cloud documents (docs +fetch, +create, +update, etc.)
- lark-drive: Cloud drive (drive +search)
- lark-contact: Contacts (contact +search-user, +get-user)
- lark-calendar: Calendar (calendar +agenda, calendars list)
- lark-base: Multi-dimensional tables (base +record-list, +table-list, etc.)
- lark-sheets: Spreadsheets
- lark-im: Instant messaging

The agent should read the relevant SKILL.md files to understand command syntax and flags.
"""
    return summary


def execute_lark_command(command: list, as_user: bool = True) -> dict:
    if as_user and "--as" not in command:
        cmd = command + ["--as", "user"]
    else:
        cmd = command
    if "--format" not in cmd:
        cmd.extend(["--format", "json"])
    result = run_lark_command(cmd)
    return result



