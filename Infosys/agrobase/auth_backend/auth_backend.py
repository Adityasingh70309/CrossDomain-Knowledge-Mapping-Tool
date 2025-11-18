import sqlite3
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from flask_cors import CORS
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# Ensure project root (agrobase) is on sys.path so local packages like `pipelines` can be imported
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)  # Allow Streamlit frontend

# --- Config ---
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "a-super-secret-key-you-must-change")
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- Database Logic ---
def get_user_db_connection():
    conn = sqlite3.connect("flask_users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()
    print("✅ User DB initialized.")

def add_user(email, hashed_password):
    conn = get_user_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return {"email": user["email"], "hashed_password": user["hashed_password"]} if user else None

# --- API Routes ---
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    if add_user(email, hashed_pw):
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"message": "Email already exists"}), 409

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    user = get_user_by_email(email)
    if user and bcrypt.check_password_hash(user["hashed_password"], password):
        token = create_access_token(identity=email)
        return jsonify({"token": token}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({"logged_in_as": current_user}), 200

@app.route('/submit_feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    current_user_email = get_jwt_identity()
    data = request.get_json()
    
    feedback_type = data.get('type')
    feedback_text = data.get('text')

    if not feedback_type or not feedback_text:
        return jsonify({"message": "Feedback type and text are required"}), 400

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO feedback (user_email, feedback_type, feedback_text) VALUES (?, ?, ?)",
            (current_user_email, feedback_type, feedback_text)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Feedback submitted successfully"}), 201
    except Exception as e:
        return jsonify({"message": f"Database error: {e}"}), 500

# --- Run the App ---
if __name__ == '__main__':
    init_user_db()
    app.run(debug=True, port=5000)

from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import pandas as pd
from werkzeug.utils import secure_filename
from pipelines import text_cleaner, extraction
from pipelines import neo4j_loader as neo4jloader

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/ingest_data", methods=["POST"])
@jwt_required()
def ingest_data():
    try:
        if "file" not in request.files:
            return jsonify({"message": "No file uploaded"}), 400
        
        file = request.files["file"]
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # --- Process file ---
        if filename.endswith(".csv"):
            df = pd.read_csv(filepath)
            text_data = " ".join(df.astype(str).values.flatten().tolist())
        else:
            text_data = file.read().decode("utf-8")

        clean_text = text_cleaner.clean_text(text_data)

        nlp = extraction.load_nlp_model()
        doc = nlp(clean_text)
        triples = extraction.extract_triples_from_doc(doc)

        stored_count = neo4jloader.store_triples_in_neo4j(triples)

        return jsonify({
            "filename": filename,
            "entities": len(doc.ents),
            "relations": len(triples),
            "triples": stored_count
        }), 200
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return jsonify({"message": f"Error: {e}"}), 500
