from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3
import time
from datetime import datetime

app = Flask(__name__)
DB_NAME = "monitor.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            status_code INTEGER,
            response_time_ms REAL,
            is_success INTEGER,
            error_message TEXT,
            checked_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_log(url, status_code, response_time_ms, is_success, error_message, checked_at):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO api_logs (url, status_code, response_time_ms, is_success, error_message, checked_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (url, status_code, response_time_ms, is_success, error_message, checked_at))
    conn.commit()
    conn.close()


def get_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_logs ORDER BY id DESC")
    logs = cursor.fetchall()
    conn.close()
    return logs


def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM api_logs")
    total_checks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM api_logs WHERE is_success = 1")
    success_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(response_time_ms) FROM api_logs WHERE response_time_ms IS NOT NULL")
    avg_response = cursor.fetchone()[0]

    conn.close()

    return {
        "total_checks": total_checks,
        "success_count": success_count,
        "avg_response": round(avg_response, 2) if avg_response else 0
    }


@app.route("/")
def index():
    logs = get_logs()
    stats = get_stats()
    return render_template("index.html", logs=logs, stats=stats)


@app.route("/check", methods=["POST"])
def check_api():
    url = request.form.get("url")

    if not url:
        return redirect(url_for("index"))

    status_code = None
    response_time_ms = None
    is_success = 0
    error_message = ""
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()

        response_time_ms = round((end_time - start_time) * 1000, 2)
        status_code = response.status_code
        is_success = 1 if response.ok else 0

    except Exception as e:
        error_message = str(e)

    save_log(url, status_code, response_time_ms, is_success, error_message, checked_at)
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)