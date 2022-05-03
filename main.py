import uvicorn
import json
from fastapi import (
    FastAPI,
    Response,
    File,
    UploadFile,
    Request,
    Depends,
    BackgroundTasks,
    Query,
    HTTPException,
)
from fastapi import Path as PathParam
from pathlib import Path
from typing import Optional
import glob
from pydantic import BaseModel
from starlette.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import ffmpeg
from pydantic import Field
import aiofiles
import os
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

  

templates = Jinja2Templates(directory="static")
app = FastAPI()
base_path = "./videos/"


# class SanatizedPathParam(str):
#     """
#     TODO Document
#     """

#     def __new__(
#         cls,
#         path: str = Query(
#             "test",
#             title="The description of the item",
#         ),
#     ):
#         return path.replace("\\", "").replace("/", "")


class UploadParam(str):
    """
    TODO Document
    """

    def __new__(
        cls,
        path: Optional[str] =
        Query(
            "",
            title="The description of the item",
        ),
    ):
        if path in next(os.walk(base_path))[1]:
            return path
        else:
            return ""      


class SanatizedPathParam(BaseModel):
    """
    TODO Document
    """

    path: str

    @classmethod
    def inject(
        cls,
        path: str = PathParam(
            "",
            description=("Text to explain this value"),
        ),
    ):
        return path.replace("\\", "").replace("/", "")


@app.post("/create_directory")
async def create_directory(
    folder_name: SanatizedPathParam = Depends(SanatizedPathParam.inject),
):
    path = base_path + folder_name
    if not os.path.exists(path):
        os.makedirs(path)


@app.get("/")
async def get_videos():
    data = {}
    files =  list(Path("./videos/").rglob("*.m3u8"))
    for file in files:
        filepath = os.path.relpath(file, base_path)
        data[file.stem] = f"http://localhost:8081/watch/{filepath}"
    return JSONResponse(content=data)


@app.get("/video/{directory_name}/{path:path}")
async def stream_video(response: Response, directory_name,path):
    response.headers["Content-Type"] = "application/x-mpegURL"
    path = f"{directory_name}/{path}"
    return FileResponse(f"./videos/{path}", filename=path)


@app.get("/watch/{directory_name}/{file_name}")
async def watch_video(request: Request,directory_name, file_name):
    return templates.TemplateResponse(
        f"index.html", {"request": request, "folder_name": directory_name, "video_name": file_name}
    )


def ffmpeg_conversion(path, file: UploadFile):
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







@app.post("/uploadfile/")
async def create_upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    folder: UploadParam = Depends(),
):
    path = f"./videos/{folder}/{file.filename}"
    async with aiofiles.open(path, "wb") as out_file:
        content = await file.read()  # async read
        await out_file.write(content)
    background_tasks.add_task(ffmpeg_conversion, path, file)
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
