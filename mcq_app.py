import streamlit as st
import json
import os
from groq import Groq
from utils import generate_markdown, generate_anki, generate_single_question
from pdf_parser import extract_text_from_pdf

st.set_page_config(page_title="QuizLab - PDF & Text MCQ Generator", page_icon="🧠", layout="centered")

# ── Theme Styling (Glassmorphic / Cyberpunk) ──────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Syne:wght@500;700;800&display=swap');

/* Global Font Settings */
* {
    font-family: 'Outfit', sans-serif;
}

h1, h2, h3, .hero-title {
    font-family: 'Syne', sans-serif;
}

/* Background gradient */
.stApp {
    background: radial-gradient(circle at 50% 50%, #0d0f1a 0%, #050608 100%) !important;
    color: #e2e8f0 !important;
}

/* Main title styling */
.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 50%, #bd00ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.03em;
    filter: drop-shadow(0px 4px 20px rgba(0, 240, 255, 0.15));
}

.hero-sub {
    font-size: 1.1rem;
    color: #94a3b8;
    text-align: center;
    margin-bottom: 2.5rem;
    font-weight: 400;
}

/* Glassmorphic Side Bar */
section[data-testid="stSidebar"] {
    background-color: rgba(10, 12, 18, 0.7) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(12px) !important;
}

section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00f0ff !important;
    font-weight: 700;
    margin-top: 1rem;
}

