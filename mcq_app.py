import streamlit as st
import json
import os
import time
import textwrap
import pandas as pd
import datetime

# Force Streamlit to reload modified backend modules
import importlib
import utils
importlib.reload(utils)
import pdf_parser
importlib.reload(pdf_parser)
import cache_manager
importlib.reload(cache_manager)

from utils import (
    generate_markdown, 
    generate_anki, 
    generate_single_question,
    generate_learning_material,
    get_tutor_explanation,
    generate_learning_report
)
from pdf_parser import extract_text_from_file
from cache_manager import get_cached_material, set_cached_material

# Set Page Config
st.set_page_config(
    page_title="QuizLab AI - Premium AI Personalized Learning Platform", 
    page_icon="🧠", 
    layout="centered"
)

# ── Local Database for Quiz History ───────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_history.json")

def save_quiz_result(quiz_title, score, total, quiz_mode, elapsed_time, topic_stats, diff_stats):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "quiz_title": quiz_title,
        "score": score,
        "total": total,
        "percentage": int((score / total) * 100) if total > 0 else 0,
        "quiz_mode": quiz_mode,
        "elapsed_time": int(elapsed_time),  # seconds
        "topic_stats": topic_stats,
        "difficulty_stats": diff_stats
    }
    history.append(entry)
    
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def get_quiz_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def clear_quiz_history():
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return True
    except Exception:
        return False


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
    background: radial-gradient(circle at 50% 50%, #080a13 0%, #030406 100%) !important;
    color: #e2e8f0 !important;
}

/* Main title styling */
.hero-title {
    font-size: 3.6rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 50%, #bd00ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.1rem;
    letter-spacing: -0.03em;
    filter: drop-shadow(0px 4px 20px rgba(0, 240, 255, 0.2));
}

.hero-sub {
    font-size: 1.15rem;
    color: #94a3b8;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 400;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.6;
}

/* Feature Badges */
.badge-grid {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    margin: -1rem auto 2.5rem auto;
    max-width: 800px;
}
.badge-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #cbd5e1;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.badge-item:hover {
    background: rgba(0, 240, 255, 0.08);
    border-color: #00f0ff;
    color: #ffffff;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
    transform: translateY(-2px);
}

/* Workflow Timeline */
.timeline-container {
    background: rgba(15, 22, 38, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1.5rem 0 2rem 0;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(8px);
}
.timeline-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 800;
    color: #ccff00;
    letter-spacing: 0.15em;
    margin-bottom: 1.2rem;
    text-transform: uppercase;
}
.timeline-steps {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}
.timeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    min-width: 90px;
}
.timeline-icon {
    font-size: 1.8rem;
    margin-bottom: 6px;
    transition: transform 0.3s;
}
.timeline-step:hover .timeline-icon {
    transform: scale(1.2) rotate(5deg);
}
.timeline-label {
    font-size: 0.8rem;
    color: #94a3b8;
    font-weight: 600;
}
.timeline-arrow {
    font-size: 1.2rem;
    color: #00f0ff;
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
    margin-bottom: 20px;
}

/* Glassmorphic Side Bar */
section[data-testid="stSidebar"] {
    background-color: rgba(6, 8, 14, 0.8) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(15px) !important;
}

section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00f0ff !important;
    font-weight: 700;
    margin-top: 1rem;
}

