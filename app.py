from flask import Flask, render_template, request, redirect, session, flash, Response, url_for, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import csv
from io import StringIO
from datetime import datetime, date, timedelta
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from calendar import monthrange, weekday
import MySQLdb.cursors
import io


app = Flask(__name__)
app.secret_key = 'your_secret_key'




# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'online_portal'

mysql = MySQL(app)


#-----uploadsssss----
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/teacher/add_assignment', methods=['GET', 'POST'])
def add_assignment():
    if 'username' not in session or session['role'] != 'teacher':
        flash('Please login first!', 'warning')
        return redirect('/login')

    teacher_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name FROM subjects WHERE teacher_id=%s", (teacher_id,))
    subjects = cursor.fetchall()

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        file_path = None

        # Handle file upload
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        cursor.execute("""
            INSERT INTO assignments (subject_id, title, description, due_date, file_path)
            VALUES (%s, %s, %s, %s, %s)
        """, (subject_id, title, description, due_date, file_path))
        mysql.connection.commit()
        cursor.close()
        flash("Assignment added successfully!", "success")
        return redirect('/teacher/add_assignment')

    cursor.close()
    return render_template('teacher_add_assignment.html', subjects=subjects)

# ------------------- Login -------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username=%s AND role=%s", (username, role))
        user = cursor.fetchone()
        cursor.close()

        if user and password == user['password']:  # For testing; later hash
            session['username'] = username
            session['role'] = role
            session['user_id'] = user['id']
            flash(f"Logged in as {role}", "success")
            if role == 'student':
                return redirect('/student/dashboard')
            elif role == 'teacher':
                return redirect('/teacher/dashboard')
            elif role == 'admin':
                return redirect('/admin/dashboard')
        else:
            flash("Invalid credentials", "danger")
            return redirect('/login')
    return render_template('login.html')


# ------------------- Logout -------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ------------------- Teacher Attendance -------------------
@app.route('/teacher/attendance', methods=['GET', 'POST'])
def teacher_attendance():
    if 'username' in session and session['role'] == 'teacher':
        teacher_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Get teacher's subjects
        cursor.execute("SELECT * FROM subjects WHERE teacher_id=%s", (teacher_id,))
        subjects = cursor.fetchall()

        if request.method == 'POST':
            date = request.form['date']
            for subject in subjects:
                subject_id = subject['id']
                # Check if attendance already marked for this subject/date
                for student_id in request.form.getlist(f'students_{subject_id}'):
                    status = request.form.get(f'status_{subject_id}_{student_id}', 'Absent')
                    cursor.execute("SELECT * FROM attendance WHERE student_id=%s AND subject_id=%s AND date=%s",
                                   (student_id, subject_id, date))
                    existing = cursor.fetchone()
                    if existing:
                        # Update existing
                        cursor.execute("UPDATE attendance SET status=%s WHERE id=%s", (status, existing['id']))
                    else:
                        cursor.execute("INSERT INTO attendance(student_id, subject_id, date, status) VALUES (%s,%s,%s,%s)",
                                       (student_id, subject_id, date, status))
            mysql.connection.commit()
            flash("Attendance saved successfully!", "success")
            return redirect('/teacher/attendance')

        # Get students for all subjects
        students = cursor.execute("SELECT id, name FROM users WHERE role='student'")
        students = cursor.fetchall()
        cursor.close()
        return render_template('teacher_attendance.html', subjects=subjects, students=students)
    else:
        return redirect('/login')




# ------------------- Student dashboard -------------------
@app.route('/student/dashboard')
def student_dashboard():
    if 'username' in session and session['role'] == 'student':
        student_id = session['user_id']
        return render_template('student_dashboard.html', student_id=student_id)
    else:
        flash("Please login first!", "warning")
        return redirect('/login')

#-----student view attenetendance-------------------------
# ------------------- Student Attendance View -------------------
@app.route('/student/view_attendance')
def student_view_attendance():
    if 'username' in session and session['role'] == 'student':
        student_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get all subjects
        cursor.execute("""
            SELECT s.id, s.name, u.name as teacher_name
            FROM subjects s
            LEFT JOIN users u ON s.teacher_id = u.id
        """)
        subjects = cursor.fetchall()

        attendance_summary = []

        for subj in subjects:
            # Get all attendance for this student and subject
            cursor.execute("""
                SELECT date, status
                FROM attendance
                WHERE subject_id = %s AND student_id = %s
                ORDER BY date ASC
            """, (subj['id'], student_id))
            records = cursor.fetchall()

            if records:
                total_classes = len(records)
                attended_count = sum(1 for r in records if r['status'] == 'Present')
                attended_dates = [r['date'].strftime('%Y-%m-%d') for r in records if r['status'] == 'Present']
                absent_dates = [r['date'].strftime('%Y-%m-%d') for r in records if r['status'] == 'Absent']
            else:
                total_classes = 0
                attended_count = 0
                attended_dates = []
                absent_dates = []

            percent = round(attended_count / total_classes * 100, 1) if total_classes else 0

            attendance_summary.append({
                'subject_name': subj['name'],
                'teacher_name': subj['teacher_name'],
                'attended': attended_count,
                'total': total_classes,
                'percent': percent,
                'attended_dates': attended_dates,
                'absent_dates': absent_dates
            })

        cursor.close()
        return render_template('student_view_attendance.html', attendance_summary=attendance_summary)
    else:
        flash("Please login first!", "warning")
        return redirect('/login')