/* Glassmorphic Card Container */
.mcq-card {
    background: rgba(20, 26, 38, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(8px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mcq-card:hover {
    border-color: rgba(204, 255, 0, 0.2);
    box-shadow: 0 12px 40px 0 rgba(204, 255, 0, 0.05);
}

.q-number {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 800;
    color: #ccff00;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.q-text {
    font-size: 1.15rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}

/* Option styling for completed answers */
.option {
    padding: 14px 20px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 1rem;
    color: #cbd5e1;
    background: rgba(15, 20, 30, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    transition: all 0.25s ease;
}

.option.correct {
    background: rgba(16, 185, 129, 0.12) !important;
    border-color: #10b981 !important;
    color: #10b981 !important;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.15) !important;
    font-weight: 600;
}

.option.wrong {
    background: rgba(239, 68, 68, 0.12) !important;
    border-color: #ef4444 !important;
    color: #ef4444 !important;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.15) !important;
    font-weight: 600;
}

/* Explanation block */
.explanation {
    margin-top: 15px;
    padding: 12px 18px;
    background: rgba(204, 255, 0, 0.05);
    border-left: 4px solid #ccff00;
    border-radius: 0 12px 12px 0;
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.6;
}

/* Performance Analytics Score Box */
.score-box {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 20px;
    padding: 2.2rem;
    text-align: center;
    margin-bottom: 2.5rem;
    box-shadow: 0 10px 30px rgba(0, 240, 255, 0.08);
}

.score-number {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 5px;
}

.score-label {
    font-size: 1.05rem;
    color: #94a3b8;
    font-weight: 500;
}

/* Difficulty Badges */
.diff-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    font-family: 'Syne', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.diff-easy { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.diff-medium { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.diff-hard { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

/* Transparent Header to remove the white bar in light mode */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Force light colors on all labels, descriptions, and markdown paragraphs */
label, p[data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] p {
    color: #e2e8f0 !important;
}

/* Customizing Streamlit widgets inputs & selectboxes */
div[data-testid="stFileUploader"] {
    background: rgba(20, 26, 38, 0.4) !important;
    border: 2px dashed rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    padding: 1.5rem !important;
    transition: border-color 0.3s;
    color: #e2e8f0 !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: rgba(0, 240, 255, 0.4) !important;
}

/* Style the uploaded file list container to be dark and match the theme */
div[data-testid*="UploadedFile"], div[class*="stUploadedFile"] {
    background-color: rgba(15, 20, 30, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
}
div[data-testid*="UploadedFile"] span, div[class*="stUploadedFile"] span {
    color: #ffffff !important;
}

/* Streamlit Buttons style override (Global) */
.stButton > button {
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 100%) !important;
    color: #050608 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    font-size: 1rem !important;
    width: 100%;
    box-shadow: 0 4px 15px rgba(0, 240, 255, 0.25) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Ensure inner text elements inside main gradient buttons are dark charcoal for high contrast */
.stButton > button p, 
.stButton > button span, 
.stButton > button div {
    color: #050608 !important;
    font-weight: 800 !important;
}

.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(0, 240, 255, 0.45) !important;
    transform: translateY(-2px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Sidebar main buttons (like Submit Quiz) */
section[data-testid="stSidebar"] .stButton > button {
    padding: 0.5rem 1.2rem !important;
    font-size: 0.95rem !important;
    border-radius: 8px !important;
    transform: none !important;
    box-shadow: 0 4px 10px rgba(0, 240, 255, 0.15) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: none !important;
}

/* Sidebar grid jump buttons (inside columns) */
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] .stButton > button {
    padding: 6px 10px !important;
    font-size: 0.88rem !important;
    border-radius: 8px !important;
    height: 38px !important;
    min-height: unset !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
}

/* Inactive jump buttons */
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"] p,
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"] span,
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"] div {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(0, 240, 255, 0.3) !important;
}
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover p,
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover span,
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover div {
    color: #00f0ff !important;
}

/* Active jump button */
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="primary"] {
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 100%) !important;
    color: #050608 !important;
    border: none !important;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
}

/* Secondary Button (Download buttons, reset buttons) */
div.stDownloadButton > button {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.5rem !important;
    font-size: 0.9rem !important;
    width: 100%;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}

div.stDownloadButton > button:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(0, 240, 255, 0.3) !important;
    color: #00f0ff !important;
}

/* Interactive Radio Override CSS */
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 10px !important;
    width: 100% !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label {
    display: flex !important;
    align-items: center !important;
    background: rgba(15, 20, 30, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    padding: 14px 20px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
    width: 100% !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    background: rgba(30, 38, 55, 0.6) !important;
    border-color: rgba(0, 240, 255, 0.3) !important;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.1) !important;
    transform: translateY(-2px) !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    background: rgba(0, 240, 255, 0.08) !important;
    border-color: #00f0ff !important;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.2) !important;
}

/* Hide Streamlit's default radio circle button */
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

/* Option letter and text format */
div[data-testid="stRadio"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
    font-size: 1rem !important;
    color: #e2e8f0 !important;
    font-weight: 500 !important;
    margin: 0 !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
    color: #00f0ff !important;
    font-weight: 600 !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) div[data-testid="stMarkdownContainer"] p::before {
    content: "⚡  ";
    color: #00f0ff;
    font-weight: 800;
}

/* Style selects, inputs, and textareas to remain dark even in light mode */
div[data-baseweb="select"] > div {
    background-color: rgba(15, 20, 30, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, input {
    background-color: rgba(15, 20, 30, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Title & Header ────────────────────────────────────────────────
st.markdown('<p class="hero-title">QuizLab</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Generate premium AI-crafted MCQs from any PDF or text.</p>', unsafe_allow_html=True)

# ── Sidebar Settings & Configurations ─────────────────────────────
# Read API key silently from secrets/env (do not expose in UI)
api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))

st.sidebar.markdown("### 🧠 Quiz Mode")
quiz_mode = st.sidebar.radio("Mode Selection", ["Classic Mode", "Adaptive Difficulty 🧠"], help="Classic generates all questions upfront. Adaptive adjusts difficulty dynamically based on your correctness.")

st.sidebar.markdown("### 🛠️ Generation Rules")
num_mcqs = st.sidebar.slider("Number of Questions", min_value=3, max_value=20, value=5, step=1)

if quiz_mode == "Adaptive Difficulty 🧠":
    difficulty = st.sidebar.selectbox("Starting Difficulty", ["Easy", "Medium", "Hard"], index=1)
else:
    difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)

custom_focus = st.sidebar.text_input("Custom Focus / Topic (Optional)", placeholder="e.g. key dates, definitions, math")

# Hardcode the model backend
model_name = "llama-3.3-70b-versatile"

diff_map = {
    "Easy": "simple recall-based questions suitable for beginners",
    "Medium": "application and understanding questions requiring conceptual clarity",
    "Hard": "analysis and evaluation questions requiring deep understanding and critical thinking"
}

# ── Input Selectors ───────────────────────────────────────────────
input_method = st.radio("Select Input Source", ["📄 Upload PDF Document", "✍️ Paste Text Content"], horizontal=True, label_visibility="collapsed")

uploaded_file = None
pasted_text = ""

if "📄 Upload PDF Document" in input_method:
    uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])
else:
    pasted_text = st.text_area("Paste text content here...", height=250, placeholder="Paste articles, study guides, notes, or essays...")

# ── Main Generation Trigger ───────────────────────────────────────
if st.button("Generate Quiz ⚡"):
    if "📄 Upload PDF Document" in input_method and not uploaded_file:
        st.error("⚠️ Please upload a PDF document first.")
    elif "✍️ Paste Text Content" in input_method and not pasted_text.strip():
        st.error("⚠️ Please paste some study text first.")
    else:
        text = ""
        error_logs = []
        if "📄 Upload PDF Document" in input_method:
            with st.spinner("Extracting text from PDF..."):
                text, error_logs = extract_text_from_pdf(uploaded_file)
        else:
            text = pasted_text

        if len(text.strip()) < 100:
            st.error("""
            ### ⚠️ Text Extraction Failed (Empty or Scanned PDF)
            
            We couldn't extract readable text from your PDF. This typically happens if:
            1. **Scanned Images**: The PDF contains photos or scanned pages instead of selectable digital text.
            2. **Layout/Form Blockers**: The file is encrypted, password-protected, or has form blocks that prevent programmatic reading.
            
            **How you can resolve this:**
            * Try uploading a **digitally created PDF** (e.g., exported directly from Google Docs, Word, or Canva).
            * Copy the text from your document manually and use the **✍️ Paste Text Content** tab above to generate your MCQs!
            """)
            
            if error_logs:
                with st.expander("🛠️ View Technical Parser Logs"):
                    for log in error_logs:
                        st.code(log, language="text")
            
            st.stop()

        # Handle Truncation and show warning if needed
        if len(text) > 8000:
            st.warning("⚠️ The document is very long. Only the first ~8,000 characters were used to generate questions to keep within AI limits.")
            text = text[:8000]

        if not api_key:
            st.error("⚠️ Groq API Key not found. Please check your environment or secrets.toml.")
            st.stop()

        if quiz_mode == "Adaptive Difficulty 🧠":
            # Set up session state for Adaptive mode
            st.session_state["quiz_mode"] = "Adaptive Difficulty 🧠"
            st.session_state["num_mcqs"] = num_mcqs
            st.session_state["study_text"] = text
            st.session_state["custom_focus"] = custom_focus
            st.session_state["difficulty_history"] = [difficulty]
            st.session_state["mcqs"] = []
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.session_state["quiz_page"] = 0

            with st.spinner("AI is crafting the first question..."):
                q_dict, err = generate_single_question(text, difficulty, [], api_key, model_name, custom_focus)
                if err:
                    st.error(f"⚠️ Groq API Error: {err}")
                    st.stop()
                elif q_dict:
                    st.session_state["mcqs"] = [q_dict]
                    st.rerun()
        else:
            # Classic Mode
            st.session_state["quiz_mode"] = "Classic Mode"
            st.session_state["difficulty"] = difficulty
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.session_state["quiz_page"] = 0

            focus_instruction = f"- Questions should focus specifically on: '{custom_focus}'." if custom_focus.strip() else ""

            prompt = f"""You are an expert exam question creator.

Based on the following text, generate exactly {num_mcqs} multiple choice questions.
Difficulty level: {difficulty} — {diff_map[difficulty]}.
{focus_instruction}

Rules:
- Each question must have exactly 4 options labeled A, B, C, D.
- Only one option is correct.
- Include a brief explanation for the correct answer.
- Categorize each question into a logical concept or sub-topic covered in the text (e.g. 'Definitions', 'Applications', 'Causes', etc.)
- Questions must be directly based on the provided text.
- Return ONLY a valid JSON array, no extra text, no markdown.

JSON format:
[
  {{
    "question": "Question text here?",
    "category": "Sub-topic or category name",
    "options": {{
      "A": "Option A",
      "B": "Option B", 
      "C": "Option C",
      "D": "Option D"
    }},
    "correct": "A",
    "explanation": "Brief explanation why A is correct."
  }}
]

TEXT:
{text}"""

            with st.spinner("AI is crafting questions..."):
                try:
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.45,
                        max_tokens=3500
                    )
                    raw = response.choices[0].message.content.strip()

                    # Clean markdown format backticks
                    if "```" in raw:
                        parts = raw.split("```")
                        for part in parts:
                            part = part.strip()
                            if part.startswith("json"):
                                part = part[4:].strip()
                            if part.startswith("["):
                                raw = part
                                break

                    mcqs = json.loads(raw)
                    st.session_state["mcqs"] = mcqs
                    st.session_state["difficulty_history"] = [difficulty] * len(mcqs)
                    st.rerun()

                except json.JSONDecodeError:
                    st.error("⚠️ AI returned invalid JSON format. Please try generating again.")
                    st.stop()
                except Exception as e:
                    st.error(f"⚠️ API Connection Error: {e}")
                    st.stop()

# ── Render Quiz UI ────────────────────────────────────────────────
if "mcqs" in st.session_state and st.session_state["mcqs"]:
    mcqs = st.session_state["mcqs"]
    submitted = st.session_state.get("submitted", False)
    active_quiz_mode = st.session_state.get("quiz_mode", "Classic Mode")

    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05)'><br>", unsafe_allow_html=True)

    # ── Sidebar Progress & Navigation (Quiz Phase) ────────────────
    if not submitted:
        current_idx = st.session_state.get("quiz_page", 0)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📝 Quiz Progress")
        
        if active_quiz_mode == "Adaptive Difficulty 🧠":
            total_qs = st.session_state.get("num_mcqs", 5)
            st.sidebar.markdown(f"Question: **{current_idx + 1} of {total_qs}**")
            st.sidebar.progress((current_idx) / total_qs)
            
            st.sidebar.markdown("### 🎯 Adaptive Difficulty State")
            curr_diff = st.session_state["difficulty_history"][current_idx]
            diff_class = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}.get(curr_diff, "medium")
            st.sidebar.markdown(f"Current Level: <span class='diff-badge diff-{diff_class}'>{curr_diff}</span>", unsafe_allow_html=True)
            st.sidebar.markdown("*(Difficulty updates dynamically based on correctness)*")
        else:
            total_qs = len(mcqs)
            answered = sum(1 for i in range(total_qs) if st.session_state["answers"].get(i) is not None)
            st.sidebar.markdown(f"Answered: **{answered} of {total_qs}**")
            st.sidebar.progress(answered / total_qs)
            
            st.sidebar.markdown("### 🎯 Jump to Question")
            cols = st.sidebar.columns(2)
            for idx in range(total_qs):
                col = cols[idx % 2]
                is_ans = st.session_state["answers"].get(idx) is not None
                if idx == current_idx:
                    label = f"Q{idx+1} ⚡"
                    btn_type = "primary"
                elif is_ans:
                    label = f"Q{idx+1} ✓"
                    btn_type = "secondary"
                else:
                    label = f"Q{idx+1}"
                    btn_type = "secondary"
                    
                if col.button(label, key=f"jump_{idx}", type=btn_type):
                    st.session_state["quiz_page"] = idx
                    st.rerun()
                    
            st.sidebar.markdown("---")
            if st.sidebar.button("Submit Quiz ✅", key="sidebar_submit"):
                st.session_state["submitted"] = True
                st.rerun()

    # ── Scoreboard Analytics (Graded Review Phase) ────────────────
    if submitted:
        correct_count = sum(
            1 for i, q in enumerate(mcqs)
            if st.session_state["answers"].get(i) == q["correct"]
        )
        pct = int((correct_count / len(mcqs)) * 100)
        
        # Display main score box
        st.markdown(f"""
        <div class="score-box">
            <div class="score-number">{correct_count}/{len(mcqs)}</div>
            <div class="score-label">{pct}% Correct · {active_quiz_mode}</div>
        </div>
        """, unsafe_allow_html=True)

        # Conceptual breakdown logic
        category_stats = {}
        missed_questions = []
        for i, q in enumerate(mcqs):
            user_ans = st.session_state["answers"].get(i)
            correct_ans = q["correct"]
            cat = q.get("category", "General Review")
            
            if cat not in category_stats:
                category_stats[cat] = [0, 0]
            
            category_stats[cat][1] += 1
            if user_ans == correct_ans:
                category_stats[cat][0] += 1
            else:
                missed_questions.append((i, q, user_ans))

        # Render custom flowchart for adaptive mode
        if active_quiz_mode == "Adaptive Difficulty 🧠":
            st.markdown("### 🗺️ Adaptive Pathway Timeline")
            
            nodes_html = []
            for idx, q in enumerate(mcqs):
                user_ans = st.session_state["answers"].get(idx)
                correct_ans = q["correct"]
                is_corr = (user_ans == correct_ans)
                node_diff = st.session_state["difficulty_history"][idx]
                
                status_icon = "✓ Correct" if is_corr else "✗ Incorrect"
                node_class = "correct" if is_corr else "incorrect"
                
                node_html = f"""
                <div class="flow-node {node_class}">
                    <div class="node-q">Q{idx+1}</div>
                    <div class="node-diff">{node_diff}</div>
                    <div class="node-status">{status_icon}</div>
                </div>
                """
                nodes_html.append(node_html)
            
            arrow_html = '<div class="flow-arrow">➔</div>'
            flowchart_html = f"""
            <style>
            .flow-container {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin: 1.5rem 0 2.5rem 0;
                padding: 1.5rem;
                background: rgba(20, 26, 38, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(8px);
            }}
            .flow-node {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 10px 18px;
                border-radius: 12px;
                min-width: 110px;
                text-align: center;
                background: rgba(15, 20, 30, 0.8);
                border: 2px solid;
                transition: all 0.3s ease;
            }}
            .flow-node.correct {{
                border-color: #10b981;
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
            }}
            .flow-node.correct .node-q, .flow-node.correct .node-status {{
                color: #10b981 !important;
            }}
            .flow-node.incorrect {{
                border-color: #ef4444;
                box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);
            }}
            .flow-node.incorrect .node-q, .flow-node.incorrect .node-status {{
                color: #ef4444 !important;
            }}
            .flow-node .node-q {{
                font-size: 0.75rem;
                text-transform: uppercase;
                font-weight: 800;
                letter-spacing: 0.1em;
                margin-bottom: 2px;
            }}
            .flow-node .node-diff {{
                font-size: 1.05rem;
                font-weight: 800;
                color: #ffffff !important;
            }}
            .flow-node .node-status {{
                font-size: 0.8rem;
                margin-top: 4px;
                font-weight: 700;
            }}
            .flow-arrow {{
                font-size: 1.6rem;
                color: #00f0ff;
                text-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
                font-family: 'Outfit', sans-serif;
                user-select: none;
            }}
            </style>
            <div class="flow-container">
            """
            
            # Combine nodes and arrows
            combined_elements = []
            for i, node in enumerate(nodes_html):
                combined_elements.append(node)
                if i < len(nodes_html) - 1:
                    combined_elements.append(arrow_html)
            
            flowchart_html += " ".join(combined_elements)
            flowchart_html += "</div>"
            st.markdown(flowchart_html, unsafe_allow_html=True)

        # Render stats grid (3 columns max)
        st.markdown("### 📊 Topic Performance breakdown")
        cat_items = list(category_stats.items())
        for idx in range(0, len(cat_items), 3):
            row_items = cat_items[idx:idx+3]
            cols = st.columns(3)
            for col, (cat, (corr, tot)) in zip(cols, row_items):
                with col:
                    col_pct = int((corr / tot) * 100)
                    accent = '#10b981' if col_pct >= 70 else '#f59e0b' if col_pct >= 40 else '#ef4444'
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 14px; text-align: center; margin-bottom: 12px; backdrop-filter: blur(5px);">
                        <div style="font-size: 0.8rem; text-transform: uppercase; color: #94a3b8; font-weight: 700; letter-spacing: 0.05em; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{cat}</div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: {accent}; margin: 6px 0;">{col_pct}%</div>
                        <div style="font-size: 0.85rem; color: #64748b;">{corr} / {tot} correct</div>
                    </div>
                    """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Render MCQ Cards ──────────────────────────────────────────
    if not submitted:
        # Quiz Phase: Render only the current active question
        current_idx = st.session_state.get("quiz_page", 0)
        q = mcqs[current_idx]
        cat = q.get("category", "General")
        diff = st.session_state["difficulty_history"][current_idx]
        diff_class = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}.get(diff, "medium")

        st.markdown(f"""
        <div style="margin-bottom: -15px;">
            <div class="q-number">
                <span>Question {current_idx+1} of {len(mcqs) if active_quiz_mode != "Adaptive Difficulty 🧠" else st.session_state.get("num_mcqs", 5)} &nbsp;·&nbsp; {cat}</span>
                <span class="diff-badge diff-{diff_class}">{diff}</span>
            </div>
            <div class="q-text">{q["question"]}</div>
        </div>
        """, unsafe_allow_html=True)

        # Restore saved radio choice index if answered
        saved_ans = st.session_state["answers"].get(current_idx)
        options_list = list(q["options"].keys())
        radio_index = options_list.index(saved_ans) if saved_ans in options_list else None

        choice = st.radio(
            f"Radio_Q{current_idx+1}",
            options=options_list,
            format_func=lambda x, q=q: f"{x}. {q['options'][x]}",
            key=f"q_{current_idx}",
            index=radio_index,
            label_visibility="collapsed"
        )
        st.session_state["answers"][current_idx] = choice
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

        if active_quiz_mode == "Adaptive Difficulty 🧠":
            total_qs = st.session_state.get("num_mcqs", 5)
            
            # Navigation row for Adaptive Mode (Submit Answer & Next)
            col_prev, col_progress, col_next = st.columns([1, 2, 1])
            with col_prev:
                # Disabled in Adaptive Mode
                st.button("⬅️ Previous", disabled=True, key="btn_prev_adaptive")
            with col_progress:
                st.progress((current_idx + 1) / total_qs)
            with col_next:
                if current_idx == total_qs - 1:
                    if st.button("Submit & View Results ✅", key="btn_adaptive_submit"):
                        st.session_state["answers"][current_idx] = choice
                        st.session_state["submitted"] = True
                        st.rerun()
                else:
                    if st.button("Submit & Next ➡️", key="btn_adaptive_next"):
                        st.session_state["answers"][current_idx] = choice
                        is_correct = (choice == q["correct"])
                        
                        # Adjust difficulty for next question
                        curr_diff = st.session_state["difficulty_history"][current_idx]
                        if is_correct:
                            next_diff = "Medium" if curr_diff == "Easy" else "Hard"
                        else:
                            next_diff = "Easy" if curr_diff == "Hard" else "Easy" if curr_diff == "Medium" else "Easy"
                        
                        # Generate next question
                        with st.spinner("AI is crafting the next question..."):
                            next_q, err = generate_single_question(
                                st.session_state["study_text"],
                                next_diff,
                                st.session_state["mcqs"],
                                api_key,
                                model_name,
                                st.session_state["custom_focus"]
                            )
                            if err:
                                st.error(f"⚠️ Error generating next question: {err}")
                            elif next_q:
                                st.session_state["mcqs"].append(next_q)
                                st.session_state["difficulty_history"].append(next_diff)
                                st.session_state["quiz_page"] = current_idx + 1
                                st.rerun()
        else:
            # Navigation row for Classic Mode
            col_prev, col_progress, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("⬅️ Previous", disabled=(current_idx == 0), key="btn_prev"):
                    st.session_state["quiz_page"] = max(0, current_idx - 1)
                    st.rerun()
            with col_progress:
                st.progress((current_idx + 1) / len(mcqs))
            with col_next:
                if current_idx == len(mcqs) - 1:
                    if st.button("Submit Quiz ✅", key="btn_submit_quiz"):
                        st.session_state["submitted"] = True
                        st.rerun()
                else:
                    if st.button("Next ➡️", key="btn_next"):
                        st.session_state["quiz_page"] = min(len(mcqs) - 1, current_idx + 1)
                        st.rerun()

    else:
        # Graded Review Phase: Show all questions scrollable so they can easily read explanations
        for i, q in enumerate(mcqs):
            user_ans = st.session_state["answers"].get(i)
            correct_ans = q["correct"]
            cat = q.get("category", "General")
            
            q_diff = st.session_state["difficulty_history"][i] if "difficulty_history" in st.session_state and i < len(st.session_state["difficulty_history"]) else st.session_state.get("difficulty", "Medium")
            q_diff_class = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}.get(q_diff, "medium")

            # Build and display static results card
            options_html = ""
            for key, val in q["options"].items():
                css_class = "option"
                badge = ""
                if key == correct_ans:
                    css_class += " correct"
                    badge = " (Correct)"
                elif key == user_ans and key != correct_ans:
                    css_class += " wrong"
                    badge = " (Your Choice)"
                options_html += f'<div class="{css_class}"><b>{key}.</b> {val}{badge}</div>'

            st.markdown(f"""
            <div class="mcq-card">
                <div class="q-number">
                    <span>Q{i+1} &nbsp;·&nbsp; {cat}</span>
                    <span class="diff-badge diff-{q_diff_class}">{q_diff}</span>
                </div>
                <div class="q-text">{q["question"]}</div>
                {options_html}
                <div class="explanation">💡 <b>Explanation:</b> {q["explanation"]}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Recommended review session details
        if missed_questions:
            st.markdown("### 🔍 Recommended Review Session")
            st.markdown("Take a closer look at the concepts below to patch your understanding:")
            for index, q, user_ans in missed_questions:
                user_label = f"{user_ans}. {q['options'].get(user_ans, 'Unanswered')}"
                corr_label = f"{q['correct']}. {q['options'].get(q['correct'], '')}"
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.04); border: 1px solid rgba(239, 68, 68, 0.12); border-radius: 12px; padding: 16px; margin-bottom: 14px;">
                    <div style="font-weight: 700; color: #ef4444; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 6px;">Q{index+1} Review · {q.get('category', 'General')}</div>
                    <div style="font-weight: 600; color: #ffffff; margin-bottom: 8px; font-size: 1.05rem;">{q['question']}</div>
                    <div style="font-size: 0.9rem; color: #94a3b8; line-height: 1.5;">
                        Your Answer: <span style="color:#ef4444; font-weight:600;">{user_label}</span><br>
                        Correct Answer: <span style="color:#10b981; font-weight:600;">{corr_label}</span>
                    </div>
                    <div class="explanation" style="margin-top:12px;">💡 <b>Key Concept:</b> {q['explanation']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Export Suite Downloader Buttons
        st.markdown("### 📥 Download Quiz Material")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(label="📄 Markdown Notes", data=generate_markdown(mcqs), file_name="quizlab_mcq_notes.md", mime="text/markdown")
        with c2:
            st.download_button(label="📦 Raw JSON", data=json.dumps(mcqs, indent=2), file_name="quizlab_mcq_data.json", mime="application/json")
        with c3:
            st.download_button(label="⚡ Anki Flashcards", data=generate_anki(mcqs), file_name="quizlab_mcq_anki.txt", mime="text/tab-separated-values")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate New Quiz 🔄"):
            st.session_state["submitted"] = False
            st.session_state["mcqs"] = []
            st.session_state["answers"] = {}
            st.session_state["difficulty_history"] = []
            st.session_state["quiz_page"] = 0
            st.rerun()