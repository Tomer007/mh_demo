import os
import logging
from dotenv import load_dotenv
from app.service.aingelz_service import AingelzSessionManager
from typing import Tuple, Optional, Dict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 5))

# Store session managers per patient
PATIENT_SESSIONS = {}

# Dummy patient info for demo (should be dynamic in real app)
DEFAULT_AGE = 30
DEFAULT_GENDER = "M"

def get_doctor_visit_assistance(user_input: str, session_history: list, patient_id: str = "demo_patient", integration: str = "aingelz") -> Tuple[str, list, Optional[Dict]]:
    # User message limit (counting only user messages)
    user_messages = [m for m in session_history if m["role"] == "user"]
    logger.debug(f"User input: {user_input}")
    logger.debug("Current message: " + str(len(user_messages)))
    if len(user_messages) >= MAX_MESSAGES:
        logger.info("Session message limit reached.")
        # Get SOAP note when limit is reached
        if patient_id in PATIENT_SESSIONS:
            session_mgr = PATIENT_SESSIONS[patient_id]
            if hasattr(session_mgr, "session_id") and session_mgr.session_id:
                try:
                    soap_note = session_mgr.get_soap_note(session_mgr.session_id)
                    summary = {"summary": soap_note}
                    return ("הגעת למספר השיחות המרבי. נשמח לעזור שוב בהמשך.", session_history, summary)
                except Exception as e:
                    logger.error(f"Error getting SOAP note at limit: {e}")
        return ("הגעת למספר השיחות המרבי. נשמח לעזור שוב בהמשך.", session_history, None)

    # Get or create session manager for this patient
    if patient_id not in PATIENT_SESSIONS:
        PATIENT_SESSIONS[patient_id] = AingelzSessionManager()
    session_mgr = PATIENT_SESSIONS[patient_id]

    try:
        if integration == "aingelz":
            if not hasattr(session_mgr, "session_id") or session_mgr.session_id is None:
                # First message: start session (POST)
                data = session_mgr.start_session(
                    patient_id=patient_id,
                    age=DEFAULT_AGE,
                    gender=DEFAULT_GENDER,
                    user_message=user_input,
                )
                assistant_reply = data["data"]["agent"]
                session_mgr.session_id = data["task_transaction_id"]
                summary = data.get("summary")
            else:
                # Subsequent messages: send message (PUT)
                data = session_mgr.send_message(user_message=user_input)
                assistant_reply = data["data"]["agent"]
                summary = data.get("summary")
                
                # Check if status is complete and return result status
                if data.get("result", {}).get("status") == "complete":
                    return assistant_reply, session_history, {"result": data["result"]}
        else:
            logger.warning(f"Integration '{integration}' is not supported.")
            return "Integraion not supported", session_history, None


        # Update session history
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply, session_history, summary

    except Exception as e:
        logger.error(f"Error communicating with Aingelz: {e}")
        return f"שגיאה בתקשורת עם ה-AI: {e}", session_history, None

def reset_patient_session(patient_id: str):
    if patient_id in PATIENT_SESSIONS:
        del PATIENT_SESSIONS[patient_id]

# (Optional) You can later add a summary function using the conversation history.


    
