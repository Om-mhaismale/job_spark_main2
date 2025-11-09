import { useState } from 'react';
import '../styles/atsScore.css';

export default function AtsScorePage() {
    const [pdfFile, setPdfFile] = useState(null);

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file && file.type === 'application/pdf') {
            setPdfFile(URL.createObjectURL(file));
        }
    };

    const handleGetScore = () => {
        // Add your scoring logic here
        console.log('Getting ATS score...');
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
                    <iframe
                        src={pdfFile}
                        className="pdf-preview"
                        title="PDF Preview"
                    />
                )}
            </div>
        </div>
    );
}
