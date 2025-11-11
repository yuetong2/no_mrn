# No MRN – Image Masking

End-to-end sample: upload an image from a React (Vite) frontend and get back a copy with NRIC/MRN-like identifiers masked on the server using OCR (Tesseract + OpenCV).

## Backend (FastAPI)

Requirements:
- Python 3.10+
- Tesseract OCR installed (Windows: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`)

Install deps:

```powershell
# From the repo root
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run server:

```powershell
python .\server.py
# API at http://127.0.0.1:8000
# Health: http://127.0.0.1:8000/health
```

Notes:
- The server exports `POST /mask` accepting `multipart/form-data` with field `file`. It returns a masked image (`image/jpeg`) and header `X-Masked-Count` with the number of masked regions.
- If Tesseract is installed in a non-default path, set the path in `no_mrn.py` (see `_win_default_tesseract`).

## Frontend (Vite + React)

From `frontend/frontend`:

```powershell
cd .\frontend\frontend
npm install
npm run dev
# Opens http://localhost:5173
```

Configure backend URL (optional):

Create `.env` in `frontend/frontend` to point to a different API origin:

```
VITE_API_URL=http://127.0.0.1:8000
```

## How it works
- `no_mrn.py` exports `mask_nric_in_image(input_path, output_path)` which runs OCR and masks identifiers matching a regex.
- `server.py` accepts file uploads, runs masking, and streams the resulting image back for download.
- `frontend/frontend/src/App.tsx` provides a simple UI to select an image and download the masked result.

## Troubleshooting
- "Could not read the uploaded image": ensure the file is a supported image type (jpg, png) and OpenCV is installed (`opencv-python`).
- Tesseract not found: install Tesseract OCR and/or update the path in `no_mrn.py`.
- CORS errors: access the frontend via `http://localhost:5173` and backend at `http://127.0.0.1:8000`. You can add more origins in `server.py`.
