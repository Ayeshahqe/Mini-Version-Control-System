from flask import Flask, render_template, session, redirect, url_for
from models.models import db, User
from routes import auth
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://root:{os.getenv('DB_PASSWORD')}@localhost/mvcs_db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

app.register_blueprint(auth)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    return render_template(
        "dashboard.html",
        user=user,
        projects=user.projects
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "error.html",
        code=404,
        message="The page or resource was not found."
    ), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()

    return render_template(
        "error.html",
        code=500,
        message="Something went wrong on the server."
    ), 500


if __name__ == "__main__":
    app.run(debug=True)
