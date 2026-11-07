import os
import shutil

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from models.models import db, User, Project, File, Version, Activity

auth = Blueprint("auth", __name__)


def log_activity(action, description):
    db.session.add(Activity(
        user_id=session["user_id"],
        action=action,
        description=description,
    ))
    db.session.commit()


@auth.route("/create-project", methods=["GET", "POST"])
def create_project():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form["name"]

        project = Project(name=name, user_id=session["user_id"])
        db.session.add(project)
        db.session.commit()

        log_activity("Project", f'Created project "{name}"')
        flash("Project created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("create_project.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))

        user = User(name=name, email=email,
                    password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))


@auth.route("/project/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    project = Project.query.get_or_404(project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    project_name = project.name

    # Delete versions, then files, then the project
    for file_record in project.files:
        Version.query.filter_by(file_id=file_record.id).delete()
        db.session.delete(file_record)

    db.session.delete(project)
    db.session.commit()

    log_activity("Delete", f'Deleted project "{project_name}"')

    # Delete stored files from disk
    folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "uploads",
        str(project_id),
    )
    shutil.rmtree(folder, ignore_errors=True)

    flash(f'Project "{project_name}" deleted.', "success")
    return redirect(url_for("dashboard"))
