from tokenizers import Tokenizer
import json
import os
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENIZER_DIR = os.path.join(SCRIPT_DIR, 'tokenizers')
SAMPLES_DIR = os.path.join(SCRIPT_DIR, 'samples')

# Load all tokenizers
ALL_TOKENIZERS = {}
if not os.path.isdir(TOKENIZER_DIR):
    print(f"❌ Error: Tokenizer directory not found at {TOKENIZER_DIR}")
    exit(1)

for filename in os.listdir(TOKENIZER_DIR):
    if filename.endswith('.json'):
        key = filename[:-5]  # remove .json
        full_path = os.path.join(TOKENIZER_DIR, filename)
        try:
            ALL_TOKENIZERS[key] = Tokenizer.from_file(full_path)
            print(f"✅ Loaded tokenizer: {key}")
        except Exception as e:
            print(f"❌ Error loading tokenizer '{key}': {e}")

if not ALL_TOKENIZERS:
    print("❌ No tokenizers loaded!")
    exit(1)

# Discover all samples
SAMPLES = set()
for filename in os.listdir(SAMPLES_DIR):
    if filename.endswith('.json') and not filename.endswith('-nows.json'):
        SAMPLES.add(filename[:-5])  # remove .json

SAMPLES = sorted(SAMPLES)
print(f"\n📁 Found {len(SAMPLES)} samples: {', '.join(SAMPLES)}")

# Use first tokenizer for demonstration
TOKENIZER_NAME = list(ALL_TOKENIZERS.keys())[0]
tokenizer = ALL_TOKENIZERS[TOKENIZER_NAME]
print(f"\n🔧 Using tokenizer: {TOKENIZER_NAME}\n")

# Process all samples
results = {}

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
    
    # Tokenize all formats
    counts = {}
    for format_name, content in sample_data.items():
        if content:
            try:
                encoded = tokenizer.encode(content)
                counts[format_name] = len(encoded.ids)
            except Exception as e:
                print(f"⚠️ Error tokenizing {sample_name}.{format_name}: {e}")
                counts[format_name] = 0
    
    if counts:
        results[sample_name] = counts

# Visualize results
def create_bar(percentage, width=20, filled_char='█', empty_char='░'):
    """Creates a progress bar string."""
    filled_width = int((percentage / 100) * width)
    empty_width = width - filled_width
    return filled_char * filled_width + empty_char * empty_width

def format_percentage(value):
    """Formats percentage to one decimal place."""
    return f"{value:5.1f}%"

print("\n" + "="*60)
print("TOKEN COUNT COMPARISON")
print("="*60 + "\n")

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

print("="*60)
print(f"Tokenizer: {TOKENIZER_NAME}")
print("="*60)
