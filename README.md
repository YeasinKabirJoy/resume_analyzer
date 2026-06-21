# ðŸ“„ Resume Analyzer

**Resume Analyzer** is a web application built with **Python** and **Django** that allows users to upload resumes and evaluate them against specific job roles. The analysis uses an ATS-first rules-based pipeline to extract structured resume data and match it against job requirements.

---

## ðŸš€ Features

- ðŸ“¤ Upload a **PDF Resume** and select a **Job Role**.
- ðŸ¤– Analyze resumes using an **LLM** to extract:
  - Personal information
  - Skills (matched/missed)
  - Experience history and total experience
- ðŸŽ¯ Compare extracted resume data with job role requirements:
  - Minimum experience
  - **Mandatory** and **Optional** skills
- ðŸ“ˆ Generate a **Resume Score** and **Verdict**:
  - `Matched`
  - `Skipped`
  - `Overqualified`
- ðŸ“ Display original uploaded PDF alongside analysis
- ðŸ”„ **Versioned Job Roles**: If a role with the same title is created again, it's saved as `v2`, `v3`, etc.
- ðŸ“š Manage:
  - Job Roles (title, required experience, mandatory & optional skills)
  - Skills (by title)
  - Submitted resumes per job role, viewable individually

---

## ðŸ–¼ï¸ Screenshots

<!-- âœ… Add screenshots or diagrams here -->
### ðŸ“¤ Dashboard
<img src="preview/dashboard.png" alt="Dashboard" width="700"/>

### ðŸ“¤ Resume Upload (Click Analyze)
<img src="preview/analyze_upload.png" alt="Resume Upload" width="700"/>

### ðŸ“¤ Active Jobs 
<img src="preview/active_job.png" alt="Active Jobs" width="700"/>

### ðŸ“¤ Resumes (Click View All Resumes)
<img src="preview/all_resume.png" alt="All Resumes" width="700"/>

### ðŸ“¤ Resume Details (Click View Details)
<img src="preview/resume_details.png" alt="Resume Details" width="700"/>

### ðŸ“¤ Job Role Create (Active Jobs -> Create Jobs)
<img src="preview/job_role_create.png" alt="Job Role Create" width="700"/>

### ðŸ“¤ Skills Add/Edit
<img src="preview/skills_crud.png" alt="Skills Crud" width="700"/>
---

## ðŸ› ï¸ Tech Stack

- **Backend**: Python, Django
- **AI/ML**: ATS-style rules-based extraction and matching
- **Frontend**: Django Templates 
- **Database**: SQLite
---

## ðŸ§ª Setup Instructions

Follow these steps to set up the project locally.

### Clone the Repository

If your project is already in an existing python3 virtualenv first install django by running

    $ git clone https://github.com/YeasinKabirJoy/resume_analyzer.git \
    cd resume_analyzer
    
      
### Create a Virtual Environment

    $ python -m virtualenv venv
    
### Activate the Virtual Environment
#### On Windows
    $ venv\Scripts\activate
#### on Mac/Linux
    $ source venv/bin/activate
    
### Install Dependencies
    $ pip install -r requirements.txt

### Running the Project

#### Apply database migrations
    $ python manage.py makemigrations 
    $ python manage.py migrate
#### Run the development server
    $ python manage.py runserver
#### Open your browser and go to
   http://127.0.0.1:8000



## ðŸ“Œ Future Improvements

- ðŸ” User authentication  
- ðŸ“ CSV export of results  
- ðŸ¤– LLM fine-tuning for more accurate skill extraction  
