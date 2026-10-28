# the routes of the application, including user authentication, project management, file uploads, version control, and activity logging.
# It defines the endpoints for creating projects, uploading files, managing versions, comparing versions, downloading files,
# restoring versions, deleting projects, and tagging versions.

import difflib  # import for comparing text files and generating unified diffs
import os
import shutil
import hashlib

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, send_file, abort, flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models.models import db, User, Project, File, Version, Activity

MAX_FILE_SIZE = 200 * 1024

ALLOWED_EXTENSIONS = {
    "txt", "md", "py", "java", "c", "cpp", "h",
    "js", "html", "css", "json", "csv", "sql",
    "xml", "pdf", "docx", "pptx", "xlsx",
    "png", "jpg", "jpeg", "gif", "zip",
}

auth = Blueprint("auth", __name__)


def log_activity(action, description):  # Log an activity in the database
    db.session.add(Activity(
        user_id=session["user_id"],
        action=action,
        description=description,
    ))
    db.session.commit()


def get_file_hash(path):    # Calculate the SHA-256 hash of a file at the given path
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


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

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))

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

        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

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

    project_versions = (
        Version.query
        .join(File, Version.file_id == File.id)
        .filter(File.project_id == project.id)
    )

    recent_versions = (
        project_versions
        .order_by(Version.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "project.html",
        project=project,
        recent_versions=recent_versions,
        total_versions=project_versions.count(),
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
            flash("No file selected.", "error")
            return redirect(url_for("auth.upload_file", project_id=project.id))

        filename = secure_filename(uploaded_file.filename)

        extension = filename.rsplit(
            ".", 1)[-1].lower() if "." in filename else ""

        if extension not in ALLOWED_EXTENSIONS:
            flash("This file type is not allowed.", "error")
            return redirect(url_for("auth.upload_file", project_id=project.id))

        uploaded_file.seek(0, os.SEEK_END)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)

        if file_size == 0:
            flash("Empty files cannot be uploaded.", "error")
            return redirect(url_for("auth.upload_file", project_id=project.id))

        if file_size > MAX_FILE_SIZE:
            flash("Maximum upload size is 200 KB.", "error")
            return redirect(url_for("auth.upload_file", project_id=project.id))

        existing_file = File.query.filter_by(
            filename=filename,
            project_id=project.id
        ).first()

        if existing_file:
            flash(
                "File already exists. Upload a new version from its history page.", "error")
            return redirect(url_for("auth.upload_file", project_id=project.id))

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
        file_hash = get_file_hash(file_path)

        version = Version(
            version_number=version_number,
            file_path=file_path,
            file_hash=file_hash,
            file_id=file_record.id
        )

        db.session.add(version)
        db.session.commit()

        log_activity(
            "Upload", f'Uploaded "{filename}" (version 1) to "{project.name}"')

        flash(f'"{filename}" uploaded successfully. Version 1 created.', "success")

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
            flash("No file selected.", "error")
            return redirect(url_for("auth.new_version", file_id=file_record.id))

        filename = secure_filename(uploaded_file.filename)

        if filename != file_record.filename:
            flash("The file name must match the original file.", "error")
            return redirect(url_for("auth.new_version", file_id=file_record.id))

        uploaded_file.seek(0, os.SEEK_END)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)

        if file_size == 0:
            flash("Empty files cannot be uploaded.", "error")
            return redirect(url_for("auth.new_version", file_id=file_record.id))

        if file_size > MAX_FILE_SIZE:
            flash("Maximum upload size is 200 KB.", "error")
            return redirect(url_for("auth.new_version", file_id=file_record.id))

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

        file_hash = get_file_hash(file_path)

        if latest_version and latest_version.file_hash == file_hash:
            os.remove(file_path)
            flash(
                f"No changes found. This file is identical to version {latest_version.version_number}.", "error")
            return redirect(url_for("auth.new_version", file_id=file_record.id))

        version = Version(
            version_number=next_version,
            file_path=file_path,
            file_hash=file_hash,
            file_id=file_record.id
        )

        db.session.add(version)
        db.session.commit()

        log_activity(
            "Upload", f'Uploaded version {next_version} of "{file_record.filename}"')

        flash(f"Version {next_version} uploaded successfully.", "success")

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


