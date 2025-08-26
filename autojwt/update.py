import os
import json
import base64
import requests
from http.server import BaseHTTPRequestHandler

# ==========================
# Config
# ==========================
GITHUB_TOKEN = "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"  # Temporary token
REPO = "UrArisha/Arisha-s-Like-bot"
FILE_PATH = "token_bd.json"
BRANCH = "main"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read incoming JSON body
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        try:
            new_data = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"Invalid JSON"}')
            return

        # Get existing file info from GitHub
        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(url, headers=headers).json()

        if "sha" not in r:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"File not found or token invalid"}')
            return

        sha = r["sha"]
        content = base64.b64encode(json.dumps(new_data, indent=2).encode()).decode()

        # Update file on GitHub
        update_data = {
            "message": "API update JSON file",
            "content": content,
            "sha": sha,
            "branch": BRANCH
        }

        res = requests.put(url, headers=headers, data=json.dumps(update_data))

        self.send_response(res.status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(res.content)
