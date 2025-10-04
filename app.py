from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, TextAreaField, validators
import mysql.connector
import json
import datetime
import requests
import base64
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Judge0 API configuration
JUDGE0_API_URL = os.getenv('JUDGE0_API_URL')
JUDGE0_API_KEY = os.getenv('JUDGE0_API_KEY')

# Language ID mapping for Judge0
LANGUAGE_IDS = {
    "python": 71,  # Python 3
    "java": 62,    # Java 13
    "cpp": 54,     # C++ 17
    "c": 50,       # C (GCC 9.2.0)
    "javascript": 63,  # JavaScript Node.js
    "csharp": 51,  # C# Mono
}

def submit_to_judge0(source_code, language_id, stdin=""):
    payload = {
        "source_code": source_code,  # Remove base64.b64encode()!
        "language_id": language_id,
        "stdin": stdin,  # Remove base64 encoding here too
        "cpu_time_limit": 5,
        "memory_limit": 256000
    }
    
    headers = {
        "X-RapidAPI-Key": JUDGE0_API_KEY,
        "X-RapidAPI-Host": os.getenv('JUDGE0_API_HOST'),
        "Content-Type": "application/json"
    }

    
    # Submit the code
    try:
        response = requests.post(
            f"{JUDGE0_API_URL}/submissions", 
            json=payload, 
            headers=headers
        )
        response.raise_for_status()
        submission = response.json()
        token = submission.get("token")
        
        if not token:
            return {"error": "Failed to submit code for execution"}
        
        # Get the submission result (with a small delay to allow processing)
        import time
        time.sleep(1)  # Wait for 1 second
        
        result_response = requests.get(
            f"{JUDGE0_API_URL}/submissions/{token}",
            headers=headers,
            params={"base64_encoded": "true", "fields": "*"}
        )
        result_response.raise_for_status()
        result = result_response.json()
        
        # Process and return the result
        processed_result = process_judge0_result(result)
        return processed_result
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Judge0 API Error: {str(e)}"}

def process_judge0_result(result):
    """Process the Judge0 API result"""
    # Status codes: https://github.com/judge0/judge0/blob/master/docs/api/submissions.md#submission-status
    status_map = {
        1: "In Queue",
        2: "Processing",
        3: "Accepted",
        4: "Wrong Answer",
        5: "Time Limit Exceeded",
        6: "Compilation Error",
        7: "Runtime Error (SIGSEGV)",
        8: "Runtime Error (SIGXFSZ)",
        9: "Runtime Error (SIGFPE)",
        10: "Runtime Error (SIGABRT)",
        11: "Runtime Error (NZEC)",
        12: "Runtime Error (Other)",
        13: "Internal Error",
        14: "Exec Format Error"
    }
    
    status_id = result.get("status", {}).get("id")
    status_description = status_map.get(status_id, "Unknown Status")
    
    # Decode outputs if they exist and are base64 encoded
    stdout = result.get("stdout")
    if stdout:
        stdout = base64.b64decode(stdout).decode('utf-8', errors='replace')
    else:
        stdout = ""
        
    stderr = result.get("stderr")
    if stderr:
        stderr = base64.b64decode(stderr).decode('utf-8', errors='replace')
    else:
        stderr = ""
        
    compile_output = result.get("compile_output")
    if compile_output:
        compile_output = base64.b64decode(compile_output).decode('utf-8', errors='replace')
    else:
        compile_output = ""
    
    # Time and memory usage
    time = result.get("time", "0")
    memory = result.get("memory", "0")
    
    return {
        "status": status_description,
        "status_id": status_id,
        "stdout": stdout,
        "stderr": stderr,
        "compile_output": compile_output,
        "time": time,
        "memory": memory,
        "success": status_id == 3  # Status 3 is "Accepted"
    }

app = Flask(__name__)

bcrypt = Bcrypt(app)

# Secret key for session management
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Change this to a secure key

