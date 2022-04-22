import uvicorn
import json
from fastapi import FastAPI, Response, File, UploadFile
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import ffmpeg
import aiofiles



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
    return FileResponse("./video/" + sanitize(fileName), filename=fileName)

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    async with aiofiles.open(f"./video/{file.filename}", 'wb') as out_file:
        content = await file.read()  # async read
        await out_file.write(content)
    
    ffmpeg.input(f"video/{file.filename}").output('./video/output.m3u8', vcodec="libx264",acodec="aac", format='hls', start_number=0, hls_time=10, hls_list_size=0, audio_bitrate="128k").run()
   
    return {"filename": file.filename,
    "fileb_content_type": file.content_type}



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
