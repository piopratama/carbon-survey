[![DOI](https://zenodo.org/badge/1155294575.svg)](https://doi.org/10.5281/zenodo.18732075)

## Database Import (Required Before Running the Project)

Before running the frontend or backend services, the **PostgreSQL database must be restored first**.

This project depends on a predefined database schema and spatial data (PostgreSQL + PostGIS).  
If the database is not imported, the backend application will fail due to missing tables, extensions, and geometry columns.

---

### Prerequisites

- Docker is running
- PostgreSQL + PostGIS container is running
- pgAdmin is accessible (e.g. http://localhost:5050)
- Database backup directory is available on your machine:


> **Important**  
> The backup was created in **directory format**, not as a single `.sql` file.  
> It must be restored as a **Directory backup** in pgAdmin.

---

### Step 1: Create the Database

1. Open **pgAdmin**
2. Connect to the PostgreSQL server
3. Right-click **Databases** → **Create** → **Database**
4. Set:
   - **Database name**: `sentinel`
   - **Owner**: `postgres` (or your configured DB user)
5. Click **Save**

---

### Step 2: Restore from Backup (`sentinel_backup`)

1. Right-click the `sentinel` database
2. Select **Restore…**
3. Configure the restore options:
   - **Format**: `Directory`
   - **Folder**: select the `sentinel_backup` directory
4. (Recommended options)
   - Enable **Clean before restore**
   - Enable **Create database objects**
5. Click **Restore**
6. Wait until the process completes successfully

---

### Step 3: Verify Database Import

After the restore process finishes, verify that:

- Tables exist (e.g. `projects`, `sampling_points`, `surveys`)
- PostGIS extension is installed
- No errors appear in the restore logs

Once verified, the database setup is complete.

---

# How to Run the Project

FRONT END :
python -m http.server 3000

BACKEND :
python -m uvicorn app.main:app --reload

# AOI Sentinel Survey System

A map-based project, sampling, and field survey management system for tree biomass studies using sampling points.

---

## 1. System Purpose

This system is designed to:
- Manage research projects based on Area of Interest (AOI)
- Generate and manage sampling points
- Allow surveyors to self-assign to sampling points
- Collect field survey data including photos
- Calculate tree biomass based on scientific parameters

---

## 2. User Roles

### Admin
Admins have full system access:
- Create and edit projects
- Define and edit AOI
- Generate sampling points
- View all surveys and surveyors
- Manage tree species master data
- Lock or delete data

### Surveyor
Surveyors are responsible for field data collection:
- Login to the system
- View active projects
- View available sampling points
- Assign themselves to sampling points
- Submit field survey data
- Upload survey photos
- View their assigned and completed surveys

---

## 3. System Workflow

### 3.1 Project Setup (Admin)
1. Admin logs in
2. Searches for a location
3. Creates a new project
4. Defines the AOI
5. Saves the project
6. Generates sampling points
7. Project becomes active for surveys

### 3.2 Surveyor Assignment
1. Surveyor logs in
2. Selects a project
3. Views sampling points on the map
4. Selects a sampling point
5. Clicks "Assign"
6. System validates:
   - Maximum 5 surveyors per point
   - Surveyor has not already joined the same point

### 3.3 Field Survey Input
Surveyors submit the following data:
- Sampling point (auto-filled)
- Survey date
- Tree name
- Scientific name (from master data)
- Tree diameter
- Tree circumference
- Tree height (optional)
- Description
- Photo 1 (required)
- Photo 2 (optional)
- Photo 3 (optional)

The system will:
- Calculate tree biomass
- Store survey data

---

## 4. Sampling Point Status

Each sampling point has one of the following statuses:
- open
- partial
- full
- done

---

## 5. System Rules

- Surveyors cannot edit AOI or projects
- Surveyors can only edit their own surveys
- Maximum 5 surveyors per sampling point
- Locked surveys cannot be deleted
- Biomass calculation is handled in the backend
- At least one photo is required per survey

---

## 6. Project Structure

SENTINEL/
- BACKEND/
- FRONTEND/
- README.md

---

## 7. Core Database Entities

- projects
- sampling_points
- surveys
- users
- survey_assignments
- tree_species

---

## 8. Minimum Viable Product (MVP)

- Authentication
- Project & AOI management
- Sampling generation
- Survey assignment
- Survey input
- Biomass calculation

---

## 9. Future Development

- Data export
- Validation workflow
- NDVI integration
- Analytics dashboard

---

## 10. License

Research and non-commercial use only.

---

## License & Copyright

© 2026 I Wayan Pio Pratama. All Rights Reserved.

This software and its documentation are the intellectual property of  
**I Wayan Pio Pratama (2026)**.

This project may not be used, reproduced, distributed, or modified 
for academic, research, publication, or commercial purposes without 
proper citation.

If you use this system, methodology, or derived outputs in any publication, 
you MUST cite it as follows:

### APA 7th Citation Format

Pratama, I. W. P. (2026). *Carbon Survey System* [Software]. GitHub.  
https://github.com/piopratama/carbon-survey

Failure to provide proper citation constitutes academic misconduct.
