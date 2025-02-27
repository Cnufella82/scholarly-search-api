from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Scholarly Search API!"}

@app.get("/search")
def search_papers(query: str, limit: int = 10):
    return {"query": query, "limit": limit, "results": []}


# API Endpoints for CrossRef, Semantic Scholar, and CORE
CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
CORE_API = "https://api.core.ac.uk/v3/search/works"

# Add your CORE API key if required
CORE_API_KEY = "YOUR_CORE_API_KEY"

def fetch_crossref(query, limit):
    """Fetch papers from CrossRef"""
    params = {"query": query, "rows": limit}
    response = requests.get(CROSSREF_API, params=params)
    if response.status_code == 200:
        data = response.json()
        return [
            {
                "title": item["title"][0] if "title" in item else "No title",
                "authors": [author["given"] + " " + author["family"] for author in item.get("author", [])],
                "abstract": None,
                "doi": item.get("DOI"),
                "url": item["URL"] if "URL" in item else None,
                "source": "CrossRef"
            }
            for item in data.get("message", {}).get("items", [])
        ]
    return []

def fetch_semantic_scholar(query, limit):
    """Fetch papers from Semantic Scholar"""
    params = {"query": query, "limit": limit, "fields": "title,authors,abstract,doi,url"}
    response = requests.get(SEMANTIC_SCHOLAR_API, params=params)
    if response.status_code == 200:
        data = response.json()
        return [
            {
                "title": item["title"],
                "authors": [author["name"] for author in item.get("authors", [])],
                "abstract": item.get("abstract"),
                "doi": item.get("doi"),
                "url": item.get("url"),
                "source": "Semantic Scholar"
            }
            for item in data.get("data", [])
        ]
    return []

def fetch_core(query, limit):
    """Fetch papers from CORE"""
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"} if CORE_API_KEY else {}
    params = {"q": query, "limit": limit}
    response = requests.get(CORE_API, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return [
            {
                "title": item.get("title", "No title"),
                "authors": item.get("authors", []),
                "abstract": item.get("abstract"),
                "doi": item.get("doi"),
                "url": item.get("downloadUrl") or item.get("fullTextUrl"),
                "source": "CORE"
            }
            for item in data.get("results", [])
        ]
    return []

def merge_results(results):
    """Merge results from all sources, avoiding duplicate DOIs"""
    merged = {}
    for paper in results:
        doi = paper.get("doi")
        key = doi if doi else paper["title"].lower()
        if key not in merged:
            merged[key] = paper
    return list(merged.values())

@app.get("/search")
def search_papers(query: str = Query(..., description="Search query"), limit: int = Query(10, description="Max results")):
    """Unified search across CrossRef, Semantic Scholar, and CORE"""
    results = []
    
    results.extend(fetch_crossref(query, limit))
    results.extend(fetch_semantic_scholar(query, limit))
    results.extend(fetch_core(query, limit))
    
    merged_results = merge_results(results)
    
    return {
        "query": query,
        "results": merged_results[:limit]  # Trim results to match limit
    }
