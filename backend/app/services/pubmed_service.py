import httpx

from ..core.config import PUBMED_API_KEY

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

SEARCH_TERM = "breast cancer"


def _params(extra: dict) -> dict:
    params = {"tool": "breastai-sns-pipeline", **extra}
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY
    return params


def fetch_latest_papers(max_results: int = 5) -> list[dict]:
    with httpx.Client(timeout=15) as client:
        search_response = client.get(
            ESEARCH_URL,
            params=_params(
                {
                    "db": "pubmed",
                    "term": SEARCH_TERM,
                    "sort": "most recent",
                    "retmax": max_results,
                    "retmode": "json",
                }
            ),
        )
        search_response.raise_for_status()
        pmids = search_response.json().get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []

        summary_response = client.get(
            ESUMMARY_URL,
            params=_params(
                {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": "json",
                }
            ),
        )
        summary_response.raise_for_status()
        result = summary_response.json().get("result", {})

    papers = []
    for pmid in pmids:
        doc = result.get(pmid)
        if not doc:
            continue
        papers.append(
            {
                "pmid": pmid,
                "title": doc.get("title", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "published_date": doc.get("pubdate"),
            }
        )
    return papers
