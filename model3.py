#
# 📜 ADVANCED ATS Resume Scorer (with Automated Keyword Suggestion)
#
# Description:
# This script scores a resume against a job description. It now AUTOMATICALLY
# suggests relevant keywords from the job description to streamline the process.
#
# Instructions:
# 1. First-time setup for keyword suggestion:
#    pip install spacy
#    python -m spacy download en_core_web_sm
# 2. Modify the USER INPUTS section.
# 3. Run the script. It will suggest keywords.
# 4. Copy the best suggestions into the `MUST_HAVE_KEYWORDS` list and re-run if needed.
#

import glob
import pandas as pd
import numpy as np
import jsonlines
import re
import os
from datetime import datetime
from collections import Counter

# --- NEW: Import spaCy for NLP ---
import spacy

# Text and File Processing
import pdfplumber
import docx

# Machine Learning
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# --- ⬇️ 1. NEW HELPER FUNCTION FOR KEYWORD SUGGESTION ⬇️ ---
def suggest_keywords_from_jd(text, top_n=15):
    """
    Analyzes job description text to suggest relevant keywords using NLP.
    """
    # List of common non-skill words to ignore
    STOP_WORDS = [
        "experience",
        "Developer",
        "team",
        "work",
        "job",
        "role",
        "company",
        "candidate",
        "skill",
        "skills",
        "requirements",
        "responsibilities",
        "knowledge",
        "ability",
        "client",
        "project",
        "projects",
        "business",
        "solution",
        "solutions",
        "system",
        "systems",
        "data",
        "product",
        "products",
        "development",
        "management",
        "analysis",
        "design",
        "report",
        "reports",
        "service",
        "services",
        "application",
        "applications",
        "inc",
    ]

    try:
        # Load the small English model for spaCy
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("❌ spaCy model 'en_core_web_sm' not found.")
        print("➡️ Please run: python -m spacy download en_core_web_sm")
        return []

    doc = nlp(text)
    keywords = []

    for token in doc:
        # Look for Proper Nouns (like 'Python', 'AWS') and all-caps words (like 'API')
        if not token.is_stop and token.text.lower() not in STOP_WORDS:
            if token.pos_ == "PROPN" or (token.is_upper and token.pos_ == "NOUN"):
                keywords.append(token.text)

    # Count frequencies and return the most common ones
    most_common_keywords = [
        word for word, count in Counter(keywords).most_common(top_n)
    ]
    return most_common_keywords


# --- [All other helper functions (generate_score_explanation, etc.) remain the same] ---
def generate_score_explanation(scores, candidate_months, required_months):
    relevance_score = scores.get("relevance_score", 0)
    experience_score = scores.get("experience_score", 0)
    keyword_score = scores.get("keyword_score", 0)
    if relevance_score > 0.7:
        relevance_reason = "Excellent semantic match..."
    elif relevance_score > 0.55:
        relevance_reason = "Good semantic match..."
    else:
        relevance_reason = "Low semantic match..."
    if keyword_score == 1.0:
        keyword_reason = "Excellent keyword match..."
    else:
        missing_keywords_str = ", ".join(scores.get("missing_keywords", []))
        keyword_reason = f"Keyword gap. Missing: {missing_keywords_str}."
    required_years = required_months / 12
    if experience_score >= 1.0:
        experience_reason = f"Excellent experience. Meets or exceeds the {required_years:.1f}-year requirement."
    else:
        experience_reason = (
            f"Low experience. Less than the required {required_years:.1f} years."
        )
    return f"🔹 Relevance: {relevance_reason}\n🔹 Keywords: {keyword_reason}\n🔹 Experience: {experience_reason}"


def calculate_keyword_score(resume_text, keywords):
    if not keywords:
        return 1.0, []
    found_count = 0
    missing = []
    for keyword in keywords:
        if re.search(r"\b" + re.escape(keyword.lower()) + r"\b", resume_text):
            found_count += 1
        else:
            missing.append(keyword)
    return found_count / len(keywords), missing


def extract_text_from_file(file_path):
    print(f"📄 Reading text from '{os.path.basename(file_path)}'...")
    text = ""
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        return text.lower()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return None


