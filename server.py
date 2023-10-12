import os

from fastapi.responses import HTMLResponse
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import requests
from starlette.responses import FileResponse

app = FastAPI()


@app.get("/server")
async def get_html():
    html_content = """
    Загрузи свой файл и он где-то выполнится
    <h1>Загрузка файла</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Загрузить">
    </form>
    """
    return HTMLResponse(content=html_content)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file is None:
        return JSONResponse(content="No file provided", status_code=400)

    if not os.path.exists("uploads"):
        os.mkdir("uploads")

    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(file.file.read())

    url = "http://127.0.0.1:8001/uploadfile/"
    files = {'file': (file.filename, open(f"uploads/{file.filename}", 'rb'))}
    response = requests.post(url, files=files)
    answer = response.content  # .replace("\n", "<br>")
    answer = str(answer).replace("\\\\n", "<br>")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Твой код улетел в космос</title>
    
    </head>
    <body>
        <div class="container">
            <h1>Твой файл с названием {file.filename} улетел в космос</h1>
            <br>
    
            <h1>Инопланетяне ответили:  </h1>
    
            <div class="blue-block">
            <p>{answer}</p>
        </div>
        </div>
    </body>
    </html>
    """ \
    + """
    <style>
        .blue-block {
            background-color: blue;
            color: white;
            padding: 20px;
        }
    </style>
    """
    return HTMLResponse(content=html_content)