# ------------------- Student View Assignments -------------------
# ------------------- Student View Assignments -------------------
@app.route('/student/view_assignments')
def student_view_assignments():
    if 'username' in session and session['role'] == 'student':
        student_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get all subjects for this student
        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()

        assignments = []
        for subj in subjects:
            cursor.execute("""
                SELECT 
                    a.id, 
                    a.title, 
                    a.description, 
                    a.due_date, 
                    u.name AS teacher_name,
                    sub.name AS subject_name,
                    IFNULL(s.file_path, NULL) AS file_path,
                    CASE 
                        WHEN s.assignment_id IS NOT NULL THEN 'Submitted' 
                        ELSE 'Pending' 
                    END AS status
                FROM assignments a
                JOIN subjects sub ON sub.id = a.subject_id
                JOIN users u ON u.id = sub.teacher_id
                LEFT JOIN submissions s 
                    ON s.assignment_id = a.id AND s.student_id = %s
                WHERE a.subject_id = %s
                ORDER BY a.due_date DESC
            """, (student_id, subj['id']))
            data = cursor.fetchall()

            for d in data:
                # ✅ Fix: convert Windows backslashes to forward slashes for correct URL
                if d['file_path']:
                    d['file_path'] = d['file_path'].replace("\\", "/")
                assignments.append(d)

        cursor.close()

        from datetime import date
        current_date = date.today()

        return render_template('student_view_assignments.html',
                               assignments=assignments,
                               current_date=current_date)
    else:
        flash("Please login first!", "warning")
        return redirect('/login')



##------submit assignment------------


@app.route('/student/submit_assignment', methods=['POST'])
def student_submit_assignment():
    if 'username' not in session or session['role'] != 'student':
        flash("Please login first!", "warning")
        return redirect('/login')

    student_id = session['user_id']
    assignment_id = request.form['assignment_id']
    file = request.files.get('file')

    if not file or file.filename == '':
        flash("No file selected!", "danger")
        return redirect(url_for('student_view_assignments'))

    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash("File type not allowed! Only PDF, DOC, DOCX, TXT files.", "danger")
        return redirect(url_for('student_view_assignments'))

    # Fetch assignment info
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM assignments WHERE id=%s", (assignment_id,))
    assignment = cursor.fetchone()
    if not assignment:
        flash('Assignment not found!', 'danger')
        return redirect(url_for('student_view_assignments'))

    from datetime import date
    if assignment['due_date'] < date.today():
        flash('Cannot submit. Deadline has passed!', 'danger')
        return redirect(url_for('student_view_assignments'))

    # Save file in static/uploads
    filename = secure_filename(file.filename)
    upload_folder = os.path.join('static', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    save_path = os.path.join(upload_folder, filename)

    file.save(save_path)

    # Store relative path in DB (uploads/filename)
    relative_path = os.path.join('uploads', filename)

    # Check submission existence
    cursor.execute("SELECT * FROM submissions WHERE student_id=%s AND assignment_id=%s",
                   (student_id, assignment_id))
    submission = cursor.fetchone()

    if submission:
        cursor.execute("UPDATE submissions SET file_path=%s, submitted_at=NOW() WHERE student_id=%s AND assignment_id=%s",
                       (relative_path, student_id, assignment_id))
        flash('Assignment resubmitted successfully!', 'success')
    else:
        cursor.execute("INSERT INTO submissions (student_id, assignment_id, file_path, submitted_at) VALUES (%s, %s, %s, NOW())",
                       (student_id, assignment_id, relative_path))
        flash('Assignment submitted successfully!', 'success')

    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('student_view_assignments'))


