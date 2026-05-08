from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

undo_stack = []  # Stack

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        name TEXT,
        program TEXT,
        year TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['user'] = 'admin'
            return redirect('/dashboard')
    return render_template('login.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    conn = get_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template('dashboard.html', students=students)

# ---------- ADD ----------
@app.route('/add', methods=['POST'])
def add():
    conn = get_db()
    conn.execute("INSERT INTO students VALUES (?, ?, ?, ?)",
                 (request.form['id'], request.form['name'],
                  request.form['program'], request.form['year']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------- DELETE ----------
@app.route('/delete/<sid>')
def delete(sid):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()

    if student:
        undo_stack.append(student)
        conn.execute("DELETE FROM students WHERE id=?", (sid,))
        conn.commit()

    conn.close()
    return redirect('/dashboard')

# ---------- UNDO ----------
@app.route('/undo')
def undo():
    if undo_stack:
        student = undo_stack.pop()
        conn = get_db()
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?)", student)
        conn.commit()
        conn.close()
    return redirect('/dashboard')

# ---------- UPDATE ----------
@app.route('/update', methods=['POST'])
def update():
    conn = get_db()
    conn.execute("""UPDATE students SET name=?, program=?, year=? WHERE id=?""",
                 (request.form['name'], request.form['program'],
                  request.form['year'], request.form['id']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------- SEARCH (AJAX) ----------
@app.route('/search', methods=['POST'])
def search():
    sid = request.form['id']
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    conn.close()

    if student:
        return jsonify({
            "id": student[0],
            "name": student[1],
            "program": student[2],
            "year": student[3]
        })
    return jsonify({"error": "Not found"})

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)