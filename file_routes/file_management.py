import os

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    send_from_directory,
    session,
    url_for,
)

from models.models import db, Project, File, Version
from routes import log_activity

file_bp = Blueprint("files", __name__, url_prefix="/projects")


def get_owned_project(project_id):
    project = db.session.get(Project, project_id)

    if project is None:
        abort(404)

    if project.user_id != session["user_id"]:
        abort(403)

    return project


def get_version_folder(project_id, file_id):
    return os.path.join(
        current_app.root_path,
        "uploads",
        str(project_id),
        str(file_id),
    )


@file_bp.route("/<int:project_id>/files/<int:file_id>/download")
def download_file(project_id, file_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    project = get_owned_project(project_id)

    file_record = File.query.filter_by(
        id=file_id,
        project_id=project.id,
    ).first_or_404()

    latest_version = (
        Version.query
        .filter_by(file_id=file_record.id)
        .order_by(Version.version_number.desc())
        .first()
    )

    if latest_version is None:
        abort(404)

    full_path = os.path.join(current_app.root_path, latest_version.file_path)

    if not os.path.isfile(full_path):
        flash("The stored file could not be found.", "error")
        return redirect(url_for("auth.project", project_id=project.id))

    return send_from_directory(
        os.path.dirname(full_path),
        os.path.basename(full_path),
        as_attachment=True,
        download_name=file_record.filename,
    )


@file_bp.route("/<int:project_id>/files/<int:file_id>/delete", methods=["POST"])
def delete_file(project_id, file_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    project = get_owned_project(project_id)

    file_record = File.query.filter_by(
        id=file_id,
        project_id=project.id,
    ).first_or_404()

    filename = file_record.filename
    versions = Version.query.filter_by(file_id=file_record.id).all()

    version_paths = [
        os.path.join(current_app.root_path, version.file_path)
        for version in versions
        if version.file_path
    ]

    folder = get_version_folder(project.id, file_record.id)

    try:
        for version in versions:
            db.session.delete(version)

        db.session.delete(file_record)
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash("Could not delete the file. Please try again.", "error")
        return redirect(url_for("auth.project", project_id=project.id))

    log_activity("Delete", f'Deleted file "{filename}" from "{project.name}"')

    for path in version_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            current_app.logger.warning("Could not remove %s", path)

    try:
        if os.path.isdir(folder) and not os.listdir(folder):
            os.rmdir(folder)
    except OSError:
        pass

    flash(f'"{filename}" and its version history were deleted.', "success")
    return redirect(url_for("auth.project", project_id=project.id))
