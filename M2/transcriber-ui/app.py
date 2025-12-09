import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import pyaudio
import wave
import os
import time
import threading
import queue
import sys
import logging
import logging.handlers
from typing import TextIO
import json
from datetime import datetime

# --- Global Configuration ---
APP_TITLE = "Azor Transcriber"
# Set to True to print output to the console (standard output/stderr).
VERBOSE = False
LOG_FILENAME = "transcriber.log"
TRANSCRIPTIONS_DIR = "transcriptions"
HISTORY_JSON = os.path.join(TRANSCRIPTIONS_DIR, "history.json")

# --- Logging Setup ---
class StreamToLogger(TextIO):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    This captures stdout/stderr, including print() statements.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        # Handle buffer and write line by line
        for line in buf.rstrip().splitlines():
            # Check if the line is not empty (prevents logging empty lines from print())
            if line.strip():
                self.logger.log(self.level, line.strip())

    def flush(self):
        # Required by TextIO interface, but we flush line-by-line in write
        pass

# Configure the global logger BEFORE application startup
def setup_logging():
    """Con gures the logging system to save all output to a le and optionally to console."""
    os.makedirs('output', exist_ok=True)
    
    # 1. Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Capture everything from INFO level up

    # 2. File Handler (Always active)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, 
        maxBytes=1024*1024*5, # 5 MB per file
        backupCount=5,
        encoding='utf-8'
    )
    # Define a simple formatter for the file
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 3. Console Handler (Only active if VERBOSE is True)
    if VERBOSE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 4. Redirect stdout and stderr to the logger
    sys.stdout = StreamToLogger(root_logger, logging.INFO)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR)

setup_logging()
logging.info("Application initialization started.")

