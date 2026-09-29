# Path: ~/academy-project/backend/app.py
import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database Connection String built from environment variables
DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_NAME = os.getenv("DB_NAME", "academydb")
DB_USER = os.getenv("DB_USER", "academy_user")
DB_PASS = os.getenv("DB_PASS", "DevSecOps@911")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    return conn

# Initialize table on startup
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course VARCHAR(100) NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, course FROM students ORDER BY id DESC;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        students = [{"id": r[0], "name": r[1], "course": r[2]} for r in rows]
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json()
    name = data.get('name')
    course = data.get('course')
    
    if not name or not course:
        return jsonify({"error": "Name and course are required"}), 400
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO students (name, course) VALUES (%s, %s) RETURNING id;", (name, course))
        student_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"id": student_id, "name": name, "course": course}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
