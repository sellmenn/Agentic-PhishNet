"""
Fact Verification Agent (Inference) — Closed-Book, Training-Aligned
Input parity with previous agent; outputs a similar JSON file.

CLI:
  --input_file <path>      Read email text from file
  --input_string "<text>"  Or pass email text directly
  --output_file <path>     Where to write the JSON (default: fact_verification_output.json)
  --model <model_name>     OpenAI model (default: gpt-4o-mini)
  --api_key <key>          Optional; otherwise uses OPENAI_API_KEY env var

Output JSON (similar to previous agent):
{
  "confidence_score": float,              # 0..1 (1 = all facts look legit)
  "summary": "Brief summary",
  "token_usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
  "highlight": [                          # suspicious spans
    {"s_idx": int, "e_idx": int, "reasoning": "why suspicious"},
    ...
  ]
}

Internally:
- Extracts claims (one call), then verifies each claim (one call per claim), closed-book.
- Aggregates per-claim results into confidence_score and highlights suspicious spans.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import openai

# ----------------------------- Config -----------------------------

@dataclass
class AgentConfig:
    base_model: str = "gpt-4o-mini"
    temperature_extract: float = 0.25
    temperature_verify: float = 0.15
    max_tokens_extract: int = 900
    max_tokens_verify: int = 400
    max_claims_per_email: int = 12  # safety cap

# Strict JSON schema used during verification (mirrors training)
RESPONSE_SCHEMA = """
Return ONLY valid JSON with EXACT keys:
{
  "is_legitimate": true or false,
  "confidence": <number between 0.0 and 1.0>,
  "reasoning": "<one concise sentence>",
  "verification_source": "model_closed_book"
}
No markdown, no code fences, no extra keys, no extra text.
""".strip()

EXTRACTION_PROMPT = (
    "Extract verifiable factual claims from this email, focusing on:\n"
    "- Company/organization names\n"
    "- Contact info (phones, emails, URLs)\n"
    "- Addresses and locations\n"
    "- Reference/account numbers or IDs\n"
    "- Dates, deadlines, timeframes\n"
    "- Financial amounts and offers\n"
    "- Procedural/policy claims\n\n"
    'Return JSON ONLY in the format: {"claims":[{"claim_text":"...","claim_type":"domain/contact/financial/'
    'procedural/other","start_index":0,"end_index":10,"verifiable":true/false,"verification_method":"..."}]}'
)

# ----------------------------- Agent ------------------------------

class FactVerificationAgent:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.config = AgentConfig(base_model=model)
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    # --------------- Internal helpers & parsing ---------------------

    def _safe_float(self, x, default=0.5) -> float:
        try:
            return float(x)
        except Exception:
            return float(default)

    def _parse_json_block(self, text: str, default=None):
        j0, j1 = text.find("{"), text.rfind("}") + 1
        if j0 != -1 and j1 > j0:
            try:
                return json.loads(text[j0:j1])
            except Exception:
                return default
        return default

    def _json_repair(self, broken_text: str) -> Optional[dict]:
        """Coerce malformed model output into valid JSON per schema (one-shot)."""
        try:
            resp = self.client.chat.completions.create(
                model=self.config.base_model,
                messages=[
                    {"role": "system", "content": "Fix outputs into EXACT JSON per the provided schema."},
                    {"role": "user", "content": f"Schema:\n{RESPONSE_SCHEMA}\n\nBroken JSON/text:\n{broken_text}"}
                ],
                temperature=0.0,
                max_tokens=200
            )
            out = resp.choices[0].message.content.strip()
            j0, j1 = out.find("{"), out.rfind("}") + 1
            if j0 != -1 and j1 > j0:
                return json.loads(out[j0:j1])
        except Exception:
            pass
        return None

    # ---------------------- Extraction phase -----------------------

    def _extract_claims(self, email_content: str) -> Tuple[List[Dict], Dict]:
        """Return (claims, usage)."""
        if not email_content.strip():
            return [], {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        try:
            resp = self.client.chat.completions.create(
                model=self.config.base_model,
                messages=[
                    {"role": "system", "content": "Extract verifiable claims with precise indices. Return JSON only."},
                    {"role": "user", "content": f"{EXTRACTION_PROMPT}\n\nEMAIL CONTENT:\n{email_content}"}
                ],
                temperature=self.config.temperature_extract,
                max_tokens=self.config.max_tokens_extract,
            )
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                "total_tokens": getattr(resp.usage, "total_tokens", 0),
            }
            txt = resp.choices[0].message.content.strip()
            obj = self._parse_json_block(txt, default={"claims": []}) or {"claims": []}
            claims = obj.get("claims", [])
        except Exception:
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            claims = []

        # Cap to avoid excessive per-claim calls
        if isinstance(claims, list):
            claims = claims[: self.config.max_claims_per_email]
        else:
            claims = []

        # Normalize/guard indices
        normed = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            s = max(0, int(c.get("start_index", 0) or 0))
            e = max(s, int(c.get("end_index", 0) or 0))
            normed.append({
                "claim_text": str(c.get("claim_text", "")),
                "claim_type": str(c.get("claim_type", "other")),
                "start_index": s,
                "end_index": e,
                "verifiable": bool(c.get("verifiable", True)),
                "verification_method": str(c.get("verification_method", ""))[:200]
            })
        return normed, usage

    # ---------------------- Verification phase ---------------------

    def _verification_prompt(self) -> str:
        return (
            "Verify the factual legitimacy of the claim conservatively (closed-book):\n"
            "- Does the structure match real-world practices (e.g., domains, contact formats, processes)?\n"
            "- Is there obvious typosquatting or unrealistic offers?\n"
            "- Is it internally coherent with typical policies and timelines?\n"
            "If uncertain, lean suspicious."
        )

    def _verify_one_claim(self, claim_text: str) -> Tuple[Dict, Dict]:
        """Closed-book verify a single claim. Returns (verification, usage)."""
        prompt = f"""{self._verification_prompt()}

