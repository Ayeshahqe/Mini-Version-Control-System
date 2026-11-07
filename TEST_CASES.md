# Mini Version Control System (MVCS)
## Test Cases

### 1. User Registration

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-01 | Register with valid information | User account is created and the user is sent to the login page |
| TC-02 | Register with an already registered email | Registration is rejected with an error message |
| TC-03 | Submit registration with missing information | Validation error is displayed |

### 2. User Login and Logout

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-04 | Login with correct email and password | User is redirected to the dashboard |
| TC-05 | Login with incorrect password | Login is rejected with an error message |
| TC-06 | Logout from the application | User session ends and the Login and Get Started buttons appear |
| TC-07 | Access a protected page without logging in | User is redirected to the login page with "Please log in to continue." |

### 3. Navigation

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-08 | Click each item in the navigation bar while logged in | Home, Dashboard, Project, History, Compare, and View Code each open their page |
| TC-09 | Check the active navigation item | The current page is highlighted in the navigation bar |
| TC-10 | Check the navigation bar when logged out | Login and Get Started are shown |
| TC-11 | Check the navigation bar when logged in | Logout is shown instead of Login and Get Started |

### 4. Project Management

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-12 | Create a project with a valid name | Project is created and a green success message is shown |
| TC-13 | Open an existing project | Project name, file count, and files are displayed |
| TC-14 | Open the Project page from the navigation bar | All of the user's projects are shown as cards |
| TC-15 | Access another user's project | Access is denied (403) |
| TC-16 | Delete a project and confirm the popup | Project, its files, and its versions are deleted |
| TC-17 | Delete a project and cancel the popup | Nothing is deleted |

### 5. File Management

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-18 | Upload a supported file | File is uploaded and a green success message is shown |
| TC-19 | Upload a file with an unsupported extension | Upload is rejected |
| TC-20 | Upload an executable file (for example `.exe`) | Upload is rejected with "Executable files are not allowed" |
| TC-21 | Upload a file larger than 100 KB | Upload is rejected with a size message |
| TC-22 | Upload an empty file | Upload is rejected with "Empty files cannot be uploaded" |
| TC-23 | Submit the upload form with no file selected | Upload is rejected with "Please choose a file" |
| TC-24 | Upload a file whose name already exists in the project | Upload is rejected with a message to use the file's version history |
| TC-25 | Download the latest version from the project page | File is downloaded successfully |
| TC-26 | Click Download ZIP on a project with files | A ZIP containing the latest version of every file is downloaded |
| TC-27 | Click Download ZIP on a project with no files | Error message "This project has no files to download" |
| TC-28 | Delete a file and confirm the popup | File and its associated versions are deleted |

### 6. Version Control

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-29 | Upload the first version of a file | Version 1 is created |
| TC-30 | Upload a changed file as a new version | Version 2 is created, Version 1 is kept, and a green success message is shown |
| TC-31 | Upload a new version with content identical to the latest version | Upload is rejected with a "No changes found" message |
| TC-32 | Upload a new version with a different file type (for example `.txt` for a `.py` file) | Upload is rejected with "The new version must be a .py file" |
| TC-33 | Upload an executable as a new version | Upload is rejected with an error message |
| TC-34 | Upload a new version larger than 100 KB | Upload is rejected with a size message |
| TC-35 | View file version history | Each version is shown with tag and date, and the newest is marked Latest |
| TC-36 | Download an older version | The selected version is downloaded with its old content |
| TC-37 | Restore an older version and confirm the popup | A new latest version is created with the older content, and older versions are kept |
| TC-38 | Restore the latest version | Rejected with "Nothing to restore: this version is identical to the latest version" |
| TC-39 | Check the version files on disk | Each version is a separate file in `uploads/<project_id>/<file_id>/` |

### 7. Version Tags

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-40 | Add a tag to a version | Tag is saved and shown in that version's row |
| TC-41 | Use the same tag on another version of the same file | Tag is rejected with an error message |
| TC-42 | Save an empty tag on a tagged version | Tag is removed |

### 8. Version Comparison and Code Viewing

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-43 | Compare two different versions from a file's history | Differences are displayed with line numbers |
| TC-44 | Check the comparison colors and totals | Added lines are green, removed lines are red, and +additions / -deletions counts are shown |
| TC-45 | Compare two versions with identical content (a version and its restored copy) | "No differences found" is shown |
| TC-46 | Select the same version twice | Error message asks for two different versions |
| TC-47 | Open the history of a file with only one version | The Compare box is not shown |
| TC-48 | Compare versions of a non-text file | System reports that only text and code files can be compared |
| TC-49 | Use the Compare page (navigation bar) to pick a file and two versions | The comparison page opens |
| TC-50 | Tick two versions of the same file in the History page and click Compare Selected Snapshots | The comparison page opens |
| TC-51 | Tick two versions of different files, or only one version | Error message asks for two versions of the same file |
| TC-52 | Click View on a text file version | The code is shown with line numbers |
| TC-53 | Open the View Code page from the navigation bar | The latest version of every text file is listed |
| TC-54 | Check the History page (navigation bar) | Every version of every file is shown with a short SHA-256 hash, author, and date |

### 9. Dashboard and Recent Activity

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-55 | Open the dashboard | Total projects, files, versions, and storage used are displayed correctly |
| TC-56 | Upload, tag, restore, and delete, then open the dashboard | Each action appears in Recent Activity, newest first |
| TC-57 | Check the project cards on the dashboard | Each card shows the project name and file count and opens the project |

### 10. User Interface

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-58 | Open the home page | Hero section, code preview, feature cards (3 per row), and how-it-works steps are shown |
| TC-59 | Check the styling of any page | The page loads with the gradient theme, not as plain unstyled HTML |
| TC-60 | Resize the browser below 900 px | Grids reduce columns and the navigation bar stays usable |
| TC-61 | Trigger an error message (for example, wrong login) | Message appears inside the styled layout, not as plain text |
| TC-62 | Open a page that does not exist | A styled 404 error page is shown |

### 11. Security and Data Integrity

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-63 | Attempt to open another user's file history, version, download, or compare URL | Access is denied (403) |
| TC-64 | Check the database password field | Password is stored as a hash, not plain text |
| TC-65 | Restart the application and check saved project data | Previously saved database records remain available |
| TC-66 | Open any protected URL after logging out | User is redirected to the login page |