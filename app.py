from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Route for the login page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "0880":
            session['role'] = 'admin'
            return redirect(url_for("admin_panel"))
        elif username.isdigit() and len(username) == 5 and password == "0770":
            session['role'] = 'teacher'
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# Route for the Dashboard (main page)
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

# Route for Generate Timetable
@app.route("/generate")
def generate():
    return render_template("generate.html", active_page="generate")

# Route for Teacher View
@app.route("/teacher")
def teacher_view():
    return render_template("teacherView.html", active_page="teacher")

# Route for Admin Panel
@app.route("/admin")
def admin_panel():
    return render_template("adminPanel.html", active_page="admin")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
