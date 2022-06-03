import uvicorn
from fastapi import (
    FastAPI,
    Response,
    UploadFile,
    Request,
    Depends,
    BackgroundTasks,
    Query,
    HTTPException,
)
import re
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from starlette.responses import FileResponse
from fastapi.responses import JSONResponse
import ffmpeg
import aiofiles
import os
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

tags_metadata = [
    {
        "name": "folders",
        "description": "Create and Delete **folders** to store your videos in",
    },
    {
        "name": "upload",
        "description": "Upload and encode video files",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

templates = Jinja2Templates(directory="static")
app = FastAPI(openapi_tags=tags_metadata)
base_path = "./videos/"


class FolderParam(str):
    """
    TODO Document
    """

    def __new__(
        cls,
        path: Optional[str] = Query(
            "",
            description="Folder directory to store uploaded files in",
        ),
    ):
        if path in next(os.walk(base_path))[1]:
            return path
        else:
            raise HTTPException(status_code=404, detail="Folder not found")


class SanatizedPathParam(BaseModel):
    """"""

    path: str

    @classmethod
    def inject(
        cls,
        path: str = Query(
            "",
            description=("Text to explain this value"),
        ),
    ):
        return path.replace("\\", "").replace("/", "")


@app.get("/folders", tags=["folders"])
async def list_directory():
    return next(os.walk(base_path))[1]


@app.post("/create_directory", tags=["folders"])
async def create_directory(
    folder_name: SanatizedPathParam = Depends(SanatizedPathParam.inject),
):
    path = base_path + folder_name
    if not os.path.exists(path):
        os.makedirs(path)


@app.delete(
    "/delete_directory", description="List Current Directories", tags=["folders"]
)
async def delete_directory(
    folder_name: FolderParam = Depends(),
):
    path = base_path + folder_name
    os.rmdir(path)


@app.get(
    "/video/{directory_name}/{path:path}",
    summary="Stream HLS",
    description="Returns a File response for currently stored HLS encoded video files",
    tags=["videos"],
)
async def stream_video(response: Response, directory_name, path):
    response.headers["Content-Type"] = "application/x-mpegURL"
    path = f"{directory_name}/{path}"
    return FileResponse(f"./videos/{path}", filename=path)


@app.get(
    "/watch/{directory_name}/{file_name}",
    summary="Watch Videos",
    description="Servers HTML to display hosted videos",
    tags=["videos"],
)
async def watch_video(request: Request, directory_name, file_name):
    return templates.TemplateResponse(
        f"index.html",
        {"request": request, "folder_name": directory_name, "video_name": file_name},
    )


def ffmpeg_conversion(path):
    ffmpeg.input(path).output(
        f"{Path(path).with_suffix('')}.m3u8",
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


def adaptive_bitrate_ffmpeg(folder, path):
    command = f"""ffmpeg -i {Path(path).name} -c:v libx264 -crf 20 -g 5 -keyint_min 5 -sc_threshold 0 -hls_time 6 -hls_playlist_type vod -hls_flags independent_segments \
    -b:v:0 800k -filter:v:0 scale=640:360 \
    -b:v:1 1200k -filter:v:1 scale=842:480 \
    -b:v:2 2400k -filter:v:2 scale=1280:720 \
    -b:v:3 4800k -filter:v:3 scale=1920:1080 \
    -map a:0 -map a:0 -map a:0 -map a:0 -c:a aac -b:a 128k -ac 1 -ar 44100\
    -map 0:v -map 0:v -map 0:v -map 0:v -f hls -var_stream_map 'v:0,a:0 v:1,a:1 v:2,a:2 v:3,a:3' \
    -master_pl_name {Path(path).stem}.m3u8 \
    -hls_segment_filename {Path(path).stem}___%v/data%02d.ts \
    -strftime_mkdir 1 \
    {Path(path).stem}___%v.m3u8"""
    subprocess.call(command, shell=True, cwd=f"./videos/{folder}")


@app.post(
    "/upload/",
    summary="Upload a standard video file",
    description="Will create a standard hls encoding of the input video",
    tags=["upload"],
)
async def create_upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    folder: FolderParam = Depends(),
):
    path = f"./videos/{folder}/{file.filename}"
    async with aiofiles.open(path, "wb") as out_file:
        content = await file.read()  # async read
        await out_file.write(content)
    background_tasks.add_task(ffmpeg_conversion, path)
    return {"filename": file.filename, "fileb_content_type": file.content_type}


@app.post(
    "/upload_adaptive_bitrate/",
    summary="Upload a file served in an adaptive bitrate format",
    description="Will create an hls encoding of the input video in the following resolutions 360,480,720,1080",
    tags=["upload"],
)
async def upload_adaptive_bitrate(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    folder: FolderParam = Depends(),
):
    path = f"./videos/{folder}/{file.filename}"
    async with aiofiles.open(path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    background_tasks.add_task(adaptive_bitrate_ffmpeg, folder, path)
    return {"filename": file.filename, "fileb_content_type": file.content_type}


@app.get(
    "/",
    summary="Root",
    description="Displays video filename and link",
)
async def get_videos():
    data = {}
    files = list(Path("./videos/").rglob("*.m3u8"))
    for file in files:
        if not re.search("[_]{3,}", str(file)):
            filepath = os.path.relpath(file, base_path)
            data[file.stem] = f"http://0.0.0.0:8080/watch/{filepath}"
    return JSONResponse(content=data)


def main():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
        reload=True,
        debug=True,
    )


if __name__ == "__main__":
    main()