#------assignment satus student
@app.route('/student/view_submission_status')
def view_submission_status():
    if 'username' in session and session['role'] == 'student':
        student_id = session['user_id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT a.title AS assignment_title,
                   s.name AS subject_name,
                   sub.status,
                   sub.marks,
                   sub.submitted_at,
                   sub.file_path
            FROM submissions sub
            JOIN assignments a ON sub.assignment_id = a.id
            JOIN subjects s ON a.subject_id = s.id
            WHERE sub.student_id = %s
            ORDER BY a.due_date DESC
        """, (student_id,))
        
        submissions = cursor.fetchall()
        cursor.close()

        return render_template('student_view_submission_status.html', submissions=submissions)
    else:
        flash("Please login first!", "warning")
        return redirect('/login')




# ------------------ Student Query Management Dashboard ------------------
@app.route('/student/query_management')
def student_query_management():
    """
    Landing page for student query management.
    Provides links to 'View Queries' and 'Raise New Query'.
    """
    if 'username' not in session or session['role'] != 'student':
        flash("Please login first!", "warning")
        return redirect('/login')

    return render_template('student_query_management.html')


# ------------------ View Submitted Queries ------------------
@app.route('/student/view_queries')
def student_view_queries():
    """
    Displays all queries submitted by the logged-in student.
    Shows subject, query, reply (if any), submission date, and status.
    """
    if 'username' not in session or session['role'] != 'student':
        flash("Please login first!", "warning")
        return redirect('/login')

    student_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT q.id, q.query_text, q.reply, q.created_at, s.name AS subject_name
        FROM queries q
        JOIN subjects s ON q.subject_id = s.id
        WHERE q.student_id = %s
        ORDER BY q.created_at DESC
    """, (student_id,))
    queries = cursor.fetchall()
    cursor.close()

    return render_template('student_view_queries.html', queries=queries)


# ------------------ Raise a New Query ------------------
@app.route('/student/raise_query', methods=['GET', 'POST'])
def student_raise_query():
    """
    Allows student to submit a new query.
    Validates input and assigns query to the teacher of the selected subject.
    """
    if 'username' not in session or session['role'] != 'student':
        flash("Please login first!", "warning")
        return redirect('/login')

    student_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        query_text = request.form.get('query_text', '').strip()

        if not subject_id:
            flash("Please select a subject!", "danger")
            return redirect('/student/raise_query')

        if not query_text:
            flash("Query text cannot be empty!", "danger")
            return redirect('/student/raise_query')

        # Get teacher for the subject
        cursor.execute("SELECT teacher_id FROM subjects WHERE id=%s", (subject_id,))
        teacher = cursor.fetchone()
        if not teacher:
            flash("Invalid subject selected!", "danger")
            return redirect('/student/raise_query')

        teacher_id = teacher['teacher_id']

        # Insert query into database
        cursor.execute("""
            INSERT INTO queries(student_id, teacher_id, subject_id, query_text)
            VALUES (%s, %s, %s, %s)
        """, (student_id, teacher_id, subject_id, query_text))
        mysql.connection.commit()
        cursor.close()

        flash("Query submitted successfully!", "success")
        return redirect('/student/view_queries')

    # GET request: fetch subjects the student has
    cursor.execute("""
        SELECT s.id, s.name
        FROM subjects s
        JOIN attendance a ON a.subject_id = s.id AND a.student_id=%s
        GROUP BY s.id
    """, (student_id,))
    subjects = cursor.fetchall()
    cursor.close()

    return render_template('student_raise_query.html', subjects=subjects)




##------stduent report


@app.route('/student/reports')
def student_reports():
    if 'username' not in session or session['role'] != 'student':
        flash("Please login first!", "warning")
        return redirect('/login')

    student_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # --- Attendance % per subject ---
    cursor.execute("""
        SELECT sub.name AS subject_name,
               ROUND(SUM(a.status='Present') / COUNT(*) * 100, 2) AS attendance_percent
        FROM attendance a
        JOIN subjects sub ON a.subject_id = sub.id
        WHERE a.student_id=%s
        GROUP BY a.subject_id
    """, (student_id,))
    attendance_rows = cursor.fetchall()
    attendance_data = {
        'labels': [r['subject_name'] for r in attendance_rows],
        'values': [r['attendance_percent'] for r in attendance_rows]
    }

    # --- Assignment submissions per subject ---
    cursor.execute("""
        SELECT sub.name AS subject_name,
               SUM(CASE WHEN s.status='Submitted' THEN 1 ELSE 0 END) AS submitted_count,
               COUNT(a.id) AS total_assignments
        FROM assignments a
        JOIN subjects sub ON a.subject_id = sub.id
        LEFT JOIN submissions s 
           ON a.id=s.assignment_id AND s.student_id=%s
        GROUP BY a.subject_id
    """, (student_id,))
    assignment_rows = cursor.fetchall()
    assignment_data = {
        'labels': [r['subject_name'] for r in assignment_rows],
        'values': [r['submitted_count'] for r in assignment_rows]
    }

    # --- Overall Attendance ---
    cursor.execute("""
        SELECT 
            SUM(a.status='Present') AS present,
            SUM(a.status='Absent') AS absent
        FROM attendance a
        WHERE a.student_id=%s
    """, (student_id,))
    overall = cursor.fetchone()
    overall_attendance = {'Present': overall['present'], 'Absent': overall['absent']}

    cursor.close()

    return render_template('student_reports.html',
                           attendance_data=attendance_data,
                           assignment_data=assignment_data,
                           overall_attendance=overall_attendance)




 
