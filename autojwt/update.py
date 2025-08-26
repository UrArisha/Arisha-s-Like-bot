import base64
import json
import requests
import os
from http.server import BaseHTTPRequestHandler

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "your-username/your-repo"   # নিজের repo নাম
FILE_PATH = "token_bd.json"        # main/root এ টার্গেট ফাইল

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_type = self.headers.get('Content-Type', '')

        if "multipart/form-data" in content_type:
            boundary = content_type.split("boundary=")[1]
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length)

            parts = body.split(b"--" + boundary.encode())
            file_content = None
            for part in parts:
                if b"Content-Disposition" in part and b"filename=" in part:
                    file_content = part.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0]
                    break

            if not file_content:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"No file uploaded"}')
                return

            try:
                new_data = json.loads(file_content.decode())
            except:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"Invalid JSON file"}')
                return

        else:
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length).decode("utf-8")
            new_data = json.loads(body)

        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(url, headers=headers).json()

        if "sha" not in r:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"File not found or token invalid"}')
            return

        sha = r["sha"]
        content = base64.b64encode(json.dumps(new_data, indent=2).encode()).decode()

        update_data = {
            "message": "API upload JSON file",
            "content": content,
            "sha": sha
        }

        res = requests.put(url, headers=headers, data=json.dumps(update_data))

        self.send_response(res.status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(res.content)
