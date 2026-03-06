import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session
from flask import send_from_directory
import mysql.connector

app = Flask(__name__)
app.secret_key = "super_secret_key_123"
app.config["UPLOAD_FOLDER"] = "uploads"

# Database connection
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="hostel_db"
    )
    cursor = db.cursor()
except:
    db = None
    cursor = None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    name = request.form["name"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])
    room = request.form["room"]

    query = "INSERT INTO students (name, email, password, room_number) VALUES (%s, %s, %s, %s)"
    values = (name, email, password, room)

    cursor.execute(query, values)
    db.commit()

    return "Registration Successful!"

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/dashboard/<email>")
def dashboard(email):

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    if session["user"] != email:
        return redirect("/")

    return render_template("dashboard.html", email=email)
    
@app.route("/login_user", methods=["POST"])
def login_user():
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
    

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():
    print("FORM SUBMITTED")
    email = request.form["email"]
    category = request.form["category"]
    description = request.form["description"]

    file = request.files.get("image")

    filename = ""
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    query = """
    INSERT INTO complaints (student_email, category, description, image)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (email, category, description, filename))
    db.commit()

    return "Complaint Submitted Successfully!"    

@app.route("/view_complaints/<email>")
def view_complaints(email):

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    if session["user"] != email:
        return redirect("/")

    query = "SELECT * FROM complaints WHERE student_email=%s"
    cursor.execute(query, (email,))
    complaints = cursor.fetchall()

    return render_template("view_complaints.html", complaints=complaints, email=email)

@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")

@app.route("/admin_login_check", methods=["POST"])
def admin_login_check():
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

@app.route("/admin_dashboard")
def admin_dashboard():

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

@app.route("/update_complaint/<int:id>", methods=["POST"])
def update_complaint(id):
    worker = request.form["worker"]
    status = request.form["status"]

    query = "UPDATE complaints SET assigned_worker=%s, status=%s WHERE id=%s"
    cursor.execute(query, (worker, status, id))
    db.commit()

    return redirect("/admin_dashboard")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/delete_complaint/<int:id>/<email>")
def delete_complaint(id, email):
    query = "DELETE FROM complaints WHERE id=%s"
    cursor.execute(query, (id,))
    db.commit()

    return redirect("/view_complaints/" + email)

@app.route("/staff_login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
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

@app.route("/staff_dashboard/<email>")
def staff_dashboard(email):

    if "role" not in session or session["role"] != "staff":
        return redirect("/")

    # Get worker name
    query = "SELECT name FROM workers WHERE email=%s"
    cursor.execute(query, (email,))
    worker = cursor.fetchone()

    if not worker:
        return "Worker not found"

    worker_name = worker[0]

    # JOIN QUERY (Important)
    query = """
    SELECT complaints.*, students.room_number
    FROM complaints
    JOIN students ON complaints.student_email = students.email
    WHERE complaints.assigned_worker=%s
    """

    cursor.execute(query, (worker_name,))
    complaints = cursor.fetchall()

    return render_template("staff_dashboard.html",
                           complaints=complaints,
                           email=email,
                           worker_name=worker_name)

@app.route("/staff_update/<int:id>/<email>", methods=["POST"])
def staff_update(id, email):

    status = request.form["status"]

    query = "UPDATE complaints SET status=%s WHERE id=%s"
    cursor.execute(query, (status, id))
    db.commit()

    return redirect("/staff_dashboard/" + email)

@app.route("/add_review/<int:id>/<email>", methods=["GET", "POST"])
def add_review(id, email):

    if request.method == "POST":
        review = request.form["review"]

        query = "UPDATE complaints SET review=%s WHERE id=%s"
        cursor.execute(query, (review, id))
        db.commit()

        return redirect("/view_complaints/" + email)

    return render_template("add_review.html", id=id, email=email)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":

    app.run(debug=True)
