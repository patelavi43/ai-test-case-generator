# AI Test Case Generator

A starter project for generating structured test cases from user stories and requirements.

## Features
- Input a feature name and requirement text
- Generate mock functional, negative, and edge test cases
- Export generated test cases as CSV
- Python FastAPI backend + simple HTML frontend

## Run backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run frontend
Open `frontend/index.html` in your browser after starting the backend.

## Next improvements
- Connect real LLM API
- Better prompt engineering
- Excel export
- Save project history
