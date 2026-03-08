import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, send_from_directory
import mysql.connector

app = Flask(__name__)
app.secret_key = "super_secret_key_123"
app.config["UPLOAD_FOLDER"] = "uploads"

# ---------------- DATABASE CONNECTION ----------------

DB_AVAILABLE = True

try:
    db = mysql.connector.connect(
        host="mainline.proxy.rlwy.net",
        user="root",
        password="YOUR_RAILWAY_PASSWORD",
        database="railway",
        port=35231
    )

    cursor = db.cursor()

except Exception as e:
    print("DATABASE CONNECTION FAILED:", e)
    db = None
    cursor = None
    DB_AVAILABLE = False


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

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    try:
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        room = request.form["room"]

        cursor.execute("SELECT MAX(id) FROM students")
        result = cursor.fetchone()
        next_id = 1 if result[0] is None else result[0] + 1

        query = "INSERT INTO students (id, name, email, password, room_number) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(query, (next_id, name, email, password, room))
        db.commit()

        return "Registration Successful!"

    except Exception as e:
        return str(e)


# ---------------- LOGIN ----------------

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login_user", methods=["POST"])
def login_user():

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    email = request.form["email"]
    password = request.form["password"]

    query = "SELECT * FROM students WHERE email=%s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user[3], password):
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

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    try:
        email = request.form["email"]
        category = request.form["category"]
        description = request.form["description"]

        file = request.files.get("image")

        filename = ""
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        cursor.execute("SELECT MAX(id) FROM complaints")
        result = cursor.fetchone()
        next_id = 1 if result[0] is None else result[0] + 1

        query = """
        INSERT INTO complaints (id, student_email, category, description, image)
        VALUES (%s,%s,%s,%s,%s)
        """

        cursor.execute(query, (next_id, email, category, description, filename))
        db.commit()

        return "Complaint Submitted Successfully!"

    except Exception as e:
        return str(e)


# ---------------- VIEW COMPLAINTS ----------------

@app.route("/view_complaints/<email>")
def view_complaints(email):

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    if session["user"] != email:
        return redirect("/")

    query = "SELECT * FROM complaints WHERE student_email=%s"
    cursor.execute(query, (email,))
    complaints = cursor.fetchall()

    return render_template("view_complaints.html", complaints=complaints, email=email)


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_check", methods=["POST"])
def admin_login_check():

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    email = request.form["email"]
    password = request.form["password"]

    query = "SELECT * FROM admin WHERE email=%s AND password=%s"
    cursor.execute(query, (email, password))
    admin = cursor.fetchone()

    if admin:
        session["user"] = email
        session["role"] = "admin"
        return redirect("/admin_dashboard")
    else:
        return "Invalid Admin Credentials"


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin_dashboard")
def admin_dashboard():

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    query = """
    SELECT complaints.*, students.room_number
    FROM complaints
    JOIN students ON complaints.student_email = students.email
    """

    cursor.execute(query)
    complaints = cursor.fetchall()

    return render_template("admin_dashboard.html", complaints=complaints)


# ---------------- UPDATE COMPLAINT ----------------

@app.route("/update_complaint/<int:id>", methods=["POST"])
def update_complaint(id):

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    worker = request.form["worker"]
    status = request.form["status"]

    query = "UPDATE complaints SET assigned_worker=%s, status=%s WHERE id=%s"
    cursor.execute(query, (worker, status, id))
    db.commit()

    return redirect("/admin_dashboard")


# ---------------- UPLOADS ----------------

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ---------------- DELETE COMPLAINT ----------------

@app.route("/delete_complaint/<int:id>/<email>")
def delete_complaint(id, email):

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    query = "DELETE FROM complaints WHERE id=%s"
    cursor.execute(query, (id,))
    db.commit()

    return redirect("/view_complaints/" + email)


# ---------------- STAFF LOGIN ----------------

@app.route("/staff_login", methods=["GET", "POST"])
def staff_login():

    if request.method == "POST":

        if not DB_AVAILABLE:
            return "Database not available in hosted demo."

        email = request.form["email"]
        password = request.form["password"]

        query = "SELECT * FROM workers WHERE email=%s AND password=%s"
        cursor.execute(query, (email, password))
        worker = cursor.fetchone()

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

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    if "role" not in session or session["role"] != "staff":
        return redirect("/")

    query = "SELECT name FROM workers WHERE email=%s"
    cursor.execute(query, (email,))
    worker = cursor.fetchone()

    if not worker:
        return "Worker not found"

    worker_name = worker[0]

    query = """
    SELECT complaints.*, students.room_number
    FROM complaints
    JOIN students ON complaints.student_email = students.email
    WHERE complaints.assigned_worker=%s
    """

    cursor.execute(query, (worker_name,))
    complaints = cursor.fetchall()

    return render_template(
        "staff_dashboard.html",
        complaints=complaints,
        email=email,
        worker_name=worker_name
    )


# ---------------- STAFF UPDATE ----------------

@app.route("/staff_update/<int:id>/<email>", methods=["POST"])
def staff_update(id, email):

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    status = request.form["status"]

    query = "UPDATE complaints SET status=%s WHERE id=%s"
    cursor.execute(query, (status, id))
    db.commit()

    return redirect("/staff_dashboard/" + email)


# ---------------- REVIEW ----------------

@app.route("/add_review/<int:id>/<email>", methods=["GET", "POST"])
def add_review(id, email):

    if not DB_AVAILABLE:
        return "Database not available in hosted demo."

    if request.method == "POST":
        review = request.form["review"]

        query = "UPDATE complaints SET review=%s WHERE id=%s"
        cursor.execute(query, (review, id))
        db.commit()

        return redirect("/view_complaints/" + email)

    return render_template("add_review.html", id=id, email=email)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
