import io
import os
import shutil
import zipfile

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, send_file)
from werkzeug.utils import secure_filename

from models.models import db, Project, File, Version
from file_routes.version import (login_required, get_upload_root, resolve_path,
                                 get_owned_project_for_files, log_activity,
                                 check_upload, create_version)

file_bp = Blueprint("file", __name__)

ALLOWED_EXTENSIONS = {
    "txt", "md", "py", "java", "c", "cpp", "h",
    "js", "html", "css", "json", "csv", "sql",
    "xml", "pdf", "docx", "pptx", "xlsx",
    "png", "jpg", "jpeg", "gif", "zip",
}


def allowed_file(filename):
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_owned_project(project_id):
    return get_owned_project_for_files(project_id)


def get_owned_file(file_id):
    file = File.query.get_or_404(file_id)
    get_owned_project(file.project_id)
    return file


def latest_of(file_id):
    return (Version.query.filter_by(file_id=file_id)
            .order_by(Version.version_number.desc()).first())


# ---------- Routes ----------

@file_bp.route("/projects/<int:project_id>/files")
@login_required
def list_files(project_id):
    project = get_owned_project(project_id)
    files = File.query.filter_by(
        project_id=project.id).order_by(File.filename).all()
    rows = [{"file": f, "latest": latest_of(f.id)} for f in files]
    return render_template("files/files.html", project=project, rows=rows)


@file_bp.route("/projects/<int:project_id>/upload", methods=["GET", "POST"])
@login_required
def upload_file(project_id):
    project = get_owned_project(project_id)

    if request.method == "POST":
        uploaded = request.files.get("file")

        # 1. Valid upload (selected, not empty, max 20 KB)
        error = check_upload(uploaded)
        if error:
            flash(error, "error")
            return redirect(request.url)

        # 2. Clean the filename
        safe_name = secure_filename(uploaded.filename)
        if safe_name == "":
            flash("Invalid filename. Please rename the file and try again.", "error")
            return redirect(request.url)

        # 3. Allowed type
        if not allowed_file(safe_name):
            flash("This file type is not allowed.", "error")
            return redirect(request.url)

        # 4. Duplicate filename in this project
        if File.query.filter_by(project_id=project.id, filename=safe_name).first():
            flash("File already exists. Upload a new version from its history page.",
                  "error")
            return redirect(request.url)

        # 5. Create the File record, then Version 1
        new_file = File(filename=safe_name, project_id=project.id)
        db.session.add(new_file)
        db.session.commit()

        try:
            create_version(new_file, uploaded=uploaded)
        except Exception:
            db.session.rollback()
            db.session.delete(new_file)
            db.session.commit()
            flash("Could not save the file. Please try again.", "error")
            return redirect(request.url)

        log_activity("Upload", 'Uploaded "%s" (version 1) to "%s"'
                     % (safe_name, project.name))
        flash("'%s' uploaded successfully. Version 1 created." %
              safe_name, "success")
        return redirect(url_for("file.list_files", project_id=project.id))

    return render_template("files/upload.html", project=project)


@file_bp.route("/files/<int:file_id>/download")
@login_required
def download_file(file_id):
    file = get_owned_file(file_id)
    latest = latest_of(file.id)

    if latest is None or not os.path.exists(resolve_path(latest.file_path)):
        flash("The file is missing on the server.", "error")
        return redirect(url_for("file.list_files", project_id=file.project_id))

    return send_file(resolve_path(latest.file_path), as_attachment=True,
                     download_name=file.filename)


@file_bp.route("/files/<int:file_id>/delete", methods=["POST"])
@login_required
def delete_file(file_id):
    file = get_owned_file(file_id)
    project_id = file.project_id
    filename = file.filename

    version_folder = os.path.join(
        get_upload_root(), str(project_id), str(file.id))
    version_paths = [resolve_path(v.file_path)
                     for v in Version.query.filter_by(file_id=file.id).all()]

    try:
        Version.query.filter_by(file_id=file.id).delete()
        db.session.delete(file)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Could not delete the file. Please try again.", "error")
        return redirect(url_for("file.list_files", project_id=project_id))

    for path in version_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
    shutil.rmtree(version_folder, ignore_errors=True)

    log_activity("Delete", 'Deleted file "%s"' % filename)
    flash("File '%s' deleted." % filename, "success")
    return redirect(url_for("file.list_files", project_id=project_id))


@file_bp.route("/projects/<int:project_id>/download-zip")
@login_required
def download_project_zip(project_id):
    project = get_owned_project(project_id)
    files = File.query.filter_by(project_id=project.id).all()

    if not files:
        flash("This project has no files to download.", "error")
        return redirect(url_for("file.list_files", project_id=project.id))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            latest = latest_of(f.id)
            if latest is not None:
                path = resolve_path(latest.file_path)
                if os.path.exists(path):
                    zf.write(path, arcname=f.filename)
    buffer.seek(0)

    zip_name = (secure_filename(project.name) or "project") + ".zip"
    return send_file(buffer, as_attachment=True,
                     download_name=zip_name, mimetype="application/zip")
