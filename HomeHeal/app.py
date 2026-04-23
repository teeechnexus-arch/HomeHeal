import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'homeheal_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'homeheal.db')

# ─── Database Setup ────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                medicine_name TEXT NOT NULL,
                dosage TEXT,
                time TEXT NOT NULL,
                frequency TEXT NOT NULL,
                notes TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                doctor_name TEXT NOT NULL,
                specialization TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS bmi_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                category TEXT NOT NULL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')

init_db()

# ─── Auth Decorator ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        hashed = generate_password_hash(password)
        try:
            with get_db() as conn:
                conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                             (name, email, hashed))
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    with get_db() as conn:
        reminders = conn.execute('SELECT * FROM reminders WHERE user_id=? AND active=1 ORDER BY time', (uid,)).fetchall()
        appointments = conn.execute('SELECT * FROM appointments WHERE user_id=? ORDER BY date DESC LIMIT 5', (uid,)).fetchall()
        bmi_latest = conn.execute('SELECT * FROM bmi_history WHERE user_id=? ORDER BY recorded_at DESC LIMIT 1', (uid,)).fetchone()
        reminder_count = conn.execute('SELECT COUNT(*) as c FROM reminders WHERE user_id=? AND active=1', (uid,)).fetchone()['c']
        appt_count = conn.execute('SELECT COUNT(*) as c FROM appointments WHERE user_id=? AND status="Pending"', (uid,)).fetchone()['c']
    now = datetime.now()
    return render_template('dashboard.html',
                           reminders=reminders,
                           appointments=appointments,
                           bmi_latest=bmi_latest,
                           reminder_count=reminder_count,
                           appt_count=appt_count,
                           now_hour=now.hour,
                           now_date=now.strftime('%d %B %Y'))

# ── BMI ───────────────────────────────────────────────────────────────────────

@app.route('/bmi', methods=['GET', 'POST'])
@login_required
def bmi():
    result = None
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            height = float(request.form['height']) / 100  # cm to m
            bmi_val = round(weight / (height ** 2), 1)
            if bmi_val < 18.5:
                category = 'Underweight'
                color = 'blue'
                tip = 'Consider a nutrient-rich diet. Consult a nutritionist if needed.'
            elif bmi_val < 25:
                category = 'Normal Weight'
                color = 'green'
                tip = 'Great! Maintain your healthy lifestyle with regular exercise and balanced diet.'
            elif bmi_val < 30:
                category = 'Overweight'
                color = 'yellow'
                tip = 'Consider increasing physical activity and moderating calorie intake.'
            else:
                category = 'Obese'
                color = 'red'
                tip = 'Please consult a healthcare professional for personalised guidance.'

            result = {'bmi': bmi_val, 'category': category, 'color': color, 'tip': tip,
                      'weight': weight, 'height': float(request.form['height'])}

            with get_db() as conn:
                conn.execute('INSERT INTO bmi_history (user_id, weight, height, bmi, category) VALUES (?,?,?,?,?)',
                             (session['user_id'], weight, float(request.form['height']), bmi_val, category))
        except (ValueError, ZeroDivisionError):
            flash('Please enter valid weight and height values.', 'error')

    with get_db() as conn:
        history = conn.execute('SELECT * FROM bmi_history WHERE user_id=? ORDER BY recorded_at DESC LIMIT 7',
                               (session['user_id'],)).fetchall()
    return render_template('bmi.html', result=result, history=history)

# ── Reminders ─────────────────────────────────────────────────────────────────

@app.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminders():
    uid = session['user_id']
    if request.method == 'POST':
        name = request.form['medicine_name'].strip()
        dosage = request.form['dosage'].strip()
        time = request.form['time']
        frequency = request.form['frequency']
        notes = request.form.get('notes', '').strip()
        with get_db() as conn:
            conn.execute('INSERT INTO reminders (user_id, medicine_name, dosage, time, frequency, notes) VALUES (?,?,?,?,?,?)',
                         (uid, name, dosage, time, frequency, notes))
        flash('Reminder added successfully!', 'success')
        return redirect(url_for('reminders'))

    with get_db() as conn:
        all_reminders = conn.execute('SELECT * FROM reminders WHERE user_id=? ORDER BY active DESC, time', (uid,)).fetchall()
    return render_template('reminders.html', reminders=all_reminders)

@app.route('/reminders/toggle/<int:rid>')
@login_required
def toggle_reminder(rid):
    with get_db() as conn:
        r = conn.execute('SELECT * FROM reminders WHERE id=? AND user_id=?', (rid, session['user_id'])).fetchone()
        if r:
            conn.execute('UPDATE reminders SET active=? WHERE id=?', (0 if r['active'] else 1, rid))
    return redirect(url_for('reminders'))

@app.route('/reminders/delete/<int:rid>')
@login_required
def delete_reminder(rid):
    with get_db() as conn:
        conn.execute('DELETE FROM reminders WHERE id=? AND user_id=?', (rid, session['user_id']))
    flash('Reminder deleted.', 'success')
    return redirect(url_for('reminders'))

# ── Appointments ──────────────────────────────────────────────────────────────

@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    uid = session['user_id']
    if request.method == 'POST':
        doctor = request.form['doctor_name'].strip()
        spec = request.form['specialization'].strip()
        date = request.form['date']
        time = request.form['time']
        reason = request.form.get('reason', '').strip()
        with get_db() as conn:
            conn.execute('INSERT INTO appointments (user_id, doctor_name, specialization, date, time, reason) VALUES (?,?,?,?,?,?)',
                         (uid, doctor, spec, date, time, reason))
        flash('Appointment requested successfully!', 'success')
        return redirect(url_for('appointments'))

    with get_db() as conn:
        all_appts = conn.execute('SELECT * FROM appointments WHERE user_id=? ORDER BY date DESC', (uid,)).fetchall()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('appointments.html', appointments=all_appts, today=today)

@app.route('/appointments/cancel/<int:aid>')
@login_required
def cancel_appointment(aid):
    with get_db() as conn:
        conn.execute('UPDATE appointments SET status="Cancelled" WHERE id=? AND user_id=?', (aid, session['user_id']))
    flash('Appointment cancelled.', 'success')
    return redirect(url_for('appointments'))

# ── Help ──────────────────────────────────────────────────────────────────────

@app.route('/help')
def help_page():
    return render_template('help.html')

# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
