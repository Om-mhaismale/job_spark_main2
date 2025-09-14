export default function Form() {
    return (
        <>
            <button>add resume</button>
            <button onClick={() => window.location.href = 'https://jobspark-resumebuilt.vercel.app/'}>
                Re-Built Resume
            </button>

            <button>Find Jobs</button>
        </>
    )
}