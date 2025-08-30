import sys, time, os # to print err msgs to the terminal  
from functools import lru_cache # caching search results so the same query doesn’t hit DuckDuckGo again
from urllib.parse import urlparse # extracts domain from link 
from ddgs import DDGS
import re # regular expressions, used for cleaning text 


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower() # extracts domain in lowercase, avoid dedupes later
    except Exception:
        return url


class WebRetriever:
    """
    DuckDuckGo retriever returning (title, url, snippet) with domain dedupe.
    """

    def __init__(
        self,
        region: str = "us-en",
        safesearch: str = "moderate",  # off | moderate | strict, filters for adult content
        timelimit: str | None = None,  # d | w | m | y, restrict to recent results
        max_per_domain: int = 1, # only allow one result per website to avoid spam 
        max_snippet_len: int = 320, # restrict snippet length 
        stderr_logging: bool = True, # whether to print errors 
        *, # everything after this must be passed as a keyword argument when called
        timeout: int = 8, # each request max 8s
        retries: int = 1, # retries once if search fails 
        backoff: float = 0.7, # delay before retrying grows exponentially, scaled by this base value
        proxy: str | None = None, # by default, don’t use any HTTP/HTTPS proxy
        overfetch: bool = False, # only fetches max_results number, not twice which is the norm 
    ):
        self.region = region 
        self.safesearch = safesearch
        self.timelimit = timelimit
        self.max_per_domain = max_per_domain
        self.max_snippet_len = max_snippet_len
        self.stderr_logging = stderr_logging
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.proxy = proxy
        self.overfetch = overfetch

    def _log(self, msg: str) -> None:
        if self.stderr_logging:
            print(f"[WebRetriever] {msg}", file=sys.stderr) # error logging format in terminal


    # Caches results so repeated searches don’t hit the web again
    # main search method: 
    @lru_cache(maxsize=512)
    def search(self, query: str, max_results: int = 6) -> list[dict]:
        """
        Takes a query string and returns a 
        list of dict with keys {"title","url","snippet","domain"},
        default of 6 results 
        """
        # Decide how many we ask the API for (overfetch only if enabled)
        fetch_n = max_results * 2 if self.overfetch else max_results
        
        # Attempt loop with backoff
        attempt = 0
        
        hits: list[dict] = []
        try:
            with DDGS(timeout=self.timeout, proxy=self.proxy) as ddg: # opens a ddgs session
                for r in ddg.text( # passes in query etc. to fetch results 
                    query, 
                    region=self.region,
                    safesearch=self.safesearch,
                    timelimit=self.timelimit,
                    max_results=fetch_n,  
                ):
                    title = (r.get("title") or "").strip()  # extracts title in each result of the query
                    url = (r.get("href") or r.get("url") or "").strip() # extracts url in each result of the query
                    snippet = (r.get("body") or r.get("snippet") or "").strip() # extracts snippet (body; content) in each result of the query 
                    if not url or not snippet: 
                        continue

                    domain = get_domain(url) # calls previous func to get domain from url
                    if not domain:
                        continue

                    if self.max_snippet_len and len(snippet) > self.max_snippet_len: # truncates snippet if too long 
                        snippet = snippet[: self.max_snippet_len].rstrip() + "…"

                    hits.append( # add results to list of dict 
                        {"title": title, "url": url, "snippet": snippet, "domain": domain}
                    )
        except Exception as e:
            attempt += 1
            self._log(f"DDG search error (attempt: {attempt}): {e!r}")
            if attempt > self.retries:
                return [] 
            time.sleep(self.backoff * (2 ** (attempt - 1)))

        # ------- prevents duplication by domain ----------- 
        seen: dict[str, int] = {} # domain name -> how many results kept from that domain
        uniq: list[dict] = [] # list of unique results we will return 
        for h in hits: # iterates through results 
            c = seen.get(h["domain"], 0) # default to 0 if not seen before
            if c < self.max_per_domain: # domain not seen before (since max_per_domain is 1)
                uniq.append(h) # add to unqiue list 
                seen[h["domain"]] = c + 1 # increment by one for that domain
            if len(uniq) >= max_results: 
                break # stop looping when collected enough results 
        return uniq # return unique list with {"title","url","snippet","domain"}


    @staticmethod # does not use self, utility method 
    def overlap_score(query: str, result_content: str) -> float:
        """
        Token overlap score in [0,1]:
        - Keeps letters, digits, and decimals (e.g., 2.5m).
        - Removes thousand separators (2,500,000 -> 2500000).
        - Normalizes currency ($2.5M -> 2.5m, €25,000 -> 25000).
        - Turns percents into a stable form (10% -> 10pct).
        - Strips most special chars, normalizes unicode dashes.
        """
        # precompiled helpers
        # CASE 1: matches money with currency, group 1: digits with optional commas, group 2: optional decimal part, group 3: optional multiplier suffix
        money_full = re.compile(r'^[\$\€\£]\s*([0-9][0-9,]*)(\.[0-9]+)?([kKmMbB])?$')
        # CASE 2: matches numbers with commas 
        number_with_commas = re.compile(r'^\d{1,3}(?:,\d{3})+(?:\.\d+)?$')
        # CASE 3: matches numbers with plain integers or decimals without commas
        number_simple = re.compile(r'^\d+(?:\.\d+)?$')

        # inner function to clean each token 
        def clean_token(t: str) -> str:
            if not t:
                return ""

            # normalize unicode spaces/dashes and lowercase
            t = t.replace("\u00A0", " ")          # replace non-breaking space with normal space
            t = t.replace("\u2013", "-").replace("\u2014", "-")  # replace en/em dash with hyphen
            t = t.strip().lower() 

            # percent: keep numeric value and mark as 'pct'
            if t.endswith("%"):
                core = t[:-1] # extract part without % from t 
                if number_with_commas.match(core): # remove commas inside numbers like 1,234.56
                    core = core.replace(",", "")
                core = re.sub(r"[^0-9.]", "", core) # keep only digits/dot
                return f"{core}pct" if core else "" 

            # CASE 1: currency amounts like $2.5M, €25,000, £1,200.50
            m = money_full.match(t)
            if m:
                intpart, decpart, mag = m.groups() # returns a tuple with all captured groups 
                val = intpart.replace(",", "") # remove comma 
                if decpart: 
                    val += decpart  # keep decimal point
                if mag:
                    return f"{val}{mag.lower()}"  # keeps magnitude suffix as lowercase e.g., 2.5m
                return val  # e.g., 25000
            
            # CASE 2: bare numbers with commas -> drop commas
            if number_with_commas.match(t):
                return t.replace(",", "")
            
            # CASE 3: bare numbers with optional decimal -> keep as-is
            if number_simple.match(t):
                return t

            # general tokens:
            # remove everything except letters, digits, and dots (to keep decimals inside alnum tokens)
            t = re.sub(r"[^a-z0-9.]", "", t)

            # collapse multiple dots (e.g., version..2 -> version.2)
            t = re.sub(r"\.{2,}", ".", t)

            # if token is just dots or empty after cleaning, drop it
            if not t or set(t) == {"."}:
                return ""

            return t

        def tokenize(s: str) -> set[str]:
            token_set: set[str] = set() # a set of strings 
            for raw in s.split(): # splits a string into tokens by spaces
                tk = clean_token(raw) # cleans each token by calling clean_token
                if tk:
                    token_set.add(tk) # add non-empty tokens to token_set  
            return token_set

        # tokenize both query and result_content (title + snippet)
        A = tokenize(query)
        B = tokenize(result_content)

        if not A or not B:
            return 0.0

        intersect = len(A & B) # intersection of shared tokens 
        denom = min(len(A), len(B)) # normalise by smaller set 
        return intersect / max(1, denom) # common / smaller set (0->no overlap, 1.0->small set completely in larger set)


    def rerank(self, query: str, hits: list[dict]) -> list[dict]:
        """
        Take the raw results, compute how well 
        each matches the query using overlap_score, 
        and sort best to worst.
        """
        scored: list[tuple[float, dict]] = [] # a list to hold tuple of (score, hit)
        for h in hits:
            s = self.overlap_score(query, f"{h.get('title','')} {h.get('snippet','')}") # calls overlap_score function
            scored.append((s, h)) # append tuple of (score, hit)
        scored.sort(key=lambda x: x[0], reverse=True) # sort descending by score
        return [h for _, h in scored] # drop the score and return only the reordered results
