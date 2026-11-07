import os
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, url_for, flash, request
from models.models import db, User
from routes import auth
from file_routes.file_management import file_bp
from file_routes.version import version_bp
from file_routes.nav import nav_bp, get_user_stats

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://root:{os.getenv('DB_PASSWORD')}@localhost/mvcs_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024
db.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(file_bp)
app.register_blueprint(version_bp)
app.register_blueprint(nav_bp)

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
        projects=user.projects,
        stats=get_user_stats(user.id)
    )


@app.errorhandler(403)
def forbidden(error):
    return render_template(
        "error.html",
        code=403,
        message="Access denied. This item does not belong to you."
    ), 403


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


@app.errorhandler(413)
def file_too_large(error):
    flash("File is too large. The maximum upload size is 100 KB.", "error")
    return redirect(request.referrer or url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
