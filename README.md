# Online Student Portal

This is our **Flask-based web portal** created for our college's final year project **H.H The Rajah's College**.  
It allows students, teachers, and admin to manage **assignments, attendance, submissions, and queries** efficiently.  
Features include user authentication for admin, teachers, and students; managing subjects, assignments, and submissions; tracking student attendance; and handling student queries with teacher responses.

---

## Folder Structure

project_folder/
├── static/
│ ├── images/
│ └── uploads/
├── templates/
├── app.py
├── config.py
├── database.sql
├── README.md
└── requirements.txt

yaml
Copy code

---

## Setup

**1. Clone the repository**  
```bash
git clone https://github.com/yourusername/repo-name.git
cd repo-name
2. Create virtual environment (optional but recommended)

bash
Copy code
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
3. Install dependencies

bash
Copy code
pip install -r requirements.txt
4. Import database
Open phpMyAdmin → Import database.sql → Go
This creates the database, tables, and initial data.

5. Run the application

bash
Copy code
python app.py
Open your browser: http://localhost:5000

## Technologies Used

Python, Flask

MySQL / MariaDB

HTML, CSS, JavaScript


Author

Karthick Kumar S, BCA
College: H.H The Rajah's College
