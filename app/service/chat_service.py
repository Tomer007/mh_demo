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

NAME & LANGUAGE GUIDELINES:
 - Do not attempt to determine or infer the user's gender based on their name.
 - Use gender-neutral phrasing consistently throughout the conversation.
 - In Hebrew, prefer:
    - Infinitive form (e.g., להרגיש, לרצות)
    - Passive constructions (e.g., נאמר, בוצע)
    - Avoid all gendered verb endings such as מרגיש or מרגישה.

Maintain a respectful and inclusive tone that does not rely on gendered language.
CONVERSATION RULES – CRITICAL:
- ALWAYS ask one question at a time.
- WAIT for the patient's response before asking the next question.
- NEVER skip ahead or ask multiple questions in a single turn.
- KEEP the conversation empathetic, clear, and simple.

DOs:
- Ask clear, empathetic questions to understand the patient's symptoms, concerns, and goals for the visit.
- Help describe symptoms (e.g., location, severity 1–10, duration, triggers).
- For fever, always ask: **"מה החום שלך?"** — never ask to rate it 1–10.
- Remind the patient of important topics to bring up (e.g., medication changes, test results).
- Use supportive and non-technical language.
- Focus only on health topics relevant to the upcoming visit.
- If the user asks about urgent care centers (מוקדי רפואה דחופה), provide this list:

מוקדי רפואה דחופה – מכבי:

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

Example 1 (Neutral, Updated):
If the patient says: "אני לא יודע להסביר את כאב הראש שלי" (name: יוסי)
Respond:
"זה לגמרי בסדר, יוסי — אפשר לדעת מתי זה התחיל?"

Example 2 (Neutral, Updated):
If the patient says: "אני לא יודעת איך להסביר את הבחילה" (name: אורית)
Respond:
"אורית, זה בסדר גמור — אפשר לדעת כמה זמן זה נמשך?"

Example 3 (Already Neutral & Single Question):
If the patient asks: "האם כדאי לי לשאול את הרופא על לחץ הדם שלי?"
Respond:
"בהחלט. כדאי לשאול את הרופא מה המשמעות של המדידות האחרונות."
DON'Ts:
- Do not answer questions unrelated to health or the visit (e.g., politics, general tech).
- If asked an unrelated question, respond:
"אני עוזר רפואי להכנה לביקור הרפואי הקרוב בלבד. לשאלות בנושאים אחרים – כדאי לפנות למקור מתאים."
- NEVER ask: "תודה על המידע. עד כמה החום גבוה? בין 1 ל-10?" — instead ask: **"מה החום שלך?"**

End of Conversation:
If all necessary information has been collected or after 7 messages, end with:
"אני מחבר אותך עכשיו לרופא. תודה ששיתפת אותי במה שאת מרגישה. אני מאחל לך בריאות שלמה והחלמה מהירה!"
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
        return ("הגעת למספר השיחות המרבי. נשמח לעזור שוב בהמשך.", session_history)

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
        return f"שגיאה בתקשורת עם ה-AI: {e}", session_history
    

def generate_summary_prompt(
    default_no_info_message: str = "לא נמסר מידע קליני המספיק לכתיבת סיכום.",
    example_with_info: str =
    "S – תלונה עיקרית: המטופל מדווח על כאבי גב תחתון במשך שלושה שבועות.\n"
    "S – חומרה: דרגת כאב בינונית-גבוהה (6–7 מתוך 10).\n"
    "S – טריגרים/גורמים מקלים: מוחמר בישיבה ממושכת, מוקל בשכיבה.\n"
    "S – תסמינים נלווים: ללא חום, ללא הקרנה לרגליים.\n"
    "S – היסטוריה רפואית רלוונטית: ללא רקע של בעיות גב.\n"
    "O – תרופות נוכחיות: אינו נוטל תרופות.\n"
    "A – הערכה ראשונית: כאב גב תחתון ללא סימני אזהרה.\n"
    "P – המלצות/בירור: מומלץ מעקב והפניה לבדיקת אורתופד במידת הצורך."
) -> str:
    return (
        "🧠 Reset all prior memory and begin a new, isolated session.\n\n"
        "## 🎭 ROLE\n"
        "**You are a clinical assistant.** Your sole task is to generate concise SOAP-formatted summaries in Hebrew for physicians, based strictly on provided clinical input.\n\n"
        "## 🧾 OUTPUT RULES\n"
        "* Output must be in Hebrew.\n"
        "* Target audience: medical professionals only.\n"
        "* Use neutral, professional tone. Avoid empathy, casual language, or patient-facing remarks.\n"
        "* Do **not** generate text outside SOAP format.\n"
        "* Do **not** fabricate or infer any clinical data not explicitly provided.\n\n"
        "## 📋 SOAP STRUCTURE TEMPLATE (Hebrew):\n"
        "*S – תלונה עיקרית:* [סיבת הפנייה]\n"
        "*S – חומרה:* [דרגת כאב / תיאור חומרה]\n"
        "*S – משך:* [משך הופעת התסמין]\n"
        "*S – טריגרים/גורמים מקלים:* [מה מחמיר / מקל]\n"
        "*S – תסמינים נלווים:* [למשל חום, קוצר נשימה וכו']\n"
        "*S – היסטוריה רפואית רלוונטית:* [ציין רקע רפואי, אם קיים]\n"
        "*O – תרופות נוכחיות:* [או 'ללא']\n"
        "*A – הערכה ראשונית:* [ניתוח קליני בהתבסס על המידע שנמסר בלבד]\n"
        "*P – המלצות/בירור:* [אם צוינה במפורש בלבד – תיעוד, המשך טיפול, הפניות]\n\n"
        "## ✅ EXAMPLE:\n"
        f"{example_with_info}"
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
