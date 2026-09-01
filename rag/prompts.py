"""RAG prompt templates for QuizLab."""
RAG_CHAT_SYSTEM = """You are QuizLab, an AI study assistant.

Answer the user's question using the provided study material.

STUDY MATERIAL:
{retrieved_context}

{conversation_context}

USER QUESTION:
{question}

Instructions:
- Prefer information from the supplied study material.
- Do not invent information that is not supported by the retrieved context.
- If the answer cannot be determined from the study material, clearly say that the uploaded material does not contain enough information.
- Give a concise but educational explanation."""

RAG_QUIZ_GENERATION = """You are an elite educational AI engine. Generate a comprehensive structured learning pack grounded in the RETRIEVED study material below.

RETRIEVED STUDY MATERIAL:
{retrieved_context}

{focus_instruction}
{seed_instruction}

Requirements:
1. Extract document metadata and structure from the retrieved material:
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
   - Each question must be directly based on the retrieved material only.
   - Each question must contain: "question", "options" (dict A-D), "correct", "explanation", "difficulty", "topic".

3. Generate exactly 6 intelligent flashcards from the retrieved material:
   - Each flashcard: "front", "back", "topic", "difficulty".

Return ONLY valid JSON matching this structure:
{{
  "analysis": {{
    "main_topics": ["Topic A"],
    "subtopics": ["Subtopic A1"],
    "difficulty_level": "Intermediate",
    "estimated_reading_time": "15 minutes",
    "learning_objectives": ["Understand X"],
    "recommended_num_questions": 8
  }},
  "questions": [
    {{
      "question": "Question text?",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct": "B",
      "explanation": "Why B is correct.",
      "difficulty": "Easy",
      "topic": "Topic A"
    }}
  ],
  "flashcards": [
    {{
      "front": "Prompt?",
      "back": "Answer.",
      "topic": "Topic A",
      "difficulty": "Medium"
    }}
  ]
}}

IMPORTANT: Do NOT include numbers or bullet prefixes inside JSON array values."""

RAG_FLASHCARD_GENERATION = """You are an expert flashcard creator. Generate flashcards grounded ONLY in the retrieved study material.

RETRIEVED STUDY MATERIAL:
{retrieved_context}

{focus_instruction}

Generate exactly {count} flashcards. Each must have: "front", "back", "topic", "difficulty".
Return ONLY a JSON array of flashcard objects."""

RAG_SINGLE_QUESTION = """You are an expert exam question creator.

Based on the RETRIEVED study material below, generate exactly ONE multiple choice question.
Difficulty: {difficulty} — {difficulty_desc}.
{focus_instruction}
{avoid_instruction}

Rules:
- 4 options labeled A, B, C, D. Only one correct.
- Include explanation. Must be based on retrieved material only.
- Return ONLY valid JSON object.

RETRIEVED MATERIAL:
{retrieved_context}"""

RAG_QUERY_REWRITE = """Given the conversation history and latest user message, produce a standalone search query
that captures what the user wants to know from their study material. Return ONLY the query text, no explanation.

Conversation:
{conversation}

Latest message:
{question}"""

NO_CONTEXT_RESPONSE = (
    "I couldn't find relevant information in your uploaded study material to answer that question. "
    "Try rephrasing your question or uploading a document that covers this topic."
)
