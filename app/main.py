from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
from app.service.chat_service import get_doctor_visit_assistance, generate_summary
import os
from dotenv import load_dotenv
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

conversations: Dict[str, List[str]] = {}

patient_name = os.getenv("PATIENT_NAME", "תומר")  

# Global variable for current patient ID
_current_patient_id = "65387911-0da8-40d0-a7c1-2da29b4acb33"
_summary_current_patient_id = ""

def get_current_patient_id() -> str:
    """Getter function for current patient ID"""
    return _current_patient_id

def set_current_patient_id(patient_id: str):
    global _current_patient_id
    _current_patient_id = patient_id

def get_summary_current_patient_id() -> str:
    """Getter function for summary current patient ID"""
    return _summary_current_patient_id

def set_summary_current_patient_id(summary_patient_id: str) -> None:
    """Setter function for summary current patient ID"""
    global _summary_current_patient_id
    _summary_current_patient_id = summary_patient_id
    logger.info("Summary current patient ID set to: %s", summary_patient_id)

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    logger.info("Landing page accessed - Request URL: %s", request.url)
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, patient_id: str = "demo-patient"):
    logger.info("Chat page accessed - Patient ID: %s, Request URL: %s", patient_id, request.url)
    # Set the current patient ID when chat page is accessed
    conv = conversations.get(patient_id, [])
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "messages": conv,
            "patient_id": patient_id,
            "patient_name": patient_name,
        }
    )


class ChatRequest(BaseModel):
    patient_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class SummaryResponse(BaseModel):
    patient_id: str
    summary: str

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    logger.info("Chat API called - Patient ID: %s, Message length: %d", req.patient_id, len(req.message))
    conv = conversations.setdefault(req.patient_id, [])
    reply, updated_conv = get_doctor_visit_assistance(req.message, conv)
    conversations[req.patient_id] = updated_conv 
    logger.info("Chat response generated for Patient ID: %s", req.patient_id)
    return {"response": reply}

@app.get("/api/summary/{patient_id}", response_model=SummaryResponse)
def summary_endpoint(patient_id: str):
    logger.info("Summary API called - Patient ID: %s", patient_id)
    conv = conversations.get(patient_id, [])
    summary = generate_summary(conv)
    logger.info("Summary generated for Patient ID: %s", patient_id)
    set_summary_current_patient_id(summary)
    return {"patient_id": patient_id, "summary": summary}

@app.get("/api/summary_for_provider", response_model=SummaryResponse)
def summary_endpoint():
    summary = get_summary_current_patient_id()
    logger.info("Summary generated for patient ID: %s summary %s ", summary ,get_current_patient_id)
    return {"patient_id": get_current_patient_id(), "summary": summary}

@app.delete("/api/session/{patient_id}")
def clear_session(patient_id: str):
    logger.info("Session clear API called - Patient ID: %s", patient_id)
    if patient_id in conversations:
        del conversations[patient_id]
        logger.info("Session cleared for Patient ID: %s", patient_id)
        return {"success": True, "message": f"Session for {patient_id} cleared."}
    logger.warning("No session found for Patient ID: %s", patient_id)
    return {"success": False, "message": f"No session found for {patient_id}."}, 404 

@app.get("/provider", response_class=HTMLResponse)
def provider(request: Request):
    logger.info("Provider page accessed - Request URL: %s", request.url)
    return templates.TemplateResponse("provider.html", {"request": request})

@app.get("/provider_deashboard", response_class=HTMLResponse)
def provider_dashboard(request: Request):
    logger.info("Provider dashboard page accessed - Request URL: %s", request.url)
    return templates.TemplateResponse("provider_deashboard.html", {"request": request})

@app.get("/provider_deashboard.html", response_class=HTMLResponse)
def provider_dashboard_html(request: Request):
    logger.info("Provider dashboard HTML page accessed - Request URL: %s", request.url)
    return templates.TemplateResponse("provider_deashboard.html", {"request": request})

