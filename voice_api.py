# from flask import Flask, request, jsonify
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)  # Allow cross-origin requests from Streamlit

# latest_text = ""  # Store latest voice input text

# @app.route("/receive", methods=["POST"])
# def receive():
#     global latest_text
#     data = request.get_json()  
#     if data and "text" in data:
#         latest_text = data["text"]
#         print(f"✅ Received voice input: '{latest_text}'")
#         return jsonify({"status": "received", "text": latest_text})
#     else:
#         print("❌ Invalid data received")
#         return jsonify({"status": "error", "message": "Invalid data"}), 400

# @app.route("/latest", methods=["GET"])
# def latest():
#     global latest_text
#     return jsonify({"text": latest_text})

# @app.route("/clear", methods=["POST"])
# def clear():
#     global latest_text
#     latest_text = ""  # Clear the stored text
#     print("🗑️ Cleared stored voice input")
#     return jsonify({"status": "cleared"})

# @app.route("/status", methods=["GET"])
# def status():
#     return jsonify({
#         "status": "running",
#         "has_text": bool(latest_text),
#         "text_preview": latest_text[:50] + "..." if len(latest_text) > 50 else latest_text
#     })

# if __name__ == "__main__":
#     print("🎙️ Voice API Server starting...")
#     print("📡 Server running at http://127.0.0.1:5001")
#     print("🔗 Endpoints:")
#     print("   POST /receive - Receive voice input")
#     print("   GET  /latest  - Get latest voice input")
#     print("   POST /clear   - Clear stored input")
#     print("   GET  /status  - Check server status")
#     app.run(host="127.0.0.1", port=5001, debug=True)





from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Store user-wise voice inputs
user_text_store = {}

@app.route("/receive", methods=["POST"])
def receive():
    data = request.get_json()
    user_id = data.get("user_id")
    text = data.get("text")

    if not user_id or not text:
        return jsonify({"status": "error", "message": "Missing user_id or text"}), 400

    user_text_store[user_id] = text
    print(f"✅ Received from {user_id}: '{text}'")
    return jsonify({"status": "received", "text": text})

@app.route("/latest", methods=["GET"])
def latest():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    return jsonify({"text": user_text_store.get(user_id, "")})

@app.route("/clear", methods=["POST"])
def clear():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    user_text_store[user_id] = ""
    print(f"🗑️ Cleared input for {user_id}")
    return jsonify({"status": "cleared"})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "running",
        "users": list(user_text_store.keys())
    })

if __name__ == "__main__":
    print("🎙️ Voice API Server starting...")
    print("📡 Server running at http://0.0.0.0:5001")
    print("🔗 Endpoints:")
    print("   POST /receive - Receive voice input")
    print("   GET  /latest  - Get latest voice input")
    print("   POST /clear   - Clear stored input")
    print("   GET  /status  - Check server status")
    app.run(host="0.0.0.0", port=5001, debug=True)
