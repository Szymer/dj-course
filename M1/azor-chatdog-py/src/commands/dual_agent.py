import sys
import os
from typing import Optional

# Support both module and direct script execution
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from src.dual_agent_discussion import DualAgentDiscussion, default_personas_path
    from src.llm.factory import create_client_from_env, get_engine_name
else:
    from ..dual_agent_discussion import DualAgentDiscussion, default_personas_path
    from ..llm.factory import create_client_from_env, get_engine_name


def run_dual_agent_interactive(personas_file: Optional[str] = None):
    personas_file = personas_file or default_personas_path()
    factory = None
    try:
        factory = create_client_from_env
        engine = get_engine_name()
    except Exception:
        factory = None
        engine = "SIMULATION"

    d = DualAgentDiscussion(personas_file, llm_client_factory=factory)
    print("Dostępne persony:")
    for i, n in enumerate(d.list_persona_names()):
        print(f"{i}: {n}")

    def pick(prompt_text: str) -> int:
        while True:
            try:
                v = int(input(prompt_text))
                if 0 <= v < len(d.personas):
                    return v
            except ValueError:
                pass
            print("Nieprawidłowy wybór, spróbuj ponownie.")

    a_idx = pick("Wybierz indeks pierwszej persony: ")
    b_idx = pick("Wybierz indeks drugiej persony: ")

    default_turns = d.config.get("default_turns", 6)
    try:
        turns = int(input(f"Liczba tur (domyślnie {default_turns}): ") or default_turns)
    except ValueError:
        turns = default_turns

    # Ask for conversation topic
    print("\n" + "="*60)
    print("TEMAT ROZMOWY")
    print("="*60)
    topic = input("\nO czym mają rozmawiać agenci?\nOpisz swój startup/pomysł/problem biznesowy:\n\n> ").strip()
    if not topic:
        topic = "Przedstaw swój pomysł na startup i poproś o feedback."
        print(f"\n(Użyto domyślnego tematu: {topic})")

    use_llm = factory is not None
    if use_llm:
        print(f"\nUżywam silnika: {engine}")
    else:
        print("\nTryb symulowany (brak klienta LLM).")

    debug = False
    try:
        ans = input("Pokaż debug sesji? (y/N): ")
        debug = ans.strip().lower() in ("y", "yes")
    except Exception:
        debug = False

    # Precreate sessions if requested for debug display
    if debug and use_llm:
        d._ensure_session(d.get_persona_by_index(a_idx))
        d._ensure_session(d.get_persona_by_index(b_idx))
        print("\n--- Debug: persona sessions ---")
        for pid, stored in d.persona_sessions.items():
            if isinstance(stored, dict):
                sess = stored.get("session")
                client = stored.get("client")
                print(f"Persona id: {pid} -> client-type: {type(client)}, session-type: {type(sess)}")
            else:
                sess = stored
                print(f"Persona id: {pid} -> session-type: {type(sess)}")
            try:
                hist = sess.get_history() if sess is not None and hasattr(sess, 'get_history') else None
                print("  history:", hist)
            except Exception as e:
                print("  (could not read history)", e)
        print("--- koniec debug ---\n")

    convo = d.run_dialogue(a_idx, b_idx, turns=turns, starter_text=topic, use_llm=use_llm)

    print("\n" + "="*60)
    print("ROZMOWA")
    print("="*60 + "\n")
    for line in convo:
        print(line)
        print()  # Empty line between turns


if __name__ == "__main__":
    run_dual_agent_interactive()
