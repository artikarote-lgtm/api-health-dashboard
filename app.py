from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_mail import Mail, Message
import requests
import time
from urllib.parse import urlparse
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# LOGIN CREDENTIALS
USERNAME = "admin"
PASSWORD = "admin123"

# EMAIL CONFIGURATION
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'arti.karote@cumminscollege.in'
app.config['MAIL_PASSWORD'] = 'eddg vtqy lvwl uybj'

mail = Mail(app)

APIS = {
    "FakeStore": "https://fakestoreapi.com/products/1",
    "GitHub": "https://api.github.com",
    "JSONPlaceholder": "https://jsonplaceholder.typicode.com/posts/1",
    "Stack Overflow": "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow",
    "DummyJSON": "https://dummyjson.com/products",
    "Weather": "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true",
    "Crypto": "https://api.coindesk.com/v1/bpi/currentprice.json"
}

response_history = []
uptime_data = {}


# LOGIN ROUTES
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


def login_required():
    return "user" in session


# URL CHECK
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# EMAIL ALERT
def send_alert(api_name, url):
    try:
        msg = Message(
            subject=f"🚨 API DOWN ALERT: {api_name}",
            sender=app.config['MAIL_USERNAME'],
            recipients=['arti.karote@cumminscollege.in']
        )

        msg.body = f"""
API DOWN ALERT

API Name: {api_name}
URL: {url}
"""

        mail.send(msg)

    except Exception as e:
        print("Email failed:", e)


def check_api(name, url):
    try:
        start = time.time()
        r = requests.get(url, timeout=5)
        response_time = round((time.time() - start) * 1000, 2)

        status = "UP" if r.status_code < 400 else "DOWN"

        if name not in uptime_data:
            uptime_data[name] = {"up": 0, "total": 0}

        uptime_data[name]["total"] += 1

        if status == "UP":
            uptime_data[name]["up"] += 1

        uptime = round(
            (uptime_data[name]["up"] / uptime_data[name]["total"]) * 100, 2
        )

        response_history.append(response_time)

        if len(response_history) > 20:
            response_history.pop(0)

        return {
            "name": name,
            "status": status,
            "response_time": response_time,
            "status_code": r.status_code,
            "uptime": uptime,
            "time": time.strftime("%H:%M:%S")
        }

    except:
        send_alert(name, url)

        return {
            "name": name,
            "status": "DOWN",
            "response_time": 0,
            "status_code": "ERROR",
            "uptime": 0,
            "time": time.strftime("%H:%M:%S")
        }


def generate_chart():
    if not response_history:
        return

    plt.figure()
    plt.plot(response_history)
    plt.savefig("static/chart.png")
    plt.close()


@app.route("/")
def home():
    if not login_required():
        return redirect("/login")

    return render_template("index.html")


@app.route("/status")
def status():
    if not login_required():
        return redirect("/login")

    data = [check_api(name, url) for name, url in APIS.items()]
    generate_chart()
    return jsonify(data)


@app.route("/add_api", methods=["POST"])
def add_api():
    data = request.json
    name = data.get("name")
    url = data.get("url")

    APIS[name] = url

    return jsonify({"message": "added"})


@app.route("/delete_api", methods=["POST"])
def delete_api():
    data = request.json
    name = data.get("name")

    if name in APIS:
        del APIS[name]

    return jsonify({"message": "deleted"})


if __name__ == "__main__":
    app.run(debug=True)