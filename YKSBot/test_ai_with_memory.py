# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 03:17:55 2025

@author: dogan
"""

import os
import openai
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

PROFILE_FILENAME = "student_profile.json"

# --- SIMULATE NEW DATA ---
# This is the data for the student's *second* exam.
new_exam_data = {
    "exam_date": str(date.today()),
    "exam_name": "Deneme Sınavı 2",
    "results": {
        "TYT Türkçe Net": 35.0,          # Improved
        "TYT Temel Matematik Net": 25.5,  # Improved
        "TYT Fen Bilimleri Net": 20.0,
        "AYT Matematik Net": 25.0,
        "AYT Fizik Net": 8.5,           # Improved
        "AYT Kimya Net": 11.5,           # Slightly worse
        "AYT Biyoloji Net": 13.0
    }
}

def load_or_create_profile():
    """Loads the student profile from a file, or creates a default one if it doesn't exist."""
    try:
        with open(PROFILE_FILENAME, 'r', encoding='utf-8') as f:
            print(f"Loading existing profile from '{PROFILE_FILENAME}'...")
            return json.load(f)
    except FileNotFoundError:
        print(f"No profile found. Creating a new one...")
        # This is the initial state of a brand new student.
        return {
            "student_info": {
                "name": "Ayşe Yılmaz",
                "goal": "Tıp Fakültesi (Medicine)",
                "weekly_hours": 18
            },
            "exam_history": [
                {
                    "exam_date": "2024-03-15",
                    "exam_name": "Deneme Sınavı 1",
                    "results": {
                        "TYT Türkçe Net": 28.5, "TYT Temel Matematik Net": 12.0, "TYT Fen Bilimleri Net": 15.75,
                        "AYT Matematik Net": 10.25, "AYT Fizik Net": 2.5, "AYT Kimya Net": 8.0, "AYT Biyoloji Net": 11.25
                    }
                }
            ]
        }

def save_profile(profile_data):
    """Saves the student profile to a file."""
    with open(PROFILE_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=4)
    print(f"Profile updated and saved to '{PROFILE_FILENAME}'.")


def create_contextual_prompt(profile_data):
    """Builds a prompt that includes the student's history for context."""
    # Use f-strings and json.dumps for clean formatting inside the prompt
    history_str = json.dumps(profile_data['exam_history'], indent=2, ensure_ascii=False)
    
    prompt = f"""
    You are "YKS Koçu," an expert AI study coach for Turkey's university exam (YKS).
    You are creating a new 1-week study plan for a student you have been tracking.
    Your output MUST be a valid JSON object and nothing else.

    **Student Profile:**
    - Name: {profile_data['student_info'].get('name')}
    - Target Major: {profile_data['student_info'].get('goal')}
    - Available Weekly Study Hours: {profile_data['student_info'].get('weekly_hours')}

    **Student's Full Exam History:**
    {history_str}

    **Your Coaching Task:**
    1.  **Analyze the student's progress.** Compare the latest exam results with the previous ones.
    2.  **Identify areas of improvement** and acknowledge them to motivate the student.
    3.  **Pinpoint subjects where they are stagnating or have declined** (e.g., Kimya in this case). These should be a priority.
    4.  Create a new 1-week study plan that addresses these findings. Focus on weak areas but also maintain strengths.
    5.  In the "weekly_summary," act like a coach. Briefly mention their progress and the focus for the upcoming week.

    The final JSON output must strictly follow this structure:
    {{
      "weekly_summary": "Your analysis and encouraging summary here.",
      "plan": [ ... a full 7-day plan ... ]
    }}
    """
    return prompt

def main():
    # Step 1: Load the student's profile (or create a new one).
    student_profile = load_or_create_profile()
    
    # Step 2: Add the new exam results to their history.
    print("\nAdding new exam results to the profile...")
    student_profile["exam_history"].append(new_exam_data)
    
    # Step 3: Create the contextual prompt.
    print("Generating a contextual prompt with the student's full history...")
    prompt = create_contextual_prompt(student_profile)
    
    print("Calling OpenAI API with the new context...")
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful study planner assistant that only outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )
        
        ai_response_str = response.choices[0].message.content
        plan_json = json.loads(ai_response_str)

        # Step 4: Save the AI's plan to a file.
        plan_filename = f"study_plan_{date.today()}.json"
        with open(plan_filename, 'w', encoding='utf-8') as f:
            json.dump(plan_json, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Success! New plan saved to '{plan_filename}'")
        
        # Step 5: Save the student's updated profile for next time.
        save_profile(student_profile)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()