# ------------------- Admin Routes -------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return redirect('/login')
    
# ---------------- Teacher Dashboard ----------------
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'username' not in session or session['role'] != 'teacher':
        flash('Please login first!', 'warning')
        return redirect('/login')
    return render_template('teacher_dashboard.html')

#---logout---


# ------------------- Mark Attendance -------------------
@app.route('/teacher/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'username' not in session or session['role'] != 'teacher':
        flash('Please login first!', 'warning')
        return redirect('/login')

    teacher_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get teacher's subjects
    cursor.execute("SELECT id, name FROM subjects WHERE teacher_id=%s", (teacher_id,))
    subjects = cursor.fetchall()

    # Get students list
    cursor.execute("SELECT id, name FROM users WHERE role='student'")
    students = cursor.fetchall()

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        date_selected = request.form['date']

        for s in students:
            sid = s['id']
            status = request.form.get(f'status_{sid}', 'Absent')
            cursor.execute("SELECT * FROM attendance WHERE student_id=%s AND subject_id=%s AND date=%s",
                           (sid, subject_id, date_selected))
            record = cursor.fetchone()
            if record:
                cursor.execute("UPDATE attendance SET status=%s WHERE id=%s", (status, record['id']))
            else:
                cursor.execute("INSERT INTO attendance(student_id, subject_id, date, status) VALUES (%s,%s,%s,%s)",
                               (sid, subject_id, date_selected, status))
        mysql.connection.commit()
        cursor.close()
        flash("Attendance saved successfully!", "success")
        return redirect('/teacher/mark_attendance')

    today = date.today().strftime('%Y-%m-%d')  # ✅ fixed line
    cursor.close()
    return render_template('teacher_mark_attendance.html', subjects=subjects, students=students, today=today)



# ------------------ View Attendance ------------------
# ------------------ View Attendance ------------------

@app.route('/teacher/view_attendance')
def view_teacher_attendance():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    show_all = request.args.get('show_all')

    # Default filter behavior
    if show_all:
        start_date = date(1, 1, 1)
        end_date = date(9999, 12, 31)
    elif not start_date_str or not end_date_str:
        start_date = end_date = date.today()
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM subjects WHERE teacher_id=%s", (teacher_id,))
    subjects = cursor.fetchall()

    attendance_data = {}
    for subj in subjects:
        cursor.execute("""
            SELECT a.date, u.name AS student_name, a.status
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            WHERE a.subject_id=%s AND a.date BETWEEN %s AND %s
            ORDER BY a.date DESC, u.name ASC
        """, (subj['id'], start_date, end_date))
        records = cursor.fetchall()
        # Ensure we always return a list even if no records found
        attendance_data[subj['name']] = records if records else []

    cursor.close()

    return render_template('teacher_view_attendance.html',
                           attendance_data=attendance_data,
                           request=request)



# ------------------ Download Attendance CSV ------------------
@app.route('/teacher/download_attendance/<subject_name>')
def download_attendance(subject_name):
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    show_all = request.args.get('show_all')

    # Default filter
    if show_all:
        start_date = date(1, 1, 1)
        end_date = date(9999, 12, 31)
    elif not start_date_str or not end_date_str:
        start_date = end_date = date.today()
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get subject ID
    cursor.execute("SELECT id FROM subjects WHERE teacher_id=%s AND name=%s",
                   (teacher_id, subject_name))
    subj = cursor.fetchone()

    if not subj:
        flash("Subject not found!", "danger")
        return redirect('/teacher/view_attendance')

    subject_id = subj['id']

    # Fetch all students
    cursor.execute("SELECT id, name FROM users WHERE role='student'")
    students = cursor.fetchall()

    # Generate list of dates in the range
    delta = (end_date - start_date).days
    date_list = [start_date + timedelta(days=i) for i in range(delta + 1)]

    # Fetch all attendance for the subject in range
    cursor.execute("""
        SELECT student_id, date, status
        FROM attendance
        WHERE subject_id=%s AND date BETWEEN %s AND %s
    """, (subject_id, start_date, end_date))
    attendance_records = cursor.fetchall()
    cursor.close()

    # Convert attendance_records to dict for lookup
    attendance_dict = {(r['student_id'], r['date']): r['status'] for r in attendance_records}

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student Name', 'Status'])

    for d in date_list:
        for s in students:
            status = attendance_dict.get((s['id'], d), 'Absent')
            writer.writerow([d.strftime('%Y-%m-%d'), s['name'], status])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{subject_name}_attendance.csv"
    )





