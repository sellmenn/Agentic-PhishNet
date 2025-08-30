"""
Fact Verification Agent (Inference) — Closed-Book, Training-Aligned

CLI:
  --input_file <path>      Read email text from file
  --input_string "<text>"  Or pass email text directly
  --output_file <path>     Where to write the JSON (default: fact_verification_output.json)
  --model <model_name>     OpenAI model (default: gpt-4o-mini)
  --api_key <key>          Optional; otherwise uses OPENAI_API_KEY env var
  --trained_path <path>    Path to final training checkpoint JSON
  --top_k_extract <int>    How many top extraction strategies to use (default: 2)
  --top_k_verify  <int>    How many top verification strategies to use (default: 3)

Output JSON:
{
  "confidence_score": float,              # 0..1
  "summary": "Brief summary",
  "token_usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
  "highlight": [
    {"s_idx": int, "e_idx": int, "reasoning": "why suspicious"},
    ...
  ]
}

Internals:
- Extract claims (one call), then verify each claim (one call per claim), closed-book.
- Uses prompts from a trained checkpoint (top-K extraction + rotating verification strategies).
- Aggregates per-claim results into confidence_score and highlights.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass

from Util.web_rag import WebRetriever 

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


RESPONSE_SCHEMA = """
Return ONLY valid JSON with EXACT keys:
{
  "is_legitimate": true or false,
  "confidence": <number between 0.0 and 1.0>,
  "reasoning": "<one concise sentence>",
  "verification_source": "model_closed_book" or "web_snippets"
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
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        trained_path: str | None = None,
        top_k_extract: int = 2,
        top_k_verify: int = 3,
        ddg_region: str = "us-en",
        ddg_safesearch: str = "moderate",
        ddg_timelimit: str | None = None,  # e.g., "m" (last month)
    ):
        self.config = AgentConfig(
            base_model=model,
            top_k_extract=max(1, int(top_k_extract)),
            top_k_verify=max(1, int(top_k_verify)),
        )
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Trained strategy holders
        self.extract_strategies: list[dict] = []   # [{"prompt", "success_rate", ...}, ...]
        self.verify_strategies: list[dict] = []    # [{"prompt", "success_rate", ...}, ...]

        # Web retriever for RAG verification
        self.web_retriever = WebRetriever(
            region=ddg_region,
            safesearch=ddg_safesearch,
            timelimit=ddg_timelimit,
            max_per_domain=1,
        )

        # Load trained strategies if available
        trained_path = trained_path or os.getenv("FACT_TRAINED_CHECKPOINT_PATH")
        self._load_trained_strategies(trained_path)

    # --------------- Strategy loading ---------------------

    def _sanitize_prompt(self, text: str) -> str:
        text = re.sub(r"```[a-zA-Z]*\s*", "", text or "")
        text = text.replace("```", "")
        return text.strip()

    def _load_trained_strategies(self, path: str | None) -> None:
        try:
            if not path or not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            extract = data.get("claim_extraction_strategies") or []
            verify = data.get("verification_strategies") or []

            cleaned_extract: list[dict] = []
            for s in extract:
                pr = self._sanitize_prompt(s.get("prompt", ""))
                if pr:
                    cleaned_extract.append({
                        "name": s.get("name", "extraction"),
                        "prompt": pr,
                        "success_rate": float(s.get("success_rate", 0.5) or 0.5)
                    })
            cleaned_extract.sort(key=lambda x: x["success_rate"], reverse=True)

            cleaned_verify: list[dict] = []
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

        except Exception as e:
            print(f"[Agent] Failed to load strategies: {e!r}", file=sys.stderr)
            self.extract_strategies = []
            self.verify_strategies = []

    # --------------- Internal helpers & parsing ---------------------

    def _safe_float(self, x, default: float = 0.5) -> float:
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

    def _json_repair(self, broken_text: str) -> dict | None:
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
        if self.extract_strategies:
            top = self.extract_strategies[: self.config.top_k_extract]
            joined = "\n\n".join([f"[Extraction Strategy {i+1}]\n{e['prompt']}" for i, e in enumerate(top)])
            return f"Use the following extraction strategies as guidance:\n{joined}\n\n{DEFAULT_EXTRACTION_PROMPT}"
        return DEFAULT_EXTRACTION_PROMPT

    def _extract_claims(self, email_content: str) -> tuple[list[dict], dict]:
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
        except Exception as e:
            print(f"[Agent] Extraction error: {e!r}", file=sys.stderr)
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            claims = []

        # Cap
        if isinstance(claims, list):
            claims = claims[: self.config.max_claims_per_email]
        else:
            claims = []

        # Normalize indices
        normed: list[dict] = []
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
            "Verify the factual legitimacy of the claim conservatively:\n"
            "- Check structural plausibility (domains, contact formats, processes)\n"
            "- Watch for typosquatting, unrealistic offers, incoherent timelines\n"
            "- If uncertain, lean suspicious"
        )

    def _select_verify_prompt_for_index(self, idx: int) -> str | None:
        if not self.verify_strategies:
            return None
        top = self.verify_strategies[: self.config.top_k_verify]
        strat = top[idx % len(top)]
        return strat.get("prompt")

    # ---- Query rewriting helpers ----

    DOMAIN_RE = re.compile(r"\b([a-z0-9-]{1,63}\.)+[a-z]{2,24}\b", re.I)
    EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,24})\b", re.I)

    def _extract_domains(self, text: str) -> list[str]:
        doms = set(self.DOMAIN_RE.findall(text) or [])
        for m in self.EMAIL_RE.finditer(text):
            doms.add(m.group(1).lower())
        return sorted({d.rstrip(".").lower() for d in doms})

    def _rewrite_query(self, claim_text: str) -> str:
        """
        If domains are present, add a site: filter; otherwise keep the claim text.
        """
        claim = " ".join(claim_text.split())
        domains = self._extract_domains(claim_text)
        if domains:
            primary = domains[0]
            return f"{claim} site:{primary}"
        return claim

    def _format_context(self, results: list[dict], max_snips: int = 3) -> str:
        """
        Short, attributed snippets with URLs for provenance.
        """
        lines: list[str] = []
        for r in results[:max_snips]:
            title = r.get("title") or r["domain"]
            url = r["url"]
            snippet = r.get("snippet", "")[:320]
            lines.append(f"- [{title}] ({url}): {snippet}")
        return "\n".join(lines)

    def _verify_one_claim(self, claim_text: str, strat_prompt: str | None) -> tuple[dict, dict]:
        base = self._verification_frame()
        guide = f"\n\nUse this verification strategy as guidance:\n{strat_prompt}" if strat_prompt else ""

        # Retrieve web context for RAG verification
        query = self._rewrite_query(claim_text)
        hits = self.web_retriever.search(query, max_results=6)
        hits = self.web_retriever.rerank(query, hits)
        context_block = f"\n\nWeb snippets (attributed):\n{self._format_context(hits)}" if hits else ""

        prompt = f"""{base}{guide}{context_block}

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
            print(f"[Agent] Verification error: {e!r}", file=sys.stderr)
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            obj = {
                "is_legitimate": False,
                "confidence": 0.5,
                "reasoning": "Error during verification",
                "verification_source": "model_closed_book"
            }

        # Normalize and set source
        source = "web_snippets" if hits else "model_closed_book"
        is_legit = 1 if bool(obj.get("is_legitimate", False)) else 0
        conf = max(0.0, min(1.0, self._safe_float(obj.get("confidence", 0.5), 0.5)))
        reasoning = str(obj.get("reasoning", ""))[:500]
        return {
            "is_legitimate": is_legit,
            "confidence": conf,
            "reasoning": reasoning,
            "verification_source": source
        }, usage

    # --------------------------- Public API -------------------------

    def analyze_email(self, email_content: str) -> dict:
        """
        Extract claims, verify each, then aggregate.
        """
        # 1) Extract claims
        claims, usage_total = self._extract_claims(email_content)

        # 2) Verify per-claim
        verifs: list[dict] = []
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
            overall_conf = 0.5

        # 4) Highlights for suspicious spans
        highlights: list[dict] = []
        for i, (c, v) in enumerate(zip(claims, verifs)):
            if v["is_legitimate"] == 0:
                s = max(0, int(c.get("start_index", 0)))
                e = max(s, int(c.get("end_index", 0)))
                reasoning = v.get("reasoning", "Suspicious claim")
                if e <= s:
                    ct = c.get("claim_text", "")
                    if ct:
                        pos = email_content.find(ct)
                        if pos != -1:
                            s = pos
                            e = pos + len(ct)
                if e > s:
                    highlights.append({"s_idx": s, "e_idx": e, "reasoning": reasoning})

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


# ------------------------------- CLI --------------------------------

def _read_input_text(args: argparse.Namespace) -> str:
    if args.input_string:
        return args.input_string
    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as f:
            return f.read()
    raise SystemExit("Provide --input_string or --input_file")


def main():
    p = argparse.ArgumentParser(description="Fact Verification Agent (with web RAG)")
    p.add_argument("--input_file", type=str, help="Path to email text")
    p.add_argument("--input_string", type=str, help="Email text directly")
    p.add_argument("--output_file", type=str, default="fact_verification_output.json")
    p.add_argument("--model", type=str, default="gpt-4o-mini")
    p.add_argument("--api_key", type=str, default=None)
    p.add_argument("--trained_path", type=str, default=None)
    p.add_argument("--top_k_extract", type=int, default=2)
    p.add_argument("--top_k_verify", type=int, default=3)

    # DDG knobs
    p.add_argument("--ddg_region", type=str, default="us-en")
    p.add_argument("--ddg_safesearch", type=str, default="moderate")
    p.add_argument("--ddg_timelimit", type=str, default=None, help='e.g. "m" (last month)')

    args = p.parse_args()

    agent = FactVerificationAgent(
        api_key=args.api_key,
        model=args.model,
        trained_path=args.trained_path,
        top_k_extract=args.top_k_extract,
        top_k_verify=args.top_k_verify,
        ddg_region=args.ddg_region,
        ddg_safesearch=args.ddg_safesearch,
        ddg_timelimit=args.ddg_timelimit,
    )

    email_text = _read_input_text(args)
    result = agent.analyze_email(email_text)

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.output_file}")


if __name__ == "__main__":
    main()
