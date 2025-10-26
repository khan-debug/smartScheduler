from flask import Flask, render_template, send_from_directory

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/<path:path>")
def send_static(path):
    if ".html" in path:
        return send_from_directory("templates", path)
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(debug=True)