# --- FFmpeg Path Configuration ---
# Add common ffmpeg installation paths to system PATH
import platform
if platform.system() == "Windows":
    # Try to find ffmpeg in common Windows installation paths
    potential_ffmpeg_paths = [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        os.path.join(os.path.expanduser("~"), "scoop", "apps", "ffmpeg", "current", "bin"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe", "ffmpeg-8.0.1-full_build", "bin"),
    ]
    ffmpeg_found = False
    for path in potential_ffmpeg_paths:
        ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            os.environ["FFMPEG_BINARY"] = ffmpeg_exe  # Set direct path for transformers
            logging.info(f"Added ffmpeg path to PATH: {path}")
            ffmpeg_found = True
            break
    
    if not ffmpeg_found:
        logging.warning("ffmpeg not found in common paths. Transcription may fail.")

# --- Whisper Dependencies ---
# Ensure you have installed: pip install torch transformers librosa
# (Librosa might require ffmpeg)
try:
    import torch
    from transformers import pipeline
except ImportError:
    logging.error("ERROR: 'transformers' or 'torch' libraries not found.")
    logging.error("Install them using: pip install torch transformers")
    exit()

# === 1. Transcription Configuration ===
MODEL_NAME = "openai/whisper-tiny"

# === History Management Functions ===
def load_history():
    """Loads transcription history from JSON file."""
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_JSON):
        return []
    try:
        with open(HISTORY_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading history: {e}")
        return []

def save_history(history):
    """Saves transcription history to JSON file."""
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    try:
        with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving history: {e}")

def add_transcription_to_history(audio_path, transcription_text):
    """Adds a new transcription entry to history."""
    history = load_history()
    entry = {
        "id": int(time.time() * 1000),  # Unique ID based on timestamp
        "timestamp": datetime.now().isoformat(),
        "audio_file": audio_path,
        "transcription": transcription_text
    }
    history.append(entry)
    save_history(history)
    logging.info(f"Added transcription to history: {entry['id']}")
    return entry

def delete_transcription_from_history(entry_id):
    """Deletes a transcription entry and its associated files."""
    history = load_history()
    entry_to_delete = None
    
    for entry in history:
        if entry['id'] == entry_id:
            entry_to_delete = entry
            break
    
    if not entry_to_delete:
        logging.warning(f"Entry {entry_id} not found in history")
        return False
    
    # Delete audio file
    audio_file = entry_to_delete['audio_file']
    if os.path.exists(audio_file):
        try:
            os.remove(audio_file)
            logging.info(f"Deleted audio file: {audio_file}")
        except Exception as e:
            logging.error(f"Error deleting audio file {audio_file}: {e}")
    
    # Remove from history
    history = [e for e in history if e['id'] != entry_id]
    save_history(history)
    logging.info(f"Deleted transcription from history: {entry_id}")
    return True

def output_filename() -> str:
    """Generates output filename for transcription results."""
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    timestamp = int(time.time() * 1000)
    return os.path.join(TRANSCRIPTIONS_DIR, f"recording-{timestamp}.wav")

def transcribe_audio(audio_path: str, model_name: str) -> str:
    """
    Loads the Whisper model and transcribes the audio file.
    This function is blocking and should be run in a separate thread.
    """
    try:
        logging.info(f"Loading model: {model_name}...")
        # Initialize pipeline
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        logging.info(f"Using device: {device}")
        
        asr_pipeline = pipeline(
            "automatic-speech-recognition", 
            model=model_name,
            device=device
        )

        logging.info(f"Starting transcription for file: {audio_path}...")
        result = asr_pipeline(audio_path)
        
        transcription = result["text"].strip()
        
        logging.info("Transcription finished.")
        return transcription

    except FileNotFoundError:
        logging.error(f"ERROR: Audio file not found at path: {audio_path}")
        return f"ERROR: Audio file not found at path: {audio_path}"
    except Exception as e:
        logging.error(f"An unexpected error occurred during transcription: {e}", exc_info=True)
        return f"An unexpected error occurred during transcription: {e}"


# === 2. Recording Configuration ===
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # Changed to standard CD quality (better compatibility)
MAX_RECORD_DURATION = 30 # Maximum recording length in seconds

# === 3. Tkinter GUI Application ===
class AudioRecorderApp:
    def __init__(self, master):
        self.master = master
        
        # 1. Set application title (window title)
        master.title(APP_TITLE)
        
        # 2. Set the application name for the OS/taskbar
        # This is cross-platform attempt to set the application name
        try:
            # For macOS and some X11 environments
            self.master.tk.call('wm', 'iconname', self.master._w, APP_TITLE)
        except tk.TclError:
            # Standard method, usually works on Windows/Linux
            self.master.wm_iconname(APP_TITLE)
            
        master.geometry("600x450") # Slightly larger window
        master.config(bg="#121212") # Set dark background for root

        # --- TKINTER WIDGET STYLES (ttk) ---
        style = ttk.Style()
        style.theme_use('default') 

        # Configure the dark background for the Notebook tabs
        style.configure('TNotebook', background='#121212', borderwidth=0)
        style.configure('TNotebook.Tab', background='#1E1E1E', foreground='white', borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', '#0F0F0F')], foreground=[('selected', 'white')])

        # 1. Define new style for dark gray buttons
        style.configure('Dark.TButton',
                        background='#333333',    
                        foreground='white',     
                        font=('Arial', 14),
                        bordercolor='#333333',
                        borderwidth=0,
                        focuscolor='#333333',
                        padding=(20, 10, 20, 10) 
                       )
        
        # 2. Define button appearance in different states (active/disabled)
        style.map('Dark.TButton',
                  background=[('active', "#991B1B"), # Lighter gray for hover/active state
                              ('disabled', '#333333')], # Disabled state uses the default background
                 )

        logging.info("GUI initialization started.")

        # Initialize PyAudio
        try:
            self.p = pyaudio.PyAudio()
            
            # Log available audio devices for debugging
            logging.info("Available audio input devices:")
            for i in range(self.p.get_device_count()):
                info = self.p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    logging.info(f"  Device {i}: {info['name']} (inputs: {info['maxInputChannels']}, rate: {info['defaultSampleRate']})")
            
        except Exception as e:
            logging.critical(f"Could not initialize PyAudio: {e}. Destroying GUI.")
            messagebox.showerror("PyAudio Error", f"Could not initialize PyAudio: {e}\nDo you have 'portaudio' installed?")
            master.destroy()
            return
            
        self.frames = []
        self.stream = None
        self.recording = False
        self.start_time = None
        self.record_timer_id = None 

        # Queue for inter-thread communication
        self.transcription_queue = queue.Queue()
        
        # --- TAB MENU SETUP (Notebook) ---
        self.notebook = ttk.Notebook(master, style='TNotebook')
        self.notebook.pack(pady=10, padx=10, fill='both', expand=True)

        # 1. Transcriber Tab
        self.transcriber_frame = tk.Frame(self.notebook, bg="#121212") # Set dark background for frame
        self.notebook.add(self.transcriber_frame, text='Transcriber')

        # 2. History Tab
        self.history_frame = tk.Frame(self.notebook, bg="#121212") # Consistent dark background
        self.notebook.add(self.history_frame, text='Transcription History')
        
        # Content for History Tab: Transcriptions List
        tk.Label(self.history_frame, text="Transcription History:", font=('Arial', 14, 'bold'), fg='white', bg="#121212").pack(pady=(10, 5))
        
        # Frame for listbox and scrollbar
        history_list_frame = tk.Frame(self.history_frame, bg="#121212")
        history_list_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        history_scrollbar = tk.Scrollbar(history_list_frame)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for history items
        self.history_listbox = tk.Listbox(history_list_frame, 
                                          yscrollcommand=history_scrollbar.set,
                                          font=('Arial', 10),
                                          bg='#1E1E1E',
                                          fg='white',
                                          selectbackground='#333333',
                                          selectforeground='white',
                                          height=10)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.config(command=self.history_listbox.yview)
        
        # Bind selection event
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)
        
        # Text display for selected transcription
        tk.Label(self.history_frame, text="Selected Transcription:", font=('Arial', 12, 'bold'), fg='white', bg="#121212").pack(pady=(10, 5))
        
        self.history_detail_display = tk.Text(self.history_frame, 
                                              height=8, 
                                              wrap=tk.WORD, 
                                              font=('Arial', 10),
                                              relief=tk.SUNKEN, 
                                              bg='#1E1E1E', 
                                              fg='white', 
                                              insertbackground='white', 
                                              state=tk.DISABLED)
        self.history_detail_display.pack(pady=5, padx=20, fill=tk.BOTH, expand=False)
        
        # Delete button
        self.delete_button = ttk.Button(self.history_frame, 
                                        text="Delete Selected", 
                                        command=self.delete_selected_transcription,
                                        style='Dark.TButton')
        self.delete_button.pack(pady=10)
        
        # Refresh button
        self.refresh_button = ttk.Button(self.history_frame, 
                                         text="Refresh History", 
                                         command=self.refresh_history_list,
                                         style='Dark.TButton')
        self.refresh_button.pack(pady=5)
        
        # Load initial history
        self.refresh_history_list()


        # 3. Settings Tab
        self.settings_frame = tk.Frame(self.notebook, bg="#121212") 
        self.notebook.add(self.settings_frame, text='Settings')

        # Content for Settings Tab
        tk.Label(self.settings_frame, text="Under construction...", font=('Arial', 18), fg='gray', bg="#121212").pack(pady=50)


        # --- Transcriber Tab Elements ---
        
        # Record Button
        self.record_button = ttk.Button(self.transcriber_frame, 
                                        text="Record", 
                                        command=self.toggle_recording, 
                                        style='Dark.TButton')
        self.record_button.pack(pady=20, fill=tk.X, padx=20) 

        # Transcribed Text Display (Read-only Text widget)
        self.transcription_display = tk.Text(self.transcriber_frame, 
                                             height=10, 
                                             wrap=tk.WORD, 
                                             font=('Arial', 11),
                                             relief=tk.SUNKEN, 
                                             bg='#1E1E1E', 
                                             fg='white', 
                                             insertbackground='white', 
                                             state=tk.DISABLED 
                                             )
        self.transcription_display.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Initial text insertion for tk.Text
        self.transcription_display.config(state=tk.NORMAL)
        self.transcription_display.insert(tk.END, "Transcribed text will appear here. Select it to copy.")
        self.transcription_display.config(state=tk.DISABLED)


        # Exit Button
        self.exit_button = ttk.Button(master, 
                                      text="Exit", 
                                      command=self.on_closing,
                                      style='Dark.TButton')
        self.exit_button.pack(pady=10)

        # Handle window closing
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the loop checking the queue
        self.master.after(100, self.check_transcription_queue)
        logging.info("GUI initialized successfully.")
    
    def copy_to_clipboard(self, text: str):
        """Copies the given text to the system clipboard."""
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        logging.info("Transcription copied to clipboard.")

    def toggle_recording(self):
        """Toggles the recording state (start/stop)."""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Starts the audio recording process."""
        self.recording = True
        self.frames = []
        self.start_time = time.time()
        logging.info("Recording started.")
        
        try:
            self.stream = self.p.open(format=FORMAT,
                                     channels=CHANNELS,
                                     rate=RATE,
                                     input=True,
                                     frames_per_buffer=CHUNK)

            # Update button text to show status
            self.record_button.config(text="Stop Recording") 
            
            # Update text display
            self.transcription_display.config(state=tk.NORMAL)
            self.transcription_display.delete('1.0', tk.END)
            self.transcription_display.insert(tk.END, "Recording in progress... (max 30s)")
            self.transcription_display.config(state=tk.DISABLED)
            
            self.read_chunk()
            # Set a timer for automatic stop
            self.record_timer_id = self.master.after(MAX_RECORD_DURATION * 1000, self.auto_stop_recording)

        except Exception as e:
            self.recording = False
            self.record_button.config(text="Record", state=tk.NORMAL) 
            logging.error(f"Microphone stream error on start: {e}")
            messagebox.showerror("Audio Error", f"Could not open microphone stream: {e}\nCheck your microphone connection and permissions.")
            if self.record_timer_id:
                self.master.after_cancel(self.record_timer_id)
                self.record_timer_id = None
            
    def read_chunk(self):
        """Reads one audio chunk and schedules the next call."""
        if self.recording:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                self.master.after(1, self.read_chunk) 
            except IOError as e:
                logging.error(f"Stream read IOError: {e}")
                self.stop_recording()

    def auto_stop_recording(self):
        """Automatically stops recording after MAX_RECORD_DURATION expires."""
        if self.recording:
            logging.info(f"Automatic stop triggered after {MAX_RECORD_DURATION} seconds.")
            self.stop_recording()
            messagebox.showinfo("Recording Finished", f"The recording was stopped automatically after {MAX_RECORD_DURATION} seconds. Starting transcription...")

    def stop_recording(self):
        """Stops the stream, saves the file, and starts the transcription thread."""
        if not self.recording:
            return

        self.recording = False
        
        if self.record_timer_id:
            self.master.after_cancel(self.record_timer_id)
            self.record_timer_id = None

        # Stop and close the stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        logging.info("Audio stream closed.")

        WAVE_OUTPUT_FILENAME = output_filename()
        self.last_audio_path = WAVE_OUTPUT_FILENAME  # Store for history
        
        # Update button status for user feedback
        self.record_button.config(text="Saving...", state=tk.DISABLED) 
        self.master.update_idletasks()

        # Save to WAVE file
        try:
            with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
            
            # Log file size for debugging
            file_size = os.path.getsize(WAVE_OUTPUT_FILENAME)
            logging.info(f"File saved successfully to {WAVE_OUTPUT_FILENAME} (size: {file_size} bytes, frames: {len(self.frames)})")
            
            # Check if file has actual audio data
            if file_size < 1000:  # Less than 1KB suggests no audio
                logging.warning(f"Audio file is very small ({file_size} bytes), may be empty or too quiet")
                messagebox.showwarning("Warning", "Audio file is very small. Make sure your microphone is working and you spoke during recording.")
            
            self.record_button.config(text="Transcribing...")
            
            # Update text in read-only Text widget
            self.transcription_display.config(state=tk.NORMAL)
            self.transcription_display.delete('1.0', tk.END)
            self.transcription_display.insert(tk.END, "Transcription in progress (this may take a while)...")
            self.transcription_display.config(state=tk.DISABLED)
            
            # === START TRANSCRIPTION IN A THREAD ===
            transcription_thread = threading.Thread(
                target=self.run_transcription,
                args=(WAVE_OUTPUT_FILENAME,),
                daemon=True
            )
            transcription_thread.start()
            logging.info("Transcription thread started.")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save WAVE file: {e}")
            self.record_button.config(text="Record", state=tk.NORMAL) 
            logging.error(f"Error saving wave file: {e}", exc_info=True)

    def run_transcription(self, audio_path):
        """
        Method executed in a separate thread. 
        Calls transcription and puts the result in the queue.
        """
        logging.info(f"Running transcription for {audio_path} in thread: {threading.get_ident()}")
        transcription = transcribe_audio(audio_path, MODEL_NAME)
        self.transcription_queue.put(transcription)

    def check_transcription_queue(self):
        """
        Checks the queue for transcription results.
        Run in the main GUI thread.
        """
        try:
            result = self.transcription_queue.get(block=False)
            
            # 1. Update Transcriber tab (main output)
            self.transcription_display.config(state=tk.NORMAL)
            self.transcription_display.delete('1.0', tk.END)
            self.transcription_display.insert(tk.END, result)
            self.transcription_display.config(state=tk.DISABLED)
            
            # 2. Add to history
            if hasattr(self, 'last_audio_path') and self.last_audio_path:
                add_transcription_to_history(self.last_audio_path, result)
                self.refresh_history_list()
            
            if "ERROR" in result:
                logging.warning("Transcription failed with error message.")
                messagebox.showerror("Transcription Failed", "Transcription returned an error. Check logs for details.")
            else:
                # Copy to clipboard upon successful transcription
                self.copy_to_clipboard(result) 
                
            self.record_button.config(text="Record", state=tk.NORMAL) # Return to normal state

        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.check_transcription_queue)
    
    def refresh_history_list(self):
        """Refreshes the history listbox with current history entries."""
        self.history_listbox.delete(0, tk.END)
        history = load_history()
        
        # Store history for reference
        self.history_entries = history
        
        if not history:
            self.history_listbox.insert(tk.END, "No transcriptions yet")
            return
        
        # Display in reverse order (newest first)
        for entry in reversed(history):
            timestamp = entry.get('timestamp', 'Unknown')
            # Parse and format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = timestamp
            
            # Preview of transcription (first 50 chars)
            preview = entry.get('transcription', '')[:50]
            if len(entry.get('transcription', '')) > 50:
                preview += '...'
            
            display_text = f"{formatted_time} - {preview}"
            self.history_listbox.insert(tk.END, display_text)
    
    def on_history_select(self, event):
        """Handles selection in the history listbox."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        # Check if "No transcriptions yet" is displayed
        if not hasattr(self, 'history_entries') or not self.history_entries:
            return
        
        # Convert to actual index (reversed list)
        actual_index = len(self.history_entries) - 1 - index
        entry = self.history_entries[actual_index]
        
        # Display full transcription
        self.history_detail_display.config(state=tk.NORMAL)
        self.history_detail_display.delete('1.0', tk.END)
        self.history_detail_display.insert(tk.END, entry.get('transcription', ''))
        self.history_detail_display.config(state=tk.DISABLED)
    
    def delete_selected_transcription(self):
        """Deletes the currently selected transcription."""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transcription to delete.")
            return
        
        index = selection[0]
        
        # Check if valid entry
        if not hasattr(self, 'history_entries') or not self.history_entries:
            return
        
        # Convert to actual index (reversed list)
        actual_index = len(self.history_entries) - 1 - index
        entry = self.history_entries[actual_index]
        
        # Confirm deletion
        timestamp = entry.get('timestamp', 'Unknown')
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = timestamp
        
        confirm = messagebox.askyesno("Confirm Deletion", 
                                      f"Delete transcription from {formatted_time}?\n\nThis will also delete the associated audio file.")
        
        if confirm:
            success = delete_transcription_from_history(entry['id'])
            if success:
                messagebox.showinfo("Deleted", "Transcription deleted successfully.")
                self.refresh_history_list()
                # Clear detail display
                self.history_detail_display.config(state=tk.NORMAL)
                self.history_detail_display.delete('1.0', tk.END)
                self.history_detail_display.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Error", "Failed to delete transcription.")

    def on_closing(self):
        """Handles clean application shutdown."""
        logging.info("Closing application...")
        if self.recording:
            self.stop_recording() 
        
        # Terminate PyAudio
        if self.p:
            self.p.terminate()
        
        self.master.destroy()
        logging.info("Application destroyed.")

# --- Application Startup ---
if __name__ == "__main__":
    logging.info("Whisper model loading might take a moment on first launch...")
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()
