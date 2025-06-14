# Patient-Doctor Chat Demo

A FastAPI + Jinja2 + TailwindCSS demo for a mobile-style patient-doctor chat assistant.

## Features

- Mobile-first, RTL, Hebrew-friendly UI
- Landing and chat pages, styled with TailwindCSS
- In-memory chat logic and summary API

## Project Structure

```
/app
  /static
    /css/tailwind.min.css
    /img/landing.png
    /img/mh_landing.png
    /img/mh_chat_background.png
  /templates
    landing.html
    chat.html
  main.py
requirements.txt
render.yaml
```

## Running Locally

```sh
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
uvicorn main:app --reload
```

Visit [http://localhost:8000/](http://localhost:8000/)

## API Usage

### POST /api/chat

Request:
```json
{ "patient_id": "string", "message": "string" }
```
Response:
```json
{ "response": "string" }
```

### GET /api/summary/{patient_id}

Response:
```json
{ "patient_id": "string", "summary": "string" }
```

## Notes

- All UI is RTL and mobile-first (TailwindCSS).
- No database, all chat logs are in-memory.
- Images must be placed in `/app/static/img/`.

## GitHub Repository

This project is hosted at: [https://github.com/Tomer007/mh_demo.git](https://github.com/Tomer007/mh_demo.git)

### To push your local project to this repository:

```sh
git init
git remote add origin https://github.com/Tomer007/mh_demo.git
git add .
git commit -m "Initial commit: Patient-Doctor Assistant FastAPI Demo"
git branch -M main
git push -u origin main
``` 