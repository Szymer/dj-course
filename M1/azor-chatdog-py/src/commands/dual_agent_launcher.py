"""
Launcher for dual agent discussion from within Azor chat.
"""
import sys
import os

def launch_dual_agent():
    """Launch the dual agent interactive discussion."""
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    
    try:
        from src.commands.dual_agent import run_dual_agent_interactive
        print("\n" + "="*60)
        print("DUAL AGENT DISCUSSION MODE")
        print("="*60 + "\n")
        run_dual_agent_interactive()
    except Exception as e:
        print(f"Błąd podczas uruchamiania dual agent: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Powrót do chatu z Azorem...")
    print("="*60 + "\n")