# (score_and_rank, consolidate_db_text, etc. are unchanged)
def score_and_rank(
    job_description, required_years, keywords, model, db_df, user_resume_info=None
):
    print("\n--- Scoring All Candidates ---")

    W_RELEVANCE, W_KEYWORDS, W_EXPERIENCE = 0.50, 0.30, 0.20

    query_vector = model.encode(job_description)
    db_vectors = np.vstack(db_df["resume_vector"].values)
    db_df["relevance_score"] = cosine_similarity([query_vector], db_vectors)[0]

    db_df["keyword_score"] = db_df["resume_text"].apply(
        lambda x: calculate_keyword_score(x, keywords)[0]
    )

    target_months = required_years * 12
    db_df["experience_score"] = db_df["total_months_experience"].apply(
        lambda m: min(m / target_months, 1.0) if target_months > 0 else 1.0
    )

    db_df["final_score"] = (
        (W_RELEVANCE * db_df["relevance_score"])
        + (W_KEYWORDS * db_df["keyword_score"])
        + (W_EXPERIENCE * db_df["experience_score"])
    ) * 100

    user_score_details = None
    if user_resume_info:
        user_vector = model.encode(user_resume_info["text"])
        user_relevance = cosine_similarity([query_vector], [user_vector])[0][0]
        user_keywords, missing_kws = calculate_keyword_score(
            user_resume_info["text"], keywords
        )
        user_experience = (
            min((user_resume_info["years_exp"] * 12) / target_months, 1.0)
            if target_months > 0
            else 1.0
        )

        user_final_score = (
            (W_RELEVANCE * user_relevance)
            + (W_KEYWORDS * user_keywords)
            + (W_EXPERIENCE * user_experience)
        ) * 100

        user_score_details = {
            "relevance_score": user_relevance,
            "keyword_score": user_keywords,
            "experience_score": user_experience,
            "missing_keywords": missing_kws,
            "final_score": user_final_score,
        }

    return db_df.sort_values(by="final_score", ascending=False), user_score_details


def consolidate_db_text(row):
    try:
        summary = row.get("summary", "") or ""
        skills_list = []
        if isinstance(row.get("skills"), dict) and "technical" in row["skills"]:
            for skill_cat in row["skills"]["technical"].values():
                if isinstance(skill_cat, list):
                    skills_list.extend([s.get("name", "") for s in skill_cat])
        responsibilities = []
        if isinstance(row.get("experience"), list):
            for job in row["experience"]:
                if isinstance(job.get("responsibilities"), list):
                    responsibilities.extend(job["responsibilities"])
        full_text = " ".join([summary] + list(set(skills_list)) + responsibilities)
        return re.sub(r"\s+", " ", full_text).strip().lower()
    except Exception:
        return ""