CLAIM:
{claim_text}

{RESPONSE_SCHEMA}
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.config.base_model,
                messages=[
                    {"role": "system", "content": "You are a cautious fact checker. Return strict JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature_verify,
                max_tokens=min(self.config.max_tokens_verify, self.config.max_tokens_extract),
            )
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                "total_tokens": getattr(resp.usage, "total_tokens", 0),
            }
            out = resp.choices[0].message.content.strip()
            obj = self._parse_json_block(out)
            if obj is None:
                obj = self._json_repair(out)
            if obj is None:
                obj = {
                    "is_legitimate": False,
                    "confidence": 0.5,
                    "reasoning": "Fallback due to JSON parse failure",
                    "verification_source": "model_closed_book"
                }
        except Exception as e:
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            obj = {
                "is_legitimate": False,
                "confidence": 0.5,
                "reasoning": f"Error: {e}",
                "verification_source": "model_closed_book"
            }

        # Normalize → integer 0/1
        is_legit = 1 if bool(obj.get("is_legitimate", False)) else 0
        conf = max(0.0, min(1.0, self._safe_float(obj.get("confidence", 0.5), 0.5)))
        reasoning = str(obj.get("reasoning", ""))[:500]
        return {
            "is_legitimate": is_legit,
            "confidence": conf,
            "reasoning": reasoning,
            "verification_source": "model_closed_book"
        }, usage

    # --------------------------- Public API -------------------------

    def analyze_email(self, email_content: str) -> Dict:
        """
        End-to-end: extract claims, verify each claim, then return the simplified
        JSON your previous agent emitted (confidence_score, summary, token_usage, highlight).
        """
        # 1) Extract claims
        claims, usage_total = self._extract_claims(email_content)

        # 2) Verify per-claim
        verifs: List[Dict] = []
        for i, c in enumerate(claims):
            ct = c.get("claim_text", "").strip()
            if not ct:
                verifs.append({
                    "claim_index": i,
                    "is_legitimate": 0,
                    "confidence": 0.5,
                    "reasoning": "Empty claim",
                    "verification_source": "model_closed_book"
                })
                continue
            v, u = self._verify_one_claim(ct)
            v["claim_index"] = i
            verifs.append(v)
            # accumulate usage
            usage_total["prompt_tokens"] += u["prompt_tokens"]
            usage_total["completion_tokens"] += u["completion_tokens"]
            usage_total["total_tokens"] += u["total_tokens"]

        # 3) Aggregate to overall confidence_score
        if verifs:
            weighted_sum = 0.0
            weight = 0.0
            for v in verifs:
                score = 1.0 if v["is_legitimate"] == 1 else 0.0
                conf = self._safe_float(v.get("confidence", 0.5), 0.5)
                weighted_sum += score * conf
                weight += conf
            overall_conf = (weighted_sum / weight) if weight > 0 else 0.5
        else:
            overall_conf = 0.5  # neutral when no claims identified

        # 4) Highlights for suspicious spans (is_legitimate == 0)
        highlights: List[Dict] = []
        for i, (c, v) in enumerate(zip(claims, verifs)):
            if v["is_legitimate"] == 0:
                s = max(0, int(c.get("start_index", 0)))
                e = max(s, int(c.get("end_index", 0)))
                reasoning = v.get("reasoning", "Suspicious claim")
                # If indices are empty, try to locate by text
                if e <= s:
                    ct = c.get("claim_text", "")
                    if ct:
                        pos = email_content.find(ct)
                        if pos != -1:
                            s = pos
                            e = pos + len(ct)
                if e > s:
                    highlights.append({"s_idx": s, "e_idx": e, "reasoning": reasoning})

        # 5) Summary
        suspicious_count = sum(1 for v in verifs if v["is_legitimate"] == 0)
        summary = (
            f"Verified {len(verifs)} factual claim(s); "
            f"{suspicious_count} appear suspicious. "
            f"Overall confidence: {overall_conf:.2f}."
        )

        return {
            "confidence_score": round(float(overall_conf), 4),
            "summary": summary,
            "token_usage": usage_total,
            "highlight": highlights
        }

