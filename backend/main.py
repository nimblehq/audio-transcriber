from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.routers import meetings, jobs, analysis

app = FastAPI(title="Meeting Transcriber")

app.include_router(meetings.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")

frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
@app.get("/{path:path}")
async def serve_spa(path: str = ""):
    # Serve API routes normally (handled by routers above)
    # Everything else gets the SPA shell
    return FileResponse(str(frontend_dir / "index.html"))
