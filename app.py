from flask import Flask, request, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__, static_folder="static", template_folder="templates")
# Corrected __name__
app.secret_key = 'temporary_key'

# Example route to verify the app runs correctly
# Home Route (Landing Page)

def get_db_connection():
    connection =  mysql.connector.connect(
        host="database-virtualclassroom.cvgemiwou5va.ap-south-1.rds.amazonaws.com",
        user="admin",
        password="Karthi000!0",
        database="database_virtualclassroom"
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and check_password_hash(result[0], password):
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')

#dashboard Route
@app.route('/dashboard')
def dashboard():
    course_urls = [
        'https://aws-project-virtualclassroom5.s3.ap-south-1.amazonaws.com/python_code.pdf',
        'https://aws-project-virtualclassroom5.s3.ap-south-1.amazonaws.com/PYTHON-PROGRAMMING-NOTES.pdf'
    ]
    course_image = url_for('static', filename='images/course_image.jpg')

    return render_template('dashboard.html', course_urls=course_urls, course_image=course_image)



# Logout
@app.route('/logout')
def logout():
    return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(debug=True)
