from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

conversations: Dict[str, List[str]] = {}

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request, patient_id: str = "demo-patient"):
    conv = conversations.get(patient_id, [])
    return templates.TemplateResponse("chat.html", {"request": request, "messages": conv, "patient_id": patient_id})


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
    conv.append(req.message)
    reply = "גגגגגגגגגגגהודעתך התקבלה: " + req.message
    conv.append(reply)
    return {"response": reply}

@app.get("/api/summary/{patient_id}", response_model=SummaryResponse)
def summary_endpoint(patient_id: str):
    conv = conversations.get(patient_id, [])
    def generate_summary(conversation):
        if any("גב" in msg for msg in conversation):
            symptom = "כאב בגב התחתון"
        else:
            symptom = "תסמין כללי"
        duration = "כמה ימים" if any("יום" in msg for msg in conversation) else "משך לא ידוע"
        additional = "החמרה או קושי בפעילות" if any("קשה" in msg or "מחמיר" in msg for msg in conversation) else "ללא תוספות"
        return f"סיבת הביקור: {symptom}. המטופל מדווח כי הבעיה נמשכת מזה {duration}. נרשמה תחושת {additional}."
    summary = generate_summary(conv)
    return {"patient_id": patient_id, "summary": summary} 