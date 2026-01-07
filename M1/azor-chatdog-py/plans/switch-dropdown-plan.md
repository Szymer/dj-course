## Plan: Terminalowy dropdown dla /switch

Krótki TL;DR — Dodajemy w Pythonowej implementacji AZØRY terminalowy, keyboard-only dropdown. Gdy użytkownik wywoła `/switch` bez argumentu, wyświetlamy interaktywną listę sesji (ID + tytuł/snippet), użytkownik wybierze klawiaturą, a wybrany `session_id` przekażemy do istniejącej funkcji `switch_session`. Implementacja minimalnie inwazyjna: nowy moduł UI + mała modyfikacja handlera komendy.

### Steps
1. Zlokalizuj handler: otwórz `M1/azor-chatdog-py/src/command_handler.py` i `M1/azor-chatdog-py/src/cli/prompt.py`; znajdź funkcję parsującą komendę `/switch` (np. `handle_switch` / `switch_command`) i potwierdź jak wywoływane jest `session_manager`.
2. Przygotuj loader sesji: rozszerz lub dodaj w `M1/azor-chatdog-py/src/session/session_manager.py` lub `M1/azor-chatdog-py/src/files/session_files.py` funkcję `list_sessions()` zwracającą listę obiektów z `session_id`, `title`, `snippet`, `updated_at`.
3. Dodaj UI picker: utwórz plik `M1/azor-chatdog-py/src/ui/session_picker.py` z funkcją `pick_session(sessions) -> session_id`. Implementacja bazowa:
   - Minimalna opcja: `InquirerPy` / `Inquirer` — prosty select z obsługą strzałek.
   - Zalecana opcja: `prompt_toolkit` — lepsza kontrola keybindings i zgodność z Windows.
   - Fallback: prosty numerowany wybór (wpisz numer + Enter).
4. Zintegruj z handlerem: w `handle_switch` (w `src/command_handler.py` lub powiązanym pliku) — jeśli komenda wywołana bez argumentu:
   - pobierz listę `sessions = list_sessions()`
   - jeśli `sessions` pusta → pokaż komunikat
   - wywołaj `selected_id = pick_session(sessions)`
   - wywołaj istniejącą funkcję przełączającą, np. `switch_session(selected_id)`
5. Wyświetlanie tytułów/snippetów: jeśli `title` istnieje pokaż go, inaczej pokaż `session_id` + skrót ostatniej wiadomości (pole `snippet`). Sortuj domyślnie po `updated_at` (ostatnio używane na górze).
6. Dokumentacja + testy manualne:
   - Dodaj krótką instrukcję do `M1/azor-chatdog-py/README.md`.
   - Przetestuj w PowerShell / Windows Terminal; sprawdź fallback w ograniczonych terminalach.

### Further Considerations
1. Biblioteka TUI: `prompt_toolkit` (zalecane — pełne keybindings, dobra kompatybilność z Windows) lub `InquirerPy` (szybsza integracja). Jeśli w przyszłości planujesz bardziej rozbudowane UI, rozważ `Textual`.
2. Miejsce integracji: najlepszy punkt wejścia to `M1/azor-chatdog-py/src/cli/prompt.py` (popup/keybindings) lub bezpośrednio w handlerze `/switch` w `M1/azor-chatdog-py/src/command_handler.py`.
3. Cross-platform: testuj na PowerShell i Windows Terminal. Przy problemach, użyj prostego numerowanego fallbacku.

### Szacunek pracy
- Odszukanie handlera i przygotowanie listy sesji — 0.5 h
- Implementacja `session_picker` z `prompt_toolkit` — 1–2 h
- Integracja z handlerem i testy — 1 h
- Dokumentacja i drobne poprawki — 0.5 h
Razem: ~3–4.5 h

