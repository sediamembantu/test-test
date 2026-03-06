"""
CADI Web API - FastAPI backend for Vercel serverless deployment.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Import the SSE pipeline runner
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import run_agent_sse

app = FastAPI(title="CADI - Climate-Aware Deal Intelligence")


class AnalyseRequest(BaseModel):
    """Request body for analysis endpoint."""
    pdf_url: str | None = None
    deal_name: str = "Nusantara Digital Sdn Bhd"


@app.get("/")
async def root():
    """Redirect root to web UI."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>CADI</title></head>
    <body>
    <script>window.location.href = '/web/index.html';</script>
    </body>
    </html>
    """)


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "CADI API"}


@app.post("/api/run")
async def run_analysis(request: AnalyseRequest):
    """
    Run CADI analysis pipeline.
    
    Returns SSE stream with step-by-step progress and final results.
    """
    
    async def event_generator():
        """Generate SSE events from pipeline."""
        # Use the demo PDF if no URL provided
        pdf_path = "data/deal/nusantara_digital.pdf"
        output_dir = "output"
        
        try:
            for event_data in run_agent_sse(pdf_path, output_dir):
                # Yield as JSON string
                yield json.dumps(event_data)
        except Exception as e:
            yield json.dumps({"error": str(e), "done": True})
    
    return EventSourceResponse(event_generator())


@app.get("/api/results/{filename}")
async def get_results(filename: str):
    """Get generated results (map.html or memo.html)."""
    output_dir = Path("output")
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    content = file_path.read_text()
    
    if filename.endswith(".html"):
        return HTMLResponse(content=content)
    else:
        return {"content": content}


# Mount static files for web UI (Vercel handles this automatically)
# app.mount("/web", StaticFiles(directory="web"), name="web")
