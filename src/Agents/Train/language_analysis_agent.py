"""
Language Analysis Agent for Phishing Detection
- Prints results to console
- Saves strict JSON output to a file
- Accepts a text file or raw string as input via CLI
- ✅ Uses trained strategies from a final training checkpoint (committee inference)
"""

import json
import re
import os
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import openai


# ---------------------------- Agent ----------------------------

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

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        trained_path: Optional[str] = None,
        committee_size: int = 3,
        top_k_strategies: int = 3
    ):
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

        # Defaults (used if no checkpoint provided)
        self.analysis_prompt = self._default_system_prompt()
        self.defender_strategies: List[Dict] = []

        # Committee settings
        self.committee_size = max(1, int(committee_size))
        self.top_k_strategies = max(1, int(top_k_strategies))

        # Load trained strategies (if provided)
        trained_path = os.getenv("LANG_TRAINED_CHECKPOINT_PATH")
        self._load_trained_strategies(trained_path)

    # ---------- Trained Strategy Loading ----------

    def _load_trained_strategies(self, path: str) -> None:
        """
        Load evolved strategies from a final training result JSON.
        Supports:
          - Language agent:   {"defender_strategies":[{name, description, prompt, success_rate,...}, ...]}
          - Fact agent:       {"verification_strategies":[{...}], "claim_extraction_strategies":[...]}
        We will use defender_strategies if present, else verification_strategies.
        """
        try:
            if not os.path.exists(path):
                # Nothing to load; will run with the default prompt
                return
            with open(path, "r", encoding="utf-8") as f:
                ckpt = json.load(f)

            # Prefer language-agent defender_strategies
            strategies = ckpt.get("defender_strategies", None)

            # Fallback: fact-agent verification_strategies (still useful guidance)
            if not strategies:
                strategies = ckpt.get("verification_strategies", None)

            if not strategies or not isinstance(strategies, list):
                return

            # Keep only items with a prompt
            cleaned = []
            for s in strategies:
                pr = (s or {}).get("prompt", "")
                if not isinstance(pr, str) or not pr.strip():
                    continue
                cleaned.append({
                    "name": s.get("name", "strategy"),
                    "description": s.get("description", ""),
                    "prompt": self._sanitize_strategy_prompt(pr),
                    "success_rate": float((s.get("success_rate", 0.5) or 0.5))
                })

            if cleaned:
                # Sort by success_rate desc and store
                cleaned.sort(key=lambda x: x["success_rate"], reverse=True)
                self.defender_strategies = cleaned

        except Exception:
            # Silently ignore loading errors and fall back to default prompt
            self.defender_strategies = []

    def _sanitize_strategy_prompt(self, text: str) -> str:
        """
        Remove Markdown code fences and keep the content; some evolved prompts may contain
        ```json ...``` or ``` ... ``` blocks.
        """
        # Strip triple backtick fences
        text = re.sub(r"```[a-zA-Z]*\s*", "", text)
        text = text.replace("```", "")
        return text.strip()

    def _default_system_prompt(self) -> str:
        return (
            "You are an expert language analysis agent specialized in detecting phishing emails through linguistic "
            "patterns.\n\nFocus on:\n"
            "1) Urgency/time pressure\n2) Authority impersonation\n3) Threat language\n4) Emotional manipulation\n"
            "5) Social engineering requests\n6) Grammar/spelling anomalies\n7) Generic greetings\n8) Reward promises\n\n"
            "Output JSON ONLY in the user's requested schema and include exact character indices for suspicious phrases."
        )

    # ---------- Public API ----------

    def analyze_email(self, email_content: str) -> Dict:
        """
        Analyze an email for phishing indicators using an ensemble (committee) of trained strategies
        if available; otherwise, use a single default prompt. Returns strict JSON.
        """
        try:
            # Build committee strategies: top-K trained prompts if present; else the default
            strategies = self._select_committee_strategies()

            # Aggregate from multiple model calls
            all_results: List[Dict] = []
            total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            # We will run up to committee_size calls, cycling over our selected strategy prompts
            for i in range(self.committee_size):
                strat_prompt = strategies[i % len(strategies)]
                result_i, usage_i = self._run_single_analysis(email_content, strat_prompt)
                all_results.append(result_i)
                # Accumulate token usage
                for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    total_usage[k] += usage_i.get(k, 0)

            # Aggregate committee outputs
            final = self._aggregate_committee(email_content, all_results, total_usage)
            return final

        except Exception as e:
            # Always return valid schema on error
            return {
                "confidence_score": 0.5,
                "summary": f"Error in language analysis: {str(e)}",
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "highlight": [],
            }

    # ---------- Single-call runner ----------

    def _run_single_analysis(self, email_content: str, strategy_prompt: Optional[str]) -> Tuple[Dict, Dict]:
        """
        Execute a single LLM analysis call using a strategy prompt (if provided).
        Returns (parsed_output_in_internal_schema, token_usage_dict).
        """
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

        # Compose messages: keep a stable system prompt, add trained strategy as guidance
        sys_prompt = self.analysis_prompt
        user_prompt = (
            (f"Use this detection strategy as guidance:\n{strategy_prompt}\n\n" if strategy_prompt else "")
            + analysis_request
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
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

        # Convert to strict output schema (internal)
        result = self._format_output(parsed, token_usage, email_content)
        return result, token_usage

    # ---------- Committee helpers ----------

    def _select_committee_strategies(self) -> List[Optional[str]]:
        """
        Return a list of strategy prompts to use for committee inference.
        If we have trained strategies, choose top-K by success_rate; else return [None] to use default only.
        """
        if self.defender_strategies:
            top = self.defender_strategies[: self.top_k_strategies]
            return [s["prompt"] for s in top if s.get("prompt")]
        # No trained strategies; run with default system prompt only
        return [None]

    def _aggregate_committee(self, email_content: str, results: List[Dict], total_usage: Dict) -> Dict:
        """
        Combine multiple single-call outputs:
          - confidence_score: mean
          - summary: take the most detailed (longest) summary
          - highlight: merge and de-duplicate spans
          - token_usage: sum over committee
        """
        if not results:
            return {
                "confidence_score": 0.5,
                "summary": "No results from ensemble.",
                "token_usage": total_usage,
                "highlight": [],
            }

        # Average confidence
        confs = [float(r.get("confidence_score", 0.5)) for r in results]
        final_conf = sum(confs) / max(1, len(confs))

        # Pick longest summary (usually most informative)
        summaries = [(r.get("summary") or "") for r in results]
        final_summary = max(summaries, key=lambda s: len(s)) if any(summaries) else "Analysis completed."

        # Merge highlights (dedupe by (s_idx, e_idx, reasoning))
        merged = []
        seen = set()
        for r in results:
            for h in r.get("highlight", []) or []:
                key = (int(h.get("s_idx", -1)), int(h.get("e_idx", -1)), str(h.get("reasoning", "")))
                if key in seen:
                    continue
                seen.add(key)
                merged.append({
                    "s_idx": key[0],
                    "e_idx": key[1],
                    "reasoning": key[2]
                })

        return {
            "confidence_score": float(final_conf),
            "summary": str(final_summary),
            "token_usage": total_usage,
            "highlight": merged,
        }

    # ---------- Parsing & Formatting ----------

    def _safe_extract_json(self, text: str) -> Optional[Dict]:
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

            # Clamp to bounds
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