From flask import Flask, request, jsonify
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
import binascii
import aiohttp
import requests
import json
import random # র‍্যান্ডম সিলেকশনের জন্য
from proto import like_pb2
from proto import like_count_pb2
from proto import uid_generator_pb2
from google.protobuf.message import DecodeError

app = Flask(__name__)

# টোকেন লোডিং ফাংশন: এটি সম্পূর্ণ তালিকা থেকে র‍্যান্ডম ১০০টি টোকেন লোড করবে
def load_tokens(server_name):
    try:
        if server_name == "IND":
            file_name = "token_ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            file_name = "token_br.json"
        else:
            file_name = "token_bd.json" 

        with open(file_name, "r") as f:
            all_tokens = json.load(f) # সমস্ত টোকেন লোড

        NUMBER_OF_TOKENS_TO_LOAD = 100 

        # যদি মোট টোকেন, লোড করার টার্গেট সংখ্যার চেয়ে বেশি হয়
        if len(all_tokens) >= NUMBER_OF_TOKENS_TO_LOAD:
            # সম্পূর্ণ তালিকা থেকে র‍্যান্ডমভাবে ১০০টি টোকেন বেছে নেওয়া হলো
            tokens = random.sample(all_tokens, NUMBER_OF_TOKENS_TO_LOAD)
        else:
            # ১০০টির কম টোকেন থাকলে, সবগুলিই ব্যবহার করা হবে
            tokens = all_tokens
        
        return tokens # এখন এটি লোড করা র‍্যান্ডম ১০০টি টোকেনের তালিকা ফেরত দেবে
        
    except Exception as e:
        app.logger.error(f"Error loading tokens for server {server_name}: {e}")
        return None

def encrypt_message(plaintext):
    try:
        key = b'Yg&tc%DEuh6%Zc^8'
        iv = b'6oyZDr22E3ychjM%'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        encrypted_message = cipher.encrypt(padded_message)
        return binascii.hexlify(encrypted_message).decode('utf-8')
    except Exception as e:
        app.logger.error(f"Error encrypting message: {e}")
        return None

def create_protobuf_message(user_id, region):
    try:
        message = like_pb2.like()
        message.uid = int(user_id)
        message.region = region
        return message.SerializeToString()
    except Exception as e:
        app.logger.error(f"Error creating protobuf message: {e}")
        return None

async def send_request(encrypted_uid, token, url):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB50"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=edata, headers=headers) as response:
                if response.status != 200:
                    app.logger.error(f"Request failed with status code: {response.status}")
                    return response.status
                return await response.text()
    except Exception as e:
        app.logger.error(f"Exception in send_request: {e}")
        return None

# পরিবর্তিত ফাংশন যা লোড করা সমস্ত টোকেন (১০০টি) ব্যবহার করবে
async def send_multiple_requests_modified(uid, server_name, url, tokens):
    try:
        region = server_name
        protobuf_message = create_protobuf_message(uid, region)
        if protobuf_message is None:
            app.logger.error("Failed to create protobuf message.")
            return None
        encrypted_uid = encrypt_message(protobuf_message)
        if encrypted_uid is None:
            app.logger.error("Encryption failed.")
            return None
            
        tasks = []
        
        # লোড করা সমস্ত (১০০টি) টোকেন ব্যবহার করে রিকোয়েস্ট তৈরি করা হলো
        for token_info in tokens:
            token = token_info["token"]
            tasks.append(send_request(encrypted_uid, token, url))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    except Exception as e:
        app.logger.error(f"Exception in send_multiple_requests: {e}")
        return None


# আগের send_multiple_requests ফাংশনটি এখন আর ব্যবহার হবে না (কিন্তু কোডে রেখে দিলাম)
async def send_multiple_requests(uid, server_name, url):
    # এই ফাংশনটি আর ব্যবহার করা হবে না, কিন্তু কোডের সামঞ্জস্যের জন্য রাখা হলো।
    # এটি আপনার মূল কোড অনুসারে শুধুমাত্র ২টি রিকোয়েস্ট পাঠাতো।
    app.logger.warning("Using deprecated send_multiple_requests. Should use send_multiple_requests_modified.")
    tokens = load_tokens(server_name)
    if tokens is None: return None
    
    # ... আগের লজিক...
    
    # যেহেতু লজিক পরিবর্তন করা হয়েছে, আমরা নতুন ফাংশনটি ব্যবহার করব।
    # সামঞ্জস্যের জন্য এখানে শুধু একটি রিটার্ন স্টেটমেন্ট রাখা হলো।
    return await send_multiple_requests_modified(uid, server_name, url, tokens)


