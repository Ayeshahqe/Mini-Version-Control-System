from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

from models.models import db, User, Project, File, Version

auth = Blueprint("auth", __name__)


@auth.route("/create-project", methods=["GET", "POST"])
def create_project():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form["name"]

        project = Project(
            name=name,
            user_id=session["user_id"]
        )

        db.session.add(project)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("create_project.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered"

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password
        )

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

        return "Invalid email or password"

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))


@auth.route("/project/<int:project_id>")
def project(project_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    project = Project.query.get_or_404(project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    return render_template(
        "project.html",
        project=project
    )


@auth.route("/project/<int:project_id>/upload", methods=["GET", "POST"])
def upload_file(project_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    project = Project.query.get_or_404(project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    if request.method == "POST":
        uploaded_file = request.files["file"]

        if uploaded_file.filename == "":
            return "No file selected"

        filename = secure_filename(uploaded_file.filename)

        existing_file = File.query.filter_by(
            filename=filename,
            project_id=project.id
        ).first()

        if existing_file:
            return "File already exists. Use the file's version page to upload a new version."

        file_record = File(
            filename=filename,
            project_id=project.id
        )

        db.session.add(file_record)
        db.session.commit()

        version_number = 1

        folder = os.path.join(
            "uploads",
            str(project.id),
            str(file_record.id)
        )

        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(
            folder,
            f"version_{version_number}_{filename}"
        )

        uploaded_file.save(file_path)

        version = Version(
            version_number=version_number,
            file_path=file_path,
            file_id=file_record.id
        )

        db.session.add(version)
        db.session.commit()

        return redirect(
            url_for("auth.project", project_id=project.id)
        )

    return render_template(
        "upload.html",
        project=project
    )


@auth.route("/file/<int:file_id>/new-version", methods=["GET", "POST"])
def new_version(file_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    file_record = File.query.get_or_404(file_id)

    project = Project.query.get_or_404(file_record.project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    if request.method == "POST":
        uploaded_file = request.files["file"]

        if uploaded_file.filename == "":
            return "No file selected"

        filename = secure_filename(uploaded_file.filename)

        if filename != file_record.filename:
            return "Please upload the same file type and name for a new version."

        # Find the latest version
        latest_version = (
            Version.query
            .filter_by(file_id=file_record.id)
            .order_by(Version.version_number.desc())
            .first()
        )

        if latest_version:
            next_version = latest_version.version_number + 1
        else:
            next_version = 1

        folder = os.path.join(
            "uploads",
            str(project.id),
            str(file_record.id)
        )

        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(
            folder,
            f"version_{next_version}_{filename}"
        )

        uploaded_file.save(file_path)

        version = Version(
            version_number=next_version,
            file_path=file_path,
            file_id=file_record.id
        )

        db.session.add(version)
        db.session.commit()

        return redirect(
            url_for("auth.file_history", file_id=file_record.id)
        )

    return render_template(
        "new_version.html",
        file=file_record,
        project=project
    )


@auth.route("/file/<int:file_id>/history")
def file_history(file_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    file_record = File.query.get_or_404(file_id)

    project = Project.query.get_or_404(file_record.project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    versions = (
        Version.query
        .filter_by(file_id=file_record.id)
        .order_by(Version.version_number.desc())
        .all()
    )

    return render_template(
        "file_history.html",
        file=file_record,
        project=project,
        versions=versions
    )


@auth.route("/version/<int:version_id>/download")
def download_version(version_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    version = Version.query.get_or_404(version_id)
    file_record = File.query.get_or_404(version.file_id)
    project = Project.query.get_or_404(file_record.project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    if not os.path.exists(version.file_path):
        return "File not found", 404

    return send_file(
        version.file_path,
        as_attachment=True,
        download_name=os.path.basename(version.file_path)
    )


@auth.route("/version/<int:version_id>/restore", methods=["POST"])
def restore_version(version_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    old_version = Version.query.get_or_404(version_id)
    file_record = File.query.get_or_404(old_version.file_id)
    project = Project.query.get_or_404(file_record.project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    if not os.path.exists(old_version.file_path):
        return "File not found", 404

    latest_version = (
        Version.query
        .filter_by(file_id=file_record.id)
        .order_by(Version.version_number.desc())
        .first()
    )

    next_version = latest_version.version_number + 1

    folder = os.path.join(
        "uploads",
        str(project.id),
        str(file_record.id)
    )

    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(
        folder,
        f"version_{next_version}_{file_record.filename}"
    )

    with open(old_version.file_path, "rb") as source:
        with open(file_path, "wb") as destination:
            destination.write(source.read())

    restored_version = Version(
        version_number=next_version,
        file_path=file_path,
        file_id=file_record.id
    )

    db.session.add(restored_version)
    db.session.commit()

    return redirect(
        url_for("auth.file_history", file_id=file_record.id)
    )
