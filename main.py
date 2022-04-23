import uvicorn
import json
from fastapi import FastAPI, Response, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import ffmpeg
import aiofiles
import os
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

templates = Jinja2Templates(directory="static")
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


@app.get("/")
async def videos():
    data = {}
    for file in os.listdir(r"./video"):
        if file.endswith(".m3u8"):
            data[file] = f"http://localhost:8081/watch/{file}"
    return JSONResponse(content=data)


@app.get("/video/{fileName}")
async def video(response: Response, fileName: str):
    response.headers["Content-Type"] = "application/x-mpegURL"
    return FileResponse("./video/" + sanitize(fileName), filename=fileName)


@app.get("/watch/{fileName}")
async def video(request: Request, fileName: str):
    return templates.TemplateResponse(
        f"index.html", {"request": request, "video_name": fileName}
    )


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    async with aiofiles.open(f"./video/{file.filename}", "wb") as out_file:
        content = await file.read()  # async read
        await out_file.write(content)
    ffmpeg.input(f"video/{file.filename}").output(
        f"./video/{Path(file.filename).stem}.m3u8",
        vcodec="libx264",
        acodec="aac",
        bitrate="3000k",
        vbufsize="6000k",
        vmaxrate="6000k",
        format="hls",
        start_number=0,
        hls_time=10,
        hls_list_size=0,
        audio_bitrate="128k",
    ).run()

    return {"filename": file.filename, "fileb_content_type": file.content_type}


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
