import os
import json
import mimetypes
import uuid
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from requests_toolbelt.multipart import decoder
from PIL import Image

HOST = "0.0.0.0"
PORT = 5000
MAX_SIZE_FILE = 5*1024*1024
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

os.makedirs("images", exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=f'{"logs"}/app.log',
    filemode='a'
)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def size_file(file_data):
    return len(file_data)<=MAX_SIZE_FILE

def secure_filename(filename):
    return filename.replace('..', '').replace('/', '').replace('\\', '')

class ImageServer(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open("./static/index.html", "rb") as f:
                self.wfile.write(f.read())
        elif self.path == "/images":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open("./static/images.html", "rb") as f:
                self.wfile.write(f.read())
        elif self.path == "/upload":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open("./static/upload.html", "rb") as f:
                self.wfile.write(f.read())
        elif self.path.startswith("/style/") or self.path.startswith("/js/") or self.path.startswith("/img/"):
            file_path = "./static" + self.path
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                mime_type, _ = mimetypes.guess_type(file_path)
                self.send_header("Content-Type", mime_type or 'application/octet-stream')
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
        else:
            self.send_error_response(404, '404 Not Found')

    def do_POST(self):
        # если приходит пост запрос на загрузку файла
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)

                saved = []
                filepath = ''

                # Проверяем верный ли формат файла
                if not content_type.startswith('multipart/form-data'):
                    raise ValueError("Content-Type must be multipart/form-data")

                try:
                    multipart_data = decoder.MultipartDecoder(body, content_type)
                except Exception as e:
                    raise ValueError(f"Parsing multipart data - {str(e)}")

                # Проверяем не превышает ли файл допустимый размер
                if not size_file(body):
                    raise ValueError("Content-Length должен быть меньше 5 Mb")

                # Читаем переданные данные
                for part in multipart_data.parts:
                    disposition = part.headers.get(b'Content-Disposition', b'').decode('utf-8')
                    if 'filename' not in disposition:
                        continue

                    # Присваиваем уникальное имя
                    ext = disposition.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4()}.{ext[:-1]}"
                    filename = secure_filename(unique_filename)
                    filepath = os.path.join("images", filename)

                    # Сохраняем файл
                    try:
                        with open(filepath, 'wb') as f:
                            f.write(part.content)
                    except Exception as e:
                        self.send_error_response(500, f"Ошибка сохранения файла ({filename}) - {str(e)}")
                        continue

                    # Делаем проверки после сохранения
                    try:
                        with Image.open(filepath) as img:
                            img.load()
                            format = img.format
                            size = img.size
                        if format.lower() not in ALLOWED_EXTENSIONS:
                            raise ValueError(f'Запрещенный формат ({format})')
                        saved.append(f"{filename} (format: {format}, size: {size})")
                    except Exception as e:
                        os.remove(filepath)
                        self.send_error_response(500, f"Не валидный файл ({filename}) - {str(e)}")
                        continue

                if saved:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"path": filepath}).encode('utf-8'))
                    logging.info(f'Успех: Файл ({filepath}) успешно сохранен')
            except Exception as e:
                self.send_error_response(500, f'Error saving file: {str(e)}')


    def send_error_response(self, param, param1):
        logging.info(f'Ошибка: {param1}')
        self.send_response(param)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": param1}).encode('utf-8'))


if __name__ == "__main__":
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, ImageServer)
    print(f"Server started on http://{HOST}:{PORT}")
    httpd.serve_forever()





