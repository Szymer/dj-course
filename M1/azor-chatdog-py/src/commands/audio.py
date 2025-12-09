from typing import List, Dict
from cli import console
import warnings
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import os

warnings.filterwarnings("ignore", category=UserWarning)

def display_full_session(history: List[Dict], session_id: str, assistant_name: str):
    """
    Displays the full session history.
    
    Args:
        history: Lista słowników w formacie {"role": "user|model", "parts": [{"text": "..."}]}
        session_id: ID sesji
        assistant_name: Nazwa asystenta do wyświetlenia
    """
    if not history:
        console.print_info("Historia sesji jest pusta.")
        return

    console.print_info(f"\n--- PEŁNA HISTORIA SESJI ({session_id}, {len(history)} wpisów) ---")
    
    for i, content in enumerate(history):
        # Handle universal dictionary format
        role = content.get('role', '')
        display_role = "TY" if role == "user" else assistant_name
        
        # Extract text from parts
        text = ""
        if 'parts' in content and content['parts']:
            text = content['parts'][0].get('text', '')
        
        # Display with appropriate function
        if role == "user":
            console.print_user(f"\n[{i+1}] {display_role}:")
            console.print_user(f"{text}")
        else:
            console.print_assistant(f"\n[{i+1}] {display_role}:")
            console.print_assistant(f"{text}")
            
    console.print_info("--------------------------------------------------------")


def synthesize_and_play_audio(text: str, speaker_wav_path: str, language: str = "pl"):
    """
    Syntetyzuje tekst na mowę za pomocą TTS (XTTS) i odtwarza dźwięk przez sounddevice.
    
    Args:
        text: Tekst do syntezy
        speaker_wav_path: Ścieżka do pliku WAV z próbką głosu
        language: Język syntezy (domyślnie "pl")
    """
    try:
        from TTS.api import TTS
        
        console.print_info("🎤 Ładowanie modelu TTS...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
        console.print_info("✅ Model załadowany")
        
        # Tworzymy tymczasowy plik do syntezy
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        console.print_info("🔊 Generowanie audio...")
        tts.tts_to_file(
            text=text,
            file_path=tmp_path,
            speaker_wav=speaker_wav_path,
            language=language
        )
        
        # Wczytujemy wygenerowany dźwięk
        data, samplerate = sf.read(tmp_path)
        
        console.print_info("▶️  Odtwarzanie...")
        # Odtwarzamy dźwięk
        sd.play(data, samplerate)
        sd.wait()  # Czekamy na zakończenie odtwarzania
        
        # Usuwamy tymczasowy plik
        os.unlink(tmp_path)
        console.print_info("✅ Odtwarzanie zakończone")
        
    except Exception as e:
        console.print_error(f"❌ Błąd podczas syntezy/odtwarzania: {e}")


def play_session_responses(history: List[Dict], speaker_wav_path: str, language: str = "pl"):
    """
    Przetwarza wszystkie odpowiedzi modelu z sesji i odtwarza je jako dźwięk.
    
    Args:
        history: Lista słowników w formacie {"role": "user|model", "parts": [{"text": "..."}]}
        speaker_wav_path: Ścieżka do pliku WAV z próbką głosu
        language: Język syntezy (domyślnie "pl")
    """
    if not history:
        console.print_info("Historia sesji jest pusta.")
        return
    
    # Filtrujemy tylko odpowiedzi modelu (nie użytkownika)
    # Obsługujemy zarówno 'model' (Gemini) jak i 'assistant' (OpenAI)
    model_responses = [
        content for content in history 
        if content.get('role') in ['model', 'assistant']
    ]
    
    if not model_responses:
        console.print_info("Brak odpowiedzi modelu w historii sesji.")
        return
    
    console.print_info(f"\n🎵 Znaleziono {len(model_responses)} odpowiedzi modelu do przetworzenia.\n")
    
    for i, content in enumerate(model_responses, 1):
        # Ekstrakcja tekstu z odpowiedzi
        # Obsługa zarówno formatu Gemini ('parts') jak i OpenAI ('content')
        text = ""
        if 'parts' in content and content['parts']:
            text = content['parts'][0].get('text', '')
        elif 'content' in content:
            text = content.get('content', '')
        
        if not text.strip():
            console.print_info(f"[{i}/{len(model_responses)}] Pusta odpowiedź, pomijam.")
            continue
        
        console.print_info(f"\n[bold]--- Odpowiedź {i}/{len(model_responses)} ---[/bold]")
        console.print_assistant(f"{text[:100]}..." if len(text) > 100 else text)
        
        # Syntetyzujemy i odtwarzamy
        synthesize_and_play_audio(text, speaker_wav_path, language)
    
    console.print_info("\n🎉 Wszystkie odpowiedzi zostały przetworzone i odtworzone.")
 
