from volcenginesdkarkruntime import Ark
from config import LLM_CONFIG
from tools import execute_lark_command, read_skill_file, get_all_skill_docs, get_skill_summary
import json
import re
import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("agent_autonomous")
logger.setLevel(logging.INFO)
log_file = LOG_DIR / f"agent_autonomous_{datetime.now().strftime('%Y%m%d')}.log"
handler = logging.FileHandler(log_file, encoding='utf-8')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


class AutonomousAgent:
    def __init__(self):
        self.client = Ark(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"]
        )
        self.model = LLM_CONFIG["model"]
        self.skill_docs = get_all_skill_docs()
        self.main_skill_content = read_skill_file("SKILL.md")

    def process_request(self, context: dict) -> dict:
        task_type = context.get("task_type", "").lower()
        agent_data = context.get("Agent_data", {})
        query_data = agent_data.get("query_data", "")

        if task_type == "help":
            return {
                "code": 0,
                "msg": "success",
                "query_data": "Agent is fully autonomous. It reads skill documentation from lark-doc folder to understand available commands.\n" + get_skill_summary()
            }

        try:
            return self._handle_autonomous(query_data, context)
        except Exception as e:
            logger.error("Processing error: " + str(e))
            return {"code": 1, "msg": "error", "query_data": str(e)}

    def _handle_autonomous(self, query_data: str, context: dict) -> dict:
        query_str = query_data if isinstance(query_data, str) else json.dumps(query_data, ensure_ascii=False)

        logger.info("User query: " + query_str)

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": "User request: " + query_str + "\n\nFirst, read the SKILL.md to understand available commands. Then determine which specific skill doc to read for detailed command syntax."}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            llm_response = response.choices[0].message.content
            logger.info("Step 1 - Skill selection response: " + llm_response[:500])

            cmd_data = self._extract_json(llm_response)

            if "read_skills" in cmd_data:
                skill_contents = {}
                for skill_path in cmd_data["read_skills"]:
                    content = read_skill_file(skill_path)
                    if content:
                        skill_contents[skill_path] = content
                    else:
                        for key in self.skill_docs:
                            if skill_path.lower() in key.lower() or key.lower() in skill_path.lower():
                                skill_contents[key] = self.skill_docs[key]
                                break

                messages = [
                    {"role": "system", "content": self._build_command_builder_prompt(skill_contents)},
                    {"role": "user", "content": "User request: " + query_str + "\n\nBased on the skill documentation, construct the exact lark-cli command to execute."}
                ]

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1
                )
                llm_response = response.choices[0].message.content
                logger.info("Step 2 - Command construction: " + llm_response[:500])

                cmd_data = self._extract_json(llm_response)

            command = cmd_data.get("command", [])
            if isinstance(command, str):
                command = self._parse_command_string(command)

            if not command:
                return {
                    "code": 0,
                    "msg": "success",
                    "query_data": llm_response
                }

            self._log_tool_chain("autonomous", ["execute: " + " ".join(command) if isinstance(command, list) else str(command)], context)
            result = execute_lark_command(command if isinstance(command, list) else [command])
            return self._format_result(result)

        except Exception as e:
            logger.error("Autonomous routing failed: " + str(e))
            return {"code": 1, "msg": "error", "query_data": "Autonomous routing failed: " + str(e)}

    def _build_system_prompt(self) -> str:
        base_prompt = """You are a fully autonomous AI Agent that controls Feishu/Lark CLI (lark-cli).

Your behavior:
1. When given a user request, FIRST read the SKILL.md file to understand available modules
2. Then determine which specific skill documentation file to read for detailed command syntax
3. Read that skill file to understand the exact command format and required parameters
4. Construct and execute the appropriate lark-cli command

Available skill documentation files in lark-doc folder:
"""
        for path in self.skill_docs.keys():
            base_prompt += "- " + path + "\n"

        base_prompt += """

IMPORTANT:
- ALWAYS read SKILL.md first to understand the module structure
- Then read the specific skill file needed for the command
- Return a JSON object like: {"read_skills": ["SKILL.md", "references/lark-doc-fetch.md"]} to request reading specific skill files
- After reading skills, return: {"command": ["lark-cli", "module", "command", "--flag", "value"]}
"""
        return base_prompt

    def _build_command_builder_prompt(self, skill_contents: dict) -> str:
        prompt = """You have read the following skill documentation:

"""
        for path, content in skill_contents.items():
            prompt += "=== " + path + " ===\n" + content[:3000] + "\n\n"

        prompt += """
Based on the documentation above, construct the exact lark-cli command to execute.

Return ONLY a JSON object:
{"command": ["lark-cli", "module", "command", "--flag", "value", ...]}

Examples:
- Search documents: {"command": ["lark-cli", "drive", "+search", "--query", "文档名", "--format", "json", "--as", "user"]}
- Fetch doc: {"command": ["lark-cli", "docs", "+fetch", "--doc", "<token>", "--format", "json", "--as", "user"]}
"""
        return prompt

    def _log_tool_chain(self, task_type: str, tool_chain: list, context: dict):
        log_data = {
            "task_type": task_type,
            "tool_chain": tool_chain,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        logger.info("TOOL_CHAIN: " + json.dumps(log_data, ensure_ascii=False))

    def _extract_json(self, text: str) -> dict:
        text = text.strip()

        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except:
            pass

        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        return {}

    def _parse_command_string(self, cmd_str: str) -> list:
        if not cmd_str:
            return []
        cmd_str = cmd_str.strip()

        if cmd_str.startswith("["):
            try:
                parsed = json.loads(cmd_str)
                if isinstance(parsed, list):
                    return parsed
            except:
                pass

        if cmd_str.startswith("lark-cli"):
            parts = []
            current = ""
            in_quotes = False
            quote_char = None

            for char in cmd_str:
                if char in '"\'' and (not in_quotes or quote_char == char):
                    if in_quotes:
                        parts.append(current)
                        current = ""
                    in_quotes = not in_quotes
                    quote_char = char if not quote_char else None
                elif char == ' ' and not in_quotes:
                    if current:
                        parts.append(current)
                        current = ""
                else:
                    current += char

            if current:
                parts.append(current)

            cleaned = []
            for part in parts:
                part = part.strip('"\'').strip()
                if part and part not in [',']:
                    cleaned.append(part)

            result = []
            i = 0
            while i < len(cleaned):
                if cleaned[i] == 'lark-cli':
                    cmd = ['lark-cli']
                    i += 1
                    while i < len(cleaned) and not cleaned[i].startswith('--'):
                        cmd.append(cleaned[i])
                        i += 1
                    while i < len(cleaned):
                        if cleaned[i].startswith('--'):
                            if i + 1 < len(cleaned) and not cleaned[i + 1].startswith('--'):
                                cmd.extend([cleaned[i], cleaned[i + 1]])
                                i += 2
                            else:
                                cmd.append(cleaned[i])
                                i += 1
                        else:
                            i += 1
                    result.append(cmd)
                else:
                    i += 1
            return result[0] if result else cleaned
        return [cmd_str]

    def _format_result(self, result: dict) -> dict:
        if isinstance(result, dict) and "code" in result and result["code"] != 0:
            return result
        return {
            "code": 0,
            "msg": "success",
            "query_data": result
        }


AgentIndata = AutonomousAgent