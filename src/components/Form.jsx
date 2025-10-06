import { useNavigate } from 'react-router-dom'

export default function Form() {
    const navigate = useNavigate()

    const handleFindJobs = () => {
        navigate('/jobs')
    }

    return (
        <>
            <button className='nav-btn'>
                ATS SCORE
            </button>
            <button className='nav-btn' onClick={() => window.location.href = 'https://jobspark-resumebuilt.vercel.app/'}>
                Re-Build Resume
            </button>
            <button className='nav-btn' onClick={handleFindJobs}>
                Find Jobs
            </button>
        </>
    )
}