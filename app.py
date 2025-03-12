from flask import Flask, render_template, request, redirect, url_for, session
import re
import random
import string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

# Database setup
def init_db():
    conn = sqlite3.connect("password_backlog.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS passwords 
                 (id INTEGER PRIMARY KEY, password TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

# Function to evaluate password strength
def evaluate_password(password):
    score = 0
    feedback = []
    
    if len(password) >= 12:
        score += 3
    elif len(password) >= 8:
        score += 2
    else:
        feedback.append("Password is too short (less than 8 characters).")
    
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Add uppercase letters for better strength.")
    
    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Add lowercase letters for better strength.")
    
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Add numbers for better strength.")
    
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 2
    else:
        feedback.append("Add special characters (e.g., !@#$%) for better strength.")
    
    common_passwords = ["password", "123456", "qwerty", "letmein"]
    if password.lower() in common_passwords:
        score -= 5
        feedback.append("This is a common password; avoid using it!")
    
    return score, feedback

# Function to generate a strong password
def generate_strong_password(length=16):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice(string.punctuation)
    ]
    password += random.choices(characters, k=length - 4)
    random.shuffle(password)
    return ''.join(password)

# Save password to database
def save_to_backlog(password):
    conn = sqlite3.connect("password_backlog.db")
    c = conn.cursor()
    c.execute("INSERT INTO passwords (password, timestamp) VALUES (?, ?)",
              (password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Home route (password scanner)
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        password = request.form.get("password")
        if password:
            if password.lower() == "admin":
                return redirect(url_for("admin_login"))
            # Save to database if not "admin" or "done"
            if password.lower() != "done":
                save_to_backlog(password)
            
            if password.lower() == "done":
                return render_template("index.html", result="Session ended.")
            
            score, feedback = evaluate_password(password)
            new_password = generate_strong_password() if score < 6 else None
            result = {
                "password": "*" * len(password),
                "score": score,
                "feedback": feedback,
                "new_password": new_password
            }
    return render_template("index.html", result=result)

# Admin login route
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    admin_password = "X!mm)23e@jW?C"
    error = None
    if request.method == "POST":
        password = request.form.get("admin_password")
        if password == admin_password:
            session["admin"] = True
            return redirect(url_for("backlog"))
        else:
            error = "Incorrect admin password."
    return render_template("admin.html", error=error)

# Admin backlog view
@app.route("/backlog")
def backlog():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("password_backlog.db")
    c = conn.cursor()
    c.execute("SELECT id, password, timestamp FROM passwords")
    passwords = c.fetchall()
    conn.close()
    
    return render_template("backlog.html", passwords=passwords)

# Logout route
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()  # Initialize database
    app.run(debug=True)
