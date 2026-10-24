# Mini Version Control System (MVCS)

A web-based application built with Python and Flask that lets users upload files, keep every version, compare changes, tag important versions, and restore earlier versions. It is a simplified, beginner-friendly version control system inspired by the core ideas of Git.

---

## 1. Problem Statement

Managing multiple versions of files manually leads to confusion, accidental overwriting, and loss of previous work. MVCS solves this by storing each version separately, identifying it by a content hash, and letting users view, download, compare, tag, and restore any version.

## 2. Objectives

- Provide user registration and login
- Let users create, open, and delete projects
- Support file upload, download, and deletion
- Maintain full version history for every file
- Identify each version by a SHA-256 content hash and detect unchanged uploads
- Let users tag important versions (for example, "v1.0")
- Restore older versions without losing newer ones
- Compare two versions of a text file with colored differences
- Show an overview of the user's work and recent activity
- Protect each user's projects and files from other users

## 3. Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL, Flask-SQLAlchemy |
| Frontend | HTML, CSS (Jinja2 templates) |
| Tools | Git, GitHub |

## 4. Features

| Feature | Description |
|---|---|
| Authentication | Register, log in, and log out with hashed passwords |
| Dashboard | Shows total projects, files, and versions, plus a card for each project |
| Recent activity | Lists the latest uploads, restores, tags, and deletions with date and time |
| Projects | Create, open, and delete your own projects |
| File upload | Upload files with type, size (maximum 200 KB), and filename validation |
| Version control | Every upload creates a new version instead of overwriting |
| Content hashing | Each version gets a SHA-256 hash, shown as a short ID such as `a3f9c21` |
| Duplicate detection | Uploading content identical to the latest version is rejected with "No changes found" |
| Version tags | Label a version (for example "v1.0"); a tag name can be used once per file |
| Version history | Every version shown in its own box with ID, date, and a "Latest" badge |
| Restore | Restoring an old version creates a new version with the old content (with confirmation) |
| Compare versions | Added lines in **green**, removed lines in **red** |
| Download | Download any version, or the latest version from the project page |
| File deletion | Delete a file and all its versions (with confirmation) |
| Notifications | Clear green success and red error messages |
| Access control | Users can only access their own projects and files |

## 5. How It Works

1. When a file is uploaded, the system calculates its **SHA-256 hash**.
2. If the hash matches the latest version, nothing has changed, so no new version is created.
3. Otherwise a new version is saved next to the older ones, and the hash becomes its short ID.
4. Restoring an old version copies its content into a new version. The new version has the same ID as the old one, which proves the content is identical.

## 6. User Interface

- **Black sidebar:** Dashboard and Logout
- **White workspace:** the actual page content
- **Red accents:** buttons, active navigation item, and important actions
- **Responsive design:** on small screens the sidebar becomes a compact top navigation bar

## 7. Database Design

| Table | Purpose |
|---|---|
| User | Account information (name, email, hashed password) |
| Project | Projects owned by a user |
| File | Files that belong to a project |
| Version | Version number, file path, SHA-256 hash, tag, and creation time |
| Activity | Log of user actions shown as Recent Activity |

Relationships: **User → Projects → Files → Versions** (one-to-many at each step). Each activity record belongs to a user.

## 8. Project Structure

```text
Mini-Version-Control-System/
├── app.py                  # App setup, dashboard, error pages
├── routes.py               # Auth, projects, versions, tags, compare, restore
├── models/
│   └── models.py           # Database models
├── file_routes/
│   ├── __init__.py
│   └── file_management.py  # File download and delete
├── templates/
│   ├── base.html           # Sidebar layout shared by all pages
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── create_project.html
│   ├── project.html
│   ├── upload.html
│   ├── new_version.html
│   ├── file_history.html
│   ├── compare_versions.html
│   └── error.html
├── static/
│   └── css/
│       └── style.css       # Black, white, and red theme
├── uploads/                # Stored file versions
├── requirements.txt
├── TEST_CASES.md
└── README.md
```

## 9. Installation and Setup

**Prerequisites:** Python, MySQL Server, Git

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ayeshahqe/Mini-Version-Control-System.git
   cd Mini-Version-Control-System
   ```

2. **Create and activate a virtual environment (Windows)**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```text
   SECRET_KEY=your_secret_key
   DB_PASSWORD=your_mysql_password
   ```
   Never upload `.env` to GitHub.

5. **Create the MySQL database**
   ```sql
   CREATE DATABASE mvcs_db;
   ```
   Tables are created automatically when the app starts.

6. **Run the application**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

## 10. How to Use

1. Register an account and log in.
2. Create a project from the Dashboard.
3. Open the project and upload a file (creates **Version 1**).
4. Open **Version History** and upload a new version (same filename required).
5. Add a tag such as `v1.0` to an important version.
6. Use **Compare Versions** to see added and removed lines.
7. Use **Restore** to bring back an older version as a new version.
8. Check the Dashboard for statistics and recent activity.

## 11. Testing

All test cases are listed in [TEST_CASES.md](TEST_CASES.md). They cover authentication, projects, files, versions, tags, comparison, dashboard, interface, and security.

## 12. Limitations

- Version comparison works only for text files
- New versions must have the same filename as the original file
- Maximum upload size is 200 KB
- Educational project, not a production-grade version control platform
- Requires a local MySQL database to run

## 13. Future Improvements

- Project snapshots (save the state of all files in a project at once)
- Snapshot comparison (added, modified, and removed files)
- Search and filter for projects and files
- Version messages (a note describing each change)
- Automated tests
- Side-by-side comparison view

## 14. Team Members

- Ayesha Haque
- Md Shahariar Refat
- Nazmul Ahsan Rifat
- Saurob Chandra Sheel