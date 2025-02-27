from fastapi import FastAPI, Query
import requests

app = FastAPI()

# API Endpoints
CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
CORE_API = "https://api.core.ac.uk/v3/search/works"

# Add your CORE API key if required
CORE_API_KEY = "YOUR_CORE_API_KEY"

@app.get("/")
def read_root():
    return {"message": "Welcome to the Scholarly Search API!"}

@app.get("/search")
def search_papers(query: str = Query(..., description="Search query"), limit: int = 10):
    """Fetch papers from CrossRef, Semantic Scholar, and CORE"""
    results = []

    # CrossRef API call
    crossref_params = {"query": query, "rows": limit}
    crossref_response = requests.get(CROSSREF_API, params=crossref_params)
    if crossref_response.status_code == 200:
        crossref_data = crossref_response.json()
        results.extend([
            {
                "title": item["title"][0] if "title" in item else "No title",
                "authors": [author["given"] + " " + author["family"] for author in item.get("author", [])],
                "abstract": None,
                "doi": item.get("DOI"),
                "url": item.get("URL"),
                "source": "CrossRef"
            }
            for item in crossref_data.get("message", {}).get("items", [])
        ])

    # Semantic Scholar API call
    semscholar_params = {"query": query, "limit": limit, "fields": "title,authors,abstract,doi,url"}
    semscholar_response = requests.get(SEMANTIC_SCHOLAR_API, params=semscholar_params)
    if semscholar_response.status_code == 200:
        semscholar_data = semscholar_response.json()
        results.extend([
            {
                "title": item["title"],
                "authors": [author["name"] for author in item.get("authors", [])],
                "abstract": item.get("abstract"),
                "doi": item.get("doi"),
                "url": item.get("url"),
                "source": "Semantic Scholar"
            }
            for item in semscholar_data.get("data", [])
        ])

    # CORE API call
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"} if CORE_API_KEY else {}
    core_params = {"q": query, "limit": limit}
    core_response = requests.get(CORE_API, headers=headers, params=core_params)
    if core_response.status_code == 200:
        core_data = core_response.json()
        results.extend([
            {
                "title": item.get("title", "No title"),
                "authors": item.get("authors", []),
                "abstract": item.get("abstract"),
                "doi": item.get("doi"),
                "url": item.get("downloadUrl") or item.get("fullTextUrl"),
                "source": "CORE"
            }
            for item in core_data.get("results", [])
        ])

    return {"query": query, "limit": limit, "results": results}
