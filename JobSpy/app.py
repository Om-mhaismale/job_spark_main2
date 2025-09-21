from flask import Flask, request, jsonify
from flask_cors import CORS
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import time
import random

app = Flask(__name__)
CORS(app)

# In-memory cache (for production, use Redis)
job_cache = {}
CACHE_DURATION = 600  # 10 minutes (increased for better efficiency)

# Site rotation and fallback strategy
PRIMARY_SITES = ["linkedin", "indeed", "google"]
SECONDARY_SITES = ["zip_recruiter", "glassdoor", "naukri"]
BACKUP_SITES = ["bayt", "bdjobs"]

# Rate limiting per site (to avoid token exhaustion)
site_last_used = {}
SITE_COOLDOWN = 60  # 1 minute cooldown between requests per site

def get_cache_key(search_term, location):
    """Generate cache key for search parameters"""
    key_string = f"{search_term.lower()}_{location.lower()}"
    return hashlib.md5(key_string.encode()).hexdigest()

def is_cache_valid(cache_entry):
    """Check if cache entry is still valid"""
    return datetime.now() - cache_entry['timestamp'] < timedelta(seconds=CACHE_DURATION)

def get_available_sites(max_sites=3):
    """Get available sites based on cooldown and rotation"""
    current_time = time.time()
    available_sites = []
    
    # Check primary sites first
    for site in PRIMARY_SITES:
        last_used = site_last_used.get(site, 0)
        if current_time - last_used > SITE_COOLDOWN:
            available_sites.append(site)
            if len(available_sites) >= max_sites:
                return available_sites
    
    # Add secondary sites if needed
    for site in SECONDARY_SITES:
        last_used = site_last_used.get(site, 0)
        if current_time - last_used > SITE_COOLDOWN:
            available_sites.append(site)
            if len(available_sites) >= max_sites:
                return available_sites
    
    # Add backup sites if still needed
    for site in BACKUP_SITES:
        last_used = site_last_used.get(site, 0)
        if current_time - last_used > SITE_COOLDOWN:
            available_sites.append(site)
            if len(available_sites) >= max_sites:
                return available_sites
    
    # If no sites available due to cooldown, use primary sites anyway
    return PRIMARY_SITES[:max_sites] if not available_sites else available_sites

def scrape_with_fallback(search_term, location, max_attempts=3):
    """Scrape jobs with fallback strategy"""
    jobs_df = pd.DataFrame()
    attempts = 0
    
    while jobs_df.empty and attempts < max_attempts:
        attempts += 1
        
        # Get available sites for this attempt
        sites_to_try = get_available_sites(max_sites=2 + attempts)  # Increase sites per attempt
        
        print(f"Attempt {attempts}: Trying sites {sites_to_try}")
        
        try:
            # Update last used time for selected sites
            current_time = time.time()
            for site in sites_to_try:
                site_last_used[site] = current_time
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            jobs_df = scrape_jobs(
                site_name=sites_to_try,
                search_term=search_term,
                location=location or "USA",
                results_wanted=30,  # Reduced to avoid overwhelming APIs
                hours_old=168,
                country_indeed='USA' if 'indeed' in sites_to_try else None,
            )
            
            if not jobs_df.empty:
                print(f"✅ Success with sites: {sites_to_try}")
                break
                
        except Exception as e:
            print(f"❌ Attempt {attempts} failed with sites {sites_to_try}: {str(e)}")
            
            # If specific site fails, mark it with longer cooldown
            for site in sites_to_try:
                if "429" in str(e) or "rate" in str(e).lower():
                    site_last_used[site] = current_time + 300  # 5 minute penalty
            
            if attempts < max_attempts:
                wait_time = 2 ** attempts  # Exponential backoff
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    return jobs_df

