"""
Language Analysis Agent for Phishing Detection
- Prints results to console
- Saves strict JSON output to a file
- Accepts a text file or raw string as input via CLI
"""

import json
import re
import os
import argparse
from typing import Dict, List
from datetime import datetime
from .helpers import _read_input_text, _print_human_readable, _write_json_output

import openai


class LanguageAnalysisAgent:
    """
    Standalone Language Analysis Agent for phishing detection.

    Returns:
      {
        "confidence_score": float (1.0 = NOT phishing, 0.0 = phishing),
        "summary": str,
        "token_usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
        "highlight": [{"s_idx": int, "e_idx": int, "reasoning": str}, ...]
      }
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.analysis_prompt = self._create_analysis_prompt()

    def _create_analysis_prompt(self) -> str:
        return (
            "You are an expert language analysis agent specialized in detecting phishing emails through linguistic "
            "patterns.\n\nFocus on:\n"
            "1) Urgency/time pressure\n2) Authority impersonation\n3) Threat language\n4) Emotional manipulation\n"
            "5) Social engineering requests\n6) Grammar/spelling anomalies\n7) Generic greetings\n8) Reward promises\n\n"
            "Output JSON ONLY in the user's requested schema and include exact character indices for suspicious phrases."
        )

    def analyze_email(self, email_content: str) -> Dict:
        """
        Analyze an email for phishing indicators using language analysis.
        Returns the strict JSON schema used by the rest of the system.
        """
        try:
            analysis_request = f"""Analyze the following email content for phishing indicators:

EMAIL CONTENT:
{email_content}

Provide your analysis in the following JSON format:
{{
    "confidence_score": 0.5,
    "summary": "Brief summary of findings",
    "suspicious_phrases": [
        {{
            "text": "exact phrase from email",
            "start_index": 0,
            "end_index": 10,
            "reasoning": "why this phrase is suspicious"
        }}
    ],
    "overall_assessment": "detailed assessment of the email"
}}

IMPORTANT:
- confidence_score: 0.0 (definitely phishing) to 1.0 (definitely legitimate)
- start_index and end_index are exact character positions (inclusive start, exclusive end)
- Include ALL suspicious phrases with indices that match the original text exactly
- Output ONLY JSON
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.analysis_prompt},
                    {"role": "user", "content": analysis_request},
                ],
                max_tokens=1000,
                temperature=0.1,
            )

            # Extract token usage (safe fallback if fields missing)
            usage = getattr(response, "usage", None)
            token_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            }

            analysis_text = response.choices[0].message.content.strip()

            # Try to parse JSON block
            parsed = self._safe_extract_json(analysis_text)
            if parsed is None:
                parsed = self._fallback_parse(analysis_text, email_content)

            # Convert to strict output schema
            result = self._format_output(parsed, token_usage, email_content)
            return result

        except Exception as e:
            # Always return valid schema, even on error
            return {
                "confidence_score": 0.5,
                "summary": f"Error in language analysis: {str(e)}",
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "highlight": [],
            }

    # ---------- Helpers ----------

    def _safe_extract_json(self, text: str) -> Dict | None:
        s = text.find("{")
        e = text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except json.JSONDecodeError:
                return None
        return None

    def _fallback_parse(self, analysis_text: str, email_content: str) -> Dict:
        """Very loose parsing when model didn't return clean JSON."""
        confidence_match = re.search(
            r'confidence[_\s]*score["\s]*:?\s*([0-9.]+)',
            analysis_text,
            re.IGNORECASE,
        )
        confidence_score = float(confidence_match.group(1)) if confidence_match else 0.5

        summary_match = re.search(
            r'summary["\s]*:?\s*["\']([^"\']+)["\']',
            analysis_text,
            re.IGNORECASE,
        )
        summary = summary_match.group(1) if summary_match else "Analysis completed (fallback parser)."

        return {
            "confidence_score": confidence_score,
            "summary": summary,
            "suspicious_phrases": [],
            "overall_assessment": (analysis_text[:200] + "...") if len(analysis_text) > 200 else analysis_text,
        }

    def _format_output(self, parsed: Dict, token_usage: Dict, email_content: str) -> Dict:
        confidence_score = float(parsed.get("confidence_score", 0.5))
        summary = parsed.get("summary") or parsed.get("overall_assessment") or "Language analysis completed."

        highlights: List[Dict] = []
        suspicious_phrases = parsed.get("suspicious_phrases", []) or []

        for phrase in suspicious_phrases:
            if not isinstance(phrase, dict):
                continue

            start_idx = int(phrase.get("start_index", 0) or 0)
            end_idx = int(phrase.get("end_index", 0) or 0)

            # Clamp and fix if needed
            start_idx = max(0, min(start_idx, len(email_content)))
            end_idx = max(0, min(end_idx, len(email_content)))

            if start_idx >= end_idx:
                # Try to locate by text
                txt = phrase.get("text", "")
                if txt:
                    found = email_content.find(txt)
                    if found != -1:
                        start_idx = found
                        end_idx = found + len(txt)
                    else:
                        continue  # skip if we can't resolve
                else:
                    continue

            highlights.append(
                {
                    "s_idx": start_idx,
                    "e_idx": end_idx,
                    "reasoning": phrase.get("reasoning", "Suspicious language pattern detected"),
                }
            )

        return {
            "confidence_score": float(confidence_score),
            "summary": str(summary),
            "token_usage": token_usage,
            "highlight": highlights,
        }


def main():
    parser = argparse.ArgumentParser(description="Language Analysis Agent (Phishing Detection)")
    parser.add_argument("--input_file", type=str, default=None, help="Path to a .txt file containing the email content.")
    parser.add_argument("--input_string", type=str, default=None, help="Raw email content as a string.")
    parser.add_argument("--output_json", type=str, default=None, help="Path to write the JSON output (default: ./outputs/language_agent_YYYYMMDD_HHMMSS.json).")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model name.")
    parser.add_argument("--api_key", type=str, default=None, help="OpenAI API key (or set OPENAI_API_KEY env var).")
    parser.add_argument("--quiet", action="store_true", help="If set, do not print human-readable output; only write JSON.")
    args = parser.parse_args()

    # Prepare input
    email_text = _read_input_text(args.input_file, args.input_string)

    # Run agent
    agent = LanguageAnalysisAgent(api_key=args.api_key, model=args.model)
    result = agent.analyze_email(email_text)

    # Always save JSON
    out_path = _write_json_output(result, args.output_json)

    # Optionally print readable summary
    if not args.quiet:
        _print_human_readable(result, email_text)
        print(f"💾 JSON saved to: {out_path}")

    # Also print the strict JSON to stdout if quiet (useful for piping)
    if args.quiet:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