# Function to get a database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/studenthome')
def home2():
    return render_template('home2.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    
    if request.method == 'POST':
        email = request.form['studentEmail']
        password = request.form['studentPassword']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for better readability

        cursor.execute("SELECT * FROM Users WHERE Email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['Password'], password):  # Assuming 'Password' is the correct column name
            if user['Role'] == 'Student':  # Ensure role is 'Student'
                session['loggedin'] = True
                session['id'] = user['UserID']
                session['email'] = user['Email']
                session['role'] = user['Role']
               

                flash("Login successful!", "success")
                return redirect(url_for('home2'))  # Redirect to home after login
            else:
                flash("You are not registered as a student.", "danger")

        else:
            flash("Invalid email or password", "danger")

    return render_template('SL.html')  # Return login page on GET request or failed login



#temporary
@app.route('/debug-questions')
def debug_questions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM aptitude_test LIMIT 5")
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(questions)

#eoftemp

@app.route('/student-at')
def student_at():
    if 'loggedin' not in session or session.get('role') != 'Student':
        flash("Please login as student first", "danger")
        return redirect(url_for('student_login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get 10 random questions with formatted dates
        cursor.execute("""
            SELECT qn_id, qn_text, options, corr_opt,
                   DATE_FORMAT(test_date, '%Y-%m-%d') AS test_date 
            FROM aptitude_test 
            ORDER BY RAND() LIMIT 10
        """)
        questions = cursor.fetchall()
        
        # Convert options JSON to dict
        for q in questions:
            q['options'] = json.loads(q['options'])
        
        return render_template('AT.html', questions=questions)
    
    finally:
        cursor.close()
        conn.close()

@app.route('/student-cc')
def student_cc():
    return render_template('CC.html')

@app.route('/student-pd')
def student_pd():
    return render_template('progdash.html')

@app.route('/api/student/progress')
def get_student_progress():
    if 'id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session['id']
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Initialize response
        response = {
            "aptitude": {"latestScore": 0, "history": [], "dates": []},
            "mockInterview": {"latestScore": 0, "history": [], "dates": []},
            "codingChallenge": {"latestScore": 0, "history": [], "dates": []}
        }
        
        # Fixed Aptitude Query
        try:
            cursor.execute("""
                SELECT 
                    DATE(response_date) as test_date,
                    AVG(score*100) as avg_score
                FROM responses
                WHERE UserID = %s
                GROUP BY test_date
                ORDER BY test_date ASC
            """, (user_id,))
            
            aptitude_results = cursor.fetchall()
            if aptitude_results:
                response["aptitude"]["history"] = [
                    float(result['avg_score']) if result['avg_score'] is not None else 0 
                    for result in aptitude_results
                ]
                response["aptitude"]["dates"] = [
                    result['test_date'].strftime('%Y-%m-%d') 
                    if hasattr(result['test_date'], 'strftime')
                    else str(result['test_date']) 
                    for result in aptitude_results
                ]
                
                cursor.execute("SELECT AVG(score*100) as latest_score FROM responses WHERE UserID = %s", (user_id,))
                latest_aptitude = cursor.fetchone()
                if latest_aptitude and latest_aptitude['latest_score'] is not None:
                    response["aptitude"]["latestScore"] = round(float(latest_aptitude['latest_score']), 1)
        except Exception as e:
            print(f"Aptitude query error: {e}")
            # Keep default values if error occurs
        
        # Get mock interview ratings with null checks
        try:
            cursor.execute("""
                SELECT rating, DATE(interview_date) as interview_date
                FROM mock_interviews
                WHERE user_id = %s AND rating IS NOT NULL
                ORDER BY interview_date ASC
            """, (user_id,))
            
            interview_results = cursor.fetchall()
            if interview_results:
                response["mockInterview"]["history"] = [float(result['rating']) * 20 if result['rating'] is not None else 0
                                                      for result in interview_results]
                response["mockInterview"]["dates"] = [result['interview_date'].strftime('%Y-%m-%d') if hasattr(result['interview_date'], 'strftime')
                                                    else str(result['interview_date'])
                                                    for result in interview_results]
                
                cursor.execute("""
                    SELECT AVG(rating) as latest_score
                    FROM mock_interviews
                    WHERE user_id = %s AND rating IS NOT NULL
                """, (user_id,))
                latest_interview = cursor.fetchone()
                if latest_interview and latest_interview['latest_score'] is not None:
                    response["mockInterview"]["latestScore"] = round(float(latest_interview['latest_score']) * 20, 1)
        except Exception as e:
            print(f"Mock interview query error: {e}")
            # Keep default values if error occurs
        
        # Get coding challenge success rate with null checks
        try:
            cursor.execute("""
                SELECT 
                    DATE(submission_time) as submission_date,
                    (SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100 as success_rate
                FROM coding_submissions
                WHERE user_id = %s
                GROUP BY DATE(submission_time)
                ORDER BY submission_date ASC
            """, (user_id,))
            
            coding_results = cursor.fetchall()
            if coding_results:
                response["codingChallenge"]["history"] = [float(result['success_rate']) if result['success_rate'] is not None else 0
                                                        for result in coding_results]
                response["codingChallenge"]["dates"] = [result['submission_date'].strftime('%Y-%m-%d') if hasattr(result['submission_date'], 'strftime')
                                                      else str(result['submission_date'])
                                                      for result in coding_results]
                
                cursor.execute("""
                    SELECT 
                        (SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100 as overall_success_rate
                    FROM coding_submissions
                    WHERE user_id = %s
                """, (user_id,))
                coding_overall = cursor.fetchone()
                if coding_overall and coding_overall['overall_success_rate'] is not None:
                    response["codingChallenge"]["latestScore"] = round(float(coding_overall['overall_success_rate']), 1)
        except Exception as e:
            print(f"Coding challenge query error: {e}")
            # Keep default values if error occurs
        
        # Check if any data was found
        data_found = (
            response["aptitude"]["latestScore"] is not None or 
            response["mockInterview"]["latestScore"] is not None or
            response["codingChallenge"]["latestScore"] is not None
        )
        
        if not data_found:
            print("No data found for user ID:", user_id)
        
        cursor.close()
        conn.close()
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({
            "error": "Failed to fetch progress data",
            "details": str(e)
        }), 500


@app.route('/student-ai')
def student_ai():
    return render_template('AI.html')

@app.route('/student-qna')
def student_qna():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT q.id, q.question_text, q.created_at, u.Name AS student_name,
               COALESCE(a.answer_text, '') AS answer_text, a.created_at AS answer_date, ua.Name AS alumni_name
        FROM questions q
        JOIN Users u ON q.user_id = u.UserID
        LEFT JOIN answers a ON q.id = a.question_id
        LEFT JOIN Users ua ON a.user_id = ua.UserID
        ORDER BY q.created_at DESC
    """)
    
    qna_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('Q&A.html', qna=qna_data)


@app.route('/ask-question', methods=['POST'])
def ask_question():
    if 'loggedin' not in session or session.get('role') != 'Student':
        flash("Only students can ask questions.", "danger")
        return redirect(url_for('student_qna'))

    question_text = request.form.get('question')
    if not question_text:
        flash("Question cannot be empty.", "danger")
        return redirect(url_for('student_qna'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO questions (user_id, question_text) VALUES (%s, %s)", 
                   (session['id'], question_text))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Your question has been posted!", "success")
    return redirect(url_for('student_qna'))
@app.route('/answer-question/<int:question_id>', methods=['POST'])
def answer_question(question_id):
    if 'loggedin' not in session or session.get('role') != 'Alumni':
        flash("Only alumni can answer questions.", "danger")
        return redirect(url_for('alumni_qna'))

    answer_text = request.form.get('answer')
    if not answer_text:
        flash("Answer cannot be empty.", "danger")
        return redirect(url_for('alumni_qna'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO answers (question_id, user_id, answer_text) VALUES (%s, %s, %s)", 
                       (question_id, session['id'], answer_text))
        conn.commit()
        flash("Your answer has been posted!", "success")
    except mysql.connector.Error as e:
        flash(f"Database Error: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('alumni_qna'))

@app.route('/student-ad')
def student_ad():
    return render_template('AD.html')

@app.route('/get_alumni')
def get_alumni():
    try:
        # Connect using your existing get_db_connection() function
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Updated query to match your actual schema:
        # - Uses Users table which we know exists (from your register route)
        # - Matches the alumni table structure you showed
        query = """
        SELECT 
            u.UserID,
            u.Name as name,
            a.grad_year,
            a.company,
            a.designation,
            a.bio
        FROM alumni a
        JOIN Users u ON a.UserID = u.UserID
        ORDER BY a.grad_year DESC
        """
        
        cursor.execute(query)
        alumni_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Enhanced response with success flag
        return jsonify({
            "success": True,
            "data": alumni_data
        })
    
    except mysql.connector.Error as e:
        print(f"MySQL Error fetching alumni data: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}"
        }), 500
        
    except Exception as e:
        print(f"General Error fetching alumni data: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/alumni-login', methods=['GET', 'POST'])
def alumni_login():
    if request.method == 'POST':
        email = request.form['alumniEmail']
        password = request.form['alumniPassword']

        # Validate if email ends with '@rajagiri.edu.in'
        if not email.endswith('@rajagiri.edu.in'):
            flash("Alumni must use an email ending with @rajagiri.edu.in", "danger")
            return redirect(url_for('alumni_login'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Users WHERE Email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['Password'], password):  # Check password
            if user['Role'] == 'Alumni':  # Ensure it's an Alumni
                session['loggedin'] = True
                session['id'] = user['UserID']
                session['email'] = user['Email']
                session['role'] = user['Role']

                flash("Login successful!", "success")
                return redirect(url_for('home3'))  # Redirect to alumni dashboard
            else:
                flash("You are not registered as an Alumni.", "danger")
        else:
            flash("Invalid email or password", "danger")

    return render_template('AL.html')  # Render Alumni Login page

@app.route('/alumnihome')
def home3():
    if 'loggedin' in session and session.get('role') == 'Alumni':
        return render_template('home3.html')  # ✅ Ensure alumni get a dedicated homepage
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('alumni_login'))  # Redirect to login if not logged in


@app.route('/alumni-qna')
def alumni_qna():
    # This route needs to fetch the Q&A data just like the student_qna route
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT q.id, q.question_text, q.created_at, u.Name AS student_name,
               COALESCE(a.answer_text, '') AS answer_text, a.created_at AS answer_date, ua.Name AS alumni_name
        FROM questions q
        JOIN Users u ON q.user_id = u.UserID
        LEFT JOIN answers a ON q.id = a.question_id
        LEFT JOIN Users ua ON a.user_id = ua.UserID
        ORDER BY q.created_at DESC
    """)
    
    qna_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('alqna.html', qna=qna_data)  # Pass the data to the template

from flask import request, jsonify

@app.route('/admin/qna')
def admin_qna():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))
    return render_template('AdminQNA.html')

@app.route('/admin/get_qnas')
def admin_get_qnas():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', 'all')
        sort_order = request.args.get('sort', 'newest')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT q.id, q.question_text, q.created_at, 
                   u.Name as student_name, 
                   a.answer_text, a.created_at as answer_date,
                   ua.Name as alumni_name
            FROM questions q
            JOIN Users u ON q.user_id = u.UserID
            LEFT JOIN answers a ON q.id = a.question_id
            LEFT JOIN Users ua ON a.user_id = ua.UserID
            WHERE 1=1
        """

        params = []
        if search_query:
            query += " AND q.question_text LIKE %s"
            params.append(f"%{search_query}%")

        if status_filter == 'answered':
            query += " AND a.answer_text IS NOT NULL"
        elif status_filter == 'pending':
            query += " AND a.answer_text IS NULL"

        if sort_order == 'newest':
            query += " ORDER BY q.created_at DESC"
        else:
            query += " ORDER BY q.created_at ASC"

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Format dates for JSON serialization
        for item in results:
            if item['created_at']:
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if item.get('answer_date'):
                item['answer_date'] = item['answer_date'].strftime('%Y-%m-%d %H:%M:%S')

        cursor.close()
        conn.close()

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete_qa', methods=['POST'])
def admin_delete_qa():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        qa_id = request.form.get('qa_id')
        delete_type = request.form.get('type')  # 'question' or 'answer'

        if not qa_id or not delete_type:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if delete_type == 'question':
            # Delete the answer first to maintain referential integrity
            cursor.execute("DELETE FROM answers WHERE question_id = %s", (qa_id,))
            cursor.execute("DELETE FROM questions WHERE id = %s", (qa_id,))
        elif delete_type == 'answer':
            cursor.execute("DELETE FROM answers WHERE question_id = %s", (qa_id,))
        else:
            return jsonify({'success': False, 'error': 'Invalid delete type'}), 400

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/alumni-about')
def alumni_about():
    return render_template('ALabout.html')



@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['adminEmail']
        password = request.form['adminPassword']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Users WHERE Email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['Password'], password):  # Check password
            if user['Role'] == 'Admin':  # Ensure it's an Admin
                session['loggedin'] = True
                session['id'] = user['UserID']
                session['email'] = user['Email']
                session['role'] = user['Role']

                flash("Admin login successful!", "success")
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
            else:
                flash("You are not registered as an Admin.", "danger")
        else:
            flash("Invalid email or password", "danger")

    return render_template('ADL.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'loggedin' in session and session.get('role') == 'Admin':
        return render_template('ADC.html')  # Admin Dashboard
    #else:
     #   flash("Unauthorized access!", "danger")
    #    return redirect(url_for('admin_login')) 

@app.route('/admin-AT')
def admin_at():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('admin_login'))
    return render_template('AdminAT.html')  # Admin interface to add questions

@app.route('/add_question', methods=['POST'])
def admin_add_question():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        # Handle form data (not JSON)
        qn_text = request.form.get('question', '').strip()
        options = {
            'A': request.form.get('optionA', '').strip(),
            'B': request.form.get('optionB', '').strip(),
            'C': request.form.get('optionC', '').strip(),
            'D': request.form.get('optionD', '').strip()
        }
        corr_opt = request.form.get('correctOption', '').strip().upper()

        # Validation
        if not qn_text:
            return jsonify({"success": False, "error": "Question text is required"}), 400
        if not all(options.values()):
            return jsonify({"success": False, "error": "All options are required"}), 400
        if corr_opt not in ['A', 'B', 'C', 'D']:
            return jsonify({"success": False, "error": "Correct option must be A, B, C, or D"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO aptitude_test 
            (qn_text, options, corr_opt) 
            VALUES (%s, %s, %s)""",
            (qn_text, json.dumps(options), corr_opt)
        )
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Question added successfully",
            "qn_id": cursor.lastrowid
        })

    except Exception as e:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@app.route('/get_questions', methods=['GET'])