#----edit attendance



# ------------------ Edit Attendance: list dates for a subject ------------------

# ------------------ Edit attendance for a specific subject + date ------------------


@app.route('/teacher/edit_attendance/<subject_name>', methods=['GET', 'POST'])
def edit_teacher_attendance(subject_name):
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    show_all = request.args.get('show_all')

    # Default filter behavior
    if show_all:
        start_date = date(1, 1, 1)
        end_date = date(9999, 12, 31)
    elif not start_date_str or not end_date_str:
        start_date = end_date = date.today()
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash("Invalid date range! Showing today's attendance instead.", "warning")
            start_date = end_date = date.today()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get subject ID
    cursor.execute("SELECT id FROM subjects WHERE teacher_id=%s AND name=%s", (teacher_id, subject_name))
    subj = cursor.fetchone()
    if not subj:
        flash("Subject not found!", "danger")
        return redirect('/teacher/view_attendance')
    subject_id = subj['id']

    if request.method == 'POST':
        # Update attendance
        for key, value in request.form.items():
            # key pattern: status_studentid_date
            if key.startswith('status_'):
                _, student_id, att_date = key.split('_')
                cursor.execute("""
                    UPDATE attendance
                    SET status=%s
                    WHERE student_id=%s AND subject_id=%s AND date=%s
                """, (value, student_id, subject_id, att_date))
        mysql.connection.commit()
        flash("Attendance updated successfully!", "success")
        return redirect(request.url)

    # Fetch attendance data
    cursor.execute("""
        SELECT a.date, u.id AS student_id, u.name AS student_name, a.status
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        WHERE a.subject_id=%s AND a.date BETWEEN %s AND %s
        ORDER BY a.date DESC, u.name ASC
    """, (subject_id, start_date, end_date))
    attendance_data = cursor.fetchall()
    cursor.close()

    return render_template('teacher_edit_attendance.html',
                           attendance_data=attendance_data,
                           subject_name=subject_name,
                           request=request)







# ------------------- View Assignments (Teacher) -------------------
@app.route('/teacher/view_assignments')
def view_assignments():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch assignments created by this teacher
    cursor.execute("""
        SELECT a.id, a.title, a.description, a.due_date, a.file_path,
               s.name AS subject_name
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        WHERE s.teacher_id=%s
        ORDER BY s.name, a.due_date ASC
    """, (teacher_id,))

    assignments = cursor.fetchall()
    cursor.close()

    return render_template('teacher_view_assignments.html', assignments=assignments)


# ------------------- Edit Assignment -------------------
@app.route('/teacher/edit_assignment/<assignment_id>', methods=['GET', 'POST'])
def edit_assignment(assignment_id):
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM assignments WHERE id=%s", (assignment_id,))
    assignment = cursor.fetchone()
    if not assignment:
        flash("Assignment not found!", "danger")
        return redirect('/teacher/view_assignments')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        cursor.execute("""
            UPDATE assignments SET title=%s, description=%s, due_date=%s
            WHERE id=%s
        """, (title, description, due_date, assignment_id))
        mysql.connection.commit()
        cursor.close()
        flash("Assignment updated successfully!", "success")
        return redirect('/teacher/view_assignments')

    cursor.close()
    return render_template('teacher_edit_assignment.html', assignment=assignment)


# ------------------- Delete Assignment -------------------
@app.route('/teacher/delete_assignment/<assignment_id>')
def delete_assignment(assignment_id):
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM assignments WHERE id=%s", (assignment_id,))
    mysql.connection.commit()
    cursor.close()
    flash("Assignment deleted successfully!", "success")
    return redirect('/teacher/view_assignments')





# ------------------- View Submissions (Teacher) -------------------

# ------------------- View Submissions (Teacher) -------------------
@app.route('/teacher/view_submissions')
def view_submissions():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get all assignments of this teacher
    cursor.execute("""
        SELECT a.id as assignment_id, a.title, a.subject_id, s.name as subject_name
        FROM assignments a
        JOIN subjects s ON a.subject_id = s.id
        WHERE s.teacher_id = %s
        ORDER BY a.due_date DESC
    """, (teacher_id,))
    assignments = cursor.fetchall()

    submissions_data = {}

    for assignment in assignments:
        assignment_id = assignment['assignment_id']

        # Left join students with submissions for this assignment
        cursor.execute("""
            SELECT u.id as student_id, u.name as student_name,
                   sub.file_path, sub.submitted_at, sub.status, sub.marks
            FROM users u
            LEFT JOIN submissions sub
            ON sub.student_id = u.id AND sub.assignment_id = %s
            WHERE u.role = 'student'
        """, (assignment_id,))
        students_submissions = cursor.fetchall()

        rows = []
        for s in students_submissions:
            file_link = url_for('static', filename=s['file_path'].replace("\\", "/")) if s['file_path'] else '-'
            row = {
                'student_name': s['student_name'],
                'file_path': file_link,
                'submitted_at': s['submitted_at'] if s['submitted_at'] else '-',
                'status': s['status'] if s['status'] else 'Pending',
                'marks': s['marks'] if s['marks'] is not None else '-'
            }
            rows.append(row)

        submissions_data[assignment['title']] = {
            'subject_name': assignment['subject_name'],
            'rows': rows
        }

    cursor.close()
    return render_template('teacher_view_submissions.html', submissions_data=submissions_data)


