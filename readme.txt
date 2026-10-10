LEGIONERS PRIORITY ENGINE INTEGRATION

Files:
- main.py: FastAPI endpoint integration
- database.py: SQLite migrations and priority persistence

BACKUP FIRST:
1. Stop the backend server (Ctrl+C in the backend server terminal).
2. Copy backend\main.py to backend\main.py.backup
3. Copy backend\database.py to backend\database.py.backup
4. Ensure backend\prioritization.py exists (the working file you tested).

INSTALL:
Copy these two files into:
C:\Users\thouf\Downloads\Legioners-Project\backend\
Overwrite main.py and database.py only after making backups.

RUN:
From the project root:
  backend\.venv\Scripts\activate.bat
  cd backend
  uvicorn main:app --reload

TEST:
1. Open http://127.0.0.1:8000/docs
2. GET /api/v1/inspections to find an existing inspection ID.
3. PATCH /api/v1/inspections/{inspection_id}/priority
   Example JSON:
   {
     "severity": 90,
     "traffic": 80,
     "road_importance": 85,
     "location_risk": 70,
     "accessibility": 75,
     "emergency_override": false
   }
4. GET /api/v1/inspections again. Check priority_score, priority_level,
   priority_explanation, and priority_factors.
5. Refresh the page; values should remain because they are stored in SQLite.

IMPORTANT:
- New detections are not automatically assigned guessed traffic/road/accessibility values.
  Set priority through the PATCH endpoint after a real inspection is created.
- Emergency override behavior is defined by prioritization.py. Treat it as a prototype
  mechanism, not an official emergency policy.
- This package does not modify detector.py or the frontend.
- If your existing prioritization.py uses different function names or return keys,
  compare it before replacing files.
