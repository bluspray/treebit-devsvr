# Treebit Predictive Ops

Log-driven incident prediction prototype using FastAPI (backend) and React + Vite (frontend).

## Project layout
- `backend/` FastAPI app with a stub `/predict` endpoint. Update the scoring logic to plug in a real model.
- `frontend/` React/Vite dashboard showing sample events and a mock risk score. Wire it to the backend when the API is ready.

## Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Endpoints:
- `GET /health` simple health check
- `POST /predict` expects a JSON array of log events:
  ```json
  [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "host": "web-01",
      "service": "nginx",
      "level": "error",
      "message": "502 upstream timeout"
    }
  ]
  ```

## Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open the shown local URL (default `http://localhost:5173`). The dashboard currently uses mock data; replace the `mockPredict` call in `src/App.tsx` with a fetch to the FastAPI `/predict` endpoint.

## Next steps
- Replace the stub scoring in `backend/app/main.py` with your model/heuristics.
- Add real log ingestion/parsing and feature extraction.
- Connect the frontend to the backend API for live scoring and alerting.
