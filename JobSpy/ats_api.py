from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import base64
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model3 import extract_text_from_file, score_and_rank, generate_score_explanation
from sentence_transformers import SentenceTransformer
import pandas as pd

app = Flask(__name__)
CORS(app)

# Initialize the model
model = SentenceTransformer("all-MiniLM-L6-v2")


@app.route("/api/get-ats-score", methods=["POST"])
def get_ats_score():
    try:
        data = request.json
        pdf_base64 = data.get("pdfData")
        job_description = data.get("jobDescription", "")

        if not pdf_base64:
            return jsonify({"error": "No PDF data provided"}), 400

        # Remove the data:application/pdf;base64, prefix if present
        if "base64," in pdf_base64:
            pdf_base64 = pdf_base64.split("base64,")[1]

        # Create a temporary file to save the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(base64.b64decode(pdf_base64))
            temp_pdf_path = temp_pdf.name

        # Extract text from PDF
        resume_text = extract_text_from_file(temp_pdf_path)

        if not resume_text:
            return jsonify({"error": "Could not extract text from PDF"}), 400

        # Load pre-processed resume database
        resumes_df = pd.DataFrame()
        if os.path.exists("resumes_with_vectors1.pkl"):
            resumes_df = pd.read_pickle("resumes_with_vectors1.pkl")

        # Score the resume
        user_info = {
            "text": resume_text,
            "years_exp": 1,
        }  # Default to 1 year experience
        _, user_scores = score_and_rank(
            job_description,
            3,  # Required years of experience
            [],  # Keywords will be automatically suggested
            model,
            resumes_df,
            user_info,
        )

        # Clean up the temporary file
        os.unlink(temp_pdf_path)

        # Return the score and explanation
        return jsonify(
            {
                "score": user_scores["final_score"],
                "explanation": generate_score_explanation(
                    user_scores,
                    12,  # Candidate months (1 year)
                    36,  # Required months (3 years)
                ),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)
