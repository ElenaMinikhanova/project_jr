import time
import psycopg2

class DBManager:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cur = None

    def __enter__(self):
        for i in range(10):
            try:
                self.conn = psycopg2.connect(**self.config)
                break
            except psycopg2.OperationalError:
                print("Postgres not ready yet, retrying...")
                time.sleep(2)
        else:
            raise RuntimeError("Could not connect to Postgres after 10 tries")
        self.cur = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def create_table(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            size INTEGER NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT NOT NULL
        );""")
        self.cur.execute("commit;")

    def add_file(self, file):
        try:
            query = f"""
            INSERT INTO images (filename, original_name, size, file_type)
            VALUES ('{file['filename']}', '{file['original_name']}', {file['size']}, '{file['file_type']}');
            """
            self.cur.execute(query)
            self.cur.execute("commit;")
            print(f"Файл {file} добавлен")
        except Exception as e:
            print(e)

    def get_list(self, page):
        query = "SELECT * FROM images;"
        if page and int(page):
            offset = (int(page) - 1) * 10
            query = f"SELECT * FROM images ORDER BY id DESC LIMIT 10 OFFSET {offset};"
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.cur.execute('SELECT COUNT(*) FROM images')
        total = self.cur.fetchone()[0]

        return rows, total

    def get_by_id(self, file_id):
        self.cur.execute(f"SELECT * FROM images WHERE id = {file_id};")
        return self.cur.fetchone()

    def delete_by_id(self, file_id):
        try:
            self.cur.execute(f"DELETE FROM images WHERE id = {file_id};")
            self.cur.execute("commit;")
        except Exception as e:
            print(e)