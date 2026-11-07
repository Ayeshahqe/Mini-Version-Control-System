# Mini Version Control System (MVCS)

A web-based application built with Python and Flask that lets users upload files, keep every version, compare changes, tag important versions, view code in the browser, and restore earlier versions. It is a simplified, beginner-friendly version control system inspired by the core ideas of Git.

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
- Let users read the code of any version in the browser
- Show an overview of the user's work and recent activity
- Protect each user's projects and files from other users

## 3. Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL, Flask-SQLAlchemy |
| Frontend | HTML, CSS (Jinja2 templates) |
| Python libraries | `hashlib`, `difflib`, `zipfile` (standard library) |
| Tools | Git, GitHub |

## 4. Features

| Feature | Description |
|---|---|
| Authentication | Register, log in, and log out with hashed passwords |
| Navigation bar | Home, Dashboard, Project, History, Compare, View Code, Login / Get Started (Logout when signed in) |
| Dashboard | Total projects, files, versions, and storage used, plus a card for each project |
| Recent activity | Latest uploads, restores, tags, and deletions with time |
| Projects | Create, open, and delete your own projects |
| File upload | Type, size (maximum 100 KB), empty-file, and filename validation |
| Executable blocking | `.exe`, `.bat`, `.msi`, `.sh` and similar files are rejected |
| Version control | Every upload creates a new version instead of overwriting |
| Content hashing | Each version has a SHA-256 hash, shown as a short ID in History |
| Duplicate detection | Content identical to the latest version is rejected with "No changes found" |
| Version tags | Label a version (for example "v1.0"); a tag name can be used once per file |
| File version history | All versions of one file with tag, date, and a "Latest" badge |
| All-versions History page | Every version of every file with hash, author, and date |
| Restore | Restoring an old version creates a new version with the old content (with confirmation) |
| Compare versions | Added lines in green, removed lines in red, with line numbers and totals |
| Compare page | Pick a file and two versions, or tick two snapshots in History |
| View Code | Read any text or code version in the browser with line numbers |
| Download | Download any version, the latest version of a file, or a whole project as a ZIP |
| File deletion | Delete a file and all its versions (with confirmation) |
| Notifications | Green success and red error messages |
| Access control | Users can only access their own projects and files |

## 5. How It Works

1. When a file is uploaded, the system checks its type, size, and name.
2. The system calculates its **SHA-256 hash**.
3. If the hash matches the latest version, nothing has changed, so no new version is created.
4. Otherwise a new version is saved next to the older ones. Old versions are never overwritten.
5. Restoring an old version copies its content into a new version. The new version has the same hash as the old one, which proves the content is identical.
6. Every page checks that the user is logged in and owns the project.

## 6. User Interface

- **Top navigation bar:** pill-style menu with the active page highlighted
- **Light theme:** white cards on a soft background
- **Indigo-to-pink gradient:** buttons, logo, badges, and headings
- **Pages:** hero home page, dashboard with statistics and activity, tables for files and history, and a code viewer with a diff view
- **Responsive design:** grids and the navigation bar adjust to smaller screens

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
├── app.py                    # App setup, home, dashboard, error pages
├── routes.py                 # Register, login, logout, create and delete project
├── models/
│   └── models.py             # Database models
├── file_routes/
│   ├── __init__.py
│   ├── file_management.py    # Project files, upload, download, delete, ZIP
│   ├── version.py            # Versions, hash check, tags, restore, view, compare
│   └── nav.py                # Projects, History, Compare, View Code pages and dashboard data
├── templates/
│   ├── base.html             # Navigation bar and layout shared by all pages
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── create_project.html
│   ├── error.html
│   ├── nav/
│   │   ├── projects.html
│   │   ├── history.html
│   │   ├── compare.html
│   │   └── code.html
│   ├── files/
│   │   ├── files.html
│   │   └── upload.html
│   └── versions/
│       ├── history.html
│       ├── upload_version.html
│       ├── view.html
│       └── diff.html
├── static/
│   └── css/
│       └── style.css         # Light theme with indigo-pink gradient
├── uploads/                  # Stored file versions
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
4. Click **Versions** on a file, then upload a new version (same file type required).
5. Add a tag such as `v1.0` to an important version.
6. Use **Compare** to see added and removed lines.
7. Use **View Code** to read a version in the browser.
8. Use **Restore** to bring back an older version as a new version.
9. Use **History** to see every version of every file with its hash.
10. Use **Download ZIP** on a project page to get the latest version of all files.
11. Check the Dashboard for statistics and recent activity.

## 11. Testing

All test cases are listed in [TEST_CASES.md](TEST_CASES.md). They cover authentication, projects, files, versions, tags, comparison, code viewing, navigation, dashboard, interface, and security.

## 12. Limitations

- Version comparison and code viewing work only for text and code files
- New versions must have the same file type as the original file
- Maximum upload size is 100 KB
- Executable files are blocked by extension only, not by content
- Educational project, not a production-grade version control platform
- Requires a local MySQL database to run

## 13. Future Improvements

- Project snapshots (save the state of all files in a project at once)
- Snapshot comparison (added, modified, and removed files)
- Search and filter for projects and files
- Version messages (a note describing each change)
- Multiple users per project
- Automated tests
- Side-by-side comparison view

## 14. Team Members

- Ayesha Haque
- Md Shahariar Refat
- Nazmul Ahsan Rifat
- Saurob Chandra Sheel