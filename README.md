# 🧠 QuizLab

**QuizLab** is a premium, high-fidelity AI-powered MCQ Generator that extracts study material from PDFs or plain text and crafts customized, exam-ready multiple-choice questions instantly using the ultra-fast **Groq API** (powered by `llama-3.3-70b-versatile`). 

Built with **Streamlit** and heavily customized with a **cyberpunk glassmorphic design system**, QuizLab offers a state-of-the-art interactive study experience.

---

## ✨ Key Features

* **🎨 Cyberpunk Glassmorphic UI**: Sleek dark theme featuring radial gradients, neon glows, custom typography, and responsive hover transitions.
* **📄 Dual Input Modes**: Upload any digital PDF or simply copy-paste plain text (notes, articles, slides) directly into the generator.
* **🧭 Step-by-Step Quiz Pagination**: Display one question card at a time for distraction-free testing, complete with smart state preservation when navigating back and forth.
* **🎯 Interactive Navigation Deck**: A sidebar progress tracker featuring a clickable numerical keypad (`Q1`, `Q2 ✓`, etc.) showing your completion status and letting you jump to any question instantly.
* **⚙️ Robust Extraction Fallback**: A dual-parser pipeline that attempts parsing using `PyMuPDF` (`fitz`) first, falling back automatically to `pdfplumber` for maximum text recovery.
* **📊 Conceptual Breakdown Grid**: After submission, view your quiz score alongside an analytics breakdown showing your accuracy percentage in each sub-topic tested.
* **🔍 Recommended Review Session**: Missed questions are consolidated into a review deck showing your choice, the correct answer, and detailed AI explanations.
* **📥 Multi-Format Export Center**: Download your study materials instantly:
  * **Markdown Study Notes**: A formatted study sheet.
  * **Raw JSON**: Standardized quiz data.
  * **Anki Flashcards (TSV)**: Ready-to-import flashcard files with HTML formatting for Anki.

---

## 🛠️ Technology Stack

* **Frontend Framework**: [Streamlit](https://streamlit.io/)
* **AI Model Engine**: [Groq Cloud API](https://console.groq.com/) (LLaMA 3.3 70B model backend)
* **Document Parsing**: [PyMuPDF](https://pymupdf.readthedocs.io/) & [pdfplumber](https://github.com/jsvine/pdfplumber)
* **Styling & UI**: Custom HTML5 & CSS3 variables (Outfit / Syne fonts, neon glow box-shadows)

---

## 🚀 Getting Started Locally

### Prerequisites
* Python 3.9 or higher installed.
* A Groq API Key (get one for free at [console.groq.com](https://console.groq.com/)).

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MeetChhugani/QuizLab.git
   cd QuizLab
   ```

2. **Install dependencies**:
   ```bash
   pip install -r Mcq_requirements.txt
   ```

3. **Configure your API Key**:
   Create a folder named `.streamlit` in the root of the project, and create a file inside it named `secrets.toml`:
   ```bash
   mkdir .streamlit
   notepad .streamlit/secrets.toml
   ```
   Add your Groq API Key in the following format:
   ```toml
   GROQ_API_KEY = "your-actual-groq-api-key-here"
   ```

4. **Run the application**:
   ```bash
   streamlit run mcq_app.py
   ```
   Open your browser to `http://localhost:8501` to start generating quizzes!

---

## ☁️ Deploying to the Web (Streamlit Community Cloud)

You can host QuizLab live for free using **Streamlit Community Cloud**:

1. Push this repository to your GitHub account.
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **New App**, select your `QuizLab` repository, set the branch to `main`, and the main file path to `mcq_app.py`.
4. Click **Advanced settings** at the bottom of the page before deploying.
5. In the **Secrets** field, paste your Groq API Key config:
   ```toml
   GROQ_API_KEY = "your-actual-groq-api-key-here"
   ```
6. Click **Save** and then **Deploy!** Your app will be live on a public URL in less than 2 minutes.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
