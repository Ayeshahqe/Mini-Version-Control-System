import os
from datetime import datetime

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash)

from models.models import User, Project, File, Version, Activity
from file_routes.version import login_required, resolve_path, file_hash, is_text_file

nav_bp = Blueprint("nav", __name__)


# ---------- Helpers ----------

def format_size(num):
    size = float(num)
    for unit in ["B", "KB", "MB"]:
        if size < 1024:
            return "%.1f %s" % (size, unit)
        size /= 1024
    return "%.1f GB" % size


def time_ago(when):
    """Turn a date into text like '5 mins ago'."""
    if when is None:
        return "never"
    seconds = int((datetime.now() - when).total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return "%d min%s ago" % (seconds // 60, "" if seconds < 120 else "s")
    if seconds < 86400:
        hours = seconds // 3600
        return "%d hour%s ago" % (hours, "" if hours == 1 else "s")
    days = seconds // 86400
    return "%d day%s ago" % (days, "" if days == 1 else "s")


def user_files(user_id):
    """All files in projects owned by this user."""
    return (File.query.join(Project, File.project_id == Project.id)
            .filter(Project.user_id == user_id)
            .order_by(File.filename).all())


def latest_version(file_id):
    return (Version.query.filter_by(file_id=file_id)
            .order_by(Version.version_number.desc()).first())


def project_cards(user_id):
    cards = []
    projects = (Project.query.filter_by(user_id=user_id)
                .order_by(Project.id.desc()).all())
    for p in projects:
        file_count = File.query.filter_by(project_id=p.id).count()
        project_versions = (Version.query
                            .join(File, Version.file_id == File.id)
                            .filter(File.project_id == p.id)
                            .order_by(Version.created_at.desc()).all())
        updated = "never"
        if project_versions:
            updated = time_ago(project_versions[0].created_at)
        cards.append({"id": p.id, "name": p.name, "files": file_count,
                      "versions": len(project_versions), "updated": updated})
    return cards


def get_user_stats(user_id):
    """Numbers and recent activity shown on the dashboard."""
    files = user_files(user_id)
    file_map = {f.id: f for f in files}
    versions = []
    if file_map:
        versions = (Version.query.filter(Version.file_id.in_(list(file_map)))
                    .order_by(Version.created_at.desc(), Version.id.desc())
                    .all())

    total_bytes = 0
    for v in versions:
        path = resolve_path(v.file_path)
        if os.path.exists(path):
            total_bytes += os.path.getsize(path)

    cards = project_cards(user_id)
    recent = (Activity.query.filter_by(user_id=user_id)
              .order_by(Activity.created_at.desc()).limit(6).all())
    activity = [{"text": a.description,
                 "sub": "%s \u2022 %s" % (a.action, time_ago(a.created_at))}
                for a in recent]

    return {"projects": len(cards), "files": len(files),
            "versions": len(versions), "storage": format_size(total_bytes),
            "cards": cards, "activity": activity}


# ---------- Routes ----------

@nav_bp.route("/projects")
@login_required
def projects():
    return render_template("nav/projects.html",
                           cards=project_cards(session["user_id"]))


@nav_bp.route("/history")
@login_required
def history_all():
    user = User.query.get(session["user_id"])
    file_map = {f.id: f for f in user_files(user.id)}
    rows = []
    if file_map:
        versions = (Version.query.filter(Version.file_id.in_(list(file_map)))
                    .order_by(Version.created_at.desc(), Version.id.desc())
                    .limit(50).all())
        for v in versions:
            path = resolve_path(v.file_path)
            if os.path.exists(path):
                h = file_hash(path)
                short = h[:8] + " ... " + h[-3:]
            else:
                short = "file missing"
            f = file_map[v.file_id]
            rows.append({"file": f, "version": v, "hash": short,
                         "author": user.name,
                         "can_view": is_text_file(f.filename)})
    return render_template("nav/history.html", rows=rows)


@nav_bp.route("/compare")
@login_required
def compare_page():
    items = []
    for f in user_files(session["user_id"]):
        if not is_text_file(f.filename):
            continue
        numbers = [v.version_number for v in
                   Version.query.filter_by(file_id=f.id)
                   .order_by(Version.version_number.desc()).all()]
        if len(numbers) >= 2:
            items.append({"file": f, "numbers": numbers})
    return render_template("nav/compare.html", items=items)


@nav_bp.route("/compare/selected")
@login_required
def compare_selected():
    """Receives the 2 checkboxes from the History page."""
    chosen = request.args.getlist("sel")
    back = url_for("nav.history_all")

    if len(chosen) != 2:
        flash("Please select exactly two snapshots to compare.", "error")
        return redirect(back)

    try:
        (f1, v1), (f2, v2) = [tuple(int(x) for x in item.split(":"))
                              for item in chosen]
    except ValueError:
        flash("Invalid selection.", "error")
        return redirect(back)

    if f1 != f2:
        flash("Please select two versions of the same file.", "error")
        return redirect(back)

    return redirect(url_for("version.diff", file_id=f1, v1=v1, v2=v2))


@nav_bp.route("/code")
@login_required
def code_page():
    rows = []
    for f in user_files(session["user_id"]):
        if not is_text_file(f.filename):
            continue
        latest = latest_version(f.id)
        if latest is None:
            continue
        rows.append({"file": f, "latest": latest,
                     "project": Project.query.get(f.project_id)})
    return render_template("nav/code.html", rows=rows)