# ------------------------------ CLI --------------------------------

def _read_input_text(input_file: Optional[str], input_string: Optional[str]) -> str:
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            return f.read()
    if input_string:
        return input_string
    # Keep the exact error wording your previous agent used:
    raise ValueError("No input provided. Use --input_file or --input_string.")

def _write_output_json(output_file: str, data: Dict) -> None:
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Fact Verification Agent (Inference)")
    parser.add_argument("--input_file", type=str, help="Path to a text file containing the email content")
    parser.add_argument("--input_string", type=str, help="Raw email text passed directly")
    parser.add_argument("--output_file", type=str, default="fact_verification_output.json", help="Path to write JSON output")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model to use")
    parser.add_argument("--api_key", type=str, default=None, help="OpenAI API key (or set OPENAI_API_KEY env var)")
    args = parser.parse_args()

    try:
        email_text = _read_input_text(args.input_file, args.input_string)
    except Exception as e:
        # Match previous agent behavior: raise with the same message
        print(str(e))
        sys.exit(1)

    # Initialize agent and analyze
    try:
        agent = FactVerificationAgent(api_key=args.api_key, model=args.model)
        result = agent.analyze_email(email_text)
    except Exception as e:
        # Return a minimal JSON on failure (still similar shape)
        result = {
            "confidence_score": 0.5,
            "summary": f"Error in fact verification: {e}",
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "highlight": []
        }

    # Write JSON file and also print the path
    _write_output_json(args.output_file, result)
    print(f"✅ Fact verification JSON written to: {args.output_file}")

if __name__ == "__main__":
    main()