@app.route('/api/jobs', methods=['POST'])
def search_jobs():
    try:
        data = request.get_json()
        search_term = data.get('search_term', '').strip()
        location = data.get('location', '').strip()
        page = data.get('page', 1)
        results_per_page = 10
        
        # Validate inputs
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400
        
        # Generate cache key
        cache_key = get_cache_key(search_term, location)
        
        # Check cache first
        if cache_key in job_cache and is_cache_valid(job_cache[cache_key]):
            print(f"🎯 Cache hit for: {search_term} in {location}")
            jobs_list = job_cache[cache_key]['jobs']
            used_sites = job_cache[cache_key].get('sites', [])
        else:
            print(f"🔍 Cache miss - Scraping for: {search_term} in {location}")
            
            # Scrape with fallback strategy
            jobs_df = scrape_with_fallback(search_term, location)
            
            # Check if we got any results
            if jobs_df.empty:
                return jsonify({
                    'jobs': [],
                    'total': 0,
                    'has_more': False,
                    'message': 'No jobs found. All job sites may be temporarily unavailable.',
                    'retry_after': 60
                })
            
            # Convert and clean data
            jobs_list = []
            used_sites = jobs_df['site'].unique().tolist() if 'site' in jobs_df.columns else []
            
            for _, job in jobs_df.iterrows():
                # Enhanced data cleaning
                description = str(job.get('description', 'No description available'))
                if len(description) > 200:
                    description = description[:200] + '...'
                
                # Better salary handling
                salary = None
                if job.get('salary_min') and job.get('salary_max'):
                    salary = f"${job.get('salary_min')}-${job.get('salary_max')}"
                elif job.get('salary_min'):
                    salary = f"${job.get('salary_min')}+"
                elif job.get('salary_max'):
                    salary = f"Up to ${job.get('salary_max')}"
                else:
                    salary = job.get('salary', 'N/A')
                
                cleaned_job = {
                    'title': job.get('title', 'N/A'),
                    'company': job.get('company', 'N/A'),
                    'location': job.get('location', 'N/A'),
                    'salary': salary,
                    'job_url': job.get('job_url', ''),
                    'description': description,
                    'date_posted': str(job.get('date_posted', 'N/A')),
                    'site': job.get('site', 'N/A'),
                    'job_type': job.get('job_type', 'N/A')
                }
                jobs_list.append(cleaned_job)
            
            # Cache the results with metadata
            job_cache[cache_key] = {
                'jobs': jobs_list,
                'sites': used_sites,
                'timestamp': datetime.now()
            }
            
            print(f"✅ Cached {len(jobs_list)} jobs from sites: {used_sites}")
        
        # Paginate cached results
        start_idx = (page - 1) * results_per_page
        end_idx = start_idx + results_per_page
        page_jobs = jobs_list[start_idx:end_idx]
        
        return jsonify({
            'jobs': page_jobs,
            'total': len(jobs_list),
            'current_page': page,
            'has_more': end_idx < len(jobs_list),
            'sources': used_sites,
            'cached': cache_key in job_cache,
            'cache_expires_in': CACHE_DURATION - int((datetime.now() - job_cache[cache_key]['timestamp']).total_seconds()) if cache_key in job_cache else 0
        })
        
    except Exception as e:
        print(f"💥 Critical Error: {str(e)}")
        return jsonify({
            'error': f'Service temporarily unavailable: {str(e)}',
            'retry_after': 120
        }), 503

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'API is running',
        'cache_size': len(job_cache),
        'site_cooldowns': {site: max(0, int(cooldown - time.time())) 
                          for site, cooldown in site_last_used.items()},
        'available_sites': get_available_sites(max_sites=10)
    })

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    global job_cache, site_last_used
    job_cache = {}
    site_last_used = {}
    return jsonify({'message': 'Cache and cooldowns cleared'})

if __name__ == '__main__':
    print("🚀 Starting Job Search API on http://localhost:5000")
    print(f"📊 Available job sites: {PRIMARY_SITES + SECONDARY_SITES + BACKUP_SITES}")
    app.run(debug=True, port=5000, threaded=True)