import os
import json
import time
import logging
import mimetypes

from PIL import Image
from urllib.parse import urlparse, parse_qs
from requests_toolbelt.multipart import decoder
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from psycopg2 import OperationalError
from db import DBManager

postgres_config = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": 'db',
    "port": '5432',
}

HOST = "0.0.0.0"
PORT = 8000
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
LOGS_DIR = os.getenv("LOGS_DIR")
BACKUPS_DIR = os.getenv("BACKUPS_DIR")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE"))
ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'gif'}

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
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

class ApiServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open("./static/index.html", "rb") as f:
                self.wfile.write(f.read())
        elif path == "/images-list":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open("./static/images.html", "rb") as f:
                self.wfile.write(f.read())
        elif path == "/upload":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open("./static/form.html", "rb") as f:
                self.wfile.write(f.read())
        elif path.startswith("/css/") or path.startswith("/js/") or path.startswith("/img/"):
            file_path = "./static" + self.path
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                mime_type, _ = mimetypes.guess_type(file_path)
                self.send_header("Content-Type", mime_type or 'application/octet-stream')
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
        elif path == '/get-images':
            page = query['page'][0] if query['page'][0].isdigit() else None
            try:
                with DBManager(postgres_config) as db:
                    rows, total = db.get_list(page)
                    img_list = [{
                        'id': f[0],
                        'filename': f[1],
                        'original_name': f[2],
                        'size': f[3],
                        'upload_time': f[4].strftime('%Y-%m-%d %H:%M:%S'),
                        'file_type': f[5]
                    } for f in rows]
            except OperationalError as e:
                raise RuntimeError(f'Не удалось подключиться к базе данных: {e}')

            try:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"list": img_list, "total": total}).encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f'Ошибка чтения изображений - {str(e)}')

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

                if len(body) <= 0:
                    raise ValueError("Content-Length должен быть больше 0")

                # Проверяем не превышает ли файл допустимый размер
                if len(body) >= (MAX_FILE_SIZE * 1024 * 1024):
                    raise ValueError(f"Content-Length должен быть меньше {MAX_FILE_SIZE}Mb")

                # читаем переданные данные в цикле
                for part in multipart_data.parts:
                    disposition = part.headers.get(b'Content-Disposition', b'').decode('utf-8')
                    if 'filename' not in disposition:
                        continue

                    filename = str(int(time.time() * 1000))
                    original_name = disposition.split('filename="')[1].split('"')[0]
                    filetype = original_name.rsplit('.', 1)[1].lower()
                    file = {
                        'original_name': original_name,
                        'filename': filename,
                        'size': len(body),
                        'file_type': filetype,
                    }

                    filepath = os.path.join(UPLOAD_DIR, f'{filename}.{filetype}')

                    # Пробуем сохранить файл
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
                        if format.lower() not in ALLOWED_EXT:
                            raise ValueError(f'Запрещенный формат ({format})')
                        saved.append(f"{filename} (format: {format}, size: {size})")
                        with DBManager(postgres_config) as db:
                            db.add_file(file)
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
                    print(f'Успех: Файл ({filepath}) успешно сохранен')
            except Exception as e:
                self.send_error_response(500, f'Error saving file: {str(e)}')

    def do_DELETE(self):
        # Удаление файла по его имени
        if self.path == '/images':
            content_length = int(self.headers.get('Content-Length', 0))
            try:
                if content_length <= 0:
                    raise ValueError('Content-Length должен быть больше 0')

                body = self.rfile.read(content_length)
                file_id = body.decode('utf-8')

                # Проверяем переданные данные на пустоту
                if not file_id or not file_id.isdigit():
                    raise ValueError('Пустое ID файла')

                with DBManager(postgres_config) as db:
                    item = db.get_by_id(int(file_id))

                # Проверяем переданные данные на соответствие в бд
                if not item:
                    raise ValueError('Файл с таким ID отсутствует')

                filepath = os.path.join(UPLOAD_DIR, os.path.basename(f'{item[1]}.{item[5]}'))

                if os.path.exists(filepath) and os.path.isfile(filepath):
                    os.remove(filepath)
                    with DBManager(postgres_config) as db:
                        db.delete_by_id(int(file_id))
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"deleted": filepath}).encode('utf-8'))
                    logging.info(f'Успех: Файл ({filepath}) успешно удален')
                    print(f'Успех: Файл ({filepath}) успешно удален')
                else:
                    raise ValueError('File is not found')
            except Exception as e:
                self.send_error_response(500, str(e))
    def send_error_response(self, code, message):
        print(f'Ошибка: {message}')
        logging.error(f'Ошибка: {message}')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

if __name__ == '__main__':
    with DBManager(postgres_config) as pg:
        pg.create_table()

    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, ApiServer)
    print("Server started on http://localhost")
    httpd.serve_forever()


