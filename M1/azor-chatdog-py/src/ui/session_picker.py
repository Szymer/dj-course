from typing import List, Optional, Dict


def pick_session(sessions: List[Dict]) -> Optional[str]:
    """
    Presents a terminal-based, keyboard-first picker for sessions.

    Order of attempts:
    1. `prompt_toolkit.shortcuts.radiolist_dialog` (best UX)
    2. Native Windows selector using `msvcrt` (arrow keys)
    3. `prompt_toolkit` typed prompt with completer
    4. Simple numbered input fallback

    Returns selected `session_id` or `None` if cancelled.
    """
    # Normalize sessions into display entries
    choices = []
    for s in sessions:
        sid = s.get('id')
        if s.get('error'):
            display = f"{sid} - ERROR"
            choices.append((sid, display))
            continue

        title = s.get('title') or ''
        snippet = s.get('snippet') or ''
        last = s.get('last_activity', 'Brak aktywności')
        msgs = s.get('messages_count', 0)

        if title:
            display = f"{sid} — {title} ({msgs} msgs) - {last}"
        elif snippet:
            display = f"{sid} — {snippet} ({msgs} msgs) - {last}"
        else:
            display = f"{sid}  ({msgs} msgs) - {last}"

        choices.append((sid, display))

    # 1) radiolist_dialog (prompt_toolkit)
    try:
        from prompt_toolkit.shortcuts import radiolist_dialog

        values = [(sid, label) for sid, label in choices]
        result = radiolist_dialog(
            title='Wybór sesji',
            text='Wybierz sesję (użyj strzałek, Enter aby potwierdzić, Esc aby anulować):',
            values=values,
        ).run()
        return result
    except Exception:
        pass

    # 2) Native Windows selector (msvcrt)
    try:
        import msvcrt
        import os

        def _windows_keyboard_select(choices_list):
            idx = 0
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print('Wybierz sesję (użyj strzałek, Enter aby potwierdzić, Esc aby anulować):')
                for i, (_, label) in enumerate(choices_list):
                    prefix = '->' if i == idx else '  '
                    print(f"{prefix} {i+1}. {label}")

                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    k = msvcrt.getwch()
                    if k == 'H' and idx > 0:
                        idx -= 1
                    elif k == 'P' and idx < len(choices_list) - 1:
                        idx += 1
                elif ch == '\r':
                    return choices_list[idx][0]
                elif ch == '\x1b':
                    return None

        return _windows_keyboard_select(choices)
    except Exception:
        pass

    # 3) prompt_toolkit typed prompt with completer
    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.completion import Completer, Completion

        class SessionCompleter(Completer):
            def get_completions(self, document, complete_event):
                text = document.text
                for sid, label in choices:
                    if not text or label.startswith(text) or sid.startswith(text):
                        yield Completion(label, start_position=-len(text))

        print("Wybierz sesję (wpisz numer, id lub część tekstu, Enter aby anulować):")
        for idx, (_, label) in enumerate(choices, start=1):
            print(f"  {idx}. {label}")

        user = prompt('> ', completer=SessionCompleter())
        if not user:
            return None

        if user.isdigit():
            idx = int(user) - 1
            if 0 <= idx < len(choices):
                return choices[idx][0]
            return None

        for sid, _ in choices:
            if user.strip() == sid:
                return sid

        for sid, label in choices:
            if user.strip().lower() in label.lower():
                return sid

        return None
    except Exception:
        pass

    # 4) Final fallback: numbered input
    print("Wybierz sesję (wpisz numer i naciśnij Enter, puste aby anulować):")
    for idx, (_, label) in enumerate(choices, start=1):
        print(f"  {idx}. {label}")
    try:
        val = input('> ').strip()
    except EOFError:
        return None

    if not val:
        return None
    if not val.isdigit():
        for sid, _ in choices:
            if val == sid:
                return sid
        return None

    idx = int(val) - 1
    if 0 <= idx < len(choices):
        return choices[idx][0]
    return None

