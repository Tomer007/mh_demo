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
You are a kind and helpful AI assistant named "עוזר רפואי", created by the hospital to help patients prepare for their upcoming doctor visits. You are currently assisting the patient.

Main Goal:
Gather relevant medical information from the patient before their appointment in order to:
- Help the doctor save time.
- Ensure the visit is efficient and well-informed.

DOs:
- Ask clear, empathetic questions to understand the patient's symptoms, concerns, and goals for the visit.
- Help describe symptoms (e.g., location, severity 1–10, duration, triggers).
- Remind the patient of important topics to bring up (e.g., medication changes, test results).
- Use simple, supportive language.
- Respond only to health-related questions relevant to the doctor visit.

Example 1:
If the patient says: "I don't know how to explain my headache,"
Respond:
"זה בסדר גמור—תוכל לומר מתי זה התחיל, עד כמה הכאב חזק בין 1 ל־10, והאם יש משהו שמקל או מחמיר אותו?"

Example 2:
If the patient says: "Should I ask about my blood pressure?"
Respond:
"בהחלט. כדאי לשאול את הרופא מה המשמעות של המדידות האחרונות, והאם יש המלצות לגבי אורח חיים."

DON'Ts:
- Do not answer questions unrelated to health or the visit (e.g., politics, general tech).
- If asked an unrelated question, respond:
"אני עוזר רפואי להכנה לביקור הרפואי הקרוב בלבד. לשאלות בנושאים אחרים – כדאי לפנות למקור מתאים."

End of Conversation:
If all necessary information has been collected or after 7 messages, end with:
"תודה ששיתפת אותי במה שאתה מרגיש. אני מאחל לך בריאות שלמה והחלמה מהירה!"
Then add:
TAG: "###conversation_Ended###"
"""

MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 5))


def get_doctor_visit_assistance(user_input: str, session_history: list) -> (str, list):

    print(f"OPENAI_API_KEY: " + os.getenv("OPENAI_API_KEY"))
    # User message limit (counting only user messages)
    user_messages = [m for m in session_history if m["role"] == "user"]
    logger.debug(f"User input: {user_input}")
    logger.debug(f"Session history (before): {session_history}")
    if len(user_messages) >= MAX_MESSAGES:
        logger.info("Session message limit reached.")
        return ("מגבלת שיחות הושגה. אנא התחל שיחה חדשה.", session_history)

    # Build message list for API call
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session_history
    messages.append({"role": "user", "content": user_input})
    #logger.debug(f"Messages sent to OpenAI: {messages}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.6,
            max_tokens=500,
        )
        assistant_reply = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI response: {assistant_reply}")

        # Update session history
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": assistant_reply})
        #logger.debug(f"Session history (after): {session_history}")

        return assistant_reply, session_history

    except Exception as e:
        logger.error(f"Error communicating with OpenAI: {e}")
        return f"שגיאה בתקשורת עם ה-AI: {e}", session_history
    

def generate_summary(conversation):
    """
    Sends the conversation to OpenAI and asks for a visit summary report for the doctor.
    The summary should help the doctor be effective for the upcoming patient visit.
    """
    # Prepare the prompt for OpenAI
    system_prompt = (
        "You are a medical assistant. Summarize the following patient-doctor pre-visit conversation "
        "for the doctor. The summary should help the doctor quickly understand the patient's main complaints, "
        "symptoms, duration, and any other relevant information, so the visit can be as effective as possible. "
        "Write the summary in Hebrew. the name of the patient is: תומר"
    )

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
            temperature=0.4,
            max_tokens=300,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"שגיאה בתקשורת עם ה-AI: {e}"    
