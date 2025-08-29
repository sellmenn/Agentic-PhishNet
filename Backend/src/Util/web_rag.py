import sys
from functools import lru_cache
from urllib.parse import urlparse
from ddgs import DDGS


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return url


class WebRetriever:
    """
    DuckDuckGo retriever returning (title, url, snippet) with domain dedupe.
    """

    def __init__(
        self,
        region: str = "us-en",
        safesearch: str = "moderate",  # off | moderate | strict
        timelimit: str | None = None,  # d | w | m | y
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
    def search(self, query: str, max_results: int = 6) -> list[dict]:
        """
        Return [{"title","url","snippet","domain"}] (domain-deduped, snippet-truncated).
        """
        hits: list[dict] = []
        try:
            with DDGS() as ddg:
                for r in ddg.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    timelimit=self.timelimit,
                    max_results=max_results * 2,  # fetch extras before dedupe
                ):
                    title = (r.get("title") or "").strip()
                    url = (r.get("href") or r.get("url") or "").strip()
                    snippet = (r.get("body") or r.get("snippet") or "").strip()
                    if not url or not snippet:
                        continue

                    domain = get_domain(url)
                    if not domain:
                        continue

                    if self.max_snippet_len and len(snippet) > self.max_snippet_len:
                        snippet = snippet[: self.max_snippet_len].rstrip() + "…"

                    hits.append(
                        {"title": title, "url": url, "snippet": snippet, "domain": domain}
                    )
        except Exception as e:
            self._log(f"error during DDG search: {e!r}")
            return []

        # dedupe by domain (cap results per domain)
        seen: dict[str, int] = {}
        uniq: list[dict] = []
        for h in hits:
            c = seen.get(h["domain"], 0)
            if c < self.max_per_domain:
                uniq.append(h)
                seen[h["domain"]] = c + 1
            if len(uniq) >= max_results:
                break
        return uniq

    @staticmethod
    def overlap_score(text: str, snippet: str) -> float:
        """
        Lightweight token-overlap score in [0,1].
        """
        a = {t.lower() for t in text.split() if t.isalnum() or t.isalpha()}
        b = {t.lower() for t in snippet.split() if t.isalnum() or t.isalpha()}
        if not a or not b:
            return 0.0
        inter = len(a & b)
        denom = min(len(a), len(b))
        return inter / max(1, denom)

    def rerank(self, query: str, hits: list[dict]) -> list[dict]:
        """
        Rerank by overlap of (title + snippet) with the query.
        """
        scored: list[tuple[float, dict]] = []
        for h in hits:
            s = self.overlap_score(query, f"{h.get('title','')} {h.get('snippet','')}")
            scored.append((s, h))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [h for _, h in scored]
