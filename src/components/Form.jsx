export default function Form() {
    return (
        <>
            <button>add resume</button>
            <button onClick={() => window.open('https://jobspark-resumebuilt.vercel.app/')}>
                Re-write Resume
            </button>
            <button>Find Jobs</button>
        </>
    )
}