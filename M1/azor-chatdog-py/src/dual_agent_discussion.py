"""
Dual-agent discussion manager (isolated sessions per persona).

This module provides a small manager that loads personas from a JSON file
and creates isolated LLM sessions per persona so prompts don't leak.
"""
import json
import os
import time
import re
from typing import Any, Dict, List, Optional


class Persona:
    def __init__(self, pid: str, name: str, prompt: str, traits: Dict = None, start_prompt: str = None):
        self.id = pid
        self.name = name
        self._prompt = prompt or ""
        self.traits = traits or {}
        self.start_prompt = start_prompt or ""

    @property
    def system_prompt(self) -> str:
        return self._prompt

    def __repr__(self) -> str:
        return f"Persona(id={self.id!r}, name={self.name!r})"


class DualAgentDiscussion:
    def __init__(self, personas_file: str, llm_client_factory: Optional[Any] = None):
        self.personas_file = personas_file
        self.personas: List[Persona] = []
        self.config: Dict = {}
        self.llm_client_factory = llm_client_factory
        self.persona_sessions: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        with open(self.personas_file, encoding="utf-8") as f:
            data = json.load(f)
        self.personas = []
        for p in data.get("personas", []):
            pid = p.get("id") or p.get("name")
            self.personas.append(Persona(pid, p.get("name", pid), p.get("prompt", ""), p.get("traits", {}), p.get("start_prompt", "")))
        self.config = {k: v for k, v in data.items() if k != "personas"}

    def list_persona_names(self) -> List[str]:
        return [p.name for p in self.personas]

    def get_persona_by_index(self, idx: int) -> Persona:
        return self.personas[idx]

    def _ensure_session(self, persona: Persona):
        if persona.id in self.persona_sessions:
            stored = self.persona_sessions[persona.id]
            return stored["session"] if isinstance(stored, dict) else stored
        if not self.llm_client_factory:
            self.persona_sessions[persona.id] = None
            return None
        # Create a fresh client instance for each persona to avoid sharing/closing issues
        client = self.llm_client_factory()
        # Note: start_prompt is NOT used in dual-agent mode (it's for external users)
        # Agents communicate directly with each other using the topic as starter
        session = client.create_chat_session(system_instruction=persona.system_prompt, history=[])
        # Store both client and session to keep client alive
        self.persona_sessions[persona.id] = {"client": client, "session": session}
        return session

    def run_dialogue(self, idx_a: int, idx_b: int, turns: int = 6, starter_text: Optional[str] = None, use_llm: bool = False):
        a = self.get_persona_by_index(idx_a)
        b = self.get_persona_by_index(idx_b)
        sess_a = self._ensure_session(a) if use_llm else None
        sess_b = self._ensure_session(b) if use_llm else None
        convo: List[str] = []
        speaker = a
        speaker_sess = sess_a
        other = b
        other_sess = sess_b

        if use_llm and speaker_sess is not None:
            if starter_text:
                current_input = starter_text
            else:
                current_input = "Kontynuuj rozmowę zgodnie z rolą."
        else:
            current_input = starter_text or f"{speaker.name} zaczyna rozmowę."

        for turn_num in range(turns):
            if use_llm and speaker_sess is not None:
                max_retries = 5
                base_retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        response = speaker_sess.send_message(current_input)
                        # Extract text from response - some clients return string, others return object with .text
                        reply_text = response.text if hasattr(response, 'text') else str(response)
                        reply = f"{speaker.name}: {reply_text}"
                        break  # Success, exit retry loop
                    except Exception as e:
                        error_msg = str(e)
                        
                        # Handle rate limit (429) with automatic retry delay from API
                        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                            # Try to extract retry delay from error message
                            wait_time = None
                            retry_match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_msg, re.IGNORECASE)
                            if retry_match:
                                wait_time = float(retry_match.group(1))
                            else:
                                wait_time = base_retry_delay * (attempt + 1)
                            
                            if attempt < max_retries - 1:
                                print(f"\n⚠️  Limit API przekroczony. Czekam {wait_time:.1f}s... (próba {attempt + 2}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                            else:
                                print(f"\n❌ Błąd API po {max_retries} próbach: przekroczony limit requestów")
                                print(f"💡 Zakończono na turze {turn_num + 1}/{turns}")
                                return convo
                        
                        # Handle server overload (503)
                        elif "503" in error_msg or "overloaded" in error_msg.lower():
                            if attempt < max_retries - 1:
                                wait_time = base_retry_delay * (attempt + 1)
                                print(f"\n⚠️  Model przeciążony, ponawiam za {wait_time}s... (próba {attempt + 2}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                            else:
                                print(f"\n❌ Błąd API po {max_retries} próbach: {error_msg}")
                                print(f"💡 Zakończono na turze {turn_num + 1}/{turns}")
                                return convo
                        else:
                            # Other error - fail immediately
                            print(f"\n❌ Błąd podczas komunikacji z LLM: {error_msg}")
                            print(f"💡 Zakończono na turze {turn_num + 1}/{turns}")
                            return convo
            else:
                tone = speaker.traits.get("tone", "neutral")
                reply = f"{speaker.name}: ({tone}) krótkie, symulowane zdanie."
                reply_text = reply
            
            convo.append(reply)
            # Pass only the text content to the next speaker (without the name prefix)
            current_input = reply_text if use_llm and speaker_sess is not None else reply
            speaker, other = other, speaker
            speaker_sess, other_sess = other_sess, speaker_sess

        return convo


def default_personas_path() -> str:
    base = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(base, "..", "personas.json"))