@auth.route("/file/<int:file_id>/compare")
def compare_versions(file_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    file_record = File.query.get_or_404(file_id)

    project = Project.query.get_or_404(file_record.project_id)

    if project.user_id != session["user_id"]:
        abort(403)

    versions = (
        Version.query
        .filter_by(file_id=file_record.id)
        .order_by(Version.version_number.asc())
        .all()
    )

    if len(versions) < 2:
        flash("Upload at least two versions before comparing.", "error")
        return redirect(url_for("auth.file_history", file_id=file_record.id))

    first_id = request.args.get("first", type=int)
    second_id = request.args.get("second", type=int)

    first_version = None
    second_version = None
    differences = None
    error_message = None

    if first_id is not None and second_id is not None:

        first_version = next(
            (v for v in versions if v.id == first_id),
            None,
        )

        second_version = next(
            (v for v in versions if v.id == second_id),
            None,
        )

        if first_version is None or second_version is None:
            abort(404)

        if first_version.id == second_version.id:
            error_message = "Please select two different versions."

        else:
            first_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                first_version.file_path,
            )

            second_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                second_version.file_path,
            )

            if not os.path.isfile(first_path) or not os.path.isfile(second_path):
                error_message = "One or both version files could not be found."

            else:
                try:
                    with open(first_path, "r", encoding="utf-8") as f:
                        first_lines = f.read().splitlines()

                    with open(second_path, "r", encoding="utf-8") as f:
                        second_lines = f.read().splitlines()

                    diff_lines = list(
                        difflib.unified_diff(
                            first_lines,
                            second_lines,
                            fromfile=f"Version {first_version.version_number}",
                            tofile=f"Version {second_version.version_number}",
                            lineterm="",
                        )
                    )

                    differences = []
                    for i, line in enumerate(diff_lines):
                        if i < 2:
                            kind = "header"
                        elif line.startswith("@@"):
                            kind = "hunk"
                        elif line.startswith("+"):
                            kind = "added"
                        elif line.startswith("-"):
                            kind = "removed"
                        else:
                            kind = "context"

                        differences.append({"kind": kind, "text": line})

                except UnicodeDecodeError:
                    error_message = (
                        "Text comparison is available only for text files."
                    )

    return render_template(
        "compare_versions.html",
        file=file_record,
        project=project,
        versions=versions,
        first_version=first_version,
        second_version=second_version,
        differences=differences,
        error_message=error_message,
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
        file_hash=get_file_hash(file_path),
        file_id=file_record.id
    )

    db.session.add(restored_version)
    db.session.commit()

    log_activity(
        "Restore", f'Restored version {old_version.version_number} of "{file_record.filename}" as version {next_version}')

    flash(
        f"Version {old_version.version_number} restored as version {next_version}.", "success")

    return redirect(
        url_for("auth.file_history", file_id=file_record.id)
    )


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


@auth.route("/version/<int:version_id>/tag", methods=["POST"])
def tag_version(version_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    version = Version.query.get_or_404(version_id)
    file_record = File.query.get_or_404(version.file_id)
    project = Project.query.get_or_404(file_record.project_id)

    if project.user_id != session["user_id"]:
        return "Access denied", 403

    tag = request.form.get("tag", "").strip()

    if tag:
        duplicate = Version.query.filter(
            Version.file_id == file_record.id,
            Version.tag == tag,
            Version.id != version.id,
        ).first()

        if duplicate:
            flash(
                f'Tag "{tag}" is already used on version {duplicate.version_number}.', "error")
            return redirect(url_for("auth.file_history", file_id=file_record.id))

    version.tag = tag or None
    db.session.commit()

    if tag:
        log_activity(
            "Tag", f'Tagged version {version.version_number} of "{file_record.filename}" as "{tag}"')

    flash("Tag saved." if tag else "Tag removed.", "success")
    return redirect(url_for("auth.file_history", file_id=file_record.id))
