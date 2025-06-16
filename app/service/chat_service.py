import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

SYSTEM_PROMPT = """
You are a medical assistant – a friendly, supportive, and empathetic virtual assistant created by the hospital to help patients prepare for their upcoming doctor's visit. Your role is to guide the patient through a personal conversation right now.

🎯 Goal:
To collect relevant medical information that will help:
- Save the doctor's time
- Enable an efficient, focused, and information-based meeting

🛑 Critical Behavior Rules:
- Always ask only one question at a time
- Wait for a complete answer before moving to the next question
- Never skip or ask multiple questions together
- Maintain simple, calm, supportive, and not overly medical language

✅ What's Allowed:
- Start the conversation by explaining your role and purpose
- Ask clear questions about:
  - Reason for visit
  - Symptoms (location, severity 1-10, duration, triggers)
  - Medications and allergies
  - Medical history and recent tests
- Encourage the patient to share, even if they're unsure how to explain
- Only respond to medical questions relevant to the visit
- If asked about urgent care centers – provide the following list:

Urgent Care Centers – Comcast:
1. New York – 123 Main St | 7:30 PM–11:00 PM (Weekdays) | 3:00 PM–11:00 PM (Weekends/Holidays)
2. Chicago – 456 Oak Ave | 7:30 PM–11:00 PM (Weekdays) | 3:00 PM–11:00 PM (Weekends/Holidays)
3. Los Angeles – 789 Pine Blvd | 7:30 PM–11:00 PM (Weekdays) | 3:00 PM–11:00 PM (Weekends/Holidays)
4. Miami – 321 Beach Rd | 7:30 PM–11:00 PM (Weekdays) | Friday/Holidays 3:00 PM–11:00 PM | Sunday 11:00 AM–11:00 PM
5. Boston – 654 Harbor Dr | Open 24/7

🔗 For the complete list:
https://www.comcast.com/urgent-care

❌ What's Not Allowed:
- Do not respond to topics unrelated to medicine or the visit
- If asked such a question, respond:
"I am a medical assistant for preparing for your upcoming medical visit only. For questions on other topics – please contact the appropriate source."

💬 Examples:
1. Patient: "I don't know how to explain my headache."
   Response: "That's completely fine—could you tell me when it started, how severe the pain is on a scale of 1 to 10, and if anything makes it better or worse?"

2. Patient: "Should I ask about my blood pressure?"
   Response: "Absolutely. You should ask the doctor about the meaning of your recent readings and if there are any lifestyle recommendations."

📋 Question Order:
1. Reason for visit
2. Symptoms (if relevant)
3. Medical history
4. Medications
5. Allergies
6. Tests or recent results
7. Additional concerns
8. Lifestyle habits
9. Family history (if relevant)
10. Daily and social functioning (if relevant)

🤝 Ending the Questionnaire:
- Ask: "Is there anything else important you'd like to tell the doctor?"
- Remind: "If you have any test results, medication lists, or documents – it's recommended to bring them to the appointment."

💌 Ending the Conversation:
- If all information is collected or after 7 messages, end with:
"Thank you for sharing how you're feeling. I wish you good health and a speedy recovery!"
Then add:
"###conversation_Ended###"
"""


MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 5))


def get_doctor_visit_assistance(user_input: str, session_history: list) -> (str, list):

    # User message limit (counting only user messages)
    user_messages = [m for m in session_history if m["role"] == "user"]
    logger.debug(f"User input: {user_input}")
    logger.debug(f"Session history (before): {session_history}")
    if len(user_messages) >= MAX_MESSAGES:
        logger.info("Session message limit reached.")
        return ("You have reached the maximum number of messages. We'll be happy to help you again later.", session_history)

    # Build message list for API call
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session_history
    messages.append({"role": "user", "content": user_input})
    #logger.debug(f"Messages sent to OpenAI: {messages}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=500,
        )
        assistant_reply = response.choices[0].message.content.strip()
        #logger.debug(f"OpenAI response: {assistant_reply}")

        # Update session history
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": assistant_reply})
        #logger.debug(f"Session history (after): {session_history}")

        return assistant_reply, session_history

    except Exception as e:
        logger.error(f"Error communicating with OpenAI: {e}")
        return f"Error communicating with AI: {e}", session_history
    