# ------------------- Update Submission Status / Marks -------------------
@app.route('/teacher/update_submission', methods=['POST'])
def update_submission():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    assignment_title = request.form['assignment_id']
    student_name = request.form['student_id']
    status = request.form['status']
    marks = request.form['marks']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get assignment_id from title
    cursor.execute("SELECT id FROM assignments WHERE title=%s", (assignment_title,))
    assignment = cursor.fetchone()
    if not assignment:
        flash("Assignment not found!", "danger")
        return redirect('/teacher/view_submissions')
    assignment_id = assignment['id']

    # Get student_id from name
    cursor.execute("SELECT id FROM users WHERE name=%s", (student_name,))
    student = cursor.fetchone()
    if not student:
        flash("Student not found!", "danger")
        return redirect('/teacher/view_submissions')
    student_id = student['id']

    # Check if submission exists
    cursor.execute("SELECT * FROM submissions WHERE assignment_id=%s AND student_id=%s",
                   (assignment_id, student_id))
    submission = cursor.fetchone()

    if submission:
        # Update existing submission
        cursor.execute("""
            UPDATE submissions
            SET status=%s, marks=%s
            WHERE assignment_id=%s AND student_id=%s
        """, (status, marks, assignment_id, student_id))
    else:
        # Insert a new record if it doesn't exist
        cursor.execute("""
            INSERT INTO submissions (assignment_id, student_id, status, marks)
            VALUES (%s, %s, %s, %s)
        """, (assignment_id, student_id, status, marks))

    mysql.connection.commit()
    cursor.close()
    flash("Submission updated successfully!", "success")
    return redirect('/teacher/view_submissions')

#--teacher view queries


