import yaml
import re
import csv
from pathlib import Path

# defLoadsYAML
def load_config(yaml_path: str):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# BIBLIOGRAPHY DETECTION
BIBLIO_HEADERS = [
    "references",
    "bibliography",
    "works cited",
    "literature"
]

# defFindsBibliographySection+numerate
def extract_bibliography_block(text: str):  
    lines = text.split("\n")
    start_idx = None

    for i, line in enumerate(lines):
        header = re.sub(r"[^a-z]", "",line.lower())
        if header in BIBLIO_HEADERS:
            start_idx = i + 1
            break

    if start_idx is None:
        return None

    return "\n".join(lines[start_idx:])

# SEGMENTATION PATTERNS

REFERENCE_START_PATTERNS = [
    r"^[A-Z][a-zA-Z\-]+,\s+[A-Z]",      # Abraham, K.
    r"^[A-Z][a-zA-Z\-]+\s+[A-Z]\.",     # Abraham K.
    r"^[A-Z][a-zA-Z\-]+\s+(?:[A-Z]\.(?:\s+[A-Z]\.)* | eds\.)", 
    r"^\d+\.\s+[A-Z]"                   # 1. Abraham
]

#Boolian-PageBegining
def is_new_reference_start(line: str): #bool
    for pattern in REFERENCE_START_PATTERNS:
        if re.match(pattern, line):
            return True
    return False

# defSegmentationOfline
def segment_bibliography_entries(bib_text: str): #list
    lines = bib_text.split("\n")
    entries = []
    current_entry = ""

    for line in lines:
        stripped = line.strip().lstrip("#").strip()

        if not stripped:
            continue

        if is_new_reference_start(stripped):
            if current_entry:
                entries.append(current_entry.strip())
            current_entry = stripped
        else:
            current_entry += " " + stripped

    if current_entry:
        entries.append(current_entry.strip())

    return entries

# defNormalizationEnties
def normalize_entry(entry: str, config: dict): #str
    if config["text_normalization"]["normalize_whitespace"]:
        entry = re.sub(r"\s+", " ", entry)
    return entry.strip()


# defPipelineExtractBibliography
def run_pipeline():
    config = load_config("/Users/aima/Desktop/Practice/projectEdubba/edubbaConfig/project_config.yaml")

    raw_path = Path(config ["paths"]["raw_texts"])
    output_path = Path(config ["paths"]["extract_bibliography"])

    if output_path.is_dir():
        raise ValueError(f"Output path {output_path} is a directory. Please provide a file path, e.g., sources.csv")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sources =[]

    for txt_file in raw_path.glob("*.txt"):
        raw_text = txt_file.read_text(encoding="utf-8")
        
        bib_block = extract_bibliography_block(raw_text)
        if not bib_block:
            print(f" No bibliography found in {txt_file.name}")
            continue
        raw_entries = segment_bibliography_entries(bib_block)
        for entry in raw_entries:
            normalized = normalize_entry(entry, config)
            sources.append({
                "source_file": txt_file.name,
                "raw_reference": normalized
            })
    if not sources:
        print("No bibliography entries extracted.")
        return

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_file", "raw_reference"])
        writer.writeheader()  # ← здесь файл реально создаётся
        if sources:
            writer.writerows(sources)
    print(f" Extracted {len(sources)} bibliography entries → {output_path}")