import os
import openai
import json
from datetime import date
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# The name of our student data file
PROFILE_FILENAME = "student_profile.json"

def load_student_profile():
    """Loads the student profile from a file, or creates a default one if it doesn't exist."""
    try:
        with open(PROFILE_FILENAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # If no profile exists, create a basic one. The first exam will be added to this.
        return {
            "student_info": {
                "name": "Ayşe Yılmaz",
                "goal": "Bilgisayar Mühendisliği",
                "weekly_hours": 20
            },
            "exam_history": [] # Start with an empty history
        }

def save_student_profile(profile_data):
    """Saves the student profile to a file."""
    with open(PROFILE_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=4)

def create_contextual_prompt(student_data):
    history_str = json.dumps(student_data.get('exam_history', []), indent=2, ensure_ascii=False)
    
    prompt = f"""
    You are "YKS Koçu," an expert AI study coach for Turkey's university exam.
    Your output MUST be a valid JSON object.
    
    **Student Profile:**
    - Target Major: {student_data['student_info'].get('goal')}
    - Weekly Hours: {student_data['student_info'].get('weekly_hours')}
    
    **Student's Full Exam History (Net Scores):**
    {history_str}
    
    **Your Task and Rules:**
    1.  Analyze the student's progress by comparing their most recent exam to previous ones. Identify subjects where they improved and subjects where they declined or stagnated.
    2.  Write a brief, encouraging summary in the "weekly_summary" field based on this analysis.
    3.  Create a 7-day study plan focused on the subjects the student needs to improve in.
    4.  **VERY IMPORTANT:** The student has NOT provided specific topics they are weak in. Therefore, you **MUST NOT** mention specific topics like 'Vektörler', 'Problemler', or 'Paragraf'. 
    5.  Instead, create general, action-oriented tasks. For example: "AYT Fizik dersinden 2 saat boyunca genel soru çözümü yap.", "TYT Türkçe dersinden 40 soru çöz.", or "Bu hafta işlenen konuları tekrar et."
    6.  The 'tasks' array must contain OBJECTS.

    **--- MANDATORY JSON OUTPUT STRUCTURE ---**
    You must follow this structure exactly. Use these English keys: "weekly_summary", "plan", "day", "tasks", "subject", "activity".
    **DO NOT include a "topic" key.**

    {{
      "weekly_summary": "Your analysis and motivational summary here.",
      "plan": [
        {{
          "day": "Pazartesi",
          "tasks": [
            {{
              "subject": "AYT Fizik",
              "activity": "Genel konu tekrarı yap ve 25 soru çöz."
            }},
            {{
              "subject": "TYT Matematik",
              "activity": "Genel soru bankasından 40 soru çöz."
            }}
          ]
        }}
      ]
    }}
    """
    return prompt
    # This function is now perfect, no changes needed here.
    # It will automatically include the full history we give it.
    history_str = json.dumps(student_data.get('exam_history', []), indent=2, ensure_ascii=False)
    
    prompt = f"""
    You are "YKS Koçu," an expert AI study coach. Your output MUST be a valid JSON object.
    
    **Student Profile:**
    - Target Major: {student_data['student_info'].get('goal')}
    - Weekly Hours: {student_data['student_info'].get('weekly_hours')}
    
    **Student's Full Exam History:**
    {history_str}
    
    **Your Task:**
    Analyze the student's progress, especially focusing on the MOST RECENT exam. Create a new 1-week study plan.
    In the "weekly_summary," act like a coach, mentioning their progress and the focus for the week.

    **--- MANDATORY JSON OUTPUT STRUCTURE ---**
    You must follow this structure exactly. Use these English keys.
    {{
      "weekly_summary": "Your analysis and motivational summary here.",
      "plan": [
        {{ "day": "Pazartesi", "tasks": [ {{"subject": "AYT Fizik", "topic": "Vektörler", "activity": "Konu anlatım videosu izle."}} ] }}
      ]
    }}
    """
    return prompt

@app.route('/generate-plan-with-new-results', methods=['POST'])
def generate_plan_with_new_results():
    try:
        # 1. Get the new exam results from the form
        new_exam_results = request.get_json()

        # 2. Load the student's existing profile (their history)
        student_profile = load_student_profile()

        # 3. Create a new exam entry and add it to the history
        new_exam_entry = {
            "exam_date": str(date.today()),
            "exam_name": f"Deneme Sınavı #{len(student_profile['exam_history']) + 1}",
            "results": new_exam_results
        }
        student_profile['exam_history'].append(new_exam_entry)

        # 4. Save the updated profile back to the file
        save_student_profile(student_profile)

        # 5. Generate the prompt with the FULL, updated history
        prompt = create_contextual_prompt(student_profile)
        
        # 6. Call OpenAI
        response = openai.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a helpful study planner assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )
        
        ai_generated_plan = response.choices[0].message.content
        return ai_generated_plan, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)