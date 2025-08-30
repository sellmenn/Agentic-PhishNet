import os, re, sys, json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

OPENAI_MODEL     = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
TRAINED_PATH     = "models/language_agent/final_training_results.json"
COMMITTEE_SIZE   = 3
TOP_K_STRATEGIES = 3
TEMPERATURE      = 0.1
MAX_TOKENS       = 1000
OUTPUT_JSON      = ""

class OpenAIChat:
    def __init__(self, model: str):
        self.model = model
        self._use_new = False
        self._client = None
        try:
            from openai import OpenAI  # type: ignore
            self._client = OpenAI()
            self._use_new = True
        except Exception:
            import openai as _openai  # type: ignore
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("OPENAI_API_KEY not set.")
            self._openai = _openai

    def chat(self, messages: List[Dict], temperature: float, max_tokens: int) -> Tuple[str, Dict]:
        if self._use_new:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content or ""
            usage = getattr(resp, "usage", None) or {}
            return content.strip(), {
                "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
                "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
                "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
            }
        else:
            resp = self._openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp["choices"][0]["message"]["content"] or ""
            usage = resp.get("usage", {}) if isinstance(resp, dict) else {}
            return content.strip(), {
                "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                "total_tokens": int(usage.get("total_tokens", 0) or 0),
            }

