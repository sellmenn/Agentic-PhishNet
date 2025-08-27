import os
from datetime import datetime
import json
from typing import Dict

# ---------- CLI Utilities ----------

def _read_input_text(input_file: str | None, input_string: str | None) -> str:
    if input_file:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            return f.read()
    if input_string is not None:
        return input_string
    raise ValueError("No input provided. Use --input_file or --input_string.")


def _write_json_output(output_obj: Dict, output_path: str | None) -> str:
    """
    Writes JSON to file. If output_path is None, generates timestamped file in ./outputs/.
    Returns the path used.
    """
    os.makedirs("outputs", exist_ok=True)
    if output_path is None or output_path.strip() == "":
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join("outputs", f"language_agent_{ts}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_obj, f, ensure_ascii=False, indent=2)
    return output_path


def _print_human_readable(result: Dict, email_content: str):
    print("=" * 80)
    print("🔍 LANGUAGE ANALYSIS AGENT — RESULT")
    print("=" * 80)
    print(f"🎯 Confidence Score: {result['confidence_score']:.2f}  (1.0 = NOT phishing, 0.0 = phishing)")
    print(f"📝 Summary: {result.get('summary','')}")
    print(f"🔢 Token Usage: {result['token_usage'].get('total_tokens', 0)} total")
    print(f"⚠️  Highlights: {len(result.get('highlight', []))}")
    if result.get("highlight"):
        print("\nHighlighted Suspicious Phrases:")
        for i, h in enumerate(result["highlight"], 1):
            s, e = h["s_idx"], h["e_idx"]
            snippet = email_content[s:e]
            print(f"  {i}. [{s}:{e}] \"{snippet}\" — {h.get('reasoning','')}")
    print()