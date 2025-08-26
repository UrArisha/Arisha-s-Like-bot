# /autojwt/update.py
import os, json, base64, requests
from http.server import BaseHTTPRequestHandler

GITHUB_TOKEN = "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"
REPO = "UrArisha/Arisha-s-Like-bot"
FILE_PATH = "token_bd.json"
BRANCH = "main"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # পুরো JSON file POST হিসেবে নাও
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        try:
            new_file_content = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"Invalid JSON"}')
            return

        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        # Get current file SHA
        r = requests.get(url, headers=headers).json()
        if "sha" not in r:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"File not found or token invalid"}')
            return

        sha = r["sha"]
        content = base64.b64encode(json.dumps(new_file_content, indent=2).encode()).decode()

        update_data = {
            "message": "Replace entire JSON file via API",
            "content": content,
            "sha": sha,
            "branch": BRANCH
        }

        res = requests.put(url, headers=headers, data=json.dumps(update_data))
        self.send_response(res.status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(res.content)
