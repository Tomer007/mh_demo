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

load_dotenv()

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

conversations: Dict[str, List[str]] = {}

patient_name = os.getenv("PATIENT_NAME", "תומר")  

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, patient_id: str = "demo-patient"):
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
    conv = conversations.setdefault(req.patient_id, [])
    reply, updated_conv = get_doctor_visit_assistance(req.message, conv)
    conversations[req.patient_id] = updated_conv 

    return {"response": reply}

@app.get("/api/summary/{patient_id}", response_model=SummaryResponse)
def summary_endpoint(patient_id: str):
    conv = conversations.get(patient_id, [])
    
    summary = generate_summary(conv)
    return {"patient_id": patient_id, "summary": summary}

@app.delete("/api/session/{patient_id}")
def clear_session(patient_id: str):
    if patient_id in conversations:
        del conversations[patient_id]

        return {"success": True, "message": f"Session for {patient_id} cleared."}
    return {"success": False, "message": f"No session found for {patient_id}."}, 404 