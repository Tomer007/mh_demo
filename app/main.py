from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
from app.service.chat_service import get_doctor_visit_assistance, reset_patient_session
import os
from dotenv import load_dotenv
import random
import logging
from starlette.middleware.base import BaseHTTPMiddleware
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

conversations: Dict[str, List[str]] = {}
patient_names: Dict[str, str] = {}  # Store patient names by patient_id

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Log request
        body = await request.body()
        logger.info(f"HTTP Request: {request.method} {request.url.path}?{request.url.query}\nHeaders: {dict(request.headers)}\nBody: {body.decode('utf-8') if body else ''}")
        response = await call_next(request)
        response_body = b""
        async for chunk in response.__dict__.get("body_iterator", []):
            response_body += chunk
        if not response_body and hasattr(response, 'body'):
            response_body = response.body
        # Ensure response_body is bytes for decode
        if isinstance(response_body, memoryview):
            response_body = response_body.tobytes()
        elif not isinstance(response_body, bytes):
            response_body = bytes(response_body)
        logger.info(f"HTTP Response: {request.method} {request.url.path} - Status: {response.status_code}\nBody: {response_body.decode('utf-8', errors='replace')}")
        return StreamingResponse(iter([response_body]), status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

app.add_middleware(LoggingMiddleware)

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    logger.info("Landing page accessed - Request URL: %s", request.url)
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, patient_id: str = "demo-patient", patient_name: str = None):
    logger.info("Chat page accessed - Patient ID: %s, Patient Name: %s, Request URL: %s", patient_id, patient_name, request.url)
    
    # Store patient name if provided
    if patient_name:
        patient_names[patient_id] = patient_name
        logger.info("Stored patient name '%s' for patient ID: %s", patient_name, patient_id)
    
    # Get stored patient name or use default
    stored_patient_name = patient_names.get(patient_id, "מטופל")
    
    conv = conversations.get(patient_id, [])
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "messages": conv,
            "patient_id": patient_id,
            "patient_name": stored_patient_name,
        }
    )


class ChatRequest(BaseModel):
    patient_id: str
    message: str
    patient_name: str = None  # Optional patient name
    integration: str = "aingelz"

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    logger.info("Chat API called - Patient ID: %s, Message length: %d, Integration: %s", req.patient_id, len(req.message), req.integration)
    
    # Store patient name if provided
    if req.patient_name:
        patient_names[req.patient_id] = req.patient_name
        logger.info("Stored patient name '%s' for patient ID: %s", req.patient_name, req.patient_id)
    
    conv = conversations.setdefault(req.patient_id, [])
    reply, updated_conv, summary = get_doctor_visit_assistance(req.message, conv, req.patient_id, req.integration)
    conversations[req.patient_id] = updated_conv 
    logger.info("Chat response generated for Patient ID: %s", req.patient_id)
    response = {"response": reply}
    
    # Check if summary contains result status
    if summary and isinstance(summary, dict) and "result" in summary:
        response["result"] = summary["result"]
    elif summary:
        if not isinstance(summary, dict):
            response["summary"] = str(summary)
        else:
            response["summary"] = str(summary)
    
    return response

@app.get("/api/summary/{patient_id}")
def get_summary(patient_id: str):
    logger.info("Summary API called - Patient ID: %s", patient_id)
    from app.service.chat_service import PATIENT_SESSIONS
    if patient_id in PATIENT_SESSIONS:
        session_mgr = PATIENT_SESSIONS[patient_id]
        if hasattr(session_mgr, "session_id") and session_mgr.session_id:
            try:
                soap_note = session_mgr.get_soap_note(session_mgr.session_id)
                return {"summary": soap_note}
            except Exception as e:
                logger.error(f"Error getting SOAP note for {patient_id}: {e}")
                return {"error": f"Failed to get SOAP note: {str(e)}"}, 500
        else:
            return {"error": "No active session found"}, 404
    else:
        return {"error": "Patient session not found"}, 404 

@app.delete("/api/session/{patient_id}")
def clear_session(patient_id: str):
    logger.info("Session clear API called - Patient ID: %s", patient_id)
    if patient_id in conversations:
        del conversations[patient_id]
        reset_patient_session(patient_id)
        logger.info("Session cleared for Patient ID: %s", patient_id)
        return {"success": True, "message": f"Session for {patient_id} cleared."}
    logger.warning("No session found for Patient ID: %s", patient_id)
    reset_patient_session(patient_id)
    return {"success": False, "message": f"No session found for {patient_id}."}, 404 

@app.get("/provider", response_class=HTMLResponse)
def provider(request: Request):
    logger.info("Provider page accessed - Request URL: %s", request.url)
    # Get current patient name from stored names or use default
    current_patient_id = "demo-patient" # Example, you might get this dynamically
    current_patient_name = patient_names.get(current_patient_id, "מטופל")
    return templates.TemplateResponse("provider.html", {"request": request, "patient_name": current_patient_name})

@app.get("/provider_deashboard", response_class=HTMLResponse)
def provider_dashboard(request: Request):
    logger.info("Provider dashboard page accessed - Request URL: %s", request.url)
    # Get current patient name from stored names or use default
    current_patient_id = "demo-patient" # Example, you might get this dynamically
    current_patient_name = patient_names.get(current_patient_id, "מטופל")
    return templates.TemplateResponse("provider_deashboard.html", {"request": request, "patient_name": current_patient_name}) 