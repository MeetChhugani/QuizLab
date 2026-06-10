import json
from groq import Groq

def generate_markdown(mcqs):
    md = "# Generated MCQ Quiz\n\n"
    for i, q in enumerate(mcqs):
        md += f"### Q{i+1}. {q['question']}\n"
        if 'category' in q:
            md += f"*Category: {q['category']}*\n\n"
        for k, v in q['options'].items():
            md += f"- [{k}] {v}\n"
        md += f"\n**Correct Answer: {q['correct']}**\n\n"
        md += f"*Explanation: {q['explanation']}*\n\n"
        md += "---\n\n"
    return md

def generate_anki(mcqs):
    anki = ""
    for q in mcqs:
        front = f"<b>{q['question']}</b><br><br>"
        options_list = [f"{k}. {v}" for k, v in q['options'].items()]
        front += "<br>".join(options_list)
        
        back = f"Correct Answer: <b>{q['correct']}</b><br><br>Explanation: {q['explanation']}"
        if 'category' in q:
            back += f"<br><br><i>Category: {q['category']}</i>"
        
        # Anki TSV uses tab as separator; strip tab characters and replace carriage returns with HTML tags
        front_clean = front.replace("\t", " ").replace("\n", "<br>")
        back_clean = back.replace("\t", " ").replace("\n", "<br>")
        anki += f"{front_clean}\t{back_clean}\n"
    return anki

def generate_single_question(text, difficulty, prev_questions, api_key, model_name, custom_focus):
    """
    Generates a single MCQ from the text context, avoiding duplicates in prev_questions.
    Returns (question_dict, error_message).
    """
    diff_map = {
        "Easy": "simple recall-based questions suitable for beginners",
        "Medium": "application and understanding questions requiring conceptual clarity",
        "Hard": "analysis and evaluation questions requiring deep understanding and critical thinking"
    }
    avoid_list = [q["question"] for q in prev_questions]
    avoid_list_str = "\n".join([f"- {title}" for title in avoid_list])
    avoid_instruction = f"IMPORTANT: Do NOT generate any of the following questions as they have already been used:\n{avoid_list_str}" if avoid_list else ""
    focus_instruction = f"- The question should focus specifically on: '{custom_focus}'." if custom_focus.strip() else ""

    prompt = f"""You are an expert exam question creator.

Based on the following text, generate exactly ONE multiple choice question.
Difficulty level: {difficulty} — {diff_map[difficulty]}.
{focus_instruction}

Rules:
- The question must have exactly 4 options labeled A, B, C, D.
- Only one option is correct.
- Include a brief explanation for the correct answer.
- Categorize the question into a logical concept or sub-topic covered in the text (e.g. 'Definitions', 'Applications', 'Causes', etc.)
- The question must be directly based on the provided text.
{avoid_instruction}
- Return ONLY a valid JSON object (not an array), no extra text, no markdown.

JSON format:
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

TEXT:
{text}"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.45,
            max_tokens=1000
        )
        raw = response.choices[0].message.content.strip()

        # Clean markdown
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    raw = part
                    break

        q_dict = json.loads(raw)
        
        # Validate structure
        required_keys = ["question", "options", "correct", "explanation"]
        if not all(k in q_dict for k in required_keys) or len(q_dict["options"]) != 4:
            raise ValueError("JSON response structure is incomplete or invalid.")
            
        return q_dict, None
    except Exception as e:
        return None, str(e)
