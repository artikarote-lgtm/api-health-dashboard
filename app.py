from flask import Flask, render_template, jsonify, request
import requests
import time
from urllib.parse import urlparse

app = Flask(__name__)

APIS = {
    "FakeStore": "https://fakestoreapi.com/products/1",
    "GitHub": "https://api.github.com",
    "JSONPlaceholder": "https://jsonplaceholder.typicode.com/posts/1"
}

# URL FORMAT CHECK
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# API CHECK (REAL VALIDATION)
def check_api(name, url):
    try:
        start = time.time()
        r = requests.get(url, timeout=5)
        response_time = round((time.time() - start) * 1000, 2)

        status = "UP" if r.status_code < 400 else "DOWN"

        return {
            "name": name,
            "status": status,
            "response_time": response_time,
            "status_code": r.status_code,
            "time": time.strftime("%H:%M:%S")
        }

    except:
        return {
            "name": name,
            "status": "DOWN",
            "response_time": 0,
            "status_code": "ERROR",
            "time": time.strftime("%H:%M:%S")
        }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify([check_api(name, url) for name, url in APIS.items()])


# ➕ ADD API (BACKEND VALIDATION ONLY)
@app.route("/add_api", methods=["POST"])
def add_api():
    data = request.json
    name = data.get("name")
    url = data.get("url")

    if not name or not url:
        return jsonify({"error": "Missing data"}), 400

    # format check
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL format"}), 400

    # REAL API CHECK (IMPORTANT FIX)
    try:
        r = requests.get(url, timeout=5)

        # Accept even redirects / API responses
        if r.status_code >= 500:
            return jsonify({"error": "API server error"}), 400

    except:
        return jsonify({"error": "API not reachable or wrong URL"}), 400

    APIS[name] = url
    return jsonify({"message": "API added successfully"})


# ❌ DELETE API
@app.route("/delete_api", methods=["POST"])
def delete_api():
    data = request.json
    name = data.get("name")

    if name in APIS:
        del APIS[name]

    return jsonify({"message": "deleted"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)