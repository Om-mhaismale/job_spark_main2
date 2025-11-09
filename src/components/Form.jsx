import { useNavigate } from 'react-router-dom'

export default function Form() {
    const navigate = useNavigate()

    const handleFindJobs = () => {
        navigate('/jobs')
    }
    const handleAtsScore = () => {
        navigate('/ats-score')
    }

    return (
        <div className="form-container">
            <button className='nav-btn ats-btn' onClick={handleAtsScore}>
                ATS SCORE
            </button>
            <button className='nav-btn' onClick={() => window.location.href = 'https://jobspark-resumebuilt.vercel.app/'}>
                Re-Build Resume
            </button>
            <button className='nav-btn' onClick={handleFindJobs}>
                Find Jobs
            </button>
        </div>
    )
}