/* Glassmorphic Card Container */
.mcq-card {
    background: rgba(18, 24, 38, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mcq-card:hover {
    border-color: rgba(0, 240, 255, 0.25);
    box-shadow: 0 12px 40px 0 rgba(0, 240, 255, 0.08);
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
    font-size: 1.18rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 1.5rem;
    line-height: 1.55;
}

/* Option styling for completed answers */
.option {
    padding: 14px 20px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 1rem;
    color: #cbd5e1;
    background: rgba(12, 16, 26, 0.6);
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
    background: rgba(204, 255, 0, 0.04);
    border-left: 4px solid #ccff00;
    border-radius: 0 12px 12px 0;
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.6;
}

/* Loading animations pipeline style */
.loading-container {
    background: rgba(10, 15, 30, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 16px;
    padding: 2.2rem;
    margin: 2rem auto;
    max-width: 500px;
    box-shadow: 0 8px 32px 0 rgba(0, 240, 255, 0.1);
    backdrop-filter: blur(10px);
}
.loading-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.35rem;
    font-weight: 800;
    text-align: center;
    color: #00f0ff;
    margin-bottom: 1.5rem;
    letter-spacing: -0.02em;
}
.loading-step {
    padding: 11px 16px;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 500;
    transition: all 0.3s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.loading-step.pending {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    color: #57657a;
}
.loading-step.active {
    background: rgba(0, 240, 255, 0.06);
    border: 1px solid #00f0ff;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.15);
}
.loading-step.done {
    background: rgba(204, 255, 0, 0.06);
    border: 1px solid #ccff00;
    color: #ccff00;
}
.loading-arrow {
    text-align: center;
    color: rgba(255, 255, 255, 0.15);
    font-size: 1.1rem;
    margin: 3px 0;
}
.status-check {
    font-size: 0.82rem;
    font-weight: 700;
}
.status-spinner {
    font-size: 0.82rem;
    font-weight: 700;
    animation: blink 0.9s infinite alternate;
}
@keyframes blink {
    0% { opacity: 0.35; }
    100% { opacity: 1; }
}

/* Performance Analytics Score Box */
.score-box {
    background: linear-gradient(135deg, rgba(20, 28, 48, 0.85), rgba(10, 15, 26, 0.85));
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 20px;
    padding: 2.2rem;
    text-align: center;
    margin-bottom: 2.5rem;
    box-shadow: 0 10px 30px rgba(0, 240, 255, 0.1);
}

.score-number {
    font-family: 'Syne', sans-serif;
    font-size: 3.8rem;
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

.diff-easy, .diff-Easy { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.diff-medium, .diff-Medium { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.diff-hard, .diff-Hard { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

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
    background: rgba(16, 22, 36, 0.45) !important;
    border: 2px dashed rgba(255, 255, 255, 0.12) !important;
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
    background-color: rgba(12, 16, 26, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
}
div[data-testid*="UploadedFile"] span, div[class*="stUploadedFile"] span {
    color: #ffffff !important;
}

/* Streamlit Buttons style override (Global) */
.stButton > button {
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 100%) !important;
    color: #030406 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    font-size: 1rem !important;
    width: 100%;
    box-shadow: 0 4px 15px rgba(0, 240, 255, 0.2) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stButton > button p, 
.stButton > button span, 
.stButton > button div {
    color: #030406 !important;
    font-weight: 800 !important;
}

.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(0, 240, 255, 0.4) !important;
    transform: translateY(-2px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Sidebar main buttons */
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

/* Sidebar grid jump buttons */
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

section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] button[kind="primary"] {
    background: linear-gradient(135deg, #ccff00 0%, #00f0ff 100%) !important;
    color: #030406 !important;
    border: none !important;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
}

/* Secondary Buttons */
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
    background: rgba(12, 16, 26, 0.5) !important;
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
    background: rgba(24, 32, 50, 0.65) !important;
    border-color: rgba(0, 240, 255, 0.3) !important;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.1) !important;
    transform: translateY(-2px) !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    background: rgba(0, 240, 255, 0.08) !important;
    border-color: #00f0ff !important;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.2) !important;
}

div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

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

/* Style selects, inputs, and textareas */
div[data-baseweb="select"] > div {
    background-color: rgba(12, 16, 26, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, input {
    background-color: rgba(12, 16, 26, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

/* Interactive Flashcard 3D structure */
.flip-card {
  background-color: transparent;
  width: 100%;
  height: 250px;
  perspective: 1000px;
  margin-bottom: 2rem;
}
.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  text-align: center;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}
.flip-card.flipped .flip-card-inner {
  transform: rotateY(180deg);
}
.flip-card-front, .flip-card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  border-radius: 16px;
  padding: 2.2rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.flip-card-front {
  background: linear-gradient(135deg, rgba(20, 26, 38, 0.85), rgba(10, 15, 25, 0.85));
  color: white;
}
.flip-card-back {
  background: linear-gradient(135deg, rgba(10, 15, 28, 0.95), rgba(26, 36, 54, 0.95));
  color: white;
  transform: rotateY(180deg);
}
.flashcard-topic {
  font-family: 'Syne', sans-serif;
  font-size: 11px;
  font-weight: 800;
  color: #00f0ff;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 15px;
}
.flashcard-text {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.5;
}

/* Heatmap activity grid */
.heatmap-container {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin: 1rem auto;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 15px;
    max-width: fit-content;
}
.heatmap-day {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    transition: all 0.2s ease;
}
.heatmap-day.lvl-0 {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.heatmap-day.lvl-1 {
    background: rgba(0, 240, 255, 0.35);
    border: 1px solid rgba(0, 240, 255, 0.6);
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
}
.heatmap-day.lvl-2 {
    background: rgba(204, 255, 0, 0.65);
    border: 1px solid rgba(204, 255, 0, 0.9);
    box-shadow: 0 0 12px rgba(204, 255, 0, 0.4);
}
.heatmap-day:hover {
    transform: scale(1.2);
}

/* Custom cards */
.custom-card {
    background: rgba(18, 25, 41, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 15px 20px;
    margin-bottom: 12px;
}
.custom-card-title {
    font-weight: 700;
    font-size: 0.82rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 5px;
}
.custom-card-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────────
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "setup"
if "material_data" not in st.session_state:
    st.session_state["material_data"] = None
if "quiz_mode" not in st.session_state:
    st.session_state["quiz_mode"] = "Classic Mode"
if "num_mcqs" not in st.session_state:
    st.session_state["num_mcqs"] = 5
if "custom_focus" not in st.session_state:
    st.session_state["custom_focus"] = ""
if "starting_difficulty" not in st.session_state:
    st.session_state["starting_difficulty"] = "Medium"
if "mcqs" not in st.session_state:
    st.session_state["mcqs"] = []
if "difficulty_history" not in st.session_state:
    st.session_state["difficulty_history"] = []
if "answers" not in st.session_state:
    st.session_state["answers"] = {}
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "quiz_page" not in st.session_state:
    st.session_state["quiz_page"] = 0
if "tutor_explanations" not in st.session_state:
    st.session_state["tutor_explanations"] = {}
if "learning_report" not in st.session_state:
    st.session_state["learning_report"] = None
if "flashcard_idx" not in st.session_state:
    st.session_state["flashcard_idx"] = 0
if "flashcard_flipped" not in st.session_state:
    st.session_state["flashcard_flipped"] = False
if "question_times" not in st.session_state:
    st.session_state["question_times"] = {}
if "question_start_time" not in st.session_state:
    st.session_state["question_start_time"] = None
if "used_questions_indices" not in st.session_state:
    st.session_state["used_questions_indices"] = []


# ── Title & Header ────────────────────────────────────────────────
st.markdown('<p class="hero-title">QuizLab AI</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Transform any study material into an AI-powered learning experience with intelligent quiz generation, adaptive assessment, and personalized insights.</p>', unsafe_allow_html=True)

# ── Sidebar Settings & Configurations ─────────────────────────────
api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
if not api_key:
    api_key = st.sidebar.text_input("Enter Groq API Key", type="password", help="Enter your Groq cloud console API Key.")
    
# Hardcode model backend
model_name = "llama-3.3-70b-versatile"

st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Caching Policy")
use_cache = st.sidebar.checkbox(
    "Use Local Cache", 
    value=True, 
    help="Enable to load previously analyzed material instantly to save Groq API credits. Disable to force a new, randomized question generation session."
)

# Render Sidebar navigation controls if study pack is ready
if st.session_state["material_data"] is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Platform Navigation")
    
    col_nav1, col_nav2 = st.sidebar.columns(2)
    if col_nav1.button("🏠 Home", key="sidebar_nav_home"):
        st.session_state["active_view"] = "extracted_knowledge"
        st.rerun()
    if col_nav2.button("📊 Analytics", key="sidebar_nav_analytics"):
        st.session_state["active_view"] = "dashboard"
        st.rerun()
        
    if st.sidebar.button("⚡ Review Flashcards", key="sidebar_nav_fc"):
        st.session_state["active_view"] = "flashcards"
        st.session_state["flashcard_idx"] = 0
        st.session_state["flashcard_flipped"] = False
        st.rerun()
        
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Upload New Material", key="sidebar_nav_reset"):
        # Reset everything
        st.session_state["active_view"] = "setup"
        st.session_state["material_data"] = None
        st.session_state["mcqs"] = []
        st.session_state["answers"] = {}
        st.session_state["submitted"] = False
        st.session_state["quiz_page"] = 0
        st.session_state["tutor_explanations"] = {}
        st.session_state["learning_report"] = None
        st.session_state["difficulty_history"] = []
        st.session_state["question_times"] = {}
        st.session_state["question_start_time"] = None
        st.session_state["used_questions_indices"] = []
        st.rerun()


# ── Loading Engine Handler ────────────────────────────────────────
def build_loading_html(steps, active_idx):
    html = "<div class='loading-container'>"
    html += "<p class='loading-title'>🧠 QuizLab AI Intelligence Engine</p>"
    for idx, (label, icon) in enumerate(steps):
        if idx < active_idx:
            html += f"<div class='loading-step done'><span>{icon} {label}</span> <span class='status-check'>✓ Done</span></div>"
        elif idx == active_idx:
            html += f"<div class='loading-step active'><span>{icon} {label}</span> <span class='status-spinner'>● Processing...</span></div>"
        else:
            html += f"<div class='loading-step pending'><span>{icon} {label}</span></div>"
        if idx < len(steps) - 1:
            html += "<div class='loading-arrow'>↓</div>"
    html += "</div>"
    return html

def load_and_analyze_material(text, custom_focus, api_key, model_name, use_cache=True):
    status_placeholder = st.empty()
    
    # Check cache
    cached = None
    if use_cache:
        cached = get_cached_material(text, custom_focus)
    is_cached = (cached is not None)
    
    pipeline_steps = [
        ("Reading Study Material...", "📂"),
        ("Understanding Concepts & Analysis...", "🧠"),
        ("Generating Quiz Questions Pool...", "🎯"),
        ("Building Flashcards & Learning Pack...", "⚡"),
        ("Ready!", "🚀")
    ]
    
    # Step 0: Reading
    html = build_loading_html(pipeline_steps, 0)
    status_placeholder.markdown(html, unsafe_allow_html=True)
    time.sleep(0.3 if is_cached else 0.8)
    
    # Step 1: Understanding
    html = build_loading_html(pipeline_steps, 1)
    status_placeholder.markdown(html, unsafe_allow_html=True)
    time.sleep(0.3 if is_cached else 1.0)
    
    if is_cached:
        # Fast-track steps for cached data
        for step_idx in range(2, 5):
            html = build_loading_html(pipeline_steps, step_idx)
            status_placeholder.markdown(html, unsafe_allow_html=True)
            time.sleep(0.15)
        status_placeholder.empty()
        return cached, None
    else:
        # Step 2: Generating Quiz Pool
        html = build_loading_html(pipeline_steps, 2)
        status_placeholder.markdown(html, unsafe_allow_html=True)
        
        # Call API 1
        temp = 0.35 if use_cache else 0.75
        seed = 0 if use_cache else int(time.time())
        material, err = generate_learning_material(text, custom_focus, api_key, model_name, temp, seed)
        if err:
            status_placeholder.empty()
            return None, err
            
        # Step 3: Building Flashcards
        html = build_loading_html(pipeline_steps, 3)
        status_placeholder.markdown(html, unsafe_allow_html=True)
        time.sleep(0.8)
        
        # Step 4: Ready
        html = build_loading_html(pipeline_steps, 4)
        status_placeholder.markdown(html, unsafe_allow_html=True)
        time.sleep(0.5)
        
        # Cache results locally
        set_cached_material(text, custom_focus, material)
        
        status_placeholder.empty()
        return material, None


# ── Rerouting Views ───────────────────────────────────────────────

# ==================================================================
# SCREEN 1: Setup View
# ==================================================================
if st.session_state["active_view"] == "setup":
    # ── Feature Badges Grid ──
    st.markdown("""
    <div class="badge-grid">
      <div class="badge-item">🧠 AI Question Generation</div>
      <div class="badge-item">📄 Intelligent PDF Analysis</div>
      <div class="badge-item">🎯 Adaptive Learning</div>
      <div class="badge-item">📊 Learning Analytics</div>
      <div class="badge-item">💬 AI Tutor</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Workflow Visualization ──
    st.markdown("""
    <div class="timeline-container">
      <p class="timeline-title">QuizLab AI Intelligence Workflow</p>
      <div class="timeline-steps">
        <div class="timeline-step">
          <div class="timeline-icon">📄</div>
          <div class="timeline-label">Upload Material</div>
        </div>
        <div class="timeline-arrow">➔</div>
        <div class="timeline-step">
          <div class="timeline-icon">🧠</div>
          <div class="timeline-label">AI Analysis</div>
        </div>
        <div class="timeline-arrow">➔</div>
        <div class="timeline-step">
          <div class="timeline-icon">🎯</div>
          <div class="timeline-label">Quiz Generation</div>
        </div>
        <div class="timeline-arrow">➔</div>
        <div class="timeline-step">
          <div class="timeline-icon">⚡</div>
          <div class="timeline-label">Adaptive Assessment</div>
        </div>
        <div class="timeline-arrow">➔</div>
        <div class="timeline-step">
          <div class="timeline-icon">📊</div>
          <div class="timeline-label">Analytics Dashboard</div>
        </div>
        <div class="timeline-arrow">➔</div>
        <div class="timeline-step">
          <div class="timeline-icon">💬</div>
          <div class="timeline-label">AI Tutor Feedback</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Main Setup form
    st.markdown("### ⚙️ Quiz Customization Options")
    
    col_mode, col_num = st.columns(2)
    with col_mode:
        quiz_mode = st.radio("Quiz Mode", ["Classic Mode", "Adaptive Difficulty 🧠"], help="Classic generates questions of a selected difficulty. Adaptive adjusts difficulty dynamically based on correctness.")
    with col_num:
        num_mcqs = st.slider("Target Number of Questions", min_value=3, max_value=12, value=5, step=1, help="Choose the total number of quiz questions.")
        
    starting_difficulty = st.selectbox("Starting / Quiz Difficulty", ["Easy", "Medium", "Hard"], index=1)
    custom_focus = st.text_input("Custom Topic Focus / Keywords (Optional)", placeholder="e.g. key equations, definitions, chapter 3, python code")

    st.markdown("### 📂 Input Study Materials")
    input_method = st.radio("Source Format", ["📄 Upload Study Material", "✍️ Paste Text Content"], horizontal=True, label_visibility="collapsed")
    
    uploaded_file = None
    pasted_text = ""
    
    if "📄 Upload Study Material" in input_method:
        uploaded_file = st.file_uploader("Upload PDF, TXT or MD File", type=["pdf", "txt", "md"])
    else:
        pasted_text = st.text_area("Paste study content here...", height=250, placeholder="Paste articles, textbook chapters, lecture notes...")

    if st.button("Generate Learning Pack ⚡"):
        if "📄 Upload Study Material" in input_method and not uploaded_file:
            st.error("⚠️ Please upload a study document first.")
        elif "✍️ Paste Text Content" in input_method and not pasted_text.strip():
            st.error("⚠️ Please paste some study text first.")
        elif not api_key:
            st.error("⚠️ Groq API Key is required. Please input your key in the sidebar.")
        else:
            text = ""
            error_logs = []
            if "📄 Upload Study Material" in input_method:
                text, error_logs = extract_text_from_file(uploaded_file)
            else:
                text = pasted_text

            if len(text.strip()) < 100:
                st.error("### ⚠️ Text Extraction Failed or Content Too Short\nWe couldn't extract readable text. Ensure the document is readable (not scanned) or copy-paste the text directly.")
                if error_logs:
                    with st.expander("🛠️ View Technical Parser Logs"):
                        for log in error_logs:
                            st.code(log)
                st.stop()
                
            # Limit length to keep in API limits
            if len(text) > 9000:
                st.warning("⚠️ Study material is very long. The first ~9,000 characters were parsed to fit educational context limits.")
                text = text[:9000]
                
            # Run combined analysis, quiz pool generation, flashcards
            material_data, err = load_and_analyze_material(text, custom_focus, api_key, model_name, use_cache)
            
            if err:
                st.error(f"⚠️ Groq API Error: {err}")
            elif material_data:
                # Save session variables
                st.session_state["material_data"] = material_data
                st.session_state["quiz_mode"] = quiz_mode
                st.session_state["num_mcqs"] = num_mcqs
                st.session_state["custom_focus"] = custom_focus
                st.session_state["starting_difficulty"] = starting_difficulty
                st.session_state["quiz_title"] = getattr(uploaded_file, "name", "Pasted Text Session") if uploaded_file else "Pasted Text Session"
                
                # Switch view
                st.session_state["active_view"] = "extracted_knowledge"
                st.rerun()

# ==================================================================
# SCREEN 2: Extracted Knowledge Page (Pre-quiz review)
# ==================================================================
elif st.session_state["active_view"] == "extracted_knowledge":
    material = st.session_state["material_data"]
    analysis = material["analysis"]
    
    st.markdown("## 📄 Intelligent Knowledge Profile")
    st.markdown("We've analyzed your document. Review the core profile below before starting your learning exercises:")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.markdown(f"""
        <div class="custom-card">
            <div class="custom-card-title">Document Difficulty</div>
            <div class="custom-card-value">{analysis['difficulty_level']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class="custom-card">
            <div class="custom-card-title">Est. Reading Time</div>
            <div class="custom-card-value">{analysis['estimated_reading_time']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat3:
        st.markdown(f"""
        <div class="custom-card">
            <div class="custom-card-title">Recommended Questions</div>
            <div class="custom-card-value">{analysis['recommended_num_questions']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_t, col_o = st.columns(2)
    with col_t:
        st.markdown("### 🧠 Identified Topics")
        for topic in analysis.get("main_topics", []):
            st.markdown(f"🔹 **{topic}**")
            
        if "subtopics" in analysis:
            st.markdown("**Subtopics Covered:**")
            st.markdown(", ".join(analysis["subtopics"]))
            
    with col_o:
        st.markdown("### 🎯 Learning Objectives")
        for obj in analysis.get("learning_objectives", []):
            st.markdown(f"✅ *{obj}*")
            
    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.08)'><br>", unsafe_allow_html=True)
    
    st.markdown("### ⚡ Interactive Learning Exercises")
    st.markdown("Select a learning activity below:")
    
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if st.button(f"✍️ Start Quiz ({st.session_state['quiz_mode']})", key="act_quiz"):
            # Set up quiz
            pool = material["questions"]
            target_mode = st.session_state["quiz_mode"]
            num_q = st.session_state["num_mcqs"]
            
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.session_state["quiz_page"] = 0
            st.session_state["tutor_explanations"] = {}
            st.session_state["learning_report"] = None
            st.session_state["question_times"] = {}
            st.session_state["question_start_time"] = time.time()
            st.session_state["used_questions_indices"] = []
            
            if target_mode == "Classic Mode":
                # Filter matching starting difficulty
                start_diff = st.session_state["starting_difficulty"]
                matched_qs = [q for q in pool if q["difficulty"].lower() == start_diff.lower()]
                
                # If not enough, backfill from other difficulties
                if len(matched_qs) < num_q:
                    backfill_qs = [q for q in pool if q["difficulty"].lower() != start_diff.lower()]
                    matched_qs.extend(backfill_qs)
                    
                # Slice to requested count
                st.session_state["mcqs"] = matched_qs[:num_q]
                st.session_state["difficulty_history"] = [q["difficulty"] for q in st.session_state["mcqs"]]
            else:
                # Adaptive Quiz mode: start with 1 question of starting difficulty
                start_diff = st.session_state["starting_difficulty"]
                matched_qs = [idx for idx, q in enumerate(pool) if q["difficulty"].lower() == start_diff.lower()]
                
                if not matched_qs:
                    # Fallback to any question
                    matched_qs = list(range(len(pool)))
                    
                first_idx = matched_qs[0]
                st.session_state["mcqs"] = [pool[first_idx]]
                st.session_state["difficulty_history"] = [pool[first_idx]["difficulty"]]
                st.session_state["used_questions_indices"] = [first_idx]
                
            st.session_state["active_view"] = "quiz"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_act2:
        if st.button("⚡ Review Flashcards", key="act_fc"):
            st.session_state["active_view"] = "flashcards"
            st.session_state["flashcard_idx"] = 0
            st.session_state["flashcard_flipped"] = False
            st.rerun()
            
    with col_act3:
        if st.button("📊 Analytics Dashboard", key="act_dash"):
            st.session_state["active_view"] = "dashboard"
            st.rerun()

# ==================================================================
# SCREEN 3: Quiz Interface (Classic & Adaptive + Graded Report)
# ==================================================================
elif st.session_state["active_view"] == "quiz":
    mcqs = st.session_state["mcqs"]
    submitted = st.session_state["submitted"]
    active_quiz_mode = st.session_state["quiz_mode"]
    total_qs = st.session_state["num_mcqs"]
    current_idx = st.session_state["quiz_page"]
    
    # Render Quiz Progress in Sidebar
    if not submitted:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📝 Active Quiz Progress")
        if active_quiz_mode == "Adaptive Difficulty 🧠":
            st.sidebar.markdown(f"Question: **{current_idx + 1} of {total_qs}**")
            st.sidebar.progress((current_idx) / total_qs)
            
            curr_diff = st.session_state["difficulty_history"][current_idx]
            st.sidebar.markdown(f"Current Level: <span class='diff-badge diff-{curr_diff}'>{curr_diff}</span>", unsafe_allow_html=True)
            st.sidebar.info("Difficulty shifts dynamically based on correctness of your answers.")
        else:
            answered = sum(1 for i in range(len(mcqs)) if st.session_state["answers"].get(i) is not None)
            st.sidebar.markdown(f"Progress: **{answered} of {len(mcqs)} Answered**")
            st.sidebar.progress(answered / len(mcqs))
            
            st.sidebar.markdown("### 🎯 Jump to Question")
            cols = st.sidebar.columns(2)
            for idx in range(len(mcqs)):
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
                    # Save time spent on previous question
                    if st.session_state["question_start_time"] is not None:
                        elapsed = time.time() - st.session_state["question_start_time"]
                        st.session_state["question_times"][current_idx] = st.session_state["question_times"].get(current_idx, 0) + elapsed
                    st.session_state["quiz_page"] = idx
                    st.session_state["question_start_time"] = time.time()
                    st.rerun()

    # Active Quiz Taking Screen
    if not submitted:
        q = mcqs[current_idx]
        topic = q.get("topic", "General")
        diff = st.session_state["difficulty_history"][current_idx]
        
        st.markdown(f"""
        <div style="margin-bottom: -15px;">
            <div class="q-number">
                <span>Question {current_idx+1} of {total_qs if active_quiz_mode == "Adaptive Difficulty 🧠" else len(mcqs)} &nbsp;·&nbsp; {topic}</span>
                <span class="diff-badge diff-{diff}">{diff}</span>
            </div>
            <div class="q-text">{q["question"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load saved selection if exists
        saved_ans = st.session_state["answers"].get(current_idx)
        options_keys = list(q["options"].keys())
        radio_idx = options_keys.index(saved_ans) if saved_ans in options_keys else None
        
        choice = st.radio(
            f"Radio_Q{current_idx+1}",
            options=options_keys,
            format_func=lambda x, q=q: f"{x}. {q['options'][x]}",
            key=f"q_{current_idx}",
            index=radio_idx,
            label_visibility="collapsed"
        )
        st.session_state["answers"][current_idx] = choice
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        
        # Navigation
        col_prev, col_spacer, col_next = st.columns([1, 2, 1])
        
        # In adaptive mode, Previous is disabled
        with col_prev:
            if active_quiz_mode == "Adaptive Difficulty 🧠":
                st.button("⬅️ Previous", disabled=True, key="btn_prev_adapt")
            else:
                if st.button("⬅️ Previous", disabled=(current_idx == 0), key="btn_prev_classic"):
                    # Save time spent
                    elapsed = time.time() - st.session_state["question_start_time"]
                    st.session_state["question_times"][current_idx] = st.session_state["question_times"].get(current_idx, 0) + elapsed
                    
                    st.session_state["quiz_page"] = max(0, current_idx - 1)
                    st.session_state["question_start_time"] = time.time()
                    st.rerun()
                    
        with col_next:
            if active_quiz_mode == "Adaptive Difficulty 🧠":
                is_last = (current_idx == total_qs - 1)
                btn_label = "Submit & View Results ✅" if is_last else "Submit & Next ➡️"
                
                if st.button(btn_label, key="btn_next_adapt"):
                    # Save selection
                    st.session_state["answers"][current_idx] = choice
                    
                    # Save question time
                    elapsed = time.time() - st.session_state["question_start_time"]
                    st.session_state["question_times"][current_idx] = st.session_state["question_times"].get(current_idx, 0) + elapsed
                    
                    if is_last:
                        st.session_state["submitted"] = True
                        st.rerun()
                    else:
                        # Local Adaptive difficulty update
                        is_correct = (choice == q["correct"])
                        curr_diff_str = st.session_state["difficulty_history"][current_idx]
                        
                        # Upgrade or downgrade
                        if is_correct:
                            next_diff = "Medium" if curr_diff_str == "Easy" else "Hard"
                        else:
                            next_diff = "Easy" if curr_diff_str == "Hard" else "Easy"
                            
                        # Grab next question from pool
                        pool = st.session_state["material_data"]["questions"]
                        used = st.session_state["used_questions_indices"]
                        
                        # Find unused questions matching next_diff
                        matched_indices = [idx for idx, q in enumerate(pool) if q["difficulty"].lower() == next_diff.lower() and idx not in used]
                        
                        if not matched_indices:
                            # Fallback: find any unused question
                            matched_indices = [idx for idx, q in enumerate(pool) if idx not in used]
                            
                        if not matched_indices:
                            # Complete fallback: find any question
                            matched_indices = list(range(len(pool)))
                            
                        next_idx = matched_indices[0]
                        st.session_state["mcqs"].append(pool[next_idx])
                        st.session_state["difficulty_history"].append(pool[next_idx]["difficulty"])
                        st.session_state["used_questions_indices"].append(next_idx)
                        
                        st.session_state["quiz_page"] = current_idx + 1
                        st.session_state["question_start_time"] = time.time()
                        st.rerun()
            else:
                is_last = (current_idx == len(mcqs) - 1)
                btn_label = "Submit Quiz ✅" if is_last else "Next ➡️"
                
                if st.button(btn_label, key="btn_next_classic"):
                    # Save choice
                    st.session_state["answers"][current_idx] = choice
                    
                    # Save time
                    elapsed = time.time() - st.session_state["question_start_time"]
                    st.session_state["question_times"][current_idx] = st.session_state["question_times"].get(current_idx, 0) + elapsed
                    
                    if is_last:
                        st.session_state["submitted"] = True
                        st.rerun()
                    else:
                        st.session_state["quiz_page"] = current_idx + 1
                        st.session_state["question_start_time"] = time.time()
                        st.rerun()

    # Graded Review Phase (Submited Quiz Results)
    else:
        correct_count = sum(1 for idx, q in enumerate(mcqs) if st.session_state["answers"].get(idx) == q["correct"])
        pct = int((correct_count / len(mcqs)) * 100)
        total_time_spent = sum(st.session_state["question_times"].values())
        
        # Display score banner
        st.markdown(f"""
        <div class="score-box">
            <div class="score-number">{correct_count}/{len(mcqs)}</div>
            <div class="score-label">{pct}% Correct · {active_quiz_mode} · {int(total_time_spent // 60)}m {int(total_time_spent % 60)}s total time</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Save to database locally (on first submit)
        if "db_saved" not in st.session_state or not st.session_state["db_saved"]:
            topic_stats = {}
            diff_stats = {}
            for idx, q in enumerate(mcqs):
                u_ans = st.session_state["answers"].get(idx)
                is_c = (u_ans == q["correct"])
                
                t = q.get("topic", "General")
                if t not in topic_stats:
                    topic_stats[t] = {"correct": 0, "total": 0}
                topic_stats[t]["total"] += 1
                if is_c:
                    topic_stats[t]["correct"] += 1
                    
                d = st.session_state["difficulty_history"][idx]
                if d not in diff_stats:
                    diff_stats[d] = {"correct": 0, "total": 0}
                diff_stats[d]["total"] += 1
                if is_c:
                    diff_stats[d]["correct"] += 1
                    
            save_quiz_result(
                quiz_title=st.session_state["quiz_title"],
                score=correct_count,
                total=len(mcqs),
                quiz_mode=active_quiz_mode,
                elapsed_time=total_time_spent,
                topic_stats=topic_stats,
                diff_stats=diff_stats
            )
            st.session_state["db_saved"] = True
            
        # ── Adaptive Pathway Timeline ──
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
                
                node_html = f'<div class="flow-node {node_class}"><div class="node-q">Q{idx+1}</div><div class="node-diff">{node_diff}</div><div class="node-status">{status_icon}</div></div>'
                nodes_html.append(node_html)
                
            arrow_html = '<div class="flow-arrow">➔</div>'
            flowchart_html = textwrap.dedent(f"""
            <style>
            .flow-container {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: center;
                gap: 15px;
                margin: 1.5rem 0 2.5rem 0;
                padding: 1.5rem;
                background: rgba(20, 26, 38, 0.45);
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
                background: rgba(12, 16, 26, 0.85);
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
            """).strip()
            
            combined_elements = []
            for i, node in enumerate(nodes_html):
                combined_elements.append(node)
                if i < len(nodes_html) - 1:
                    combined_elements.append(arrow_html)
            flowchart_html += " ".join(combined_elements)
            flowchart_html += "</div>"
            st.markdown(flowchart_html, unsafe_allow_html=True)

        # ── AI Learning Report ──
        if st.session_state["learning_report"] is None:
            # Prepare quiz stats for LLM analysis (API Call 2)
            quiz_statistics = {
                "score": f"{correct_count}/{len(mcqs)}",
                "percentage": pct,
                "quiz_mode": active_quiz_mode,
                "elapsed_time_seconds": total_time_spent,
                "questions": [
                    {
                        "question": q["question"],
                        "topic": q.get("topic", "General"),
                        "difficulty": st.session_state["difficulty_history"][idx],
                        "user_answer": st.session_state["answers"].get(idx),
                        "correct_answer": q["correct"],
                        "is_correct": (st.session_state["answers"].get(idx) == q["correct"])
                    }
                    for idx, q in enumerate(mcqs)
                ]
            }
            
            with st.spinner("AI is generating your personalized Learning Report..."):
                report, err = generate_learning_report(quiz_statistics, api_key, model_name)
                if err:
                    st.error(f"Failed to generate report: {err}")
                elif report:
                    st.session_state["learning_report"] = report
                    
        # Render Learning Report
        report = st.session_state["learning_report"]
        if report:
            st.markdown("## 📊 AI Personalized Learning Report")
            
            col_rep1, col_rep2 = st.columns([1, 2])
            with col_rep1:
                st.markdown(f"""
                <div class="score-box" style="padding: 1.5rem; margin-bottom:1rem; border-color: rgba(204,255,0,0.2);">
                    <div style="font-size:0.8rem; text-transform:uppercase; color:#94a3b8; font-weight:700;">Overall Skill Level</div>
                    <div class="score-number" style="font-size:2rem; margin:10px 0;">{report['overall_skill_level']}</div>
                    <div style="font-size:0.8rem; text-transform:uppercase; color:#94a3b8; font-weight:700; margin-top:20px;">Interview Readiness</div>
                    <div class="score-number" style="font-size:2.8rem; margin:10px 0; background:linear-gradient(135deg, #00f0ff 0%, #bd00ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{report['interview_readiness']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_rep2:
                st.markdown("### 🔍 Learning Summary")
                st.write(report["learning_summary"])
                st.markdown(f"*Motivational Feedback:* \"{report['motivational_feedback']}\"")
                
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("#### 🌟 Strong Topics")
                for item in report.get("strong_topics", []):
                    st.markdown(f"✅ {item}")
                st.markdown("#### ⚠️ Common Mistake Patterns")
                for item in report.get("common_mistakes", []):
                    st.markdown(f"❌ {item}")
            with col_t2:
                st.markdown("#### 📉 Weak Topics")
                for item in report.get("weak_topics", []):
                    st.markdown(f"🔸 {item}")
                st.markdown("#### 🗺️ Next Recommended Topics")
                for item in report.get("recommended_next_topics", []):
                    st.markdown(f"🚀 {item}")
                    
            st.markdown("### 📅 Actionable Personalized Study Plan")
            for item in report.get("study_plan", []):
                st.markdown(f"▪️ {item}")
            st.markdown("<br><hr style='border-color: rgba(255,255,255,0.08)'><br>", unsafe_allow_html=True)

        # ── Graded Questions & On-Demand AI Tutor ──
        st.markdown("## 🔍 Question-by-Question Review")
        
        for i, q in enumerate(mcqs):
            user_ans = st.session_state["answers"].get(i)
            correct_ans = q["correct"]
            cat = q.get("topic", q.get("category", "General"))
            q_diff = st.session_state["difficulty_history"][i]
            
            options_html = ""
            for key, val in q["options"].items():
                css_class = "option"
                badge = ""
                if key == correct_ans:
                    css_class += " correct"
                    badge = " (Correct Answer)"
                elif key == user_ans and key != correct_ans:
                    css_class += " wrong"
                    badge = " (Your Selection)"
                options_html += f'<div class="{css_class}"><b>{key}.</b> {val}{badge}</div>'
                
            st.markdown(textwrap.dedent(f"""
            <div class="mcq-card">
                <div class="q-number">
                    <span>Question {i+1} &nbsp;·&nbsp; {cat}</span>
                    <span class="diff-badge diff-{q_diff}">{q_diff}</span>
                </div>
                <div class="q-text">{q["question"]}</div>
                {options_html}
                <div class="explanation">💡 <b>Explanation:</b> {q["explanation"]}</div>
            </div>
            """), unsafe_allow_html=True)
            
            # AI Tutor Section
            tutor_key = f"tutor_{i}"
            if tutor_key in st.session_state["tutor_explanations"]:
                t_exp = st.session_state["tutor_explanations"][tutor_key]
                st.markdown(f"""
                <div style="background: rgba(0, 240, 255, 0.04); border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 12px; padding: 18px; margin-bottom: 25px; margin-top: -10px;">
                    <div style="font-weight: 800; color: #00f0ff; font-family: 'Syne', sans-serif; font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span>💬 AI Tutor Insight</span>
                    </div>
                    <p><b>Why Correct:</b> {t_exp['why_correct']}</p>
                    <p><b>Why Selected Incorrect:</b> {t_exp['why_incorrect']}</p>
                    <p><b>In Simple Terms:</b> {t_exp['simple_explanation']}</p>
                    <p><b>💡 Analogy:</b> <i>{t_exp['analogy']}</i></p>
                    <p><b>🔑 Memory Trick:</b> <code>{t_exp['memory_trick']}</code></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button("💬 Ask AI Tutor to Explain Answer", key=f"btn_tutor_{i}"):
                    with st.spinner("AI Tutor is analyzing..."):
                        t_data, err = get_tutor_explanation(
                            question=q["question"],
                            options=q["options"],
                            correct=correct_ans,
                            selected=user_ans if user_ans else "None",
                            api_key=api_key,
                            model_name=model_name
                        )
                        if err:
                            st.error(f"Tutor failed: {err}")
                        elif t_data:
                            st.session_state["tutor_explanations"][tutor_key] = t_data
                            st.rerun()

        st.markdown("---")
        
        # Download Panel
        st.markdown("### 📥 Download Quiz Materials")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(label="📄 Markdown Notes", data=generate_markdown(mcqs), file_name="quizlab_mcq_notes.md", mime="text/markdown")
        with c2:
            st.download_button(label="📦 Raw JSON", data=json.dumps(mcqs, indent=2), file_name="quizlab_mcq_data.json", mime="application/json")
        with c3:
            st.download_button(label="⚡ Anki Flashcards", data=generate_anki(mcqs), file_name="quizlab_mcq_anki.txt", mime="text/tab-separated-values")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Reset control buttons
        col_nav_back, col_nav_fc = st.columns(2)
        if col_nav_back.button("🏠 Return to Homepage", key="btn_return_home"):
            st.session_state["active_view"] = "setup"
            st.session_state["material_data"] = None
            st.session_state["mcqs"] = []
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.session_state["quiz_page"] = 0
            st.session_state["tutor_explanations"] = {}
            st.session_state["learning_report"] = None
            st.session_state["db_saved"] = False
            st.session_state["used_questions_indices"] = []
            st.rerun()
            
        if col_nav_fc.button("⚡ Study Flashcards", key="btn_go_fc"):
            st.session_state["active_view"] = "flashcards"
            st.session_state["flashcard_idx"] = 0
            st.session_state["flashcard_flipped"] = False
            st.rerun()

# ==================================================================
# SCREEN 4: Flashcards Review View
# ==================================================================
elif st.session_state["active_view"] == "flashcards":
    flashcards = st.session_state["material_data"]["flashcards"]
    fc_idx = st.session_state["flashcard_idx"]
    flipped = st.session_state["flashcard_flipped"]
    
    st.markdown("## ⚡ AI Interactive Flashcards")
    st.markdown("Review terms and concepts extracted from your study material:")
    
    card = flashcards[fc_idx]
    
    # Render Flashcard
    flipped_class = "flipped" if flipped else ""
    st.markdown(f"""
    <div class="flip-card {flipped_class}">
      <div class="flip-card-inner">
        <div class="flip-card-front">
          <div class="flashcard-topic">{card.get('topic', 'Concept')} · {card.get('difficulty', 'Medium')}</div>
          <div class="flashcard-text">{card['front']}</div>
          <div style="font-size:0.8rem; color:#64748b; margin-top:25px;">⚡ Click Flip below to see description</div>
        </div>
        <div class="flip-card-back">
          <div class="flashcard-topic">{card.get('topic', 'Concept')} · {card.get('difficulty', 'Medium')}</div>
          <div class="flashcard-text" style="font-size:1.1rem; font-weight:400; color:#e2e8f0;">{card['back']}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Controls
    col_flip, col_prev, col_next = st.columns([1, 1, 1])
    with col_flip:
        if st.button("🔄 Flip Card", key="fc_btn_flip"):
            st.session_state["flashcard_flipped"] = not flipped
            st.rerun()
    with col_prev:
        if st.button("⬅️ Previous Card", disabled=(fc_idx == 0), key="fc_btn_prev"):
            st.session_state["flashcard_idx"] = max(0, fc_idx - 1)
            st.session_state["flashcard_flipped"] = False
            st.rerun()
    with col_next:
        if st.button("Next Card ➡️", disabled=(fc_idx == len(flashcards) - 1), key="fc_btn_next"):
            st.session_state["flashcard_idx"] = min(len(flashcards) - 1, fc_idx + 1)
            st.session_state["flashcard_flipped"] = False
            st.rerun()
            
    st.markdown(f"<p style='text-align:center; color:#94a3b8; font-weight:500;'>Card {fc_idx + 1} of {len(flashcards)}</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Back to Knowledge Profile", key="fc_back_home"):
        st.session_state["active_view"] = "extracted_knowledge"
        st.rerun()

# ==================================================================
# SCREEN 5: Local Analytics Dashboard View
# ==================================================================
elif st.session_state["active_view"] == "dashboard":
    st.markdown("## 📊 Personal Learning Analytics Dashboard")
    st.markdown("This dashboard tracks your performance metrics locally without hitting the Groq API.")
    
    history = get_quiz_history()
    
    if not history:
        st.info("No quiz history recorded yet. Complete a quiz to see analytics!")
        if st.button("🏠 Back to Homepage", key="dash_back_home_empty"):
            st.session_state["active_view"] = "extracted_knowledge" if st.session_state["material_data"] else "setup"
            st.rerun()
    else:
        # Compute Overall Metrics
        total_quizzes = len(history)
        total_score = sum(h["score"] for h in history)
        total_questions = sum(h["total"] for h in history)
        avg_percentage = int((total_score / total_questions) * 100) if total_questions > 0 else 0
        avg_time = sum(h["elapsed_time"] for h in history) / total_quizzes if total_quizzes > 0 else 0
        
        # Cards row
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            st.markdown(f"""
            <div class="custom-card">
                <div class="custom-card-title">Completed</div>
                <div class="custom-card-value">{total_quizzes} Quizzes</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c2:
            st.markdown(f"""
            <div class="custom-card">
                <div class="custom-card-title">Avg Accuracy</div>
                <div class="custom-card-value">{avg_percentage}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c3:
            st.markdown(f"""
            <div class="custom-card">
                <div class="custom-card-title">Avg Resp Time</div>
                <div class="custom-card-value">{int(avg_time // 60)}m {int(avg_time % 60)}s</div>
            </div>
            """, unsafe_allow_html=True)
        with col_c4:
            st.markdown(f"""
            <div class="custom-card">
                <div class="custom-card-title">Total Questions</div>
                <div class="custom-card-value">{total_questions} Qs</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Topic Analysis
        topic_acc = {}
        for h in history:
            for topic, stats in h.get("topic_stats", {}).items():
                if topic not in topic_acc:
                    topic_acc[topic] = {"correct": 0, "total": 0}
                topic_acc[topic]["correct"] += stats["correct"]
                topic_acc[topic]["total"] += stats["total"]
                
        topic_percentages = {}
        for topic, stats in topic_acc.items():
            topic_percentages[topic] = int((stats["correct"] / stats["total"]) * 100)
            
        strongest = [t for t, p in topic_percentages.items() if p >= 70]
        weakest = [t for t, p in topic_percentages.items() if p < 50]
        
        col_list1, col_list2 = st.columns(2)
        with col_list1:
            st.markdown("### 🌟 Strongest Concepts (>=70% Accuracy)")
            if strongest:
                for s in strongest:
                    st.markdown(f"✅ **{s}** ({topic_percentages[s]}%)")
            else:
                st.markdown("*No topics at this level yet. Keep practicing!*")
        with col_list2:
            st.markdown("### ⚠️ Weakest Concepts (<50% Accuracy)")
            if weakest:
                for w in weakest:
                    st.markdown(f"🔸 **{w}** ({topic_percentages[w]}%)")
            else:
                st.markdown("*None! You are demonstrating excellent baseline comprehension.*")
                
        st.markdown("<br><hr style='border-color: rgba(255,255,255,0.08)'><br>", unsafe_allow_html=True)
        
        # Render Heatmap activity
        st.markdown("### 📅 Study Consistency Grid (Last 14 Days)")
        st.markdown("Consistent daily practice accelerates deep concept encoding.")
        
        today = datetime.date.today()
        activity = {}
        for h in history:
            date_str = h["timestamp"].split(" ")[0]
            activity[date_str] = activity.get(date_str, 0) + 1
            
        heatmap_html = "<div class='heatmap-container'>"
        for i in range(13, -1, -1):
            day = today - datetime.timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            count = activity.get(day_str, 0)
            
            if count == 0:
                lvl = "lvl-0"
            elif count == 1:
                lvl = "lvl-1"
            else:
                lvl = "lvl-2"
            
            day_label = day.strftime("%b %d")
            heatmap_html += f"<div class='heatmap-day {lvl}' title='{day_label}: {count} quiz(zes)'></div>"
        heatmap_html += "</div>"
        st.markdown(heatmap_html, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts Row
        st.markdown("### 📈 Performance Visualizations")
        col_ch1, col_ch2 = st.columns(2)
        
        with col_ch1:
            st.markdown("#### Concept Accuracy Breakdown")
            if topic_percentages:
                df_topic = pd.DataFrame(list(topic_percentages.items()), columns=["Concept", "Accuracy (%)"])
                st.bar_chart(df_topic.set_index("Concept"))
            else:
                st.write("Insufficient data for topic charting.")
                
        with col_ch2:
            st.markdown("#### Accuracy Trend Over Time")
            trend_data = [{"Index": i+1, "Accuracy (%)": h["percentage"]} for i, h in enumerate(history)]
            df_trend = pd.DataFrame(trend_data)
            st.line_chart(df_trend.set_index("Index"))
            
        # Difficulty Stats
        diff_acc = {}
        for h in history:
            for d, stats in h.get("difficulty_stats", {}).items():
                if d not in diff_acc:
                    diff_acc[d] = {"correct": 0, "total": 0}
                diff_acc[d]["correct"] += stats["correct"]
                diff_acc[d]["total"] += stats["total"]
                
        diff_percentages = {}
        for d, stats in diff_acc.items():
            diff_percentages[d] = int((stats["correct"] / stats["total"]) * 100)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Performance by Question Difficulty")
        if diff_percentages:
            df_diff = pd.DataFrame(list(diff_percentages.items()), columns=["Difficulty", "Accuracy (%)"])
            st.bar_chart(df_diff.set_index("Difficulty"))
            
        st.markdown("<br><hr style='border-color: rgba(255,255,255,0.08)'><br>", unsafe_allow_html=True)
        
        # Past logs table
        st.markdown("### 📜 Past Sessions Logs")
        df_history = pd.DataFrame([
            {
                "Date": h["timestamp"],
                "Material": h["quiz_title"],
                "Score": f"{h['score']}/{h['total']}",
                "Accuracy": f"{h['percentage']}%",
                "Mode": h["quiz_mode"],
                "Time Spent": f"{h['elapsed_time'] // 60}m {h['elapsed_time'] % 60}s"
            }
            for h in reversed(history)
        ])
        st.dataframe(df_history, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🏠 Return to Platform", key="dash_back_home"):
                st.session_state["active_view"] = "extracted_knowledge" if st.session_state["material_data"] else "setup"
                st.rerun()
        with col_b2:
            if st.button("🗑️ Clear Learning History", key="dash_clear_history"):
                if clear_quiz_history():
                    st.success("History cleared successfully!")
                    st.rerun()