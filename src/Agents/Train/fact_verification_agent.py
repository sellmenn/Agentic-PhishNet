"""
Fact Verification Agent (Inference) — Closed-Book, Training-Aligned
Input parity with previous agent; outputs a similar JSON file.

CLI:
  --input_file <path>      Read email text from file
  --input_string "<text>"  Or pass email text directly
  --output_file <path>     Where to write the JSON (default: fact_verification_output.json)
  --model <model_name>     OpenAI model (default: gpt-4o-mini)
  --api_key <key>          Optional; otherwise uses OPENAI_API_KEY env var
  --trained_path <path>    Path to final training checkpoint JSON
  --top_k_extract <int>    How many top extraction strategies to use (default: 2)
  --top_k_verify  <int>    How many top verification strategies to use (default: 3)

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
- Uses evolved prompts from a trained checkpoint (top-K extraction + rotating verification strategies).
- Aggregates per-claim results into confidence_score and highlights suspicious spans.
"""

import argparse
import json
import os
import re
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
    top_k_extract: int = 2
    top_k_verify: int = 3

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

DEFAULT_EXTRACTION_PROMPT = (
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
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        trained_path: Optional[str] = None,
        top_k_extract: int = 2,
        top_k_verify: int = 3,
    ):
        self.config = AgentConfig(
            base_model=model,
            top_k_extract=max(1, int(top_k_extract)),
            top_k_verify=max(1, int(top_k_verify)),
        )
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Trained strategy holders
        self.extract_strategies: List[Dict] = []   # list of {"prompt", "success_rate", ...}
        self.verify_strategies: List[Dict] = []    # list of {"prompt", "success_rate", ...}

        # Load trained strategies if available
        trained_path = os.getenv("FACT_TRAINED_CHECKPOINT_PATH")
        self._load_trained_strategies(trained_path)

    # --------------- Strategy loading ---------------------

    def _sanitize_prompt(self, text: str) -> str:
        # Strip code fences like ```json ... ``` or ```
        text = re.sub(r"```[a-zA-Z]*\s*", "", text or "")
        text = text.replace("```", "")
        return text.strip()

    def _load_trained_strategies(self, path: str) -> None:
        """
        Load strategies from a final training results JSON. Supports both fact-agent and (as fallback)
        language-agent checkpoints:
          - Fact agent: claim_extraction_strategies, verification_strategies
          - Language agent: defender_strategies (ignored here)
        """
        try:
            if not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Fact agent fields
            extract = data.get("claim_extraction_strategies") or []
            verify = data.get("verification_strategies") or []

            # Some checkpoints may nest strategies inside another object
            if not extract and isinstance(data.get("knowledge_base"), dict):
                # nothing else to do; just robustness
                pass

            # Clean and sort extraction strategies
            cleaned_extract = []
            for s in extract:
                pr = self._sanitize_prompt(s.get("prompt", ""))
                if pr:
                    cleaned_extract.append({
                        "name": s.get("name", "extraction"),
                        "prompt": pr,
                        "success_rate": float(s.get("success_rate", 0.5) or 0.5)
                    })
            cleaned_extract.sort(key=lambda x: x["success_rate"], reverse=True)

            # Clean and sort verification strategies
            cleaned_verify = []
            for s in verify:
                pr = self._sanitize_prompt(s.get("prompt", ""))
                if pr:
                    cleaned_verify.append({
                        "name": s.get("name", "verification"),
                        "prompt": pr,
                        "success_rate": float(s.get("success_rate", 0.5) or 0.5)
                    })
            cleaned_verify.sort(key=lambda x: x["success_rate"], reverse=True)

            self.extract_strategies = cleaned_extract
            self.verify_strategies = cleaned_verify

        except Exception:
            # Fail soft: run with defaults if file is malformed
            self.extract_strategies = []
            self.verify_strategies = []

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

    def _compose_extraction_instruction(self) -> str:
        """
        Combine top-K extraction strategies (if any) + the default extraction prompt.
        """
        if self.extract_strategies:
            top = self.extract_strategies[: self.config.top_k_extract]
            joined = "\n\n".join([f"[Extraction Strategy {i+1}]\n{e['prompt']}" for i, e in enumerate(top)])
            return f"Use the following extraction strategies as guidance:\n{joined}\n\n{DEFAULT_EXTRACTION_PROMPT}"
        return DEFAULT_EXTRACTION_PROMPT

    def _extract_claims(self, email_content: str) -> Tuple[List[Dict], Dict]:
        """Return (claims, usage)."""
        if not email_content.strip():
            return [], {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        try:
            extraction_instruction = self._compose_extraction_instruction()
            resp = self.client.chat.completions.create(
                model=self.config.base_model,
                messages=[
                    {"role": "system", "content": "Extract verifiable claims with precise indices. Return JSON only."},
                    {"role": "user", "content": f"{extraction_instruction}\n\nEMAIL CONTENT:\n{email_content}"}
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

    def _verification_frame(self) -> str:
        return (
            "Verify the factual legitimacy of the claim conservatively (closed-book):\n"
            "- Does the structure match real-world practices (e.g., domains, contact formats, processes)?\n"
            "- Is there obvious typosquatting or unrealistic offers?\n"
            "- Is it internally coherent with typical policies and timelines?\n"
            "If uncertain, lean suspicious."
        )

    def _select_verify_prompt_for_index(self, idx: int) -> Optional[str]:
        """
        Rotate through top-K verification strategies; returns strategy prompt or None if none loaded.
        """
        if not self.verify_strategies:
            return None
        top = self.verify_strategies[: self.config.top_k_verify]
        strat = top[idx % len(top)]
        return strat.get("prompt")

    def _verify_one_claim(self, claim_text: str, strat_prompt: Optional[str]) -> Tuple[Dict, Dict]:
        """Closed-book verify a single claim using (optional) trained strategy guidance. Returns (verification, usage)."""
        base = self._verification_frame()
        guide = f"\n\nUse this verification strategy as guidance:\n{strat_prompt}" if strat_prompt else ""
        prompt = f"""{base}{guide}

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
        End-to-end: extract claims (guided by trained extraction strategies), verify each claim
        (rotating through trained verification strategies), then return the simplified schema.
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
            guide = self._select_verify_prompt_for_index(i)
            v, u = self._verify_one_claim(ct, guide)
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