def admin_get_questions():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT qn_id, qn_text, options, corr_opt, 
                   DATE_FORMAT(test_date, '%Y-%m-%d %H:%i:%s') AS test_date 
            FROM aptitude_test 
            ORDER BY test_date DESC
        """)
        questions = cursor.fetchall()
        
        # Convert JSON options to dict
        for q in questions:
            q['options'] = json.loads(q['options'])
        
        return jsonify(questions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@app.route('/delete_question', methods=['POST'])
def admin_delete_question():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        qn_id = request.form.get('qn_id')
        if not qn_id:
            return jsonify({"error": "Question ID is required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete responses first to maintain referential integrity
        cursor.execute("DELETE FROM responses WHERE qn_id = %s", (qn_id,))
        # Then delete the question
        cursor.execute("DELETE FROM aptitude_test WHERE qn_id = %s", (qn_id,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"Question {qn_id} and its responses deleted"
        })
    except Exception as e:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# ----- Student Side -----


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'loggedin' not in session or session.get('role') != 'Student':
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        qn_id = request.form.get('qn_id')
        selected_option = request.form.get('selected_option', '').upper()
        user_id = session['id']

        if not qn_id or not selected_option:
            return jsonify({"success": False, "error": "Missing question ID or selected option"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get correct answer
        cursor.execute(
            "SELECT corr_opt FROM aptitude_test WHERE qn_id = %s", 
            (qn_id,)
        )
        question = cursor.fetchone()
        
        if not question:
            return jsonify({"success": False, "error": "Invalid question ID"}), 400

        is_correct = (selected_option == question['corr_opt'])
        score = 1 if is_correct else 0

        # Record response
        cursor.execute(
            """INSERT INTO responses 
            (UserID, qn_id, selected_option, score) 
            VALUES (%s, %s, %s, %s)""",
            (user_id, qn_id, selected_option, score)
        )
        conn.commit()
        
        return jsonify({
            "success": True,
            "is_correct": is_correct,  
            "correct_option": question['corr_opt'],
            "score": score
        })

    except Exception as e:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@app.route('/admin-CC')
def admin_cc():
    return render_template('AdminCC.html')

@app.route('/api/coding-challenges', methods=['GET'])
def get_challenges():
    if 'loggedin' not in session:
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, description, input_format, 
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at 
            FROM coding_challenges
            ORDER BY created_at DESC
        """)
        challenges = cursor.fetchall()
        
        return jsonify(challenges)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/coding-challenges', methods=['POST'])
