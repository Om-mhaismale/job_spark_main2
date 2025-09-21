from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from jobspy import scrape_jobs
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/jobs")
def get_jobs(
    keywords: str = Query(..., description="Search term"),
    location: str = Query("", description="Location"),
    results: int = Query(20, description="Number of results"),
):
    google_search_term = f"{keywords} jobs near {location} since yesterday"
    
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "zip_recruiter", "google"],
        search_term=keywords,
        google_search_term=google_search_term,
        location=location,
        results_wanted=results,
        hours_old=72,
        country_indeed='USA',
    )
    
    # Replace NaN/inf with None
    jobs = jobs.replace({np.nan: None, np.inf: None, -np.inf: None})
    
    return jobs.to_dict(orient='records')
