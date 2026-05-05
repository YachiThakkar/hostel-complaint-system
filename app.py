import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, send_from_directory

app = Flask(__name__)
app.secret_key = "super_secret_key_123"
app.config["UPLOAD_FOLDER"] = "uploads"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():
    conn = get_db()
    cursor = conn.cursor()

    name = request.form["name"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])
    room = request.form["room"]

    cursor.execute(
        "INSERT INTO students (name, email, password, room_number) VALUES (?, ?, ?, ?)",
        (name, email, password, room)
    )

    conn.commit()
    conn.close()

    return "Registration Successful!"


# ---------------- LOGIN ----------------

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login_user", methods=["POST"])
def login_user():
    conn = get_db()
    cursor = conn.cursor()

    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("SELECT * FROM students WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user"] = email
        session["role"] = "student"
        return redirect("/dashboard/" + email)
    else:
        return "Invalid Email or Password"


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/dashboard/<email>")
def dashboard(email):
    if "role" not in session or session["role"] != "student":
        return redirect("/")

    if session["user"] != email:
        return redirect("/")

    return render_template("dashboard.html", email=email)


# ---------------- SUBMIT COMPLAINT ----------------

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():
    conn = get_db()
    cursor = conn.cursor()

    email = request.form["email"]
    category = request.form["category"]
    description = request.form["description"]

    file = request.files.get("image")

    filename = ""
    if file and file.filename != "":
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    cursor.execute(
        "INSERT INTO complaints (student_email, category, description, image) VALUES (?, ?, ?, ?)",
        (email, category, description, filename)
    )

    conn.commit()
    conn.close()

    return "Complaint Submitted Successfully!"


# ---------------- VIEW COMPLAINTS ----------------

@app.route("/view_complaints/<email>")
def view_complaints(email):
    if "role" not in session or session["role"] != "student":
        return redirect("/")

    if session["user"] != email:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM complaints WHERE student_email=?", (email,))
    complaints = cursor.fetchall()

    conn.close()

    return render_template("view_complaints.html", complaints=complaints, email=email)


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_check", methods=["POST"])
def admin_login_check():
    conn = get_db()
    cursor = conn.cursor()

    email = request.form["email"]
    password = request.form["password"]

    cursor.execute("SELECT * FROM admin WHERE email=? AND password=?", (email, password))
    admin = cursor.fetchone()

    conn.close()

    if admin:
        session["user"] = email
        session["role"] = "admin"
        return redirect("/admin_dashboard")
    else:
        return "Invalid Admin Credentials"


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin_dashboard")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT complaints.*, students.room_number
        FROM complaints
        JOIN students ON complaints.student_email = students.email
    """)

    complaints = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html", complaints=complaints)


# ---------------- UPDATE COMPLAINT ----------------

@app.route("/update_complaint/<int:id>", methods=["POST"])
def update_complaint(id):
    conn = get_db()
    cursor = conn.cursor()

    worker = request.form["worker"]
    status = request.form["status"]

    cursor.execute(
        "UPDATE complaints SET assigned_worker=?, status=? WHERE id=?",
        (worker, status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")


# ---------------- DELETE COMPLAINT ----------------

@app.route("/delete_complaint/<int:id>/<email>")
def delete_complaint(id, email):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/view_complaints/" + email)


# ---------------- STAFF LOGIN ----------------

@app.route("/staff_login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM workers WHERE email=? AND password=?", (email, password))
        worker = cursor.fetchone()

        conn.close()

        if worker:
            session["user"] = email
            session["role"] = "staff"
            return redirect("/staff_dashboard/" + email)
        else:
            return "Invalid Credentials"

    return render_template("staff_login.html")


# ---------------- STAFF DASHBOARD ----------------

@app.route("/staff_dashboard/<email>")
def staff_dashboard(email):
    if "role" not in session or session["role"] != "staff":
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM workers WHERE email=?", (email,))
    worker = cursor.fetchone()

    if not worker:
        return "Worker not found"

    worker_name = worker["name"]

    cursor.execute("""
        SELECT complaints.*, students.room_number
        FROM complaints
        JOIN students ON complaints.student_email = students.email
        WHERE complaints.assigned_worker=?
    """, (worker_name,))

    complaints = cursor.fetchall()

    conn.close()

    return render_template("staff_dashboard.html",
                           complaints=complaints,
                           email=email,
                           worker_name=worker_name)


# ---------------- STAFF UPDATE ----------------

@app.route("/staff_update/<int:id>/<email>", methods=["POST"])
def staff_update(id, email):
    conn = get_db()
    cursor = conn.cursor()

    status = request.form["status"]

    cursor.execute("UPDATE complaints SET status=? WHERE id=?", (status, id))

    conn.commit()
    conn.close()

    return redirect("/staff_dashboard/" + email)


# ---------------- REVIEW ----------------

@app.route("/add_review/<int:id>/<email>", methods=["GET", "POST"])
def add_review(id, email):
    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        review = request.form["review"]

        cursor.execute("UPDATE complaints SET review=? WHERE id=?", (review, id))

        conn.commit()
        conn.close()

        return redirect("/view_complaints/" + email)

    return render_template("add_review.html", id=id, email=email)


# ---------------- FILES ----------------

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)