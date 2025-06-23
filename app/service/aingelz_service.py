import os
import requests
from datetime import timedelta
from app.service.exmple_aingelz.generateJWT import JWTGenerator
from app.service.exmple_aingelz.data_models import Patient, PatientProxy, Service, DataTransmit, TaskData
import time

AINGELZ_ENDPOINT = os.getenv("AINGELZ_ENDPOINT")
AINGELZ_PATH = os.getenv("AINGELZ_PATH")
AINGELZ_ACCOUNT = os.getenv("AINGELZ_ACCOUNT")
AINGELZ_USER = os.getenv("AINGELZ_USER")
AINGELZ_ROLE = os.getenv("AINGELZ_ROLE")
AINGELZ_PRIVATE_KEY = os.getenv("PRIVATE_KEY", os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/private_key.pem")))
AINGELZ_SNOWFLAKE_URL = os.getenv("AINGELZ_SNOWFLAKE_URL")
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

API_TIMEOUT_SEC = 20

MOCK_SOAP_NOTE = {
    "soap_note": {
        "objective": "- Headache duration: 3 days\n- Headache location: Frontal region\n- Pain characteristics: Dull\n- Pain intensity: 8/10\n- Associated symptoms:\n  * Intermittent nausea (7/10 severity)\n- Negative findings:\n  * No photophobia\n  * No current medications\n  * No known allergies\n  * No relevant past medical history",
        "subjective": "30-year-old male presents with chief complaint of severe headache persisting for 3 days. Patient describes the headache as dull in quality, located in the frontal region of the head, with severity rated as 8/10. Associated symptoms include intermittent nausea rated as 7/10 severity. Patient denies photophobia. No relevant past medical history reported. No current medications. No known allergies."
    }
}

class AingelzSessionManager:
    def __init__(self):
        self.token = None
        self.session_id = None

    def get_token(self):
        if not self.token:
            if not AINGELZ_ACCOUNT or not AINGELZ_USER:
                raise ValueError("AINGELZ_ACCOUNT and AINGELZ_USER environment variables must be set.")
            jwt = JWTGenerator(
                AINGELZ_ACCOUNT,
                AINGELZ_USER,
                AINGELZ_PRIVATE_KEY,
                timedelta(minutes=30),
                timedelta(minutes=10),
            ).get_token()
            self.token = self.token_exchange(jwt)
        return self.token

    def token_exchange(self, jwt):
        scope_role = f"session:role:{AINGELZ_ROLE}" if AINGELZ_ROLE else None
        scope = f"{scope_role} {AINGELZ_ENDPOINT}" if scope_role else AINGELZ_ENDPOINT
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "scope": scope,
            "assertion": jwt,
        }
        url = f"{AINGELZ_SNOWFLAKE_URL}/oauth/token"
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.text

    def start_session(self, patient_id, age, gender, user_message, proxy=None, agent_message="What is your main health concern?"):
        self.get_token()
        url = f"https://{AINGELZ_ENDPOINT}{AINGELZ_PATH}"
        payload = {
            "task": "Intake Flow",
            "language": "HE",
            "interactions_limit": 5,
            "task_data": {
                "patient": {
                    "id": patient_id,
                    "age": age,
                    "gender": gender,
                    "patient_proxy": proxy or {"relation_to_patient": "parent", "gender": gender},
                },
                "services": [],
            },
            "data_transmit": {"agent": agent_message, "user": user_message},
        }
        headers = {
            "Authorization": f'Snowflake Token="{self.token}"',
            "Content-Type": "application/json",
            "Accept": "application/json, text/html",
        }
        response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT_SEC)
        response.raise_for_status()
        data = response.json()
        self.session_id = data["task_transaction_id"]
        return data

    def get_soap_note(self, task_transaction_id):
        if USE_MOCK:
            return MOCK_SOAP_NOTE
            
        url = f"https://{AINGELZ_ENDPOINT}/intake_flow/soap_note/{task_transaction_id}"
        headers = {
            "Authorization": f'Snowflake Token="{self.token}"',
            "Content-Type": "application/json",
            "Accept": "application/json, text/html",
        }
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(url, headers=headers, timeout=API_TIMEOUT_SEC)
            print("task_transaction_id:", task_transaction_id)
            print("status: ", response.status_code)
            if response.status_code == 200:
                return response.json()
            if attempt < max_attempts - 1:
                time.sleep(10)
        # After 5 minutes or last attempt, return last response (could be 202 or error)
        try:
            print(response.json());
            return response.json()
        except Exception:
            return {"error": "Failed to retrieve SOAP note after multiple attempts."}

    def send_message(self, user_message):
        self.get_token()
        url = f"https://{AINGELZ_ENDPOINT}{AINGELZ_PATH}"
        payload = {
            "task_transaction_id": self.session_id,
            "data_transmit": {"agent": "", "user": user_message},
        }
        headers = {
            "Authorization": f'Snowflake Token="{self.token}"',
            "Content-Type": "application/json",
            "Accept": "application/json, text/html",
        }
        response = requests.put(url, json=payload, headers=headers, timeout=API_TIMEOUT_SEC)
        response.raise_for_status()
        data = response.json()
        # If status is complete, fetch soap note and wrap in summary model
        if data.get("result", {}).get("status") == "complete":
            print("Task Completed")
        return data