class LanguageAnalysisAgent:
    def __init__(
        self,
        trained_path: Optional[str] = TRAINED_PATH,
        committee_size: int = COMMITTEE_SIZE,
        top_k_strategies: int = TOP_K_STRATEGIES,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        model: str = OPENAI_MODEL,
    ):
        self.llm = OpenAIChat(model)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.committee_size = max(1, int(committee_size))
        self.top_k_strategies = max(1, int(top_k_strategies))
        self.system_prompt = self._system_prompt()
        self.strategies = self._load_trained_strategies(trained_path)

    def _system_prompt(self) -> str:
        return (
            "You are a language analysis agent that classifies emails for phishing using reasoning-only, no external tools. "
            "Output JSON ONLY with this schema:\n"
            '{\n  "confidence_score": float,  // 0.0 = phishing, 1.0 = not phishing\n'
            '  "summary": "string",\n'
            '  "token_usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},\n'
            '  "highlight": [{"s_idx": int, "e_idx": int, "reasoning": "string"}]\n}\n'
            "IMPORTANT: Ensure that the start and end index do not end up in the middle of words. The phrase highlighted should form full words."
        )

    def _load_trained_strategies(self, path: Optional[str]) -> List[str]:
        if not path or not os.path.exists(path):
            return [self._default_strategy()]
        try:
            with open(path, "r", encoding="utf-8") as f:
                ckpt = json.load(f)
        except Exception:
            return [self._default_strategy()]
        candidates = []
        for key in ["defender_strategies", "defender_prompts", "verification_strategies"]:
            v = ckpt.get(key)
            if isinstance(v, list) and v:
                candidates = v
                break
        prompts: List[Tuple[str, float]] = []
        for s in candidates:
            p = (s or {}).get("prompt") or (s or {}).get("instruction") or ""
            if not isinstance(p, str) or not p.strip():
                continue
            sr = s.get("success_rate", 0.5)
            try:
                prompts.append((self._strip_md_fences(p.strip()), float(sr)))
            except Exception:
                prompts.append((self._strip_md_fences(p.strip()), 0.5))
        if not prompts:
            p = ckpt.get("defender_prompt_prefix") or ckpt.get("defender_prompt") or ""
            if isinstance(p, str) and p.strip():
                return [self._strip_md_fences(p.strip())]
            return [self._default_strategy()]
        prompts.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in prompts[: self.top_k_strategies]]

    def _strip_md_fences(self, text: str) -> str:
        text = re.sub(r"```[a-zA-Z]*\s*", "", text)
        return text.replace("```", "").strip()

    def _default_strategy(self) -> str:
        return (
            "Analyze strictly for phishing cues via reasoning. Make a binary call but report confidence on [0,1]. "
            "Be explicit in why specific spans are suspicious and provide exact indices for each span."
        )

    def analyze_email(self, email_content: str) -> Dict:
        if not email_content or not email_content.strip():
            return self._out(0.5, "Empty input.", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, [])
        prompts = self.strategies or [self._default_strategy()]
        k = min(self.committee_size, max(1, len(prompts)))
        results: List[Dict] = []
        usage_tot = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        for i in range(k):
            strat = prompts[i % len(prompts)]
            one, u = self._run(email_content, strat)
            results.append(one)
            for t in usage_tot:
                usage_tot[t] += int(u.get(t, 0))
        return self._aggregate(email_content, results, usage_tot)

    def _run(self, email_text: str, strategy: Optional[str]) -> Tuple[Dict, Dict]:
        user_prompt = (
            (f"Strategy:\n{strategy}\n\n" if strategy else "")
            + "Email to analyze:\n---\n"
            + email_text
            + "\n---\n"
            "Return JSON ONLY with keys: confidence_score, summary, token_usage, highlight.\n"
            "Rules:\n"
            "- confidence_score in [0,1], where 0=phishing, 1=not phishing.\n"
            "- highlight is a list of objects: {\"s_idx\":int,\"e_idx\":int,\"reasoning\":string} with character indices.\n"
            "- No extra commentary outside JSON."
        )
        txt, usage = self.llm.chat(
            messages=[{"role": "system", "content": self.system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        parsed = self._extract_json(txt)
        if parsed is None:
            parsed = {"confidence_score": 0.5, "summary": "Unparseable model output.", "highlight": []}
        return self._normalize(parsed, usage, email_text), usage

    def _extract_json(self, text: str) -> Optional[Dict]:
        s, e = text.find("{"), text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                return None
        return None

    def _is_word_char(self, ch: str) -> bool:
        return ch.isalnum() or ch in "_-/'"

    def _expand_to_word_bounds(self, text: str, s: int, e: int) -> Tuple[int, int]:
        n = len(text)
        s = max(0, min(s, n))
        e = max(0, min(e, n))
        if s >= e: return s, e
        while s > 0 and self._is_word_char(text[s-1]) and self._is_word_char(text[s]):
            s -= 1
        while e < n and e > 0 and self._is_word_char(text[e-1]) and (e < n and self._is_word_char(text[e])):
            e += 1
        while s < e and text[s].isspace(): s += 1
        while e > s and text[e-1].isspace(): e -= 1
        return s, e

    def _valid_span(self, text: str, s: int, e: int) -> bool:
        if e - s < 2:
            return False
        fragment = text[s:e]
        if not re.search(r"[A-Za-z0-9]", fragment):
            return False
        if re.fullmatch(r"\W+", fragment or ""):
            return False
        return True

    def _merge_overlaps(self, spans: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
        if not spans: return []
        spans.sort(key=lambda x: (x[0], x[1]))
        merged: List[Tuple[int, int, str]] = []
        cur_s, cur_e, cur_r = spans[0]
        for s, e, r in spans[1:]:
            if s <= cur_e + 1:
                cur_e = max(cur_e, e)
                if len(r) > len(cur_r):
                    cur_r = r
            else:
                merged.append((cur_s, cur_e, cur_r))
                cur_s, cur_e, cur_r = s, e, r
        merged.append((cur_s, cur_e, cur_r))
        return merged

    def _clean_highlights(self, email_text: str, raw: List[Dict]) -> List[Dict]:
        n = len(email_text)
        spans: List[Tuple[int, int, str]] = []
        for h in raw:
            try:
                s = int(h.get("s_idx", 0) or 0)
                e = int(h.get("e_idx", 0) or 0)
                reason = str(h.get("reasoning") or "Suspicious span")
            except Exception:
                continue
            s, e = max(0, min(s, n)), max(0, min(e, n))
            if s >= e: continue
            s, e = self._expand_to_word_bounds(email_text, s, e)
            if s >= e: continue
            if not self._valid_span(email_text, s, e): continue
            spans.append((s, e, reason))
        dedup: Dict[Tuple[int, int], str] = {}
        for s, e, r in spans:
            key = (s, e)
            if key not in dedup or len(r) > len(dedup[key]):
                dedup[key] = r
        spans = [(s, e, dedup[(s, e)]) for (s, e) in dedup]
        spans = self._merge_overlaps(spans)
        spans = spans[:20]
        return [{"s_idx": s, "e_idx": e, "reasoning": r} for s, e, r in spans]

    def _normalize(self, obj: Dict, usage: Dict, email_text: str) -> Dict:
        cs = float(obj.get("confidence_score", 0.5))
        cs = 0.0 if cs < 0 else 1.0 if cs > 1 else cs
        summary = str(obj.get("summary") or "Analysis complete.")
        hl_in = obj.get("highlight", []) or []
        prelim = []
        for h in hl_in:
            if not isinstance(h, dict): continue
            try:
                s_idx = int(h.get("s_idx", 0) or 0)
                e_idx = int(h.get("e_idx", 0) or 0)
            except Exception:
                continue
            s_idx = max(0, min(s_idx, len(email_text)))
            e_idx = max(0, min(e_idx, len(email_text)))
            if s_idx >= e_idx: continue
            reason = str(h.get("reasoning") or "Suspicious span")
            prelim.append({"s_idx": s_idx, "e_idx": e_idx, "reasoning": reason})
        hl_out = self._clean_highlights(email_text, prelim)
        return self._out(cs, summary, usage, hl_out)

    def _aggregate(self, email_text: str, results: List[Dict], usage_tot: Dict) -> Dict:
        if not results:
            return self._out(0.5, "No committee outputs.", usage_tot, [])
        confs = [float(r.get("confidence_score", 0.5)) for r in results]
        final_conf = sum(confs) / max(1, len(confs))
        summaries = [(r.get("summary") or "") for r in results]
        final_summary = max(summaries, key=lambda s: len(s)) if any(summaries) else "Analysis complete."
        merged, seen = [], set()
        for r in results:
            for h in r.get("highlight", []) or []:
                s, e, rr = int(h.get("s_idx", -1)), int(h.get("e_idx", -1)), str(h.get("reasoning", ""))
                key = (s, e, rr)
                if key in seen: continue
                seen.add(key); merged.append({"s_idx": s, "e_idx": e, "reasoning": rr})
        merged = self._clean_highlights(email_text, merged)
        return self._out(float(final_conf), final_summary, usage_tot, merged)

    def _out(self, confidence_score: float, summary: str, usage: Dict, highlight: List[Dict]) -> Dict:
        return {
            "confidence_score": float(confidence_score),
            "summary": str(summary),
            "token_usage": {
                "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                "total_tokens": int(usage.get("total_tokens", 0) or 0),
            },
            "highlight": highlight,
        }

def _read_text() -> str:
    if os.path.exists("email.txt"):
        with open("email.txt", "r", encoding="utf-8") as f:
            return f.read()
    env_text = os.environ.get("EMAIL_TEXT", None)
    if env_text is not None and str(env_text).strip():
        return env_text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("No email text provided. Put text in ./email.txt, set EMAIL_TEXT env, or pipe to stdin.")

def _write_json(obj: Dict) -> str:
    os.makedirs("outputs", exist_ok=True)
    path = OUTPUT_JSON
    if not path or not path.strip():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join("outputs", f"language_agent_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path

def main():
    email_text = _read_text()
    agent = LanguageAnalysisAgent(
        trained_path=TRAINED_PATH,
        committee_size=COMMITTEE_SIZE,
        top_k_strategies=TOP_K_STRATEGIES,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        model_name=OPENAI_MODEL,
    )
    result = agent.analyze_email(email_text)
    out_path = _write_json(result)
    print(json.dumps(result, ensure_ascii=False))
    print(f"\nSaved: {out_path}")

if __name__ == "__main__":
    main()
