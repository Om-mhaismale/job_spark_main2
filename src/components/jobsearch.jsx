import { useState, useCallback, useMemo } from 'react'
import React from 'react'
import '../styles/jobsearch.css'

export default function JobSearch() {
    const [searchTerm, setSearchTerm] = useState('')
    const [location, setLocation] = useState('')
    const [jobs, setJobs] = useState([])
    const [loading, setLoading] = useState(false)
    const [page, setPage] = useState(1)
    const [hasMore, setHasMore] = useState(false)
    const [error, setError] = useState('')

    // Memoized search function to prevent unnecessary re-renders
    const searchJobs = useCallback(async (pageNum = 1, appendResults = false) => {
        setLoading(true)
        setError('')
        
        try {
            const response = await fetch('http://localhost:5000/api/jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    search_term: searchTerm.trim() || 'software engineer',
                    location: location.trim() || 'India',
                    page: pageNum
                })
            })
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
            
            const data = await response.json()
            
            if (data.error) {
                throw new Error(data.error)
            }
            
            if (appendResults) {
                setJobs(prev => [...prev, ...data.jobs])
            } else {
                setJobs(data.jobs)
            }
            
            setHasMore(data.has_more)
            setPage(pageNum)
        } catch (error) {
            console.error('Error fetching jobs:', error)
            setError(error.message)
        } finally {
            setLoading(false)
        }
    }, [searchTerm, location])

    const handleSearch = useCallback(() => {
        if (!searchTerm.trim()) {
            setError('Please enter a job title or keywords')
            return
        }
        setPage(1)
        setJobs([]) // Clear previous results
        searchJobs(1, false)
    }, [searchJobs, searchTerm])

    const handleLoadMore = useCallback(() => {
        const nextPage = page + 1
        searchJobs(nextPage, true)
    }, [searchJobs, page])

    // Memoized job cards to prevent unnecessary re-renders
    const jobCards = useMemo(() => 
        jobs.map((job, index) => (
            <JobCard key={`${job.company}-${job.title}-${index}`} job={job} />
        )), [jobs]
    )

    return (
        <div className="job-search-container">
            <div className="search-header">
                <h1 className="page-title">Find Your Dream Job</h1>
                <p className="page-subtitle">Search from thousands of opportunities</p>
            </div>
            
            {/* Search Form */}
            <div className="search-form">
                <div className="input-group">
                    <div className="input-container">
                        <input 
                            type="text" 
                            placeholder="Job title, keywords, or company..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="search-input"
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        />
                        <span className="input-icon">🔍</span>
                    </div>
                    
                    <div className="input-container">
                        <input 
                            type="text" 
                            placeholder="Location (city, state, country)..."
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            className="search-input"
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        />
                        <span className="input-icon">📍</span>
                    </div>
                    
                    <button 
                        onClick={handleSearch}
                        disabled={loading}
                        className={`search-btn ${loading ? 'loading' : ''}`}
                    >
                        {loading ? (
                            <div className="spinner"></div>
                        ) : (
                            'Search Jobs'
                        )}
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="error-message">
                    <span className="error-icon">⚠️</span>
                    {error}
                </div>
            )}

            {/* Results Count */}
            {jobs.length > 0 && !loading && (
                <div className="results-count">
                    Found {jobs.length} job{jobs.length !== 1 ? 's' : ''} 
                    {searchTerm && ` for "${searchTerm}"`}
                    {location && ` in ${location}`}
                </div>
            )}

            {/* Job Results */}
            <div className="jobs-container">
                {jobCards}
            </div>

            {/* Load More Button */}
            {hasMore && jobs.length > 0 && (
                <div className="load-more-container">
                    <button 
                        onClick={handleLoadMore}
                        disabled={loading}
                        className={`load-more-btn ${loading ? 'loading' : ''}`}
                    >
                        {loading ? (
                            <>
                                <div className="spinner small"></div>
                                Loading more jobs...
                            </>
                        ) : (
                            'Load More Jobs'
                        )}
                    </button>
                </div>
            )}

            {/* No Results */}
            {jobs.length === 0 && !loading && searchTerm && !error && (
                <div className="no-results">
                    <div className="no-results-icon">🔍</div>
                    <h3>No jobs found</h3>
                    <p>Try adjusting your search criteria or location</p>
                </div>
            )}
        </div>
    )
}

// Optimized JobCard component with memo
const JobCard = React.memo(({ job }) => (
    <div className="job-card">
        <div className="job-header">
            <h3 className="job-title">{job.title}</h3>
            <div className="company-info">
                <span className="company-name">{job.company}</span>
                <span className="job-location">📍 {job.location}</span>
            </div>
        </div>
        
        <div className="job-details">
            {job.salary && job.salary !== 'N/A' && (
                <div className="salary-info">
                    💰 {job.salary}
                </div>
            )}
            
            {job.description && (
                <p className="job-description">{job.description}</p>
            )}
        </div>
        
        <div className="job-actions">
            {job.date_posted && job.date_posted !== 'N/A' && (
                <span className="post-date">📅 {job.date_posted}</span>
            )}
            {job.job_url && (
                <a 
                    href={job.job_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="apply-btn"
                >
                    Apply Now →
                </a>
            )}
        </div>
    </div>
))