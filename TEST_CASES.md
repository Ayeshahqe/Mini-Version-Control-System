# Mini Version Control System (MVCS)
## Test Cases

### 1. User Registration

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-01 | Register with valid information | User account is created successfully |
| TC-02 | Register with an already registered email | Registration is rejected with an error message |
| TC-03 | Submit registration with missing information | Validation error is displayed |

### 2. User Login and Logout

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-04 | Login with correct email and password | User is redirected to the dashboard |
| TC-05 | Login with incorrect password | Login is rejected with an error message |
| TC-06 | Logout from the application | User session ends |
| TC-07 | Access a protected page without logging in | User is redirected to the login page |

### 3. Project Management

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-08 | Create a project with a valid name | Project is created and a green success message is shown |
| TC-09 | Open an existing project | Project name, file count, and files are displayed |
| TC-10 | Access another user's project | Access is denied |
| TC-11 | Delete a project and confirm the popup | Project, its files, and its versions are deleted |
| TC-12 | Delete a project and cancel the popup | Nothing is deleted |

### 4. File Management

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-13 | Upload a supported file | File is uploaded and a green success message is shown |
| TC-14 | Upload a file with an unsupported extension | Upload is rejected |
| TC-15 | Upload a file larger than 200 KB | Upload is rejected with a size message |
| TC-16 | Upload a file whose name already exists in the project | Upload is rejected with a message to use the file's version history |
| TC-17 | Download the latest version from the project page | File is downloaded successfully |
| TC-18 | Delete a file and confirm the popup | File and its associated versions are deleted |

### 5. Version Control

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-19 | Upload the first version of a file | Version 1 is created with a short ID |
| TC-20 | Upload a changed file with the same filename | A new version is created and a green success message is shown |
| TC-21 | Upload a new version with content identical to the latest version | Upload is rejected with a "No changes found" message |
| TC-22 | Upload a new version with a different filename | Upload is rejected with an error message in the styled layout |
| TC-23 | View file version history | Each version is shown with ID and date, and the newest is marked Latest |
| TC-24 | Download an older version | The selected version is downloaded |
| TC-25 | Restore an older version and confirm the popup | A new version is created with the older content and the same ID |
| TC-26 | Check the Restore button on the latest version | Restore button is not shown |

### 6. Version Tags

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-27 | Add a tag to a version | Tag is saved and shown as a badge on that version |
| TC-28 | Use the same tag on another version of the same file | Tag is rejected with an error message |
| TC-29 | Save an empty tag on a tagged version | Tag is removed |

### 7. Version Comparison

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-30 | Compare two different versions | Differences between the versions are displayed |
| TC-31 | Check the comparison colors | Added lines are green and removed lines are red |
| TC-32 | Compare two versions with identical content (a version and its restored copy) | The system reports that the content is identical |
| TC-33 | Select the same version twice | Error message asks for two different versions |
| TC-34 | Open the history of a file with only one version | Compare Versions button is not shown |
| TC-35 | Compare versions of a non-text file | System reports that comparison is available only for text files |

### 8. Dashboard and Recent Activity

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-36 | Open the dashboard | Total projects, files, and versions are displayed correctly |
| TC-37 | Upload, tag, restore, and delete, then open the dashboard | Each action appears in Recent Activity, newest first |
| TC-38 | Check the project cards on the dashboard | Each card shows the project name and file count and opens the project |

### 9. User Interface

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-39 | Log in and view any page | Black sidebar with Dashboard and Logout is shown |
| TC-40 | Check the active sidebar item | Dashboard is highlighted in red |
| TC-41 | Resize the browser below 768 px | Sidebar becomes a compact top navigation bar |
| TC-42 | Trigger an error message (for example, wrong login) | Message appears inside the styled layout, not as plain text |

### 10. Security and Data Integrity

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-43 | Attempt to access another user's file | Access is denied |
| TC-44 | Check the database password field | Password is stored as a hash, not plain text |
| TC-45 | Restart the application and check saved project data | Previously saved database records remain available |