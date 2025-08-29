from __future__ import annotations

import sys
from functools import lru_cache
from typing import Dict, List, Optional
from urllib.parse import urlparse
from ddgs import DDGS


def _domain_of(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc.lower()
    except Exception:
        return url


class WebRetriever:
    """
    DuckDuckGo web retriever that returns attributed results
    (title, url, snippet), deduped by domain, with optional recency bias.
    """

    def __init__(
        self,
        region: str = "us-en",
        safesearch: str = "moderate",  # "off" | "moderate" | "strict"
        timelimit: Optional[str] = None,  # e.g. "d" | "w" | "m" | "y"
        max_per_domain: int = 1,
        max_snippet_len: int = 320,
        stderr_logging: bool = True,
    ):
        self.region = region
        self.safesearch = safesearch
        self.timelimit = timelimit
        self.max_per_domain = max_per_domain
        self.max_snippet_len = max_snippet_len
        self.stderr_logging = stderr_logging

    def _log(self, msg: str) -> None:
        if self.stderr_logging:
            print(f"[WebRetriever] {msg}", file=sys.stderr)

    @lru_cache(maxsize=512)
    def search(self, query: str, max_results: int = 6) -> List[Dict]:
        """
        Return a list of dicts: {"title": str, "url": str, "snippet": str, "domain": str}.
        Dedupes by domain and truncates snippets for prompt hygiene.
        """
        results: List[Dict] = []
        try:
            with DDGS() as ddgs:
                for res in ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    timelimit=self.timelimit,
                    max_results=max_results * 2,  # fetch a few more before dedupe
                ):
                    title = (res.get("title") or "").strip()
                    url = (res.get("href") or res.get("url") or "").strip()
                    snippet = (res.get("body") or res.get("snippet") or "").strip()
                    if not url or not snippet:
                        continue
                    domain = _domain_of(url)
                    if not domain:
                        continue
                    if self.max_snippet_len and len(snippet) > self.max_snippet_len:
                        snippet = snippet[: self.max_snippet_len].rstrip() + "…"
                    results.append(
                        {"title": title, "url": url, "snippet": snippet, "domain": domain}
                    )
        except Exception as e:
            self._log(f"error during DDG search: {e!r}")
            return []

        # Deduplicate by domain (cap results per domain)
        seen_count: Dict[str, int] = {}
        uniq: List[Dict] = []
        for r in results:
            c = seen_count.get(r["domain"], 0)
            if c < self.max_per_domain:
                uniq.append(r)
                seen_count[r["domain"]] = c + 1
            if len(uniq) >= max_results:
                break
        return uniq

    @staticmethod
    def overlap_score(text: str, snippet: str) -> float:
        """
        Extremely lightweight token overlap score in [0,1].
        """
        a = {t.lower() for t in text.split() if t.isalnum() or t.isalpha()}
        b = {t.lower() for t in snippet.split() if t.isalnum() or t.isalpha()}
        if not a or not b:
            return 0.0
        inter = len(a & b)
        denom = min(len(a), len(b))
        return inter / max(1, denom)

    def rerank(self, query: str, hits: List[Dict]) -> List[Dict]:
        """
        Rerank by a naive overlap score of (title+snippet) with the query.
        """
        scored = []
        for h in hits:
            s = self.overlap_score(query, f"{h.get('title','')} {h.get('snippet','')}")
            scored.append((s, h))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [h for _, h in scored]
