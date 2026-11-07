import os
import shutil
import hashlib
import difflib
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, abort, send_file, current_app)
from sqlalchemy import func
from werkzeug.utils import secure_filename

from models.models import db, File, Project, Version, Activity

version_bp = Blueprint("version", __name__)

TEXT_EXTENSIONS = {"txt", "py", "java", "c", "cpp", "h", "html", "css", "js",
                   "json", "md", "csv", "sql", "xml"}
MAX_VIEW_BYTES = 200000          # limit for viewing / comparing
MAX_FILE_SIZE = 100 * 1024       # 100 KB upload limit


class DuplicateVersionError(Exception):
    """Raised when the new content is identical to the latest version."""
    pass


# ---------- Helper functions ----------

def login_required(view):
    """Redirect to login if the user is not logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def log_activity(action, description):
    """Save one line in the Activity table (shown on the dashboard)."""
    db.session.add(Activity(user_id=session["user_id"],
                            action=action, description=description))
    db.session.commit()


def check_upload(uploaded):
    """Return an error message if the upload is not valid, else None."""
    if uploaded is None or uploaded.filename == "":
        return "Please choose a file."
    uploaded.seek(0, os.SEEK_END)
    size = uploaded.tell()
    uploaded.seek(0)
    if size == 0:
        return "Empty files cannot be uploaded."
    if size > MAX_FILE_SIZE:
        return "Maximum upload size is 100 KB."
    return None


def get_upload_root():
    folder = current_app.config.get(
        "UPLOAD_FOLDER", os.path.join(current_app.root_path, "uploads"))
    return os.path.abspath(folder)


def get_owned_file(file_id):
    file = File.query.get_or_404(file_id)
    project = Project.query.get_or_404(file.project_id)
    if project.user_id != session["user_id"]:
        abort(403)
    return file


def get_owned_project_for_files(project_id):
    """Return the Project only if it belongs to the logged-in user, else 403."""
    project = Project.query.get_or_404(project_id)
    if project.user_id != session["user_id"]:
        abort(403)
    return project


def get_owned_version(version_id):
    version = Version.query.get_or_404(version_id)
    file = get_owned_file(version.file_id)
    return version, file


def get_next_version_number(file_id):
    latest = (db.session.query(func.max(Version.version_number))
              .filter(Version.file_id == file_id).scalar())
    if latest is None:
        return 1
    return latest + 1


def resolve_path(file_path):
    """Turn the path saved in the database into a real path on disk."""
    if os.path.isabs(file_path):
        return file_path
    path = os.path.join(get_upload_root(), file_path)
    if os.path.exists(path):
        return path
    return os.path.join(current_app.root_path, file_path)


def file_hash(path):
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def is_text_file(filename):
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in TEXT_EXTENSIONS


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def create_version(file, uploaded=None, copy_from=None):
    """
    Save a NEW version for a file. Never overwrites an old one.
    Raises DuplicateVersionError if the content equals the latest version.
    """
    number = get_next_version_number(file.id)
    safe_name = secure_filename(file.filename) or "file"

    # uploads/<project_id>/<file_id>/version_<n>_<filename>
    relative_path = os.path.join(str(file.project_id), str(file.id),
                                 "version_%d_%s" % (number, safe_name))
    full_path = os.path.join(get_upload_root(), relative_path)

    if os.path.exists(full_path):
        raise FileExistsError("Version file already exists on disk")

    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    if uploaded is not None:
        uploaded.save(full_path)
    else:
        shutil.copyfile(copy_from, full_path)

    # Hash check: compare with the latest version
    new_hash = file_hash(full_path)
    latest = (Version.query.filter_by(file_id=file.id)
              .order_by(Version.version_number.desc()).first())
    if latest is not None:
        latest_path = resolve_path(latest.file_path)
        if latest.file_hash:
            same = (latest.file_hash == new_hash)
        else:
            same = os.path.exists(latest_path) and file_hash(
                latest_path) == new_hash
        if same:
            os.remove(full_path)
            raise DuplicateVersionError("Same content as the latest version")

    new_version = Version(version_number=number,
                          file_path=relative_path,
                          file_hash=new_hash,
                          created_at=datetime.now(),
                          file_id=file.id)
    db.session.add(new_version)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        os.remove(full_path)
        raise
    return new_version


# ---------- Routes ----------

@version_bp.route("/files/<int:file_id>/versions")
@login_required
def history(file_id):
    file = get_owned_file(file_id)
    versions = (Version.query.filter_by(file_id=file.id)
                .order_by(Version.version_number.desc()).all())
    return render_template("versions/history.html", file=file,
                           versions=versions, can_view=is_text_file(file.filename))


@version_bp.route("/files/<int:file_id>/versions/upload", methods=["GET", "POST"])
@login_required
def upload_version(file_id):
    file = get_owned_file(file_id)

    if request.method == "POST":
        uploaded = request.files.get("file")

        error = check_upload(uploaded)
        if error:
            flash(error, "error")
            return redirect(request.url)

        try:
            new_version = create_version(file, uploaded=uploaded)
        except DuplicateVersionError:
            flash(
                "No changes found. The file is identical to the latest version.", "error")
            return redirect(request.url)
        except Exception:
            flash("Could not save the new version. Please try again.", "error")
            return redirect(request.url)

        log_activity("Upload", 'Uploaded version %d of "%s"'
                     % (new_version.version_number, file.filename))
        flash("Version %d uploaded successfully." % new_version.version_number,
              "success")
        return redirect(url_for("version.history", file_id=file.id))

    return render_template("versions/upload_version.html", file=file)


@version_bp.route("/versions/<int:version_id>/download")
@login_required
def download_version(version_id):
    version, file = get_owned_version(version_id)
    path = resolve_path(version.file_path)

    if not os.path.exists(path):
        flash("The file for this version is missing on the server.", "error")
        return redirect(url_for("version.history", file_id=file.id))

    return send_file(path, as_attachment=True, download_name=file.filename)


@version_bp.route("/versions/<int:version_id>/restore", methods=["POST"])
@login_required
def restore_version(version_id):
    version, file = get_owned_version(version_id)
    old_path = resolve_path(version.file_path)

    if not os.path.exists(old_path):
        flash("Cannot restore: the old version file is missing.", "error")
        return redirect(url_for("version.history", file_id=file.id))

    try:
        new_version = create_version(file, copy_from=old_path)
    except DuplicateVersionError:
        flash(
            "Nothing to restore: this version is identical to the latest version.", "error")
        return redirect(url_for("version.history", file_id=file.id))
    except Exception:
        flash("Could not restore the version. Please try again.", "error")
        return redirect(url_for("version.history", file_id=file.id))

    log_activity("Restore", 'Restored version %d of "%s" as version %d'
                 % (version.version_number, file.filename,
                    new_version.version_number))
    flash("Version %d restored as Version %d."
          % (version.version_number, new_version.version_number), "success")
    return redirect(url_for("version.history", file_id=file.id))


@version_bp.route("/versions/<int:version_id>/tag", methods=["POST"])
@login_required
def tag_version(version_id):
    version, file = get_owned_version(version_id)
    tag = request.form.get("tag", "").strip()[:30]

    if tag:
        duplicate = Version.query.filter(
            Version.file_id == file.id,
            Version.tag == tag,
            Version.id != version.id).first()
        if duplicate:
            flash('Tag "%s" is already used on version %d.'
                  % (tag, duplicate.version_number), "error")
            return redirect(url_for("version.history", file_id=file.id))

    version.tag = tag or None
    db.session.commit()

    if tag:
        log_activity("Tag", 'Tagged version %d of "%s" as "%s"'
                     % (version.version_number, file.filename, tag))
    flash("Tag saved." if tag else "Tag removed.", "success")
    return redirect(url_for("version.history", file_id=file.id))


@version_bp.route("/versions/<int:version_id>/view")
@login_required
def view_version(version_id):
    version, file = get_owned_version(version_id)
    history_url = url_for("version.history", file_id=file.id)

    if not is_text_file(file.filename):
        flash(
            "This file type cannot be viewed in the browser. Please download it.", "error")
        return redirect(history_url)

    path = resolve_path(version.file_path)
    if not os.path.exists(path):
        flash("The file for this version is missing on the server.", "error")
        return redirect(history_url)

    if os.path.getsize(path) > MAX_VIEW_BYTES:
        flash("This file is too large to view. Please download it.", "error")
        return redirect(history_url)

    return render_template("versions/view.html", file=file,
                           version=version, content=read_text(path))


@version_bp.route("/files/<int:file_id>/diff")
@login_required
def diff(file_id):
    file = get_owned_file(file_id)
    history_url = url_for("version.history", file_id=file.id)

    old_no = request.args.get("v1", type=int)
    new_no = request.args.get("v2", type=int)

    if old_no is None or new_no is None:
        flash("Please choose two versions to compare.", "error")
        return redirect(history_url)
    if old_no == new_no:
        flash("Please choose two different versions.", "error")
        return redirect(history_url)
    if old_no > new_no:
        old_no, new_no = new_no, old_no

    if not is_text_file(file.filename):
        flash("Only text and code files can be compared.", "error")
        return redirect(history_url)

    old_v = Version.query.filter_by(file_id=file.id,
                                    version_number=old_no).first_or_404()
    new_v = Version.query.filter_by(file_id=file.id,
                                    version_number=new_no).first_or_404()

    old_path = resolve_path(old_v.file_path)
    new_path = resolve_path(new_v.file_path)
    if not os.path.exists(old_path) or not os.path.exists(new_path):
        flash("One of the version files is missing on the server.", "error")
        return redirect(history_url)

    if (os.path.getsize(old_path) > MAX_VIEW_BYTES or
            os.path.getsize(new_path) > MAX_VIEW_BYTES):
        flash("These files are too large to compare.", "error")
        return redirect(history_url)

    old_lines = read_text(old_path).splitlines()
    new_lines = read_text(new_path).splitlines()

    # Each row: (css_class, old_line_no, new_line_no, sign, text)
    diff_lines = []
    added = 0
    removed = 0
    old_n = 0
    new_n = 0
    raw = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
    for line in raw[2:]:
        if line.startswith("@@"):
            parts = line.split()
            old_n = int(parts[1][1:].split(",")[0])
            new_n = int(parts[2][1:].split(",")[0])
            diff_lines.append(("diff-hunk", "", "", "", line))
        elif line.startswith("+"):
            diff_lines.append(("diff-add", "", new_n, "+", line[1:]))
            new_n += 1
            added += 1
        elif line.startswith("-"):
            diff_lines.append(("diff-del", old_n, "", "-", line[1:]))
            old_n += 1
            removed += 1
        else:
            diff_lines.append(("diff-ctx", old_n, new_n, " ", line[1:]))
            old_n += 1
            new_n += 1

    return render_template("versions/diff.html", file=file,
                           old_no=old_no, new_no=new_no,
                           diff_lines=diff_lines, added=added, removed=removed)
