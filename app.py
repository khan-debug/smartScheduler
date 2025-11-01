from flask import Flask, render_template

app = Flask(__name__)

# Route for the Dashboard (main page)
@app.route("/")
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