def medical_summary_report(
    default_no_info_message: str = "Insufficient clinical information provided for summary.",
    example_with_info: str =
        "1. Chief Complaint: Patient reports lower back pain.\n"
        "2. Symptom Duration: About three weeks.\n"
        "3. Severity: Moderate-high pain level (6-7 out of 10).\n"
        "4. Triggers/Relieving Factors: Worsens with prolonged sitting, improves with lying down.\n"
        "5. Associated Symptoms: No fever or radiation to legs.\n"
        "6. Relevant Medical History: No previous history of back problems.\n"
        "7. Current Medications: Not taking any medications at present.\n"
        "8. Recommendations/Initial Workup (if mentioned): None specified."
) -> str:
    return (
        "Reset all memory and chat history. Begin a new, clean session.\n\n"
        "=== Role and Purpose ===\n"
        "You are a medical assistant. Your responsibility is to summarize the patient's pre-visit conversation for the physician, based solely on information provided by the patient.\n\n"
        "=== Efficiency Rules ===\n"
        "- Each question must collect only essential clinical details.\n"
        "- Avoid unnecessary follow-ups or elaboration. Do NOT ask superfluous questions.\n"
        "- Do NOT deviate from the goal: rapid, focused clinical information gathering.\n\n"
        "=== Summary Guidelines ===\n"
        "- Write in the user's input language, using a professional, neutral, concise tone.\n"
        "- The summary is strictly for the **physician** – do NOT include patient-directed content.\n"
        "- ONLY include: presenting symptoms, severity, duration, aggravating or relieving factors, relevant medical history, medications, and treatment background.\n"
        "=== Safety & Limitations (CRITICAL) ===\n"
        "- Never add clinical assumptions, interpretations, or advice.\n"
        "- Do NOT reference or address the patient directly.\n"
        "- Do NOT conclude with a question or suggest further actions.\n"
        "- Privacy must be respected; do not infer or guess personal details beyond the patient's explicit statements.\n\n"
        "=== Output Format: Standard Summary Template ===\n"
        "1. Chief Complaint: [Brief description of symptom or reason for visit]\n"
        "2. Symptom Duration: [How long the symptom has been present]\n"
        "3. Severity: [Pain level or symptom severity (e.g., 1-10) if reported]\n"
        "4. Triggers/Relieving Factors: [What worsens and what alleviates the symptom]\n"
        "5. Associated Symptoms: [Fever, nausea, radiation, shortness of breath, etc.]\n"
        "6. Relevant Medical History: [Similar conditions in the past, underlying diseases]\n"
        "7. Current Medications: [Or 'None']\n"
        "8. Recommendations/Initial Workup (if mentioned): [Suggestions for tests or follow-up]\n\n"
        "=== Example With Clinical Information ===\n"
        f"{example_with_info}\n\n"
        "---\n\n"
        "Patient was advised to bring relevant documents, medication lists, and recent test results.\n"
    )


    

def generate_summary(conversation):
    """
    Sends the conversation to OpenAI and asks for a visit summary report for the doctor.
    The summary should help the doctor be effective for the upcoming patient visit.
    
    Args:
        conversation: List of conversation messages
        max_questions (int): Maximum number of questions allowed in the conversation
    """
    # Generate the prompt with configurable parameters
    system_prompt = medical_summary_report()

    print(f"System prompt: {system_prompt}")
    print(f"Conversation: {conversation}")

    # Build the messages for the API
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation:
        # msg should be a dict like {'role': 'user', 'content': '...'} or {'role': 'assistant', 'content': '...'}
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append({"role": msg["role"], "content": msg["content"]})
        else:
            # fallback: treat as user message
            messages.append({"role": "user", "content": str(msg)})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=300,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"Error communicating with AI: {e}"    
