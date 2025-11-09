import { useState } from 'react';
import '../styles/atsScore.css';

export default function AtsScorePage() {
    const [pdfFile, setPdfFile] = useState(null);
    const [showProgress, setShowProgress] = useState(false);
    const [progress, setProgress] = useState(0);
    const [score, setScore] = useState(null);

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file && file.type === 'application/pdf') {
            setPdfFile(URL.createObjectURL(file));
        }
    };

    const handleGetScore = async () => {
        if (!pdfFile) {
            alert('Please upload a PDF first');
            return;
        }

        setShowProgress(true);
        setProgress(0);

        // Simulate progress while waiting for the actual score
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
            // TODO: Replace with actual API call to your Python backend
            const response = await fetch('/api/get-ats-score', {
                method: 'POST',
                body: JSON.stringify({ pdfUrl: pdfFile }),
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            // Complete the progress bar
            setProgress(100);
            setTimeout(() => {
                setShowProgress(false);
                setScore(data.score);
            }, 500);
        } catch (error) {
            console.error('Error getting score:', error);
            setShowProgress(false);
            alert('Error getting score. Please try again.');
        } finally {
            clearInterval(progressInterval);
        }
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
