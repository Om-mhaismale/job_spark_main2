import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header.jsx'
import Content from './components/Content.jsx'
import Form from './components/Form.jsx'
import JobSearch from './components/jobsearch.jsx'
import AtsScorePage from './pages/AtsScorePage.jsx'

function App() {
  return (
    <Router>
      <Header/>
      <Routes>
        <Route path="/" element={
          <>
            <Content/>
            <Form/>
          </>
        } />
        <Route path="/jobs" element={<JobSearch/>} />
        <Route path="/ats-score" element={<AtsScorePage/>} />
      </Routes>
    </Router>
  )
}

export default App
