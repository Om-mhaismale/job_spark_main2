import { useState } from 'react';
import '../styles/atsScore.css';

export default function AtsScorePage() {
    const [pdfFile, setPdfFile] = useState(null);
    const [showProgress, setShowProgress] = useState(false);
    const [progress, setProgress] = useState(0);
    const [score, setScore] = useState(null);
    const [jobDescription, setJobDescription] = useState('');
    const [explanation, setExplanation] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file && file.type === 'application/pdf') {
            setPdfFile(URL.createObjectURL(file));
            setSelectedFile(file);
        }
    };

    const handleGetScore = async () => {
        if (!selectedFile) {
            alert('Please upload a PDF first');
            return;
        }

        setShowProgress(true);
        setProgress(0);

        // Convert PDF to base64
        const reader = new FileReader();
        reader.readAsDataURL(selectedFile);
        
        reader.onload = async () => {
            const base64PDF = reader.result;
            
            // Simulate initial progress
            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 500);

            try {
                const response = await fetch('http://localhost:5000/api/get-ats-score', {
                    method: 'POST',
                    body: JSON.stringify({ 
                        pdfData: base64PDF,
                        jobDescription: jobDescription 
                    }),
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
            
                // Complete the progress bar
                setProgress(100);
                setTimeout(() => {
                    setShowProgress(false);
                    setScore(data.score);
                    setExplanation(data.explanation);
                }, 500);
            } catch (error) {
                console.error('Error getting score:', error);
                setShowProgress(false);
                alert('Error getting score. Please try again.');
            } finally {
                clearInterval(progressInterval);
            }
        };
    };

    return (
        <div className="ats-page">
            <div className="sidebar">
                <div></div> {/* Empty div for spacing */}
                <div className="sidebar-buttons">
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileUpload}
                        style={{ display: 'none' }}
                        id="pdf-upload"
                    />
                    <label htmlFor="pdf-upload" className="sidebar-btn">
                        Upload PDF
                    </label>
                    <textarea
                        className="sidebar-textarea"
                        placeholder="Paste job description here..."
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                    />
                    <button className="sidebar-btn" onClick={handleGetScore}>
                        Get Score
                    </button>
                </div>
            </div>
            <div className="main-content">
                {!pdfFile ? (
                    <div className="upload-area">
                        <label htmlFor="pdf-upload" className="upload-btn">
                            Upload PDF
                        </label>
                        <p className="upload-text">Upload your resume in PDF format</p>
                    </div>
                ) : (
                    <>
                        <iframe
                            src={pdfFile}
                            className="pdf-preview"
                            title="PDF Preview"
                        />
                        {score && (
                            <div className="score-overlay">
                                <h2>Your Resume Scored: {score.toFixed(1)}</h2>
                                {explanation && (
                                    <div className="score-explanation">
                                        <p>{explanation}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}

                {showProgress && (
                    <div className="progress-modal">
                        <div className="progress-content">
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill"
                                    style={{ width: `${progress}%` }}
                                ></div>
                            </div>
                            <p>Analyzing your resume... {progress}%</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}