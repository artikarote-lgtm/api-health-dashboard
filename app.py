from flask import Flask, render_template, jsonify, request
from flask_mail import Mail, Message
import requests
import time
from urllib.parse import urlparse
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

mail = Mail(app)

APIS = {
    "FakeStore": "https://fakestoreapi.com/products/1",
    "GitHub": "https://api.github.com",
    "JSONPlaceholder": "https://jsonplaceholder.typicode.com/posts/1"
}

# Store response time history
response_history = []

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

        # store response time
        response_history.append(response_time)

        # keep last 20 values
        if len(response_history) > 20:
            response_history.pop(0)

        return {
            "name": name,
            "status": status,
            "response_time": response_time,
            "status_code": r.status_code,
            "time": time.strftime("%H:%M:%S")
        }

    except:
        send_alert(name, url)   # 🔴 NEW LINE ADDED
        return {
            "name": name,
            "status": "DOWN",
            "response_time": 0,
            "status_code": "ERROR",
            "time": time.strftime("%H:%M:%S")
        }


# GENERATE CHART
def generate_chart():
    if not response_history:
        return

    plt.figure()
    plt.plot(response_history, marker='o')
    plt.title("API Response Time")
    plt.xlabel("Requests")
    plt.ylabel("Response Time (ms)")
    
    if not os.path.exists("static"):
        os.makedirs("static")

    plt.savefig("static/chart.png")
    plt.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/status")
def status():
    data = [check_api(name, url) for name, url in APIS.items()]
    
    # Generate graph
    generate_chart()

    return jsonify(data)


# ➕ ADD API
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

    # REAL API CHECK
    try:
        r = requests.get(url, timeout=5)

        if r.status_code >= 500:
            return jsonify({"error": "API server error"}), 400

    except:
        return jsonify({"error": "API not reachable"}), 400

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


# GRAPH ROUTE
@app.route("/chart")
def chart():
    return render_template("chart.html")

def send_alert(api_name, url):
    try:
        msg = Message(
            subject=f"🚨 API DOWN ALERT: {api_name}",
            sender=app.config['MAIL_USERNAME'],
            recipients=['your_email@gmail.com']
        )

        msg.body = f"""
        ALERT!

        API Name: {api_name}
        URL: {url}
        Status: DOWN ❌

        Please check immediately.
        """

        mail.send(msg)

    except Exception as e:
        print("Email failed:", e)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)