@app.route('/teacher/view_queries')
def teacher_view_queries():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT q.id, q.query_text, q.reply, q.created_at,
               u.name AS student_name, s.name AS subject_name
        FROM queries q
        JOIN users u ON q.student_id = u.id
        JOIN subjects s ON q.subject_id = s.id
        WHERE q.teacher_id = %s
        ORDER BY q.created_at DESC
    """, (teacher_id,))
    queries = cursor.fetchall()
    cursor.close()
    return render_template('teacher_view_queries.html', queries=queries)


@app.route('/teacher/reply_query', methods=['POST'])
def teacher_reply_query():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    query_id = request.form['query_id']
    reply_text = request.form['reply']

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE queries SET reply=%s WHERE id=%s", (reply_text, query_id))
    mysql.connection.commit()
    cursor.close()
    flash("Reply updated successfully!", "success")
    return redirect('/teacher/view_queries')




#-------reportas and analytics teacher



# ---------------------------------
# Teacher Reports & Analytics Route
# ---------------------------------
@app.route('/teacher/reports')
def teacher_reports():
    if 'username' not in session or session['role'] != 'teacher':
        flash("Please login first!", "warning")
        return redirect('/login')

    teacher_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Total students
    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='student'")
    total_students = cursor.fetchone()['total']

    # Total assignments per subject
    cursor.execute("""
        SELECT s.name AS subject_name, COUNT(a.id) AS total_assignments
        FROM subjects s
        LEFT JOIN assignments a ON s.id = a.subject_id
        WHERE s.teacher_id=%s
        GROUP BY s.id
    """, (teacher_id,))
    assignment_rows = cursor.fetchall()
    assignment_data = {
        'labels': [row['subject_name'] for row in assignment_rows],
        'values': [row['total_assignments'] for row in assignment_rows]
    }
    total_assignments = sum(assignment_data['values'])

    # Attendance % per subject
    cursor.execute("""
        SELECT s.name AS subject_name,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_count,
               COUNT(a.id) AS total_count
        FROM subjects s
        LEFT JOIN attendance a ON s.id = a.subject_id
        WHERE s.teacher_id=%s
        GROUP BY s.id
    """, (teacher_id,))
    attendance_rows = cursor.fetchall()
    attendance_data = {
        'labels': [row['subject_name'] for row in attendance_rows],
        'values': [round((row['present_count'] / row['total_count'] * 100) if row['total_count'] else 0, 2) for row in attendance_rows]
    }
    avg_attendance = round(sum(attendance_data['values']) / len(attendance_data['values']), 2) if attendance_data['values'] else 0

    # Overall class attendance pie
    cursor.execute("""
        SELECT status, COUNT(*) AS count
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE s.teacher_id=%s
        GROUP BY status
    """, (teacher_id,))
    overall_rows = cursor.fetchall()
    overall_attendance = {row['status']: row['count'] for row in overall_rows}

    cursor.close()
    return render_template(
        'teacher_reports.html',
        total_students=total_students,
        avg_attendance=avg_attendance,
        total_assignments=total_assignments,
        attendance_data=attendance_data,
        assignment_data=assignment_data,
        overall_attendance=overall_attendance
    )







# ---- Add Student ----
@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            student_id = request.form['id']
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            cursor = mysql.connection.cursor()
            try:
                cursor.execute("INSERT INTO users (id, username, password, role, name, email) VALUES (%s,%s,%s,'student',%s,%s)",
                               (student_id, username, password, name, email))
                mysql.connection.commit()
                flash(f"Student {name} added successfully!", "success")
            except:
                flash("Error: Could not add student (maybe ID/username exists)", "danger")
            cursor.close()
            return redirect('/admin/add_student')
        return render_template('admin_add_student.html')
    else:
        return redirect('/login')
    
# ---- Edit Student ----
@app.route('/admin/edit_student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE id=%s AND role='student'", (student_id,))
        student = cursor.fetchone()
        if not student:
            flash("Student not found!", "danger")
            return redirect('/admin/view_users')
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            try:
                cursor.execute("""UPDATE users SET username=%s, password=%s, name=%s, email=%s
                                  WHERE id=%s""", (username, password, name, email, student_id))
                mysql.connection.commit()
                flash(f"Student {name} updated successfully!", "success")
            except:
                flash("Error: Could not update student (maybe username exists)", "danger")
            return redirect('/admin/view_users')
        cursor.close()
        return render_template('admin_edit_student.html', student=student)
    else:
        return redirect('/login')


# ---- Add Teacher ----
@app.route('/admin/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            teacher_id = request.form['id']
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            cursor = mysql.connection.cursor()
            try:
                cursor.execute("INSERT INTO users (id, username, password, role, name, email) VALUES (%s,%s,%s,'teacher',%s,%s)",
                               (teacher_id, username, password, name, email))
                mysql.connection.commit()
                flash(f"Teacher {name} added successfully!", "success")
            except:
                flash("Error: Could not add teacher (maybe ID/username exists)", "danger")
            cursor.close()
            return redirect('/admin/add_teacher')
        return render_template('admin_add_teacher.html')
    else:
        return redirect('/login')
    
# ---- Edit Teacher ----
@app.route('/admin/edit_teacher/<teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE id=%s AND role='teacher'", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            flash("Teacher not found!", "danger")
            return redirect('/admin/view_users')
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            try:
                cursor.execute("""UPDATE users SET username=%s, password=%s, name=%s, email=%s
                                  WHERE id=%s""", (username, password, name, email, teacher_id))
                mysql.connection.commit()
                flash(f"Teacher {name} updated successfully!", "success")
            except:
                flash("Error: Could not update teacher (maybe username exists)", "danger")
            return redirect('/admin/view_users')
        cursor.close()
        return render_template('admin_edit_teacher.html', teacher=teacher)
    else:
        return redirect('/login')


# ---- Add Subject ----
@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name FROM users WHERE role='teacher'")
        teachers = cursor.fetchall()
        if request.method == 'POST':
            subject_id = request.form['id']
            name = request.form['name']
            teacher_id = request.form['teacher_id']
            try:
                cursor.execute("INSERT INTO subjects (id, name, teacher_id) VALUES (%s,%s,%s)",
                               (subject_id, name, teacher_id))
                mysql.connection.commit()
                flash(f"Subject {name} added successfully!", "success")
            except:
                flash("Error: Could not add subject (maybe ID exists)", "danger")
            return redirect('/admin/add_subject')
        cursor.close()
        return render_template('admin_add_subject.html', teachers=teachers)
    else:
        return redirect('/login')
    
# ---- Edit Subject ----
@app.route('/admin/edit_subject/<subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM subjects WHERE id=%s", (subject_id,))
        subject = cursor.fetchone()
        if not subject:
            flash("Subject not found!", "danger")
            return redirect('/admin/view_subjects')
        cursor.execute("SELECT id, name FROM users WHERE role='teacher'")
        teachers = cursor.fetchall()
        if request.method == 'POST':
            name = request.form['name']
            teacher_id = request.form['teacher_id']
            try:
                cursor.execute("UPDATE subjects SET name=%s, teacher_id=%s WHERE id=%s", (name, teacher_id, subject_id))
                mysql.connection.commit()
                flash(f"Subject {name} updated successfully!", "success")
            except:
                flash("Error: Could not update subject (maybe ID exists)", "danger")
            return redirect('/admin/view_subjects')
        cursor.close()
        return render_template('admin_edit_subject.html', subject=subject, teachers=teachers)
    else:
        return redirect('/login')


# ---- Delete User ----
@app.route('/admin/delete_user', methods=['GET', 'POST'])
def delete_user():
    if 'username' in session and session['role'] == 'admin':
        if request.method == 'POST':
            role = request.form['role']
            user_id = request.form['id']
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE id=%s AND role=%s", (user_id, role))
            user = cursor.fetchone()
            if user:
                cursor.execute("DELETE FROM users WHERE id=%s AND role=%s", (user_id, role))
                mysql.connection.commit()
                flash(f"{role.capitalize()} {user['username']} deleted successfully!", "success")
            else:
                flash("User not found!", "danger")
            cursor.close()
            return redirect('/admin/delete_user')
        return render_template('admin_delete_user.html')
    else:
        return redirect('/login')

# ---- View Users ----
@app.route('/admin/view_users')
def view_users():
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        return render_template('admin_view_users.html', users=users)
    else:
        return redirect('/login')
    
# ---- Delete User Direct ----
@app.route('/admin/delete_user_direct/<role>/<user_id>')
def delete_user_direct(role, user_id):
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE id=%s AND role=%s", (user_id, role))
        user = cursor.fetchone()
        if user:
            cursor.execute("DELETE FROM users WHERE id=%s AND role=%s", (user_id, role))
            mysql.connection.commit()
            flash(f"{role.capitalize()} {user['username']} deleted successfully!", "success")
        else:
            flash("User not found!", "danger")
        cursor.close()
        return redirect('/admin/view_users')
    else:
        return redirect('/login')


# ---- View Subjects ----
@app.route('/admin/view_subjects')
def view_subjects():
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT subjects.id, subjects.name, users.name AS teacher_name
            FROM subjects
            LEFT JOIN users ON subjects.teacher_id = users.id
        """)
        subjects = cursor.fetchall()
        cursor.close()
        return render_template('admin_view_subjects.html', subjects=subjects)
    else:
        return redirect('/login')