def create_protobuf(uid):
    try:
        message = uid_generator_pb2.uid_generator()
        message.saturn_ = int(uid)
        message.garena = 1
        return message.SerializeToString()
    except Exception as e:
        app.logger.error(f"Error creating uid protobuf: {e}")
        return None

def enc(uid):
    protobuf_data = create_protobuf(uid)
    if protobuf_data is None:
        return None
    encrypted_uid = encrypt_message(protobuf_data)
    return encrypted_uid

def make_request(encrypt, server_name, token):
    try:
        if server_name == "IND":
            url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        else:
            url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
        edata = bytes.fromhex(encrypt)
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB50"
        }
        response = requests.post(url, data=edata, headers=headers, verify=False)
        hex_data = response.content.hex()
        binary = bytes.fromhex(hex_data)
        decode = decode_protobuf(binary)
        if decode is None:
            app.logger.error("Protobuf decoding returned None.")
        return decode
    except Exception as e:
        app.logger.error(f"Error in make_request: {e}")
        return None

def decode_protobuf(binary):
    try:
        items = like_count_pb2.Info()
        items.ParseFromString(binary)
        return items
    except DecodeError as e:
        app.logger.error(f"Error decoding Protobuf data: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Unexpected error during protobuf decoding: {e}")
        return None

@app.route('/like', methods=['GET'])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    if not uid or not server_name:
        return jsonify({"error": "UID and server_name are required"}), 400

    try:
        def process_request():
            
            # ১. র‍্যান্ডম ১০০টি টোকেন লোড করা হলো
            tokens = load_tokens(server_name) 
            if tokens is None or not tokens:
                raise Exception("Failed to load tokens or no tokens available.")
            
            # ২. লাইক চেকিং-এর জন্য লোড হওয়া ১০০টি টোকেনের মধ্যে প্রথমটি ব্যবহার করা হলো
            token_for_info = tokens[0]['token'] 
            
            encrypted_uid = enc(uid)
            if encrypted_uid is None:
                raise Exception("Encryption of UID failed.")

            # লাইক চেকিং: BEFORE
            before = make_request(encrypted_uid, server_name, token_for_info)
            if before is None:
                raise Exception("Failed to retrieve initial player info.")
            try:
                jsone = MessageToJson(before)
            except Exception as e:
                raise Exception(f"Error converting 'before' protobuf to JSON: {e}")
            data_before = json.loads(jsone)
            before_like = data_before.get('AccountInfo', {}).get('Likes', 0)
            try:
                before_like = int(before_like)
            except Exception:
                before_like = 0
            app.logger.info(f"Likes before command: {before_like}")

            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"

            # ৩. লাইক পাঠানো: লোড হওয়া সমস্ত (১০০টি) টোকেন ব্যবহার করা হলো
            asyncio.run(send_multiple_requests_modified(uid, server_name, url, tokens)) 
            # Note: এখানে 'tokens' লিস্টটি (র‍্যান্ডম ১০০টি টোকেন) পাস করা হচ্ছে।

            # লাইক চেকিং: AFTER (একই token_for_info ব্যবহার করে)
            after = make_request(encrypted_uid, server_name, token_for_info)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")
            try:
                jsone_after = MessageToJson(after)
            except Exception as e:
                raise Exception(f"Error converting 'after' protobuf to JSON: {e}")
            data_after = json.loads(jsone_after)
            after_like = int(data_after.get('AccountInfo', {}).get('Likes', 0))
            player_uid = int(data_after.get('AccountInfo', {}).get('UID', 0))
            player_name = str(data_after.get('AccountInfo', {}).get('PlayerNickname', ''))
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2
            result = {
                "LikesGivenByAPI": like_given,
                "LikesbeforeCommand": before_like,
                "LikesafterCommand": after_like,
                "PlayerNickname": player_name,
                "UID": player_uid,
                "status": status
            }
            return result

        result = process_request()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "credits": "powerd by rohan",
        "Telegram like bot username": "@profilelikeff"
    })
if __name__ == '__main__':
    
    app.run(debug=True, use_reloader=False)
