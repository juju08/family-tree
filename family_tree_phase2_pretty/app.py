import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'instance' / 'family_tree.db'
UPLOAD_DIR = BASE_DIR / 'static' / 'uploads'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-before-hosting')
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'julianm')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '5upp0rt*')


def db():
    if 'db' not in g:
        DB_PATH.parent.mkdir(exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop('db', None)
    if conn:
        conn.close()


def slug(name):
    return ''.join(c.lower() if c.isalnum() else '-' for c in name).strip('-').replace('--','-')


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id') and not session.get('is_admin'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def current_user():
    if session.get('is_admin'):
        return {'is_admin': True, 'id': None, 'name': 'Admin'}
    if session.get('user_id'):
        row = db().execute('SELECT * FROM people WHERE id=?', (session['user_id'],)).fetchone()
        if row:
            return dict(row) | {'is_admin': False}
    return None


def can_edit(person_id):
    if session.get('is_admin'):
        return True
    uid = session.get('user_id')
    if not uid:
        return False
    if person_id == uid:
        return True
    person = db().execute('SELECT * FROM people WHERE id=?', (person_id,)).fetchone()
    if not person:
        return False
    # Can edit spouse
    if person['spouse_id'] == uid:
        return True
    # Can edit direct children
    if person['parent1_id'] == uid or person['parent2_id'] == uid:
        return True
    return False


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def init_db():
    conn = db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS people (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        display_name TEXT NOT NULL,
        birthday TEXT,
        notes TEXT,
        parent1_id TEXT,
        parent2_id TEXT,
        spouse_id TEXT,
        photo TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    ''')
    admin = conn.execute('SELECT id FROM admin_users WHERE username=?', (ADMIN_USERNAME,)).fetchone()
    if not admin:
        conn.execute('INSERT INTO admin_users(username,password_hash) VALUES (?,?)',
                     (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)))
    if not conn.execute('SELECT 1 FROM people LIMIT 1').fetchone():
        seed_people(conn)
    conn.commit()


def add(conn, name, birthday='', parent1=None, parent2=None, spouse=None, notes=''):
    parts = name.split()
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ''
    pid = slug(name)
    now = datetime.utcnow().isoformat()
    conn.execute('''INSERT OR REPLACE INTO people
    (id, first_name, last_name, display_name, birthday, parent1_id, parent2_id, spouse_id, notes, created_at, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (pid, first, last, name, birthday, parent1, parent2, spouse, notes, now, now))
    return pid


def set_spouse(conn, a, b):
    if a and b:
        conn.execute('UPDATE people SET spouse_id=? WHERE id=?', (b, a))
        conn.execute('UPDATE people SET spouse_id=? WHERE id=?', (a, b))


def seed_people(conn):
    gladys = add(conn, 'Gladys Perez', 'Nov 24, 1944')
    andres = add(conn, 'Andres Torres', 'Nov 30, 1942')
    set_spouse(conn, andres, gladys)

    nelly = add(conn, 'Nelly Rivera', 'Apr 19, 1964', andres, gladys)
    noemi = add(conn, 'Noemi Torres', 'Jul 9, 1965', andres, gladys)
    freddy = add(conn, 'Freddy Torres', 'Apr 1, 1967', andres, gladys)
    glenda = add(conn, 'Glenda Torres', 'Jun 12, 1968', andres, gladys)
    sylvia = add(conn, 'Sylvia Diaz', 'Aug 11, 1970', andres, gladys)
    yolanda = add(conn, 'Yolanda Bustos', 'Jan 4, 1973', andres, gladys)
    jessica = add(conn, 'Jessica Torres', 'Mar 18, 1981', andres, gladys, notes='No children')

    joshua_r = add(conn, 'Joshua Rivera', 'Feb 12, 1990', nelly)
    yazmin = add(conn, 'Yazmin Rivera', 'Sep 24, 1996')
    set_spouse(conn, joshua_r, yazmin)
    add(conn, 'Sofia Rivera', 'Apr 2, 2011', joshua_r, yazmin)
    add(conn, 'Ezra Rivera', 'Jul 19, 2021', joshua_r, yazmin)
    add(conn, 'Genevive Rivera', 'Sep 2024', joshua_r, yazmin)
    add(conn, 'Joselyn Rivera', 'Nov 23, 1994', nelly)
    jennifer = add(conn, 'Jennifer Modlin', 'Jul 13, 1983', nelly)
    brian = add(conn, 'Brian Modlin', 'Jun 29, 1975')
    set_spouse(conn, jennifer, brian)
    for name, bday in [('Jonathan Modlin','Sep 13, 1999'),('Brendan Modlin','May 29, 2006'),('Julian Modlin','Oct 23, 2008'),('Briella Modlin','Dec 16, 2010'),('Jalon Modlin','Jul 4, 2015'),('Brooklyn Modlin','Mar 6, 2017'),('Juliette Modlin','Mar 16, 2019'),('Blake Modlin','Jul 25, 2021')]:
        add(conn, name, bday, jennifer, brian)

    add(conn, 'Louie Bustos', 'Nov 23, 1995', yolanda)
    add(conn, 'Steven Bustos', 'May 31, 1998', yolanda)

    freddyjr = add(conn, 'Freddy Jr. Torres', 'Jul 17, 1986', freddy)
    add(conn, 'Dominic Torres', 'May 19, 2014', freddyjr)
    omar = add(conn, 'Omar Torres', 'Jun 11, 1987', freddy)
    for name,bday in [('Gabriella Torres','Jun 25, 2007'),('Rosalyn Torres','May 23, 2011'),('Annalise Torres','Jun 13, 2012'),('Destiny Torres','Oct 19, 2020')]:
        add(conn, name, bday, omar)
    ary = add(conn, 'Ary Torres', 'Aug 20, 1992', freddy)
    for name,bday in [('Aiden Torres','Jan 10, 2014'),('Jamir Eugene','Apr 7, 2013'),('Jaelyn Eugene','Oct 5, 2017'),('Alexander Eugene','Aug 24, 2018'),('Jaelani Eugene','Jul 2, 2021')]:
        add(conn, name, bday, ary)

    jerica = add(conn, 'Jerica Figueroa', 'May 4, 1988', glenda)
    add(conn, 'Kiara Costner', 'Jun 4, 2009', jerica)
    add(conn, 'Johnnie Figueroa', 'Jun 19, 1989', glenda)

    omi = add(conn, 'Omi Muniz', 'May 6, 1986', noemi)
    add(conn, 'Estela Demastus', 'Nov 11, 2014', omi)
    liza = add(conn, 'Liza Muniz', 'May 23, 1989', noemi)
    add(conn, 'Eric Colon (EJ)', 'May 21, 2016', liza)
    add(conn, 'Eliana Colon', 'Dec 20, 2019', liza)
    add(conn, 'Papo Muniz', 'Jul 25, 1990', noemi)

    add(conn, 'David Diaz', 'Oct 9, 1991', sylvia)
    marie = add(conn, 'Marie Diaz', 'Feb 16, 1994', sylvia)
    add(conn, 'Sophia Grace', 'Feb 10, 2022', marie)
    add(conn, 'Joshua Diaz', 'Apr 9, 2001', sylvia)


def people_options():
    return db().execute('SELECT id, display_name FROM people ORDER BY display_name').fetchall()


@app.before_request
def ensure_db():
    init_db()


@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user())


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode == 'admin':
            username = request.form.get('username','').strip()
            password = request.form.get('password','')
            row = db().execute('SELECT * FROM admin_users WHERE username=?', (username,)).fetchone()
            if row and check_password_hash(row['password_hash'], password):
                session.clear(); session['is_admin'] = True
                return redirect(url_for('index'))
            flash('Admin login failed.')
        else:
            first = request.form.get('first_name','').strip()
            last = request.form.get('last_name','').strip()
            row = db().execute('SELECT * FROM people WHERE lower(first_name)=lower(?) AND lower(last_name)=lower(?)', (first,last)).fetchone()
            if row:
                session.clear(); session['user_id'] = row['id']
                return redirect(url_for('index'))
            flash('Name not found. Try the exact first and last name from the family tree.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/tree')
@login_required
def api_tree():
    rows = [dict(r) for r in db().execute('SELECT * FROM people ORDER BY display_name').fetchall()]
    return jsonify(rows)


@app.route('/people')
@login_required
def people():
    rows = db().execute('SELECT * FROM people ORDER BY display_name').fetchall()
    return render_template('people.html', rows=rows, user=current_user())


@app.route('/person/new', methods=['GET','POST'])
@login_required
def person_new():
    if request.method == 'POST':
        if not session.get('is_admin'):
            parent1 = session.get('user_id')
            parent2 = db().execute('SELECT spouse_id FROM people WHERE id=?', (parent1,)).fetchone()['spouse_id']
        else:
            parent1 = request.form.get('parent1_id') or None
            parent2 = request.form.get('parent2_id') or None
        name = request.form.get('display_name','').strip()
        if not name:
            flash('Name is required.'); return redirect(request.url)
        pid = slug(name)
        if db().execute('SELECT 1 FROM people WHERE id=?',(pid,)).fetchone():
            pid = f'{pid}-{uuid4().hex[:6]}'
        parts = name.split(); first=parts[0]; last=parts[-1] if len(parts)>1 else ''
        now = datetime.utcnow().isoformat()
        db().execute('''INSERT INTO people(id,first_name,last_name,display_name,birthday,notes,parent1_id,parent2_id,created_at,updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?)''',
                     (pid,first,last,name,request.form.get('birthday','').strip(),request.form.get('notes','').strip(),parent1,parent2,now,now))
        db().commit()
        flash('Person added.')
        return redirect(url_for('person_edit', person_id=pid))
    return render_template('edit_person.html', person=None, options=people_options(), user=current_user(), is_new=True)


@app.route('/person/<person_id>/edit', methods=['GET','POST'])
@login_required
def person_edit(person_id):
    person = db().execute('SELECT * FROM people WHERE id=?', (person_id,)).fetchone()
    if not person:
        return 'Not found', 404
    if not can_edit(person_id):
        flash('You can only edit yourself, your spouse, and your children.')
        return redirect(url_for('people'))
    if request.method == 'POST':
        display_name = request.form.get('display_name','').strip()
        if not display_name:
            flash('Name is required.'); return redirect(request.url)
        parts = display_name.split(); first=parts[0]; last=parts[-1] if len(parts)>1 else ''
        birthday = request.form.get('birthday','').strip()
        notes = request.form.get('notes','').strip()
        spouse_id = request.form.get('spouse_id') or None
        parent1_id = person['parent1_id']; parent2_id = person['parent2_id']
        if session.get('is_admin'):
            parent1_id = request.form.get('parent1_id') or None
            parent2_id = request.form.get('parent2_id') or None
        photo = person['photo']
        f = request.files.get('photo')
        if f and f.filename and allowed_file(f.filename):
            ext = secure_filename(f.filename).rsplit('.',1)[1].lower()
            fname = f'{person_id}-{uuid4().hex[:8]}.{ext}'
            UPLOAD_DIR.mkdir(exist_ok=True)
            f.save(UPLOAD_DIR / fname)
            photo = fname
        db().execute('''UPDATE people SET first_name=?, last_name=?, display_name=?, birthday=?, notes=?, spouse_id=?, parent1_id=?, parent2_id=?, photo=?, updated_at=? WHERE id=?''',
                     (first,last,display_name,birthday,notes,spouse_id,parent1_id,parent2_id,photo,datetime.utcnow().isoformat(),person_id))
        if spouse_id:
            db().execute('UPDATE people SET spouse_id=? WHERE id=?', (person_id, spouse_id))
        db().commit()
        flash('Saved.')
        return redirect(url_for('person_edit', person_id=person_id))
    return render_template('edit_person.html', person=person, options=people_options(), user=current_user(), is_new=False)


@app.route('/birthdays')
@login_required
def birthdays():
    rows = db().execute('SELECT display_name,birthday FROM people WHERE birthday IS NOT NULL AND birthday != "" ORDER BY birthday').fetchall()
    return render_template('birthdays.html', rows=rows, user=current_user())


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
