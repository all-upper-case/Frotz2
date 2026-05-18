import datetime
import json
import os
import requests
import system_prompts

VENICE_API_KEY = os.environ.get("VENICE_API_KEY") or os.environ.get("MISTRAL_API_KEY")
API_URL = "https://api.venice.ai/api/v1/chat/completions"
DEBUG_LOG_FILE = "debug_log.txt"
LAST_TURN_FILE = "last_turn_debug.txt"
LORE_FILE = "lore.txt"
DEFAULT_MODEL = os.environ.get("VENICE_MODEL", "zai-org-glm-4.7")

class LLMInterface:
    def __init__(self):
        self.model = DEFAULT_MODEL

    def log_console(self, msg):
        print(f"\n[AI] {msg}", flush=True)

    def get_lore(self):
        if os.path.exists(LORE_FILE):
            with open(LORE_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return "".join([l for l in lines if not l.startswith("WORLD_NAME:")])
        return "A mysterious text adventure."

    def _extract_usage(self, response_json):
        usage = response_json.get('usage', {}) if isinstance(response_json, dict) else {}
        return {
            "input_tokens": usage.get('prompt_tokens', 0),
            "output_tokens": usage.get('completion_tokens', 0),
            "total_tokens": usage.get('total_tokens', 0)
        }

    def _write_debug_log(self, role, output_data, usage_info):
        self.log_console(f"Completed {role}. Total Tokens: {usage_info['total_tokens']}")
        with open(DEBUG_LOG_FILE, "a", encoding='utf-8') as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"--- {ts} [{role}] ---\n"
                f"[USAGE]: in={usage_info.get('input_tokens')} out={usage_info.get('output_tokens')} tot={usage_info.get('total_tokens')}\n"
                f"[OUTPUT]: {json.dumps(output_data, indent=2)}\n\n"
            )

    def _write_last_turn_debug(self, messages, output_data):
        """Writes the raw inputs and outputs of the last 2 turns."""
        current_turn = {
            "timestamp": datetime.datetime.now().isoformat(),
            "messages_sent_to_llm": messages,
            "raw_response_from_llm": output_data
        }

        history = []
        if os.path.exists(LAST_TURN_FILE):
            try:
                with open(LAST_TURN_FILE, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list): history = content
            except: pass

        history.append(current_turn)
        history = history[-2:]

        with open(LAST_TURN_FILE, "w", encoding='utf-8') as f:
            json.dump(history, f, indent=2)

    def _req(self, system, user, role):
        if not VENICE_API_KEY:
            self.log_console("ERROR: API KEY MISSING")
            return {"error": "No API Key", "narrative": "Error: VENICE_API_KEY not found."}

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.5,
            "reasoning_effort": "medium",
            "venice_parameters": {
                "enable_web_search": "off",
                "enable_web_scraping": False,
                "enable_web_citations": False,
                "include_venice_system_prompt": False,
                "include_search_results_in_stream": False
            }
        }

        self.log_console(f"Sending Request: {role}...")
        resp = None

        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            res_json = resp.json()

            message = res_json["choices"][0]["message"]
            raw_content = message.get("content", "")

            # Robust parsing for potentially multimodal or non-string content
            if isinstance(raw_content, list):
                text_parts = []
                for part in raw_content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                raw_content = "".join(text_parts)

            if not isinstance(raw_content, str) or not raw_content.strip():
                raise ValueError(f"Model returned empty or non-string content: {raw_content!r}")

            data = json.loads(raw_content)

            usage = self._extract_usage(res_json)
            data["_usage"] = usage

            self._write_debug_log(role, data, usage)
            self._write_last_turn_debug(messages, data)

            return data

        except requests.HTTPError as e:
            body = ""
            try:
                body = resp.text[:2000] if resp is not None else ""
            except Exception:
                pass
            self.log_console(f"HTTP ERROR: {str(e)} | BODY: {body}")
            return {
                "narrative": f"The world logic ripples... (Venice HTTP Error: {e})",
                "error": True
            }

        except json.JSONDecodeError as e:
            body = ""
            try:
                if resp is not None:
                    res_json = resp.json()
                    body = json.dumps(res_json, indent=2)[:3000]
            except Exception:
                try:
                    body = resp.text[:3000] if resp is not None else ""
                except Exception:
                    pass

            self.log_console(f"JSON PARSE ERROR: {str(e)} | BODY: {body}")
            return {
                "narrative": f"The world logic ripples... (JSON Parse Error: {e})",
                "error": True
            }

        except Exception as e:
            self.log_console(f"ERROR: {str(e)}")
            return {
                "narrative": f"The world logic ripples... (AI Error: {e})",
                "error": True
            }

    def generate_genesis(self):
        lore = self.get_lore()
        self.log_console("STARTING GENESIS...")
        return self._req(system_prompts.PROMPT_GENESIS.format(lore_bible=lore), "Initiate World Genesis.", "GENESIS")

    def generate_room(self, prev_room, direction, thread, blueprint, map_summary):
        lore = self.get_lore()
        p_name = prev_room['name'] if prev_room else "The Void"
        p_desc = prev_room['description'] if prev_room else "Nothingness."
        sys = system_prompts.PROMPT_ARCHITECT.format(
            lore_bible=lore, narrative_thread=thread, blueprint=blueprint,
            map_summary=map_summary, prev_name=p_name, prev_desc=p_desc, direction=direction
        )
        return self._req(sys, "Describe the new area.", "ARCHITECT")

    def process_turn(self, user_input, thread, context_dump):
        lore = self.get_lore()
        sys = system_prompts.PROMPT_DM.format(
            lore_bible=lore, narrative_thread=thread, 
            context_dump=context_dump
        )
        return self._req(sys, f"PLAYER ACTION: {user_input}", "DM")

    def generate_fix(self, item_name, current_desc, user_instruction):
        sys = system_prompts.PROMPT_FIXER.format(
            item_name=item_name, 
            current_desc=current_desc, 
            user_instruction=user_instruction
        )
        return self._req(sys, "Fix this item description.", "FIXER")


    def get_available_models(self):
        if not VENICE_API_KEY: return []
        try:
            headers = {"Authorization": f"Bearer {VENICE_API_KEY}"}
            # Fetch full model list with specs
            resp = requests.get("https://api.venice.ai/api/v1/models?type=text", headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get('data', []):
                spec = m.get('model_spec', {})
                caps = spec.get('capabilities', {})
                pricing = spec.get('pricing', {})
                
                # We prioritize models with text capabilities or reasoning
                if m.get('type') == 'text' or caps.get('supportsReasoning'):
                    models.append({
                        "id": m['id'],
                        "name": spec.get('name', m['id']),
                        "description": spec.get('description', ''),
                        "context_window": spec.get('availableContextTokens', 'Unknown'),
                        "reasoning": caps.get('supportsReasoning', False),
                        "pricing": {
                            "prompt": pricing.get('prompt', '0'),
                            "completion": pricing.get('completion', '0')
                        }
                    })
            return models
        except Exception as e:
            self.log_console(f"Model Fetch Error: {e}")
            return []