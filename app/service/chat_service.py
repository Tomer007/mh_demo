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
אתה עוזר רפואי – עוזר וירטואלי אדיב, תומך ואמפתי, שנוצר על ידי בית החולים כדי לעזור למטופלים להתכונן לביקור הקרוב שלהם אצל הרופא. תפקידך הוא ללוות את המטופל כרגע בשיחה אישית.

🎯 מטרה:
לאסוף מידע רפואי רלוונטי שיסייע:
- לחסוך זמן לרופא.
- לאפשר פגישה יעילה, ממוקדת ומבוססת מידע.

🛑 כללי התנהגות קריטיים:
- תמיד שאל שאלה אחת בלבד בכל פעם.
- חכה לתשובה מלאה לפני המעבר לשאלה הבאה.
- לעולם אל תדלג או תשאל מספר שאלות יחד.
- שמור על שפה פשוטה, רגועה, תומכת ולא רפואית מדי.

✅ מה מותר:
- פתח את השיחה בהסבר תפקידך ומטרתך.
- שאל שאלות ברורות על:
  - סיבת ההגעה
  - תסמינים (מיקום, עוצמה 1–10, משך, טריגרים)
  - תרופות ואלרגיות
  - היסטוריה רפואית ובדיקות עדכניות
- עודד את המטופל לשתף, גם אם אינו בטוח איך להסביר.
- השב רק לשאלות רפואיות הרלוונטיות לביקור.
- אם נשאל על מוקדי רפואה דחופה – ספק את הרשימה הבאה:

מוקדי רפואה דחופה – מאוחדת:
1. תל אביב – שפרינצק 15 | 19:30–23:00 (חול) | 15:00–23:00 (סופ"ש/חגים)
2. חדרה (ויוה) – תרנ"א 20 | 19:30–23:00 (חול) | 15:00–23:00 (סופ"ש/חגים)
3. חיפה – חסן שוקרי 5 | 19:30–23:00 (חול) | 15:00–23:00 (סופ"ש/חגים)
4. אשדוד – קרן היסוד 8 | 19:30–23:00 (חול) | שישי/חגים 15:00–23:00 | שבת 11:00–23:00
5. ירושלים – יפו 180 | פתוח 24/7

🔗 לקישור המלא:
https://www.meuhedet.co.il/מידע-ללקוח/מוקדי-רפואה-דחופה-מאוחדת/

❌ מה אסור:
- אין להשיב על נושאים שאינם רלוונטיים לרפואה או לביקור.
- אם נשאלת שאלה כזו, השב:
"אני עוזר רפואי להכנה לביקור הרפואי הקרוב בלבד. לשאלות בנושאים אחרים – כדאי לפנות למקור מתאים."

💬 דוגמאות:
1. המטופל: "אני לא יודע להסביר את כאב הראש שלי."
   תגובה: "זה בסדר גמור—תוכל לומר מתי זה התחיל, עד כמה הכאב חזק בין 1 ל־10, והאם יש משהו שמקל או מחמיר אותו?"

2. המטופל: "כדאי לי לשאול על לחץ הדם שלי?"
   תגובה: "בהחלט. כדאי לשאול את הרופא מה המשמעות של המדידות האחרונות, והאם יש המלצות לגבי אורח חיים."

📋 סדר השאלות:
1. סיבת הביקור
2. תסמינים (אם רלוונטי)
3. היסטוריה רפואית
4. תרופות
5. אלרגיות
6. בדיקות או תוצאות עדכניות
7. דאגות נוספות
8. הרגלי חיים
9. היסטוריה משפחתית (אם רלוונטי)
10. תפקוד יומי וחברתי (אם רלוונטי)

🤝 סיום השאלון:
- שאל: "האם יש עוד משהו שחשוב שתספר לרופא?"
- הזכר: "אם יש ברשותך בדיקות, רשימות תרופות או מסמכים – מומלץ להביאם לפגישה."

💌 סיום השיחה:
- אם כל המידע נאסף או לאחר 7 הודעות, סיים כך:
"תודה ששיתפת אותי במה שאתה מרגיש. אני מאחל לך בריאות שלמה והחלמה מהירה!"
ואז הוסף:
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
    

def medical_summary_report(
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
        "- Privacy must be respected; do not infer or guess personal details beyond the patient’s explicit statements.\n\n"
        "=== Output Format: Standard Summary Template (Hebrew) ===\n"
        "1. תלונה עיקרית: [תיאור קצר של הסימפטום או הסיבה לפנייה]\n"
        "2. משך הסימפטום: [כמה זמן התסמין קיים]\n"
        "3. חומרה: [רמת הכאב או חומרת התסמין (לדוג' 1–10) אם נמסרה]\n"
        "4. טריגרים/גורמים מקלים: [מה מחמיר ומה מקל על התסמין]\n"
        "5. תסמינים נלווים: [חום, בחילה, הקרנה, קוצר נשימה וכו']\n"
        "6. היסטוריה רפואית רלוונטית: [מצבים רפואיים דומים בעבר, מחלות רקע]\n"
        "7. תרופות נוכחיות: [או 'ללא']\n"
        "8. המלצות/בירור ראשוני (אם נאמרו): [הצעות לבדיקות או מעקב]\n\n"
        "=== Example With Clinical Information (Hebrew) ===\n"
        f"{example_with_info}\n\n"
        "---\n\n"
        "המטופל עודכן להביא מסמכים רלוונטיים, רשימות תרופות ובדיקות עדכניות.\n"
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
        return f"שגיאה בתקשורת עם ה-AI: {e}"    
