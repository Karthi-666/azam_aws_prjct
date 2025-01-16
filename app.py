from flask import Flask, request, redirect, url_for, render_template,session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__, static_folder="static", template_folder="templates")
# Corrected __name__
app.secret_key = 'temporary_key'

# Example route to verify the app runs correctly
# Home Route (Landing Page)

# Define the upload folder (where files will be stored)
UPLOAD_FOLDER = os.path.join('static', 'files')
ALLOWED_EXTENSIONS = {'pdf'}  # Allow only PDF files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def get_db_connection():
    connection =  mysql.connector.connect(
        host="localhost",
        user="root",
        password="Karthi000!0",
        database="virtualclassroom"
    )
    if connection.is_connected():
        print('Successfully Connected to MySQL database')
        return connection
    else:
        print('Failed to connect to MySQL database')
        return None

@app.route('/')
def home():
    return render_template('home.html')

#Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password,method='sha256')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

#Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate user credentials
        user = validate_user(username)
        if not user:
            return 'User not found', 404
        
        if check_password_hash(user['password_hash'], password):
            session['user'] = username
            session['role'] = update_and_get_user_role(username)
            return redirect(url_for('home'))
        else:
            return 'Invalid credentials', 401

    return render_template('login.html')


def validate_user(username):
    """Fetch user details from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return {'password_hash': result[0]} if result else None


def update_and_get_user_role(username):
    """Update role for admin and retrieve the user's role."""
    conn = get_db_connection()
    
    # Use separate cursors for each query to avoid unread results.
    cursor_update = conn.cursor()
    if username == "admin":
        cursor_update.execute("UPDATE users SET role='admin' WHERE username=%s", (username,))
        conn.commit()
    cursor_update.close()
    
    cursor_select = conn.cursor()
    cursor_select.execute("SELECT role FROM users WHERE username = %s", (username,))
    user_role = cursor_select.fetchone()
    cursor_select.close()
    
    conn.close()
    return user_role[0] if user_role else 'user'

#dashboard Route
# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch course details from the database
    cursor.execute("SELECT course_name, youtube_link FROM courses")
    youtube_links = [(course_name, youtube_link.replace("youtu.be/", "www.youtube.com/embed/")) for course_name, youtube_link in cursor.fetchall()]

    # Fetch materials from the database
    cursor.execute("SELECT course_name, file_path FROM materials")
    materials = cursor.fetchall()
    
    cursor.close()
    conn.close()
    course_image = url_for('static', filename='images/course_image.jpg')
    updated_materials = [(course, os.path.basename(file_path)) for course, file_path in materials]
    return render_template('dashboard.html', course_image=course_image,youtube_links=youtube_links, materials=updated_materials)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admindashboard', methods=['GET', 'POST'])
def admindashboard():
    if request.method == 'POST':
        # Handle the uploaded file and save to the server
        if 'material' not in request.files:
            return 'No file part', 400
        
        file = request.files['material']
        if file.filename == '':
            return 'No selected file', 400

        if file and allowed_file(file.filename):
            # Secure the filename to prevent directory traversal
            filename = secure_filename(file.filename)
            file_path = os.path.join('files', filename)  # Relative path
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Extract course name, description, and store in database
            course_name = request.form['course-name']
            description = request.form['description']
            
            # Save course information to the database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO materials (course_name, description, file_path) VALUES (%s, %s, %s)",(course_name, description, file_path))
            conn.commit()
            cursor.close()
            conn.close()
            
            return 'File uploaded successfully!', 200
        else:
            return 'Invalid file type. Only PDFs are allowed.', 400
    # List files in the `static/files` directory
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_data = [{'course': 'Unknown', 'file': f} for f in uploaded_files]

    # Retrieve existing materials from DB or folder
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_name, file_path FROM materials")
    db_materials = cursor.fetchall()
    cursor.close()
    conn.close()

    # Combine database records with static folder files
    for material in db_materials:
        file_data.append({'course': material[0], 'file': os.path.basename(material[1])})

    return render_template('admindashboard.html', materials=file_data)


# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(debug=True)