# ---- Delete Subject ----
@app.route('/admin/delete_subject/<subject_id>')
def delete_subject(subject_id):
    if 'username' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM subjects WHERE id=%s", (subject_id,))
        subject = cursor.fetchone()
        if subject:
            cursor.execute("DELETE FROM subjects WHERE id=%s", (subject_id,))
            mysql.connection.commit()
            flash(f"Subject {subject['name']} deleted successfully!", "success")
        else:
            flash("Subject not found!", "danger")
        cursor.close()
        return redirect('/admin/view_subjects')
    else:
        return redirect('/login')




#-------reports to admin

# ----- Admin Reports & Analytics -----
@app.route('/admin/reports')
def admin_reports():
    if 'username' not in session or session['role'] != 'admin':
        flash("Please login first!", "warning")
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. Gettt all subjectss
    cursor.execute("SELECT id, name FROM subjects")
    subjects = cursor.fetchall()

    # 2. Attendance % per subject
    attendance_labels = []
    attendance_values = []
    for sub in subjects:
        cursor.execute("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_count
            FROM attendance
            WHERE subject_id=%s
        """, (sub['id'],))
        result = cursor.fetchone()
        total = result['total'] or 0
        present = result['present_count'] or 0
        percent = round((present / total) * 100, 2) if total > 0 else 0
        attendance_labels.append(sub['name'])
        attendance_values.append(percent)

    attendance_data = {"labels": attendance_labels, "values": attendance_values}

    # 3. Assignment submissions count per subject
    assignment_labels = []
    assignment_values = []
    for sub in subjects:
        cursor.execute("""
            SELECT COUNT(s.id) AS submissions_count
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE a.subject_id=%s
        """, (sub['id'],))
        result = cursor.fetchone()
        count = result['submissions_count'] or 0
        assignment_labels.append(sub['name'])
        assignment_values.append(count)

    assignment_data = {"labels": assignment_labels, "values": assignment_values}

    # 4. Overall attendance (pie chart)     
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_count,
            SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) AS absent_count
        FROM attendance
    """)
    result = cursor.fetchone()
    overall_attendance = {
        "Present": result['present_count'] or 0,
        "Absent": result['absent_count'] or 0
    }

    cursor.close()
    return render_template(
        'admin_reports.html',
        attendance_data=attendance_data,
        assignment_data=assignment_data,
        overall_attendance=overall_attendance
    )




#-------make sure this is always at end   !!!!

if __name__ == "__main__":
    app.run(debug=True)