def main():
    """Main function to run the ATS scorer."""
    # --- 1. USER INPUTS ---
    JOB_DESCRIPTION = """
    We are seeking a creative and Full Stack Developer to join our innovative team. In this role, you will be responsible for developing and implementing cutting-edge, AI-powered solutions that solve real-world problems. The ideal candidate will have hands-on experience with Python, computer vision libraries like OpenCV, and NLP models such as GPT-4 to build sophisticated analytics tools. You should also be a proficient full-stack developer, with skills in front-end frameworks like React.js and Next.js, and back-end technologies including Flask and Node.js. Experience with various databases such as MySQL and MongoDB is essential. You will be expected to contribute to all phases of the development lifecycle, from concept and design to testing and deployment, and a passion for building intelligent, data-driven applications is a must.
    """
    REQUIRED_EXPERIENCE_YEARS = 3
    CANDIDATE_EXPERIENCE_YEARS = 1
    # Try environment variable first (set by your upload handler), otherwise pick the most recent uploaded resume
    uploaded_env = os.environ.get("UPLOADED_RESUME_PATH") or os.environ.get(
        "UPLOADED_FILE"
    )
    if uploaded_env and os.path.exists(uploaded_env):
        USER_RESUME_PATH = uploaded_env
    else:
        # Look in an 'uploads' folder first, then fallback to any pdf/docx/txt in cwd
        candidates = (
            glob.glob("uploads/*.*")
            + glob.glob("*.pdf")
            + glob.glob("*.docx")
            + glob.glob("*.txt")
        )
        candidates = [
            c
            for c in candidates
            if os.path.splitext(c)[1].lower() in (".pdf", ".docx", ".txt")
        ]
        if candidates:
            USER_RESUME_PATH = max(
                candidates, key=os.path.getmtime
            )  # most recently modified file
        else:
            # final fallback (keeps previous behavior)
            USER_RESUME_PATH = "professional resume.docx-2.pdf"
    print(f"📥 Using uploaded resume: {USER_RESUME_PATH}")

    # --- 2. AUTOMATED KEYWORD SUGGESTION ---
    print("🧠 Analyzing job description to suggest keywords...")
    suggested_keywords = suggest_keywords_from_jd(JOB_DESCRIPTION)
    print("✅ Suggested Keywords:", suggested_keywords)
    print(
        "➡️ Please review the list above and update the `MUST_HAVE_KEYWORDS` list below if needed.\n"
    )

    # --- 3. CONFIRM KEYWORDS ---
    MUST_HAVE_KEYWORDS = suggested_keywords

    # --- 4. LOAD AND PREPROCESS DATABASE ---
    PROCESSED_DATA_PATH = "resumes_with_vectors1.pkl"
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # --- THIS IS THE MISSING BLOCK ---
    if os.path.exists(PROCESSED_DATA_PATH):
        print(f"🚀 Found pre-processed data. Loading '{PROCESSED_DATA_PATH}'...")
        resumes_df = pd.read_pickle(PROCESSED_DATA_PATH)
    else:
        print("⏳ No pre-processed data found. Processing from scratch...")
        try:
            with jsonlines.open("master_resumes_transformed[1].jsonl") as reader:
                resumes_data = [line for line in reader]
            resumes_df = pd.DataFrame(resumes_data)
            print(f"✅ Loaded {len(resumes_df)} resumes from 'resume.jsonl'.")
        except FileNotFoundError:
            print(
                "⚠️ 'resume.jsonl' not found. Ranking against other candidates will be skipped."
            )
            resumes_df = pd.DataFrame()

        if not resumes_df.empty:
            resumes_df["total_months_experience"] = resumes_df["experience"].apply(
                lambda x: sum(
                    int(
                        re.search(
                            r"(\d+)", job.get("dates", {}).get("duration", "0")
                        ).group(1)
                    )
                    for job in x
                    if isinstance(x, list)
                )
            )
            resumes_df["resume_text"] = resumes_df.apply(consolidate_db_text, axis=1)
            resumes_df.dropna(subset=["resume_text"], inplace=True)
            resumes_df = resumes_df[resumes_df["resume_text"].str.strip() != ""].copy()
            resumes_df["resume_vector"] = resumes_df["resume_text"].apply(
                lambda x: model.encode(x)
            )
            resumes_df.to_pickle(PROCESSED_DATA_PATH)
            print(f"✅ Saved processed data to '{PROCESSED_DATA_PATH}'.")

    # --- 5. ANALYZE AND SCORE ---
    print("\n" + "=" * 50 + "\nANALYZING YOUR RESUME\n" + "=" * 50)
    user_resume_text = extract_text_from_file(USER_RESUME_PATH)

    if user_resume_text:
        user_info = {"text": user_resume_text, "years_exp": CANDIDATE_EXPERIENCE_YEARS}

        # Pass the correct resumes_df to the function
        ranked_candidates, user_scores = score_and_rank(
            JOB_DESCRIPTION,
            REQUIRED_EXPERIENCE_YEARS,
            MUST_HAVE_KEYWORDS,
            model,
            resumes_df,
            user_info,
        )

        user_score_reason = generate_score_explanation(
            user_scores, CANDIDATE_EXPERIENCE_YEARS * 12, REQUIRED_EXPERIENCE_YEARS * 12
        )

        print("\n" + "⭐" * 15 + " YOUR ATS SCORE " + "⭐" * 15)
        print(f"FINAL SCORE: {user_scores['final_score']:.1f} / 100")
        print("-" * 55)
        print(f"Score Breakdown & Reasoning:\n{user_score_reason}")
        print("⭐" * 55)
    else:
        print("Could not process the user resume.")


if __name__ == "__main__":
    main()
