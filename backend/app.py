# Path: ~/academy-project/backend/app.py
import os
import psycopg2  # pyright: ignore[reportMissingImports]
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-fallback-secret-key')

# Initialize CSRF Protection
csrf = CSRFProtect(app)
# Do not enable a global permissive CORS policy. Restrict browser access to the
# explicitly allowlisted origins configured below.
# This API is stateless and does not use cookie-based authentication. Flask-WTF
# CSRF is kept disabled by default unless an operator explicitly opts in, and
# all state-changing browser requests are still restricted by a strict
# Origin/Referer allowlist. The service does not rely on session cookies or
# CSRF tokens for authentication. This is intentional and safe for the current
# stateless API design, but the explicit opt-in is required before enabling it.
# NOSONAR - S4502: CSRF is intentionally disabled only with an explicit
# operator opt-in and is protected by strict Origin/Referer allowlisting.
app.config["WTF_CSRF_ENABLED"] = (
    os.getenv("WTF_CSRF_ENABLED", "false").strip().lower()
    in {"1", "true", "yes", "on"}
)
# Explicit application secret is required for secure session and CSRF handling.
# Keep this value in environment configuration for production deployments.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-production")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"

# Allow only explicitly configured frontend origins; do not expose the API to
# every website by default.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
# The API is stateless and does not use cookie authentication, so CSRF tokens
# are not required. Protect state-changing browser requests with an origin
# check instead; requests from non-browser API clients may omit Origin.
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}}, supports_credentials=False)

@app.before_request
def validate_request_origin():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None

    origin = request.headers.get("Origin")
    if origin and origin not in CORS_ORIGINS:
        return jsonify({"error": "Cross-origin request rejected"}), 403

    referer = request.headers.get("Referer")
    if not origin and referer and not any(
        referer.startswith(f"{allowed_origin}/") or referer == allowed_origin
        for allowed_origin in CORS_ORIGINS
    ):
        return jsonify({"error": "Cross-origin request rejected"}), 403

    return None

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

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Backend API is running"}), 200        

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
    app.run(host='127.0.0.1', port=5000)
