from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    projects = db.relationship("Project", backref="owner", lazy=True)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    files = db.relationship("File", backref="project", lazy=True)


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey(
        "project.id"), nullable=False)

    versions = db.relationship("Version", backref="file", lazy=True)


class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_id = db.Column(db.Integer, db.ForeignKey("file.id"), nullable=False)
