import uvicorn
import json
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse





app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def sanitize(item: str) -> str:
    """Make sure they can't do a directory transversal attack"""
    return item.replace("\\", "").replace("/", "")


@app.get("/video/{fileName}")
async def video(response: Response, fileName: str):
    response.headers["Content-Type"] = "application/x-mpegURL"
    return FileResponse("video/" + sanitize(fileName), filename=fileName)

@app.get("/video/{video_name}/{segment_number}.ts", response_class=FileResponse)
async def get_segment(video_name: str, segment_number: str):
    segment = "video" / sanitize(video_name) / f"{sanitize(segment_number)}.ts"
    if not segment.exists():
        return HTMLResponse(status_code=404)
    return segment

# @app.get("/markers")
# async def markers(response: Response, ts_start: float = -1.0):
#     markers = cache.get("markers", [])
#     markers = [m for m in markers if m["time"] > ts_start]
#     return JSONResponse(content=json.dumps({"markers": markers}))


app.mount("/", StaticFiles(directory="static", html=True), name="static")


def main():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        log_level="debug",
        reload=True,
        debug=True,
    )


if __name__ == "__main__":
    main()
