from __future__ import annotations

import os
import shutil
import tempfile
import mimetypes
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from no_mrn import mask_nric_in_image

app = FastAPI(title="MRN/NRIC Masking API")

# Allow Vite dev server and production frontend
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Add your Render frontend URL here after deployment:
    # "https://your-frontend-name.onrender.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/mask")
async def mask(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Validate content type roughly
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = ''.join(Path(file.filename).suffixes) or ".jpg"
    
    # Create temp files that persist until after the response is sent
    in_fd, in_path = tempfile.mkstemp(suffix=suffix, prefix="in_")
    out_fd, out_path = tempfile.mkstemp(suffix=".jpg", prefix="masked_")
    
    # Close the file descriptors (we just need the paths)
    os.close(in_fd)
    os.close(out_fd)
    
    try:
        # Save uploaded file
        with open(in_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Run masking with debug=True to see OCR output in terminal
        masked_path, masked_count = mask_nric_in_image(in_path, out_path, debug=True)

        # Prepare response filename
        safe_name = Path(file.filename).stem
        download_name = f"masked_{safe_name}.jpg"

        media_type = mimetypes.guess_type(download_name)[0] or "image/jpeg"
        headers = {
            "X-Masked-Count": str(masked_count),
            "Cache-Control": "no-store",
        }
        
        # Schedule cleanup after response is sent
        background_tasks.add_task(os.unlink, in_path)
        background_tasks.add_task(os.unlink, out_path)
        
        return FileResponse(
            path=masked_path,
            media_type=media_type,
            filename=download_name,
            headers=headers,
        )
    except HTTPException:
        raise
    except FileNotFoundError:
        # Clean up on error
        try:
            os.unlink(in_path)
        except:
            pass
        try:
            os.unlink(out_path)
        except:
            pass
        raise HTTPException(status_code=400, detail="Could not read the uploaded image")
    except Exception as e:
        # Clean up on error
        try:
            os.unlink(in_path)
        except:
            pass
        try:
            os.unlink(out_path)
        except:
            pass
        # Log in real usage; return generic error
        return JSONResponse(status_code=500, content={"error": "Processing failed", "detail": str(e)})


# Entry point for `python server.py` during development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
