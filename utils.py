import json
import re
from groq import Groq

def _pre_clean_json_text(s):
    """
    Cleans up common LLM JSON formatting errors like list bullet characters
    or numbers inside arrays (e.g. 1. "Item" -> "Item").
    """
    if not s:
        return s
    # Match numbered prefixes (e.g. 1. ") or bullet prefixes (e.g. - " or * ")
    # before a string value and replace with just the quote.
    cleaned = re.sub(r'(\d+\.\s*|[-*]\s*)(")', r'\2', s)
    return cleaned

def _repair_json(s):
    """
    Attempts to repair truncated or slightly malformed JSON strings by balancing
    unclosed quotes, braces, and brackets, and removing trailing commas.
    """
    s = s.strip()
    if not s:
        return s
        
    open_chars = []
    in_string = False
    escape = False
    
    for char in s:
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in ('{', '['):
                open_chars.append(char)
            elif char in ('}', ']'):
                if open_chars:
                    open_chars.pop()
                    
    # If we are inside an unclosed string at the end of truncation, close the string
    if in_string:
        s += '"'
        
    # Strip trailing commas, colons, or whitespace that make it invalid before appending brackets/braces
    while s and s[-1] in (',', ':', ' ', '\n', '\r', '\t'):
        s = s[:-1]
        
    # Close any unclosed braces/brackets in reverse order
    while open_chars:
        c = open_chars.pop()
        if c == '{':
            s += '}'
        elif c == '[':
            s += ']'
            
    return s

def _clean_and_parse_json(raw_text):
    """
    Cleans markdown code blocks and attempts to parse valid JSON from text.
    Uses pre-cleaning regex and fallback active JSON repair if truncated.
    """
    # Pre-clean list numbers/bullets
    raw = _pre_clean_json_text(raw_text).strip()
    
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith(("{", "[")):
                try:
                    return json.loads(part)
                except Exception:
                    try:
                        return json.loads(_repair_json(part))
                    except Exception:
                        pass
    try:
        return json.loads(raw)
    except Exception as e:
        # Try repairing raw
        try:
            return json.loads(_repair_json(raw))
        except Exception:
            pass

        # Fallback: locate matching outer brackets
        first_curly = raw.find("{")
        first_bracket = raw.find("[")
        
        start_idx = -1
        if first_curly != -1 and first_bracket != -1:
            start_idx = min(first_curly, first_bracket)
        elif first_curly != -1:
            start_idx = first_curly
        elif first_bracket != -1:
            start_idx = first_bracket

        last_curly = raw.rfind("}")
        last_bracket = raw.rfind("]")
        
        end_idx = -1
        if last_curly != -1 and last_bracket != -1:
            end_idx = max(last_curly, last_bracket)
        elif last_curly != -1:
            end_idx = last_curly
        elif last_bracket != -1:
            end_idx = last_bracket

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            substring = raw[start_idx:end_idx+1]
            try:
                return json.loads(substring)
            except Exception:
                try:
                    return json.loads(_repair_json(substring))
                except Exception:
                    pass
                    
            # Try to repair a truncated substring that lacks closing characters
            try:
                truncated_substring = raw[start_idx:]
                return json.loads(_repair_json(truncated_substring))
            except Exception:
                pass
        
        # Log raw response for diagnostic purposes
        try:
            import os
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groq_error_debug.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Exception: {str(e)}\n\nRaw Text:\n{raw_text}")
        except Exception:
            pass
            
        raise e

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
        q_dict = _clean_and_parse_json(raw)
        
        # Validate structure
        required_keys = ["question", "options", "correct", "explanation"]
        if not all(k in q_dict for k in required_keys) or len(q_dict["options"]) != 4:
            raise ValueError("JSON response structure is incomplete or invalid.")
            
        return q_dict, None
    except Exception as e:
        return None, str(e)

