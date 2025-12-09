"""
Tokenization comparison using OpenAI's tiktoken library.
This script compares JSON, JSON compact, YAML, and TOON formats
using various tiktoken encodings (GPT-3.5, GPT-4, etc.)
"""

import tiktoken
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(SCRIPT_DIR, 'samples')

# Available tiktoken encodings
ENCODINGS = {
    'gpt-3.5-turbo': 'cl100k_base',
    'gpt-4': 'cl100k_base',
    'gpt-4o': 'o200k_base',
    'text-davinci-003': 'p50k_base',
    'text-embedding-ada-002': 'cl100k_base',
}

def create_bar(percentage, width=20, filled_char='█', empty_char='░'):
    """Creates a progress bar string."""
    filled_width = int((percentage / 100) * width)
    empty_width = width - filled_width
    return filled_char * filled_width + empty_char * empty_width

def format_percentage(value):
    """Formats percentage to one decimal place."""
    return f"{value:5.1f}%"

# Discover all samples
SAMPLES = set()
for filename in os.listdir(SAMPLES_DIR):
    if filename.endswith('.json') and not filename.endswith('-nows.json'):
        SAMPLES.add(filename[:-5])  # remove .json

SAMPLES = sorted(SAMPLES)
print(f"📁 Found {len(SAMPLES)} samples: {', '.join(SAMPLES)}\n")

# Process each encoding
for model_name, encoding_name in ENCODINGS.items():
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        print(f"✅ Loaded encoding: {encoding_name} (used by {model_name})")
    except Exception as e:
        print(f"❌ Error loading encoding '{encoding_name}': {e}")
        continue
    
    results = {}
    
    # Process all samples
    for sample_name in SAMPLES:
        sample_data = {}
        
        # Load JSON
        file_path = os.path.join(SAMPLES_DIR, f"{sample_name}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample_data['JSON'] = f.read()
        except FileNotFoundError:
            sample_data['JSON'] = ""
        
        # Load JSON compact (nows)
        file_path = os.path.join(SAMPLES_DIR, f"{sample_name}-nows.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample_data['JSON compact'] = f.read()
        except FileNotFoundError:
            sample_data['JSON compact'] = ""
        
        # Load TOON
        file_path = os.path.join(SAMPLES_DIR, f"{sample_name}.toon")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample_data['TOON'] = f.read()
        except FileNotFoundError:
            sample_data['TOON'] = ""
        
        # Load YAML
        file_path = os.path.join(SAMPLES_DIR, f"{sample_name}.yaml")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample_data['YAML'] = f.read()
        except FileNotFoundError:
            sample_data['YAML'] = ""
        
        # Tokenize all formats using tiktoken
        counts = {}
        for format_name, content in sample_data.items():
            if content:
                try:
                    tokens = encoding.encode(content)
                    counts[format_name] = len(tokens)
                except Exception as e:
                    print(f"⚠️ Error tokenizing {sample_name}.{format_name}: {e}")
                    counts[format_name] = 0
        
        if counts:
            results[sample_name] = counts
    
    # Visualize results for this encoding
    print("\n" + "="*70)
    print(f"ENCODING: {encoding_name} ({model_name})")
    print("="*70 + "\n")
    
    for sample_name in SAMPLES:
        if sample_name not in results:
            continue
        
        counts = results[sample_name]
        
        # Find minimum (best) count
        min_count = min(counts.values())
        
        # Sort by token count (ascending - best first)
        sorted_formats = sorted(counts.items(), key=lambda x: x[1])
        
        print(sample_name)
        
        for idx, (format_name, count) in enumerate(sorted_formats):
            # Calculate percentage relative to minimum
            percentage = (min_count / count) * 100 if count > 0 else 0
            
            # Create bar
            bar = create_bar(percentage, width=20)
            
            # Mark the best (minimum) with arrow
            prefix = "→ " if count == min_count else "  "
            
            # Format output
            print(f"{prefix}{format_name:15} {bar}    {format_percentage(percentage)} ({count})")
        
        print()  # Empty line between samples

print("\n" + "="*70)
print("END OF REPORT")
print("="*70)
print("\n💡 Note: tiktoken encodings are optimized for English text.")
print("   For Polish text, specialized tokenizers (like bielik) may be more efficient.")
