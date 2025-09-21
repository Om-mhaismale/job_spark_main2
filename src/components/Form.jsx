import { useNavigate } from 'react-router-dom'

export default function Form() {
    const navigate = useNavigate()

    const handleFindJobs = () => {
        navigate('/jobs')
    }

    return (
        <>
            <button>add resume</button>
            <button onClick={() => window.location.href = 'https://jobspark-resumebuilt.vercel.app/'}>
                Re-Built Resume
            </button>
            <button onClick={handleFindJobs}>Find Jobs</button>
        </>
    )
}