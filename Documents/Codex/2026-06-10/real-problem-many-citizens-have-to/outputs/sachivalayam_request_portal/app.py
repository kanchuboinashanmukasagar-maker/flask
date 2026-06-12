from datetime import datetime
from functools import wraps
import os
import sqlite3
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "requests.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-sachivalayam-portal"

OFFICER_USERNAME = "officer"
OFFICER_PASSWORD = "sachivalayam123"

OFFICERS = {
    "drainage": "Sanitation Officer - Ward 4",
    "street_lights": "Electrical Officer - Zone 2",
    "water_supply": "Water Works Officer - Ward 6",
    "certificate": "Revenue Assistant",
    "pension": "Welfare Assistant",
    "other": "Sachivalayam Coordinator",
}

SAMPLE_REQUESTS = [
    {
        "tracking_id": "SVM-2026-1001",
        "citizen_name": "Ravi Kumar",
        "phone": "9876543210",
        "ward": "Ward 4",
        "category": "drainage",
        "title": "Drainage overflow near market road",
        "description": "Drainage water is overflowing near the market road entrance.",
        "documents": "Location photo submitted",
        "status": "In Progress",
        "officer": OFFICERS["drainage"],
    },
    {
        "tracking_id": "SVM-2026-1002",
        "citizen_name": "Anusha Reddy",
        "phone": "9876501234",
        "ward": "Ward 2",
        "category": "street_lights",
        "title": "Street light not working",
        "description": "Street light near school junction has not worked for three days.",
        "documents": "No documents missing",
        "status": "Pending",
        "officer": OFFICERS["street_lights"],
    },
    {
        "tracking_id": "SVM-2026-1003",
        "citizen_name": "Shaik Sameer",
        "phone": "9876512345",
        "ward": "Ward 6",
        "category": "certificate",
        "title": "Income certificate application",
        "description": "Applied for income certificate and waiting for verification.",
        "documents": "Ration card copy required",
        "status": "Documents Missing",
        "officer": OFFICERS["certificate"],
    },
    {
        "tracking_id": "SVM-2026-1004",
        "citizen_name": "Mary Joseph",
        "phone": "9876523456",
        "ward": "Ward 1",
        "category": "water_supply",
        "title": "Low water pressure",
        "description": "Water pressure is very low in the morning supply window.",
        "documents": "No documents missing",
        "status": "Completed",
        "officer": OFFICERS["water_supply"],
    },
]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id TEXT UNIQUE NOT NULL,
                citizen_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                ward TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                documents TEXT NOT NULL,
                status TEXT NOT NULL,
                officer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        if count == 0:
            now = datetime.now().strftime("%d %b %Y, %I:%M %p")
            for item in SAMPLE_REQUESTS:
                conn.execute(
                    """
                    INSERT INTO requests (
                        tracking_id, citizen_name, phone, ward, category, title,
                        description, documents, status, officer, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["tracking_id"],
                        item["citizen_name"],
                        item["phone"],
                        item["ward"],
                        item["category"],
                        item["title"],
                        item["description"],
                        item["documents"],
                        item["status"],
                        item["officer"],
                        now,
                        now,
                    ),
                )


@app.before_request
def prepare_database():
    init_db()


def new_tracking_id():
    return f"SVM-{datetime.now().year}-{uuid4().hex[:6].upper()}"


def get_request_by_tracking_id(tracking_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM requests WHERE tracking_id = ?",
            (tracking_id.strip().upper(),),
        ).fetchone()


def officer_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("officer_logged_in"):
            flash("Officer login is required to access that page.", "error")
            return redirect(url_for("officer_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def index():
    with get_db() as conn:
        rows = conn.execute("SELECT status FROM requests").fetchall()
        total = len(rows)
        pending = sum(1 for row in rows if row["status"] in {"Pending", "Documents Missing"})
        in_progress = sum(1 for row in rows if row["status"] == "In Progress")
        completed = sum(1 for row in rows if row["status"] == "Completed")

    return render_template(
        "index.html",
        stats={
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
        },
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        citizen_name = request.form["citizen_name"].strip()
        phone = request.form["phone"].strip()
        ward = request.form["ward"].strip()
        category = request.form["category"]
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        documents = request.form["documents"].strip() or "No documents missing"

        if not all([citizen_name, phone, ward, category, title, description]):
            flash("Please fill every required field before submitting.", "error")
            return redirect(url_for("register"))

        tracking_id = new_tracking_id()
        now = datetime.now().strftime("%d %b %Y, %I:%M %p")
        officer = OFFICERS.get(category, OFFICERS["other"])

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO requests (
                    tracking_id, citizen_name, phone, ward, category, title,
                    description, documents, status, officer, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tracking_id,
                    citizen_name,
                    phone,
                    ward,
                    category,
                    title,
                    description,
                    documents,
                    "Pending",
                    officer,
                    now,
                    now,
                ),
            )

        flash(f"Request registered successfully. Your ID is {tracking_id}.", "success")
        return redirect(url_for("track", tracking_id=tracking_id))

    return render_template("register.html", officers=OFFICERS)


@app.route("/track", methods=["GET", "POST"])
@app.route("/track/<tracking_id>")
def track(tracking_id=None):
    if request.method == "POST":
        return redirect(url_for("track", tracking_id=request.form["tracking_id"]))

    record = None
    if tracking_id:
        record = get_request_by_tracking_id(tracking_id)
        if record is None:
            flash("No request found for that application or complaint ID.", "error")

    return render_template("track.html", record=record, tracking_id=tracking_id)


@app.route("/officer/login", methods=["GET", "POST"])
def officer_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        next_page = request.form.get("next") or url_for("dashboard")

        if username == OFFICER_USERNAME and password == OFFICER_PASSWORD:
            session["officer_logged_in"] = True
            session["officer_name"] = "Sachivalayam Officer"
            flash("Officer login successful.", "success")
            return redirect(next_page)

        flash("Invalid officer username or password.", "error")

    return render_template("login.html", next=request.args.get("next", ""))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@officer_required
def dashboard():
    query = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    sql = "SELECT * FROM requests WHERE 1 = 1"
    params = []
    if query:
        sql += """
            AND (
                tracking_id LIKE ? OR citizen_name LIKE ? OR phone LIKE ? OR
                ward LIKE ? OR title LIKE ? OR officer LIKE ?
            )
        """
        search = f"%{query}%"
        params.extend([search] * 6)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC"

    with get_db() as conn:
        records = conn.execute(sql, params).fetchall()
        counts = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'Documents Missing' THEN 1 ELSE 0 END) AS missing,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed
            FROM requests
            """
        ).fetchone()

    return render_template(
        "dashboard.html",
        records=records,
        counts=counts,
        query=query,
        status=status,
        statuses=["Pending", "Documents Missing", "In Progress", "Completed"],
    )


@app.route("/request/<tracking_id>", methods=["GET", "POST"])
@officer_required
def request_detail(tracking_id):
    record = get_request_by_tracking_id(tracking_id)
    if record is None:
        flash("Request not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        status = request.form["status"]
        officer = request.form["officer"].strip()
        documents = request.form["documents"].strip() or "No documents missing"
        now = datetime.now().strftime("%d %b %Y, %I:%M %p")

        with get_db() as conn:
            conn.execute(
                """
                UPDATE requests
                SET status = ?, officer = ?, documents = ?, updated_at = ?
                WHERE tracking_id = ?
                """,
                (status, officer, documents, now, tracking_id),
            )

        flash("Request updated successfully.", "success")
        return redirect(url_for("request_detail", tracking_id=tracking_id))

    return render_template(
        "detail.html",
        record=record,
        officers=sorted(set(OFFICERS.values())),
        statuses=["Pending", "Documents Missing", "In Progress", "Completed"],
    )


if __name__ == "__main__":
    app.run(debug=True)