def add_challenge():
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        input_format = request.form.get('inputFormat')
        expected_output = request.form.get('expectedOutput')
        
        # Validate required fields
        if not all([title, description, input_format, expected_output]):
            return jsonify({"error": "All fields are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert the new challenge
        cursor.execute("""
            INSERT INTO coding_challenges 
            (title, description, input_format, expected_output, created_at) 
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, input_format, expected_output, datetime.datetime.now()))
        
        conn.commit()
        challenge_id = cursor.lastrowid
        
        return jsonify({
            "success": True,
            "message": "Challenge added successfully",
            "id": challenge_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/coding-challenges/<int:challenge_id>', methods=['DELETE'])
def delete_challenge(challenge_id):
    if 'loggedin' not in session or session.get('role') != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete related submissions first (to maintain referential integrity)
        cursor.execute("DELETE FROM coding_submissions WHERE challenge_id = %s", (challenge_id,))
        
        # Then delete the challenge
        cursor.execute("DELETE FROM coding_challenges WHERE id = %s", (challenge_id,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"Challenge {challenge_id} deleted successfully"
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/get_challenges')
def get_challenges_alias():
    return student_get_challenges()

# Student routes for coding challenges
@app.route('/get_challenges')
def student_get_challenges():
    if 'loggedin' not in session or session.get('role') != 'Student':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, description, input_format
            FROM coding_challenges
            ORDER BY created_at DESC
        """)
        challenges = cursor.fetchall()
        
        return jsonify({"challenges": challenges})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Route to submit code (already exists)
@app.route('/submit_code', methods=['POST'])
def submit_code():
    if 'loggedin' not in session or session.get('role') != 'Student':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        data = request.json
        user_id = session['id']
        challenge_id = data.get('challenge_id')
        code = data.get('code')
        input_data = data.get('input', '')
        language = data.get('language', 'python')  # Default to Python
        
        if not all([challenge_id, code]):
            return jsonify({"error": "Missing required fields"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get expected output for evaluation
        cursor.execute("SELECT expected_output FROM coding_challenges WHERE id = %s", (challenge_id,))
        challenge = cursor.fetchone()
        
        if not challenge:
            return jsonify({"error": "Challenge not found"}), 404
        
        expected_output = challenge['expected_output']
        
        # Submit to Judge0
        language_id = LANGUAGE_IDS.get(language.lower())
        if not language_id:
            return jsonify({"error": f"Unsupported language: {language}"}), 400
        
        judge0_result = submit_to_judge0(code, language_id, input_data)
        
        # Check if output matches expected
        is_correct = False
        if judge0_result.get("status_id") == 3:  # If execution was successful
            user_output = judge0_result.get("stdout", "").strip()
            expected = expected_output.strip()
            is_correct = user_output == expected
        
        # Record submission in database
        status = "Correct" if is_correct else "Incorrect"
        if judge0_result.get("status_id") != 3:
            status = judge0_result.get("status", "Error")
            
        cursor.execute("""
            INSERT INTO coding_submissions 
            (user_id, challenge_id, submitted_code, input_data, output, expected_output, 
             submission_time, status, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, challenge_id, code, input_data, 
            judge0_result.get("stdout", ""), expected_output,
            datetime.datetime.now(), status, language
        ))
        
        conn.commit()
        
        # Prepare response
        response_data = {
            "success": True,
            "status": judge0_result.get("status"),
            "output": judge0_result.get("stdout", ""),
            "is_correct": is_correct,
            "execution_time": f"{judge0_result.get('time', '0')} seconds",
            "memory_used": f"{judge0_result.get('memory', '0')} KB"
        }
        
        if judge0_result.get("stderr"):
            response_data["error_output"] = judge0_result.get("stderr")
        if judge0_result.get("compile_output"):
            response_data["compile_output"] = judge0_result.get("compile_output")
            
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin-ProgressDash')
def admin_pd():
    return render_template('AdminPD.html')

@app.route('/student_MI')
def student_MI():
    if 'loggedin' not in session or session['role'] != 'Student':
        flash('Please login as a student to access this page')
        return redirect(url_for('home'))
    return render_template('MI.html')
    
class AlumniFeedbackForm(FlaskForm):
    meeting_id = SelectField('Interview Session', coerce=str, validators=[validators.InputRequired()])
    professional_presentation = IntegerField('Professional Presentation (1-5)', 
                                           validators=[validators.NumberRange(min=1, max=5), validators.InputRequired()])
    communication_skills = IntegerField('Communication Skills (1-5)', 
                                      validators=[validators.NumberRange(min=1, max=5), validators.InputRequired()])
    technical_competence = IntegerField('Technical Competence (1-5)', 
                                      validators=[validators.NumberRange(min=1, max=5), validators.InputRequired()])
    overall_rating = IntegerField('Overall Rating (1-5)', 
                                 validators=[validators.NumberRange(min=1, max=5), validators.InputRequired()])
    feedback_comments = TextAreaField('Feedback & Suggestions', 
                                    validators=[validators.InputRequired(), validators.Length(min=10)])

@app.route('/alumni_MI', methods=['GET', 'POST'])
def alumni_MI():
    if 'loggedin' not in session or session['role'] != 'Alumni':
        flash('Please login as an alumni to access this page', 'danger')
        return redirect(url_for('home'))

    form = AlumniFeedbackForm()
    
    # Get available interview sessions
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.meeting_id, m.interview_type, m.interview_date, u.Name as student_name
        FROM mock_interviews m
        JOIN Users u ON m.user_id = u.UserID
        WHERE m.alumni_id IS NULL OR m.alumni_id = %s
        ORDER BY m.interview_date DESC
    """, (session['id'],))
    interviews = cursor.fetchall()
    cursor.close()
    conn.close()

    # Populate meeting_id choices
    form.meeting_id.choices = [
        (interview['meeting_id'], 
         f"{interview['student_name']} - {interview['interview_type']} interview ({interview['interview_date'].strftime('%Y-%m-%d')})")
        for interview in interviews
    ]

    if form.validate_on_submit():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update the mock interview record
            cursor.execute("""
                UPDATE mock_interviews 
                SET professional_presentation = %s,
                    communication_skills = %s,
                    technical_competence = %s,
                    rating = %s,
                    feedback = %s,
                    alumni_id = %s,
                    reviewed_at = NOW()
                WHERE meeting_id = %s
            """, (
                form.professional_presentation.data,
                form.communication_skills.data,
                form.technical_competence.data,
                form.overall_rating.data,
                form.feedback_comments.data,
                session['id'],
                form.meeting_id.data
            ))
            
            conn.commit()
            flash('Feedback submitted successfully!', 'success')
            return redirect(url_for('alumni_MI'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error submitting feedback: {str(e)}', 'danger')
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    return render_template('AMI.html', form=form, interviews=interviews)


@app.route('/api/save_meeting_id', methods=['POST'])
def save_meeting_id():
    if 'loggedin' not in session or session['role'] != 'Alumni':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create a new mock interview record
        cursor.execute("""
            INSERT INTO mock_interviews 
            (meeting_id, alumni_id, interview_date, interview_type)
            VALUES (%s, %s, NOW(), 'general')
        """, (data['meeting_id'], session['id']))
        
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Meeting created'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/get_pending_interviews', methods=['GET'])
def get_pending_interviews():
    if 'loggedin' not in session or session['role'] != 'Alumni':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.meeting_id, m.interview_type, m.interview_date, u.Name as student_name
            FROM mock_interviews m
            JOIN Users u ON m.user_id = u.UserID
            WHERE (m.alumni_id IS NULL OR m.alumni_id = %s) AND m.rating IS NULL
            ORDER BY m.interview_date DESC
        """, (session['id'],))
        interviews = cursor.fetchall()
        return jsonify({'status': 'success', 'interviews': interviews})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/submit_alumni_rating', methods=['POST'])
def submit_alumni_rating():
    if 'loggedin' not in session or session['role'] != 'Alumni':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE mock_interviews 
            SET professional_presentation = %s,
                communication_skills = %s,
                technical_competence = %s,
                rating = %s,
                feedback = %s,
                alumni_id = %s,
                reviewed_at = NOW()
            WHERE meeting_id = %s
        """, (
            data['professional_presentation'],
            data['communication_skills'],
            data['technical_competence'],
            data['overall_rating'],
            data['feedback_comments'],
            session['id'],
            data['meeting_id']
        ))
        
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Feedback submitted successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/get_student_feedback/<meeting_id>', methods=['GET'])
def get_student_feedback(meeting_id):
    if 'loggedin' not in session or session['role'] != 'Alumni':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.interview_type, m.rating as student_rating, m.feedback as student_feedback
            FROM mock_interviews m
            WHERE m.meeting_id = %s
        """, (meeting_id,))
        interview = cursor.fetchone()
        
        if not interview:
            return jsonify({'error': 'Interview not found'}), 404
            
        return jsonify({
            'interview_type': interview['interview_type'],
            'student_rating': interview['student_rating'],
            'student_feedback': interview['student_feedback']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.route('/api/get_student_interviews', methods=['GET'])
def get_student_interviews():
    if 'loggedin' not in session or session['role'] != 'Student':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.meeting_id, m.interview_type, m.interview_date, u.Name as alumni_name
            FROM mock_interviews m
            LEFT JOIN Users u ON m.alumni_id = u.UserID
            WHERE m.user_id = %s OR (m.user_id IS NULL AND m.alumni_id IS NOT NULL)
            ORDER BY m.interview_date DESC
        """, (session['id'],))
        interviews = cursor.fetchall()
        return jsonify({'status': 'success', 'interviews': interviews})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/get_interview_details/<meeting_id>', methods=['GET'])
def get_interview_details(meeting_id):
    if 'loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT interview_type FROM mock_interviews 
            WHERE meeting_id = %s
        """, (meeting_id,))
        interview = cursor.fetchone()
        return jsonify(interview or {})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/submit_interview_feedback', methods=['POST'])
def submit_interview_feedback():
    if 'loggedin' not in session or session['role'] != 'Student':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update the mock interview record with student feedback
        cursor.execute("""
            UPDATE mock_interviews 
            SET user_id = %s,
                interview_type = %s,
                feedback = %s,
                rating = %s
            WHERE meeting_id = %s
        """, (
            data['user_id'],
            data['interview_type'],
            json.dumps({
                'experience': data['experience'],
                'challenges': data['challenges']
            }),
            data['rating'],
            data['meeting_id']
        ))
        
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Feedback submitted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

        
@app.route('/logout')
def logout():
    session.clear()  # Clear session for all user types
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))  # Redirect to the main page



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = None
        cursor = None

        try:
            # Extract form data
            name = request.form.get('name')
            email = request.form.get('email')
            password_raw = request.form.get('password')
            role = request.form.get('role')

            # Debugging: Print received data
            print("\n--- Received Registration Data ---")
            print(json.dumps(request.form.to_dict(), indent=4))

            # Ensure required fields are present
            if not all([name, email, password_raw, role]):
                flash("All fields are required.", "danger")
                return redirect(url_for('register'))

            conn = get_db_connection()
            cursor = conn.cursor()

            # 🔹 **Check if the email is already registered**
            cursor.execute("SELECT * FROM Users WHERE Email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("This email is already registered. Please use a different email.", "danger")
                return redirect(url_for('register'))  # Show error on registration page

            # 🔹 **Encrypt the password**
            password = bcrypt.generate_password_hash(password_raw).decode('utf-8')

            # 🔹 **Insert into Users table**
            cursor.execute("INSERT INTO Users (Name, Email, Password, Role) VALUES (%s, %s, %s, %s)", 
                           (name, email, password, role))
            conn.commit()
            user_id = cursor.lastrowid  # Get the new UserID

            # 🔹 **Insert into role-specific tables**
            if role == "Student":
                batch_year = request.form.get('batch_year')
                if not batch_year:
                    flash("Batch year is required for students.", "danger")
                    return redirect(url_for('register'))
                cursor.execute("INSERT INTO Student (UserID, student_id, batch_year) VALUES (%s, %s, %s)", 
                               (user_id, user_id, batch_year))

            elif role == "Alumni":
                grad_year = request.form.get('grad_year')
                company = request.form.get('company', '')
                designation = request.form.get('designation', '')
                bio = request.form.get('bio', '')
                if not grad_year:
                    flash("Graduation year is required for alumni.", "danger")
                    return redirect(url_for('register'))
                cursor.execute("INSERT INTO Alumni (UserID, alumni_id, grad_year, company, designation, bio) VALUES (%s, %s, %s, %s, %s, %s)", 
                               (user_id, user_id, grad_year, company, designation, bio))

            elif role == "Admin":
                position = request.form.get('position')
                if not position:
                    flash("Position is required for admins.", "danger")
                    return redirect(url_for('register'))
                cursor.execute("INSERT INTO Admin (UserID, admin_id, position) VALUES (%s, %s, %s)", 
                               (user_id, user_id, position))

            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('home'))  # Redirect to home after successful registration

        except mysql.connector.Error as e:
            print("\n--- MySQL Error ---")
            print(str(e))  # Print error in console
            flash(f"MySQL Error: {str(e)}", "danger")

        except Exception as e:
            print("\n--- General Error ---")
            print(str(e))  # Print error in console
            flash(f"An error occurred: {str(e)}", "danger")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('register.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

