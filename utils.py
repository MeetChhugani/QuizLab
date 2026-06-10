import json

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
