export default function Form() {
    return (
        <>
            <button>add resume</button>
            <button onClick={() => window.open('https://jobspark-resumebuilt.vercel.app/', '_blank')}>
                Re-write Resume
            </button>
            <button>Find Jobs</button>
        </>
    )
}