def generate_learning_material(text, custom_focus, api_key, model_name, temperature=0.35, seed=0):
    """
    Executes API Call 1: Combined analysis, question pool (Easy, Medium, Hard), and flashcards.
    Returns (material_dict, error_message).
    """
    focus_instruction = f"- Focus the generation specifically on the topic or keyword: '{custom_focus}'." if custom_focus.strip() else ""
    seed_instruction = f"\n- Ensure this generation session is unique and focuses on different aspects, questions, and details than previous sessions (Session Seed: {seed})." if seed else ""
    
    prompt = f"""You are an elite educational AI engine. Analyze the provided study material and generate a comprehensive structured learning pack.{seed_instruction}

Study Material:
\"\"\"{text}\"\"\"

Requirements:
1. Extract document metadata and structure:
   - "main_topics": A list of the main concepts/topics found.
   - "subtopics": A list of subtopics covered.
   - "difficulty_level": Overall text difficulty (Easy, Intermediate, or Advanced).
   - "estimated_reading_time": Estimated time to read this material (in minutes, e.g. "12 minutes").
   - "learning_objectives": List of key learning outcomes.
   - "recommended_num_questions": Recommended number of questions for this material.

2. Generate a balanced question pool of exactly 12 multiple choice questions:
   - 4 Easy questions (focus on core definitions and recall).
   - 4 Medium questions (focus on application and conceptual understanding).
   - 4 Hard questions (focus on critical analysis, debugging/scenarios, and evaluations).
   {focus_instruction}
   - Each question must contain: "question" (text), "options" (dict of keys A, B, C, D), "correct" (key letter), "explanation" (detailed text), "difficulty" ("Easy", "Medium", or "Hard"), and "topic" (subtopic name).

3. Generate exactly 6 intelligent flashcards:
   - Each flashcard must contain: "front" (question or concept to define), "back" (detailed answer/explanation), "topic" (subtopic name), and "difficulty" ("Easy", "Medium", or "Hard").

Return ONLY a valid JSON object matching the exact schema below, with no wrapping markdown, no extra conversational text, and no invalid formatting.
IMPORTANT: Do NOT include numbers or bullet point prefixes (like 1., 2., -, *) inside your JSON array values or keys. The JSON arrays must contain raw, plain string elements only.

JSON output structure:
{{
  "analysis": {{
    "main_topics": ["Topic A", "Topic B"],
    "subtopics": ["Subtopic A1", "Subtopic B1"],
    "difficulty_level": "Intermediate",
    "estimated_reading_time": "15 minutes",
    "learning_objectives": ["Understand X", "Apply Y"],
    "recommended_num_questions": 8
  }},
  "questions": [
    {{
      "question": "Question text?",
      "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
      "correct": "B",
      "explanation": "Why B is correct.",
      "difficulty": "Easy",
      "topic": "Topic A"
    }}
  ],
  "flashcards": [
    {{
      "front": "Flashcard front prompt?",
      "back": "Flashcard back answer detail.",
      "topic": "Topic A",
      "difficulty": "Medium"
    }}
  ]
}}"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4096
        )
        raw = response.choices[0].message.content.strip()
        data = _clean_and_parse_json(raw)
        
        # Validations
        if "analysis" not in data or "questions" not in data or "flashcards" not in data:
            raise ValueError("Missing critical fields in combined generation response.")
            
        return data, None
    except Exception as e:
        return None, str(e)

def get_tutor_explanation(question, options, correct, selected, api_key, model_name):
    """
    On-Demand API Call: Generates an AI tutor explanation for a specific question based on user response.
    Returns (explanation_dict, error_message).
    """
    prompt = f"""You are a supportive, brilliant personal AI Tutor. Provide a highly engaging explanation of the following question.

Question:
{question}

Options:
{json.dumps(options, indent=2)}

Correct Option: {correct}
User Selected Option: {selected}

Please generate the tutoring explanation as a JSON object containing the following keys:
- "why_correct": Clear explanation of why the correct option ({correct}) is right.
- "why_incorrect": Explanation of why the user's selected option ({selected}) is incorrect (if they selected the wrong answer. If they selected correct, write a congratulatory sentence highlighting why the distractor options are wrong).
- "simple_explanation": A 2-sentence simplified explanation of the core concept.
- "analogy": A memorable real-world analogy explaining the concept.
- "memory_trick": A clever mnemonic or memory trick to never forget this concept.

Return ONLY a valid JSON object matching this structure."""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.45,
            max_tokens=1000
        )
        raw = response.choices[0].message.content.strip()
        data = _clean_and_parse_json(raw)
        
        required = ["why_correct", "why_incorrect", "simple_explanation", "analogy", "memory_trick"]
        if not all(k in data for k in required):
            raise ValueError("Tutor JSON response is missing required keys.")
            
        return data, None
    except Exception as e:
        return None, str(e)

def generate_learning_report(quiz_statistics, api_key, model_name):
    """
    API Call 2: Generate personalized learning report.
    Returns (report_dict, error_message).
    """
    prompt = f"""You are an expert Educational Data Analyst. Review the following quiz statistics and construct a comprehensive, personalized study plan and interview readiness report.

Quiz Stats:
{json.dumps(quiz_statistics, indent=2)}

Please generate the report as a JSON object containing the following keys:
- "overall_skill_level": e.g., "Beginner", "Intermediate", "Advanced", or "Expert".
- "strong_topics": List of topics/concepts the user demonstrated solid mastery of.
- "weak_topics": List of topics/concepts the user struggled with or got wrong.
- "common_mistakes": List of cognitive traps or misunderstandings highlighted by the mistakes.
- "learning_summary": A detailed synthesis summarizing their performance.
- "interview_readiness": A percentage score (e.g. "82%") representing readiness for professional interviews on these concepts, followed by a short explanation.
- "study_plan": A step-by-step actionable plan with numbered advice items for revision.
- "recommended_next_topics": List of advanced or adjacent topics they should study next.
- "motivational_feedback": A inspiring, personalized closing message.

Return ONLY a valid JSON object matching this structure.
IMPORTANT: Do NOT include list numbers or bullet prefixes (like 1., 2., -, *) inside your JSON array values or keys. The JSON arrays must contain raw, plain string elements only. (Example: "study_plan": ["Item A", "Item B"] and NOT "study_plan": [1. "Item A", 2. "Item B"])."""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096
        )
        raw = response.choices[0].message.content.strip()
        data = _clean_and_parse_json(raw)
        
        required = ["overall_skill_level", "strong_topics", "weak_topics", "learning_summary", 
                    "interview_readiness", "study_plan", "recommended_next_topics", "motivational_feedback"]
        if not all(k in data for k in required):
            raise ValueError("Learning Report JSON response is missing required keys.")
            
        return data, None
    except Exception as e:
        return None, str(e)
