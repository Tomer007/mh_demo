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
- If the user asks about urgent care centers (מוקדי רפואה דחופה), provide this list:

מוקדי רפואה דחופה – מאוחדת:

1. תל אביב  
📍 כתובת: שפרינצק 15, תל אביב  
🕒 ימי חול: 19:30–23:00 | סופי שבוע וחגים: 15:00–23:00  

2. חדרה (ויוה)  
📍 כתובת: תרנ"א 20, חדרה  
🕒 ימי חול: 19:30–23:00 | סופי שבוע וחגים: 15:00–23:00  

3. חיפה – מרפאת בית מאי  
📍 כתובת: חסן שוקרי 5, חיפה  
🕒 ימי חול: 19:30–23:00 | סופי שבוע וחגים: 15:00–23:00  

4. אשדוד  
📍 כתובת: קרן היסוד 8, אשדוד  
🕒 ימי חול: 19:30–23:00 | שישי וחגים: 15:00–23:00 | שבת: 11:00–23:00  

5. ירושלים  
📍 כתובת: יפו 180, ירושלים  
🕒 פתוח 24/7  

- If the user asks for a link to the full list, provide:  
https://www.meuhedet.co.il/%D7%9E%D7%99%D7%93%D7%A2-%D7%9C%D7%9C%D7%A7%D7%95%D7%97/%D7%9E%D7%95%D7%A7%D7%93%D7%99-%D7%A8%D7%A4%D7%95%D7%90%D7%94-%D7%93%D7%97%D7%95%D7%A4%D7%94-%D7%9E%D7%90%D7%95%D7%97%D7%93%D7%AA/

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
        return ("מגבלת שיחות הושגה. תודה על שיתוף הפעולה.", session_history)

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
        #logger.debug(f"OpenAI response: {assistant_reply}")

        # Update session history
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": assistant_reply})
        #logger.debug(f"Session history (after): {session_history}")

        return assistant_reply, session_history

    except Exception as e:
        logger.error(f"Error communicating with OpenAI: {e}")
        return f"שגיאה בתקשורת עם ה-AI: {e}", session_history
    

def generate_summary_prompt(
    max_questions: int = 4,
    default_no_info_message: str = "לא נמסר מידע קליני המספיק לכתיבת סיכום.",
    example_with_info: str = 
    "1. תלונה עיקרית: המטופל מדווח על כאבי גב תחתון.\n"
    "2. משך הסימפטום: כשלושה שבועות.\n"
    "3. חומרה: דרגת כאב בינונית-גבוהה (6–7 מתוך 10).\n"
    "4. טריגרים/גורמים מקלים: מוחמר בישיבה ממושכת, משתפר בשכיבה.\n"
    "5. תסמינים נלווים: אין חום או הקרנה לרגליים.\n"
    "6. היסטוריה רפואית רלוונטית: ללא היסטוריה קודמת של בעיות גב.\n"
    "7. תרופות נוכחיות: אינו נוטל תרופות כרגע.\n"
    "8. המלצות/בירור ראשוני (אם נאמרו): לא צוינו."
) -> str:
    return (
        "Reset all memory and chat history. Begin a new, clean session.\n\n"
        "**Role:**\n"
        "You are a medical assistant. Your responsibility is to summarize the patient's pre-visit conversation for the physician, based solely on information provided by the patient.\n\n"
        "**Efficiency Requirement:**\n"
        f"* Be highly efficient. Strive to complete the full summary after **no more than {max_questions} questions** to the patient.\n"
        "* Use each question strategically to gather only the most essential clinical details.\n"
        "* Avoid unnecessary follow-ups or elaboration beyond the core goal of visit preparation.\n\n"
        "**Summary Guidelines:**\n"
        f"* Write in user input language, using a professional, neutral, and concise tone.\n"
        "* The summary is intended for the **physician only** and supports clinical efficiency. Do not include content directed at the patient.\n"
        "* Include only essential clinical details: presenting symptoms, severity, duration, aggravating or relieving factors, relevant medical history, medications, and treatment background.\n"
        f"* If no sufficient information is available, write: *\"{default_no_info_message}\"*\n\n"
        "**Limitations:**\n"
        "* Never add assumptions, personal interpretations, or clinical advice.\n"
        "* Do not address or reference the patient directly.\n"
        "* Never conclude with a question or suggest further actions.\n\n"
        "---\n\n"
        "**Template – Standard Summary Format (Hebrew):**\n"
        "*1. תלונה עיקרית:* [תיאור קצר של הסימפטום או הסיבה לפנייה]\n"
        "*2. משך הסימפטום:* [כמה זמן התסמין קיים]\n"
        "*3. חומרה:* [רמת הכאב או חומרת התסמין (לדוג' 1–10) אם נמסרה]\n"
        "*4. טריגרים/גורמים מקלים:* [מה מחמיר ומה מקל על התסמין]\n"
        "*5. תסמינים נלווים:* [חום, בחילה, הקרנה, קוצר נשימה וכו']\n"
        "*6. היסטוריה רפואית רלוונטית:* [מצבים רפואיים דומים בעבר, מחלות רקע]\n"
        "*7. תרופות נוכחיות:* [או 'ללא']\n"
        "*8. המלצות/בירור ראשוני (אם נאמרו):* [הצעות לבדיקות או מעקב]\n\n"
        "**Example – With Clinical Information (Hebrew):**\n"
        f"{example_with_info}\n\n"
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
    system_prompt = generate_summary_prompt(MAX_MESSAGES)

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
        return f"שגיאה בתקשורת עם ה-AI: {e}"    
