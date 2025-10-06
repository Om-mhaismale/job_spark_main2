import { useClerk, UserButton, useUser } from "@clerk/clerk-react"

export default function Header() {
    const {user} = useUser();
    const {openSignIn} = useClerk();
    return (<>
    <header> 
        <div className="header-content">
            <img src="./job_spark/src/assets/react.svg" alt="" />
            <h1>Job Spark</h1>
            </div>
        {/* <nav>
                <a href="#home">Home</a>
                <a href="#jobs">Jobs</a>
                <a href="#about">About Us</a>
                <a href="#contact">Contact</a>
        </nav> */}
        {
            !user ?(<button onClick={openSignIn} className="sign-in-button">
            Sign In
        </button> ) :(
            <UserButton></UserButton>
        )
        }
          
    </header>
  </>
        
    )
}