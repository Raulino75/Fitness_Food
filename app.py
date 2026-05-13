import sqlite3
import json
import os
import re
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, g, session)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fitness-food-secret-key-2026-change-in-production')
app.permanent_session_lifetime = 28800  # 8 horas

DATABASE = 'fitness_food.db'

# ─── DATABASE ───────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'cliente'
                CHECK(rol IN ('admin', 'cliente')),
            objetivo TEXT DEFAULT 'mantener'
                CHECK(objetivo IN ('perder_peso', 'mantener', 'ganar_masa')),
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            calorias_por_100g REAL NOT NULL,
            categoria TEXT DEFAULT 'general',
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            alimento_id INTEGER NOT NULL,
            gramos REAL NOT NULL,
            calorias REAL NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES auth_usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (alimento_id) REFERENCES alimentos(id) ON DELETE RESTRICT
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_registros_usuario ON registros(usuario_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_registros_fecha ON registros(fecha)')
    db.commit()

    cursor.execute("SELECT id FROM auth_usuarios WHERE rol='admin' LIMIT 1")
    if not cursor.fetchone():
        admin_hash = generate_password_hash('Admin1234!')
        cursor.execute(
            "INSERT INTO auth_usuarios (nombre, email, password_hash, rol, objetivo) VALUES (?,?,?,?,?)",
            ('Administrador', 'admin@fitnessfood.com', admin_hash, 'admin', 'mantener')
        )
        db.commit()
        print("Admin creado: admin@fitnessfood.com / Admin1234!")

    try:
        with open('alimentos.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data['alimentos']:
            cursor.execute(
                "INSERT OR IGNORE INTO alimentos (nombre, calorias_por_100g, categoria) VALUES (?,?,?)",
                (item['nombre'], item['calorias_por_100g'], item.get('categoria', 'general'))
            )
        db.commit()
        print("Alimentos cargados desde JSON")
    except FileNotFoundError:
        print("alimentos.json no encontrado")

    db.close()

# ─── SESION ─────────────────────────────────────

def guardar_sesion(usuario):
    session.permanent = True
    session['usuario_id']     = usuario['id']
    session['usuario_nombre'] = usuario['nombre']
    session['usuario_rol']    = usuario['rol']
    session['usuario_email']  = usuario['email']

def sesion_activa():
    return 'usuario_id' in session

# ─── DECORADORES ────────────────────────────────

def login_requerido(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not sesion_activa():
            flash('Debes iniciar sesion para acceder.', 'warning')
            return redirect(url_for('login'))
        g.usuario_id = session['usuario_id']
        g.rol        = session['usuario_rol']
        return f(*args, **kwargs)
    return decorado

def solo_admin(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not sesion_activa():
            return redirect(url_for('login'))
        # Verificar rol directo desde BD, no desde sesión
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        usuario = db.execute(
            'SELECT rol FROM auth_usuarios WHERE id=? AND activo=1',
            (session['usuario_id'],)
        ).fetchone()
        db.close()
        if not usuario or usuario['rol'] != 'admin':
            flash('No tienes permisos para acceder a esta seccion.', 'danger')
            return redirect(url_for('inicio'))
        return f(*args, **kwargs)
    return decorado

def api_login_requerido(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not sesion_activa():
            return jsonify({'error': 'Sesion requerida'}), 401
        g.usuario_id = session['usuario_id']
        g.rol        = session['usuario_rol']
        return f(*args, **kwargs)
    return decorado

def api_solo_admin(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if session.get('usuario_rol') != 'admin':
            return jsonify({'error': 'Acceso restringido a administradores'}), 403
        return f(*args, **kwargs)
    return decorado

# ─── AUTH ────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if sesion_activa():
        return redirect(url_for('inicio'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        db       = get_db()
        usuario  = db.execute(
            'SELECT * FROM auth_usuarios WHERE email=? AND activo=1', (email,)
        ).fetchone()
        if not usuario or not check_password_hash(usuario['password_hash'], password):
            flash('Email o contrasena incorrectos.', 'danger')
            return render_template('login.html', email=email)
        guardar_sesion(usuario)
        flash('Bienvenido, ' + usuario['nombre'] + '!', 'success')
        return redirect(url_for('inicio'))
    return render_template('login.html')

@app.route('/registro-cuenta', methods=['GET', 'POST'])
def registro():
    if sesion_activa():
        return redirect(url_for('inicio'))
    if request.method == 'POST':
        nombre    = request.form.get('nombre', '').strip()
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '')
        confirmar = request.form.get('confirmar', '')
        objetivo  = request.form.get('objetivo', 'mantener')

        errors = []
        if not nombre or len(nombre) < 2:
            errors.append('El nombre debe tener al menos 2 caracteres.')
        if not re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Email invalido.')
        if len(password) < 8:
            errors.append('La contrasena debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', password):
            errors.append('La contrasena debe tener al menos una mayuscula.')
        if not re.search(r'\d', password):
            errors.append('La contrasena debe tener al menos un numero.')
        if password != confirmar:
            errors.append('Las contrasenas no coinciden.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('registro.html', nombre=nombre, email=email, objetivo=objetivo)

        db = get_db()
        if db.execute('SELECT id FROM auth_usuarios WHERE email=?', (email,)).fetchone():
            flash('Ya existe una cuenta con ese email.', 'danger')
            return render_template('registro.html', nombre=nombre, email=email, objetivo=objetivo)

        db.execute(
            'INSERT INTO auth_usuarios (nombre, email, password_hash, rol, objetivo) VALUES (?,?,?,?,?)',
            (nombre, email, generate_password_hash(password), 'cliente', objetivo)
        )
        db.commit()
        flash('Cuenta creada exitosamente! Inicia sesion.', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesion cerrada correctamente.', 'info')
    return redirect(url_for('login'))

# ─── RUTAS PRINCIPALES ──────────────────────────

@app.route('/')
@login_requerido
def inicio():
    db = get_db()
    if session.get('usuario_rol') == 'admin':
        estadisticas = {
            'usuarios':  db.execute('SELECT COUNT(*) FROM auth_usuarios WHERE activo=1').fetchone()[0],
            'alimentos': db.execute('SELECT COUNT(*) FROM alimentos').fetchone()[0],
            'registros': db.execute('SELECT COUNT(*) FROM registros').fetchone()[0],
            'calorias':  int(db.execute('SELECT COALESCE(SUM(calorias),0) FROM registros').fetchone()[0]),
        }
        return render_template('index.html', estadisticas=estadisticas)

    usuario_id = session.get('usuario_id')
    estadisticas = {
        'registros': db.execute('SELECT COUNT(*) FROM registros WHERE usuario_id=?', (usuario_id,)).fetchone()[0],
        'calorias':  int(db.execute('SELECT COALESCE(SUM(calorias),0) FROM registros WHERE usuario_id=?', (usuario_id,)).fetchone()[0]),
        'calorias_hoy': int(db.execute(
            "SELECT COALESCE(SUM(calorias),0) FROM registros WHERE usuario_id=? AND DATE(fecha)=DATE('now')",
            (usuario_id,)
        ).fetchone()[0]),
    }
    return render_template('index.html', estadisticas=estadisticas)

@app.route('/acerca')
@login_requerido
def acerca():
    return render_template('acerca.html')

# ─── USUARIOS ───────────────────────────────────

@app.route('/usuarios')
@login_requerido
@solo_admin
def lista_usuarios():
    db       = get_db()
    usuarios = db.execute(
        'SELECT id, nombre, email, rol, objetivo, activo, fecha_creacion FROM auth_usuarios ORDER BY fecha_creacion DESC'
    ).fetchall()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/nuevo-usuario', methods=['POST'])
@login_requerido
@solo_admin
def crear_usuario():
    nombre   = request.form.get('nombre', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    objetivo = request.form.get('objetivo', 'mantener')
    rol      = request.form.get('rol', 'cliente')

    if not nombre or not email or not password:
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('lista_usuarios'))

    db = get_db()
    if db.execute('SELECT id FROM auth_usuarios WHERE email=?', (email,)).fetchone():
        flash('Ya existe una cuenta con ese email.', 'danger')
        return redirect(url_for('lista_usuarios'))

    db.execute(
        'INSERT INTO auth_usuarios (nombre, email, password_hash, rol, objetivo) VALUES (?,?,?,?,?)',
        (nombre, email, generate_password_hash(password), rol, objetivo)
    )
    db.commit()
    flash('Usuario ' + nombre + ' creado correctamente.', 'success')
    return redirect(url_for('lista_usuarios'))

@app.route('/editar-usuario/<int:usuario_id>', methods=['POST'])
@login_requerido
def editar_usuario(usuario_id):
    if g.rol != 'admin' and g.usuario_id != usuario_id:
        flash('No tienes permisos para editar este usuario.', 'danger')
        return redirect(url_for('inicio'))

    objetivo = request.form.get('objetivo')
    db       = get_db()

    if g.rol == 'admin':
        rol    = request.form.get('rol')
        activo = 1 if request.form.get('activo') == '1' else 0
        db.execute(
            'UPDATE auth_usuarios SET objetivo=?, rol=?, activo=? WHERE id=?',
            (objetivo, rol, activo, usuario_id)
        )
    else:
        db.execute('UPDATE auth_usuarios SET objetivo=? WHERE id=?', (objetivo, usuario_id))

    db.commit()
    flash('Usuario actualizado correctamente.', 'success')
    return redirect(url_for('lista_usuarios') if g.rol == 'admin' else url_for('inicio'))

@app.route('/eliminar-usuario', methods=['POST'])
@login_requerido
@solo_admin
def eliminar_usuario():
    usuario_id = request.form.get('usuario_id')
    if not usuario_id:
        flash('ID de usuario requerido.', 'danger')
        return redirect(url_for('lista_usuarios'))
    if int(usuario_id) == g.usuario_id:
        flash('No puedes eliminarte a ti mismo.', 'danger')
        return redirect(url_for('lista_usuarios'))
    db = get_db()
    db.execute('DELETE FROM auth_usuarios WHERE id=?', (usuario_id,))
    db.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('lista_usuarios'))

# ─── ALIMENTOS ──────────────────────────────────

@app.route('/alimentos/vista')
@login_requerido
def lista_alimentos_web():
    db        = get_db()
    alimentos = db.execute('SELECT * FROM alimentos ORDER BY nombre').fetchall()
    return render_template('alimentos.html', alimentos=alimentos)

# ─── REGISTROS ──────────────────────────────────

@app.route('/registros/<int:usuario_id>')
@login_requerido
def registros_usuario(usuario_id):
    if g.rol != 'admin' and g.usuario_id != usuario_id:
        flash('No tienes permisos para ver los registros de otro usuario.', 'danger')
        return redirect(url_for('inicio'))

    db      = get_db()
    usuario = db.execute('SELECT * FROM auth_usuarios WHERE id=?', (usuario_id,)).fetchone()
    if not usuario:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('inicio'))

    registros = db.execute('''
        SELECT r.id, r.gramos, r.calorias, r.fecha,
               a.nombre AS alimento_nombre, a.calorias_por_100g
        FROM registros r
        JOIN alimentos a ON r.alimento_id = a.id
        WHERE r.usuario_id = ?
        ORDER BY r.fecha DESC
    ''', (usuario_id,)).fetchall()

    alimentos = db.execute('SELECT id, nombre, calorias_por_100g FROM alimentos ORDER BY nombre').fetchall()
    return render_template('registros.html', usuario=usuario, registros=registros, alimentos=alimentos)

@app.route('/crear-registro', methods=['POST'])
@login_requerido
def crear_registro():
    usuario_id  = request.form.get('usuario_id', g.usuario_id)
    if g.rol != 'admin' and int(usuario_id) != g.usuario_id:
        flash('No puedes registrar consumos para otro usuario.', 'danger')
        return redirect(url_for('inicio'))

    alimento_id = request.form.get('alimento_id')
    gramos      = request.form.get('gramos')

    if not alimento_id or not gramos:
        flash('Todos los campos son requeridos.', 'danger')
        return redirect(url_for('registros_usuario', usuario_id=usuario_id))

    db       = get_db()
    alimento = db.execute('SELECT calorias_por_100g FROM alimentos WHERE id=?', (alimento_id,)).fetchone()
    if not alimento:
        flash('Alimento no encontrado.', 'danger')
        return redirect(url_for('registros_usuario', usuario_id=usuario_id))

    calorias = (alimento['calorias_por_100g'] * float(gramos)) / 100
    db.execute(
        'INSERT INTO registros (usuario_id, alimento_id, gramos, calorias) VALUES (?,?,?,?)',
        (usuario_id, alimento_id, gramos, calorias)
    )
    db.commit()
    flash('Registro creado exitosamente.', 'success')
    return redirect(url_for('registros_usuario', usuario_id=usuario_id))

@app.route('/registro/<int:registro_id>', methods=['DELETE'])
@login_requerido
def eliminar_registro(registro_id):
    db       = get_db()
    registro = db.execute('SELECT usuario_id FROM registros WHERE id=?', (registro_id,)).fetchone()
    if not registro:
        return jsonify({'error': 'Registro no encontrado'}), 404
    if g.rol != 'admin' and registro['usuario_id'] != g.usuario_id:
        return jsonify({'error': 'Sin permisos'}), 403
    db.execute('DELETE FROM registros WHERE id=?', (registro_id,))
    db.commit()
    return jsonify({'mensaje': 'Registro eliminado'})

# ─── API ────────────────────────────────────────

@app.route('/api/usuarios')
@api_login_requerido
@api_solo_admin
def api_usuarios():
    db       = get_db()
    usuarios = db.execute(
        'SELECT id, nombre, email, rol, objetivo, activo, fecha_creacion FROM auth_usuarios'
    ).fetchall()
    return jsonify([dict(u) for u in usuarios])

@app.route('/api/alimentos')
@api_login_requerido
def api_alimentos():
    db        = get_db()
    alimentos = db.execute('SELECT * FROM alimentos ORDER BY nombre').fetchall()
    return jsonify([dict(a) for a in alimentos])

@app.route('/api/estadisticas')
@api_login_requerido
def api_estadisticas():
    db = get_db()
    if g.rol == 'admin':
        stats = {
            'usuarios':       db.execute('SELECT COUNT(*) FROM auth_usuarios WHERE activo=1').fetchone()[0],
            'alimentos':      db.execute('SELECT COUNT(*) FROM alimentos').fetchone()[0],
            'registros':      db.execute('SELECT COUNT(*) FROM registros').fetchone()[0],
            'calorias_total': db.execute('SELECT COALESCE(SUM(calorias),0) FROM registros').fetchone()[0],
        }
    else:
        uid   = g.usuario_id
        stats = {
            'registros':      db.execute('SELECT COUNT(*) FROM registros WHERE usuario_id=?', (uid,)).fetchone()[0],
            'calorias_total': db.execute('SELECT COALESCE(SUM(calorias),0) FROM registros WHERE usuario_id=?', (uid,)).fetchone()[0],
            'calorias_hoy':   db.execute(
                "SELECT COALESCE(SUM(calorias),0) FROM registros WHERE usuario_id=? AND DATE(fecha)=DATE('now')", (uid,)
            ).fetchone()[0],
        }
    return jsonify(stats)

@app.route('/api/cargar-alimentos-json', methods=['POST'])
@api_login_requerido
@api_solo_admin
def cargar_alimentos_json():
    try:
        with open('alimentos.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        db    = get_db()
        count = 0
        for item in data['alimentos']:
            cur = db.execute(
                'INSERT OR IGNORE INTO alimentos (nombre, calorias_por_100g, categoria) VALUES (?,?,?)',
                (item['nombre'], item['calorias_por_100g'], item.get('categoria', 'general'))
            )
            count += cur.rowcount
        db.commit()
        return jsonify({'mensaje': str(count) + ' alimentos cargados'})
    except FileNotFoundError:
        return jsonify({'error': 'alimentos.json no encontrado'}), 404

@app.route('/api/perfil')
@api_login_requerido
def api_perfil():
    db      = get_db()
    usuario = db.execute(
        'SELECT id, nombre, email, rol, objetivo, fecha_creacion FROM auth_usuarios WHERE id=?',
        (g.usuario_id,)
    ).fetchone()
    return jsonify(dict(usuario))

# ─── ARRANQUE ───────────────────────────────────

def obtener_registros_usuario(usuario_id):
    db   = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    rows = db.execute('''
        SELECT r.*, a.nombre AS alimento_nombre
        FROM registros r JOIN alimentos a ON r.alimento_id=a.id
        WHERE r.usuario_id=?
    ''', (usuario_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)