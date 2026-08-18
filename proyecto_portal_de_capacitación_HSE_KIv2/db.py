import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "capacitaciones.db"

def get_connection():
    return sqlite3.connect(DB_PATH, timeout=30)  # timeout de 30 segundos

def init_db():
    """Crea las tablas necesarias y carga datos iniciales."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre_completo TEXT,
            activo BOOLEAN DEFAULT 1
        )
    ''')

    # Tabla empleados (con columna rol)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT DEFAULT 'operativo',
            usuario_id INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    # --- Tabla roles ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    ''')

    # Insertar roles iniciales (incluyendo los nuevos)
    roles_iniciales = [
        "administrativo",
        "operativo",
        "Administrativo Zona Franca",
        "Operativo Zona Franca",
        "APC Administrativo",
        "APC Operativo"   
    ]
    for rol in roles_iniciales:
        try:
            cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (rol,))
        except sqlite3.IntegrityError:
            pass  # ya existe

    # Agregar columna rol si no existe (para bases de datos antiguas)
    cursor.execute("PRAGMA table_info(empleados)")
    columnas_emp = [col[1] for col in cursor.fetchall()]
    if 'rol' not in columnas_emp:
        cursor.execute("ALTER TABLE empleados ADD COLUMN rol TEXT DEFAULT 'operativo'")

    # Tabla clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            codigo TEXT UNIQUE NOT NULL
        )
    ''')

    # Agregar columna logo_filename a clientes si no existe
    cursor.execute("PRAGMA table_info(clientes)")
    columnas = [col[1] for col in cursor.fetchall()]
    if 'logo_filename' not in columnas:
        cursor.execute("ALTER TABLE clientes ADD COLUMN logo_filename TEXT")

    # Tabla cursos (con vigencia_dias y url)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            cliente_id INTEGER NOT NULL,
            descripcion TEXT,
            duracion_horas INTEGER,
            vigencia_dias INTEGER DEFAULT 0,
            url TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    ''')
    cursor.execute("PRAGMA table_info(cursos)")
    columnas_cursos = [col[1] for col in cursor.fetchall()]
    if 'vigencia_dias' not in columnas_cursos:
        cursor.execute("ALTER TABLE cursos ADD COLUMN vigencia_dias INTEGER DEFAULT 0")
    # Migrar columna url si no existe
    if 'url' not in columnas_cursos:
        cursor.execute("ALTER TABLE cursos ADD COLUMN url TEXT")

    # Tabla asignaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asignaciones (
            id INTEGER PRIMARY KEY,
            empleado_id INTEGER NOT NULL,
            curso_id INTEGER NOT NULL,
            fecha_asignacion DATE NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            FOREIGN KEY(empleado_id) REFERENCES empleados(id),
            FOREIGN KEY(curso_id) REFERENCES cursos(id)
        )
    ''')

    # Insertar datos de clientes si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        clients_data = [
            ("ECOPETROL", "EC"),
            ("GEOPARK", "GP"),
            ("GRAN TIERRA", "GT"),
            ("PAREX", "PX"),
            ("IHSA", "IH"),
            ("APC", "AP"),
            ("SIERRACOL", "SC"),
            ("FRONTERA", "FR"),
            ("CARRAO", "CR"),
            ("ARROW EXPLORATION", "AE"),
            ("ONGC Videsh", "OV"),
            ("SAN AGUSTIN ENERGY", "SA"),
        ]
        for nombre, codigo in clients_data:
            cursor.execute("INSERT INTO clientes (nombre, codigo) VALUES (?, ?)", (nombre, codigo))

    # Migrar cliente GENERAL a APC (si existe)
    migrar_cliente_general_a_apc()

    # Insertar empleados iniciales (con rol='operativo')
    cursor.execute("SELECT COUNT(*) FROM empleados")
    if cursor.fetchone()[0] == 0:
        empleados_data = [
            ("1051635722", "ADDISON ORTIZ GONZÁLEZ"),
            ("12139028", "ALDEMAR IBÁÑEZ GOMEZ"),
            ("1122647054", "ALEJANDRO MARIO TAFUR SAMIENTO"),
            ("1121823950", "ANDRES ALBERTO HERRERA CASTRO"),
            ("1006697345", "ANDRES FELIPE CRUZ CASTIBLANCO"),
            ("7696884", "ANDRES GONGORA DÍAZ"),
            ("86085878", "ANDRES JAVIER MARTÍNEZ LEÓN"),
            ("1014313482", "ANYELO RUEDA RUEDA DAZA"),
            ("86064053", "CARLOS ANDRES ANGARITA VILLA"),
            ("1121843173", "CARLOS ANDRES PRIETO LOPEZ"),
            ("80829854", "CHRISTIAN JOHNATAN PRIETO MONDRAGÓN"),
            ("9434524", "CRISTIAN YESID TAPIAS BALLESTEROS"),
            ("1123323382", "DANIEL ALFONSO PABON C"),
            ("1049395728", "DANIEL ERMIDES ALVARADO RAMIREZ"),
            ("1123512484", "DAVID LEONARDO CASTILLO PADILLA"),
            ("1121866925", "DIDIER CLAVIJO CHAVERRA"),
            ("7721807", "DIEGO FERNANDO MORALES ORTÍZ"),
            ("1098676393", "EMMANUEL SANDOVAL GARNICA"),
            ("1121857148", "FABIO ALEXANDER TRIGOS MARTINEZ"),
            ("1118537085", "FERNANDO ALBEIRO TAPIAS BALLESTEROS"),
            ("1023941935", "FERNANDO GONZALEZ MORA"),
            ("80022365", "FERNANDO TORRES LEON"),
            ("1121903842", "FIDEL DAVID TEJEIRO ROJAS"),
            ("7719574", "FRANCISCO JAVIER RIVERA PERDOMO"),
            ("1081155239", "GERARDO ANDRES PÉREZ NIETO"),
            ("1121860796", "HECTOR LEONARDO PARRA"),
            ("1126243623", "ISAÍAS ERNESTO BUSTAMANTE MESA"),
            ("1116785274", "IVAN DARIO ROSERO PEREZ"),
            ("1116773635", "JAMES EMIRO SUESCUN PEREZ"),
            ("1075239898", "JEFFERSON ALEXANDER ROJAS FIERRO"),
            ("12117056", "JESUS LO JADER LOSADA STERLING"),
            ("1149588", "JOHAN MENCIAS"),
            ("1075216527", "JOHN HARVY MEDINA RODRIGUEZ"),
            ("7726426", "JOHN JAVIER PASCUAS VARGAS"),
            ("1073233220", "JORGE BERMUDEZ"),
            ("7698250", "JORGE ELIECER ORTIGOZA CANGREJO"),
            ("1121856822", "JORGE ENRIQUE BOTERO RINCON"),
            ("86081690", "JORGE HERNÁN DÍAZ"),
            ("7710188", "JORGE ROJAS ESQUIVEL"),
            ("80109871", "JOSE ALEXANDER CRIADO"),
            ("4964440", "JOSE GABRIEL IBARRA GOMEZ"),
            ("98625497", "JUAN DIEGO MORALES AGUDELO"),
            ("1120818084", "JUAN ESTEBAN CARO PADILLA"),
            ("1072714424", "JUAN FELIPE HERNANDEZ MARIN"),
            ("1098794317", "JUAN NICOLAS CASTILLO FORERO"),
            ("12138421", "LIBARDO SILVA GUARNIZO"),
            ("1121914071", "MANUEL ALEJANDRO LOPEZ ALFONSO"),
            ("13567460", "MARLON STICK PEREZ"),
            ("1034304090", "MICHEL OMAÑA SIERRA"),
            ("1121850261", "MIGUEL ANGEL DIAZ NIETO"),
            ("86076008", "NÉSTOR ADELIO CASTAÑEDA PENAGOS"),
            ("1075236596", "ODAIR JOSE POLO OVIEDO"),
            ("1019013255", "OSCAR FAVIAN PACHON SARMIENTO"),
            ("1116807529", "OSCAR JUNIOR DE LA CRUZ LAGUNA"),
            ("1104133854", "PABLO ANDRÉS ESCOBAR PARRA"),
            ("4904038", "ROGNY RAMOS RAMOS"),
            ("1075230409", "SAMUEL TRUJILLO CERQUERA"),
            ("1051634643", "SNEYDER ARROYO MIELES"),
            ("1082214011", "VICTOR JAVIER CORONADO CUEVAS"),
            ("7694140", "WILLINGTON  CUMBE MACIAS"),
            ("1122120041", "WILMAR  BONILLA ALDANA"),
            ("1121929448", "WILVER RIAÑO OIDOR"),
            ("1121894671", "YEFFERSON RAUL MANCERA PARRADO"),
            ("1122652247", "YEIMER DANILO BOLIVAR ORTIZ"),
            ("1075211411", "YEINSON CARRERA MENSA"),
            ("83092928", "YEISON FERNANDO MURCIA SANCHEZ"),
            ("1006534817", "YIMI ALEXANDER PEDRAZA BONILLA"),
            ("1122141343", "YOJAN STIVEN PEREZ PAEZ")
        ]
        for cedula, nombre in empleados_data:
            cursor.execute("INSERT INTO empleados (cedula, nombre, rol) VALUES (?, ?, 'operativo')", (cedula, nombre))

    # Insertar usuarios predefinidos (coordinadores, admin)
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'coord1'")
    if cursor.fetchone()[0] == 0:
        hashed = generate_password_hash("coord1pass")
        cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)",
                       ("coord1", hashed, "coordinador", "Coordinador HSE 1", 1))
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'coord2'")
    if cursor.fetchone()[0] == 0:
        hashed = generate_password_hash("coord2pass")
        cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)",
                       ("coord2", hashed, "coordinador", "Coordinador HSE 2", 1))
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed = generate_password_hash("admin123")
        cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)",
                       ("admin", hashed, "admin", "Developer Admin", 1))

    # Crear usuarios para empleados (username = cédula, password = cédula)
    cursor.execute("SELECT id, cedula, nombre FROM empleados WHERE usuario_id IS NULL")
    empleados_sin_usuario = cursor.fetchall()
    for emp_id, cedula, nombre in empleados_sin_usuario:
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (cedula,))
        if not cursor.fetchone():
            hashed = generate_password_hash(cedula)
            cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)",
                           (cedula, hashed, "empleado", nombre, 1))
            user_id = cursor.lastrowid
            cursor.execute("UPDATE empleados SET usuario_id = ? WHERE id = ?", (user_id, emp_id))
        else:
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (cedula,))
            user_id = cursor.fetchone()[0]
            cursor.execute("UPDATE empleados SET usuario_id = ? WHERE id = ?", (user_id, emp_id))

    # Actualizar vigencias y corregir asignaciones
    actualizar_vigencias_cursos(conn, cursor)
    corregir_asignaciones_sin_vencimiento(conn, cursor)

    # Asignar URLs automáticas a cursos especiales (Geopark, Frontera, Parex)
    actualizar_urls_cursos_especiales(conn, cursor)   # <-- NUEVO

    conn.commit()
    conn.close()

def migrar_cliente_general_a_apc():
    """Migra el cliente 'GENERAL' a 'APC' (si existe)."""
    conn = get_connection()
    cursor = conn.cursor()
    # Buscar cliente GENERAL
    cursor.execute("SELECT id FROM clientes WHERE nombre = 'GENERAL'")
    row = cursor.fetchone()
    if row:
        general_id = row[0]
        # Buscar cliente APC
        cursor.execute("SELECT id FROM clientes WHERE nombre = 'APC'")
        apc_row = cursor.fetchone()
        if apc_row:
            apc_id = apc_row[0]
            # Actualizar cursos de GENERAL a APC
            cursor.execute("UPDATE cursos SET cliente_id = ? WHERE cliente_id = ?", (apc_id, general_id))
            # Eliminar cliente GENERAL
            cursor.execute("DELETE FROM clientes WHERE id = ?", (general_id,))
            print(f"Cliente 'GENERAL' migrado a 'APC' (fusionado).")
        else:
            # Cambiar nombre de GENERAL a APC
            cursor.execute("UPDATE clientes SET nombre = 'APC', codigo = 'AP' WHERE id = ?", (general_id,))
            print(f"Cliente 'GENERAL' renombrado a 'APC'.")
        conn.commit()
    conn.close()

def autenticar_usuario(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, rol, nombre_completo, activo FROM usuarios WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[5] == 1 and check_password_hash(user[2], password):
        return {
            "id": user[0],
            "username": user[1],
            "rol": user[3],
            "nombre": user[4] or user[1]
        }
    return None

@st.cache_data(ttl=300)
def obtener_empleados():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, cedula, nombre, rol FROM empleados ORDER BY nombre", conn)
    conn.close()
    return df

# --------------------- FUNCIONES PARA RENUMERACIÓN DE EMPLEADOS ---------------------
def _renumerar_empleados(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM empleados ORDER BY id")
    old_ids = [row[0] for row in cursor.fetchall()]
    new_id_map = {old_id: new_id for new_id, old_id in enumerate(old_ids, start=1)}
    for old_id, new_id in new_id_map.items():
        cursor.execute("UPDATE empleados SET id = ? WHERE id = ?", (new_id, old_id))
        cursor.execute("UPDATE asignaciones SET empleado_id = ? WHERE empleado_id = ?", (new_id, old_id))
    conn.commit()

def agregar_empleado(cedula, nombre, rol='operativo'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(id) FROM empleados")
        max_id = cursor.fetchone()[0] or 0
        nuevo_id = max_id + 1
        cursor.execute("INSERT INTO empleados (id, cedula, nombre, rol) VALUES (?, ?, ?, ?)", (nuevo_id, cedula, nombre, rol))
        hashed = generate_password_hash(cedula)
        cursor.execute("INSERT INTO usuarios (username, password_hash, rol, nombre_completo, activo) VALUES (?, ?, ?, ?, ?)",
                       (cedula, hashed, "empleado", nombre, 1))
        user_id = cursor.lastrowid
        cursor.execute("UPDATE empleados SET usuario_id = ? WHERE id = ?", (user_id, nuevo_id))
        conn.commit()
        st.cache_data.clear()  # Limpiar caché para reflejar cambios
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()



def actualizar_empleado(emp_id, cedula, nombre, rol):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE empleados SET cedula = ?, nombre = ?, rol = ? WHERE id = ?", (cedula, nombre, rol, emp_id))
        cursor.execute("SELECT usuario_id FROM empleados WHERE id = ?", (emp_id,))
        row = cursor.fetchone()
        if row and row[0]:
            cursor.execute("UPDATE usuarios SET username = ?, nombre_completo = ? WHERE id = ?", (cedula, nombre, row[0]))
        conn.commit()
        st.cache_data.clear()  # Limpiar caché para reflejar cambios
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def eliminar_empleado(emp_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT usuario_id FROM empleados WHERE id = ?", (emp_id,))
        row = cursor.fetchone()
        user_id = row[0] if row else None
        cursor.execute("DELETE FROM asignaciones WHERE empleado_id = ?", (emp_id,))
        cursor.execute("DELETE FROM empleados WHERE id = ?", (emp_id,))
        if user_id:
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        _renumerar_empleados(conn)
        conn.commit()
        st.cache_data.clear()  # Limpiar caché para reflejar cambios
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar empleado: {e}")
        return False
    finally:
        conn.close()

# --------------------- CLIENTES ---------------------

@st.cache_data(ttl=300)
def obtener_clientes():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, nombre, codigo, logo_filename FROM clientes ORDER BY nombre", conn)
    conn.close()
    return df

def agregar_cliente(nombre, codigo):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (nombre, codigo) VALUES (?, ?)", (nombre, codigo))
        conn.commit()
        st.cache_data.clear()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def actualizar_cliente(cliente_id, nombre, codigo):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE clientes SET nombre = ?, codigo = ? WHERE id = ?", (nombre, codigo, cliente_id))
        conn.commit()
        st.cache_data.clear()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def eliminar_cliente(cliente_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cursos WHERE cliente_id = ?", (cliente_id,))
    cursos = cursor.fetchall()
    for curso in cursos:
        cursor.execute("DELETE FROM asignaciones WHERE curso_id = ?", (curso[0],))
    cursor.execute("DELETE FROM cursos WHERE cliente_id = ?", (cliente_id,))
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    st.cache_data.clear()
    conn.close()

def actualizar_logo_cliente(cliente_id, logo_filename):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clientes SET logo_filename = ? WHERE id = ?", (logo_filename, cliente_id))
    conn.commit()
    conn.close()

# --------------------- CURSOS ---------------------

@st.cache_data(ttl=300)
def obtener_cursos_por_cliente(cliente_id=None):
    conn = get_connection()
    if cliente_id:
        query = """
            SELECT c.id, c.nombre, c.descripcion, c.duracion_horas, c.vigencia_dias, c.url, cl.nombre as cliente
            FROM cursos c
            JOIN clientes cl ON c.cliente_id = cl.id
            WHERE c.cliente_id = ?
            ORDER BY c.nombre
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id,))
    else:
        query = """
            SELECT c.id, c.nombre, c.descripcion, c.duracion_horas, c.vigencia_dias, c.url, cl.nombre as cliente
            FROM cursos c
            JOIN clientes cl ON c.cliente_id = cl.id
            ORDER BY cl.nombre, c.nombre
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def agregar_curso(nombre, cliente_id, descripcion, duracion_horas, vigencia_dias=0, url=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Si no se proporcionó URL, verificar si es un curso especial
    if url is None:
        # Obtener nombre del cliente
        cursor.execute("SELECT nombre FROM clientes WHERE id = ?", (cliente_id,))
        cliente_row = cursor.fetchone()
        if cliente_row:
            cliente_nombre = cliente_row[0]
            # Mapeo de (nombre_curso, cliente_nombre) -> URL
            urls_especiales = {
                ("INDUCCIÓN HSEQ GEOPARK", "GEOPARK"): "https://capacitacionesgeopark.salasvirtuales.info/",
                ("MANUAL CONTROL TRABAJO", "FRONTERA"): "https://forms.office.com/pages/responsepage.aspx?id=DNU3JmDFbEOJl-vmPJZW_ZpLhxKngllFiyDSKxxg0plUM0VVTEpGRjdSVU43VFdHNzIxU0tTWklIMy4u&origin=lprLink&route=shorturl",
                ("INDUCCIÓN HSEQ FRONTERA", "FRONTERA"): "https://forms.office.com/pages/responsepage.aspx?id=DNU3JmDFbEOJl-vmPJZW_dSn9BPUc4dNgkyN2XjAfCNUQlFZTDZNMzJZTE41MFJXTDFTMFZFODk1NSQlQCN0PWcu&origin=QRCode&qrcodeorigin=presentation&route=shorturl",
                ("INDUCCIÓN HSEQ PAREX", "PAREX"): "https://controlingreso.parexresources.com/es-ES/"
            }
            url = urls_especiales.get((nombre, cliente_nombre))
    
    cursor.execute("""
        INSERT INTO cursos (nombre, cliente_id, descripcion, duracion_horas, vigencia_dias, url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, cliente_id, descripcion, duracion_horas, vigencia_dias, url))
    conn.commit()
    st.cache_data.clear()
    conn.close()

def actualizar_curso(curso_id, nombre, cliente_id, descripcion, duracion_horas, vigencia_dias=0, url=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cursos
        SET nombre = ?, cliente_id = ?, descripcion = ?, duracion_horas = ?, vigencia_dias = ?, url = ?
        WHERE id = ?
    """, (nombre, cliente_id, descripcion, duracion_horas, vigencia_dias, url, curso_id))
    conn.commit()
    st.cache_data.clear()
    conn.close()

def eliminar_curso(curso_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM asignaciones WHERE curso_id = ?", (curso_id,))
    cursor.execute("DELETE FROM cursos WHERE id = ?", (curso_id,))
    conn.commit()
    st.cache_data.clear()
    conn.close()

def obtener_vigencia_curso(curso_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vigencia_dias FROM cursos WHERE id = ?", (curso_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

# --------------------- ASIGNACIONES ---------------------
def empleado_tiene_curso_vigente(empleado_id, curso_id):
    """
    Retorna True si el empleado ya tiene una asignación del curso
    con fecha_vencimiento >= hoy (es decir, vigente).
    """
    conn = get_connection()
    cursor = conn.cursor()
    hoy = date.today().isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM asignaciones
        WHERE empleado_id = ? AND curso_id = ?
          AND fecha_vencimiento >= ?
          AND estado != 'vencido'   -- por si acaso
    """, (empleado_id, curso_id, hoy))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def asignar_curso(empleado_id, curso_id, fecha_vencimiento=None, fecha_asignacion=None, estado='pendiente'):
    """
    Asigna un curso a un empleado.
    - estado puede ser: 'pendiente', 'sin_ejecucion', 'completado', 'vencido', etc.
    - Si fecha_vencimiento es None, se calcula automáticamente según la vigencia del curso.
    """
    if fecha_asignacion is None:
        fecha_asignacion = date.today().isoformat()
    
    if fecha_vencimiento is None:
        vigencia = obtener_vigencia_curso(curso_id)
        if vigencia == -1:
            fecha_vencimiento = date(9999, 12, 31).isoformat()
        else:
            fecha_vencimiento = (date.fromisoformat(fecha_asignacion) + timedelta(days=vigencia)).isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO asignaciones (empleado_id, curso_id, fecha_asignacion, fecha_vencimiento, estado)
        VALUES (?, ?, ?, ?, ?)
    """, (empleado_id, curso_id, fecha_asignacion, fecha_vencimiento, estado))  # <-- uso del parámetro estado
    conn.commit()
    st.cache_data.clear()
    conn.close()

def actualizar_estado_asignacion(asignacion_id, nuevo_estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE asignaciones SET estado = ? WHERE id = ?", (nuevo_estado, asignacion_id))
    conn.commit()
    conn.close()

def eliminar_asignacion(asignacion_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM asignaciones WHERE id = ?", (asignacion_id,))
    conn.commit()
    st.cache_data.clear()
    conn.close()

def actualizar_asignacion(asignacion_id, estado=None, fecha_vencimiento=None, fecha_asignacion=None):
    """
    Actualiza el estado, fecha de vencimiento y/o fecha de asignación de una asignación.
    Todos los parámetros son opcionales; solo se actualizan los que no sean None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        if estado is not None:
            updates.append("estado = ?")
            params.append(estado)
        if fecha_vencimiento is not None:
            updates.append("fecha_vencimiento = ?")
            params.append(fecha_vencimiento)
        if fecha_asignacion is not None:
            updates.append("fecha_asignacion = ?")
            params.append(fecha_asignacion)
        if updates:
            query = f"UPDATE asignaciones SET {', '.join(updates)} WHERE id = ?"
            params.append(asignacion_id)
            cursor.execute(query, params)
            conn.commit()
            st.cache_data.clear()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def obtener_asignaciones(empleado_id=None):
    conn = get_connection()
    if empleado_id:
        query = """
            SELECT a.id, e.nombre as empleado, e.cedula as cedula,
                   cu.nombre as curso, cl.nombre as cliente, cu.url as url_curso,
                   a.fecha_asignacion, a.fecha_vencimiento, a.estado
            FROM asignaciones a
            JOIN empleados e ON a.empleado_id = e.id
            JOIN cursos cu ON a.curso_id = cu.id
            JOIN clientes cl ON cu.cliente_id = cl.id
            WHERE a.empleado_id = ?
            ORDER BY a.fecha_vencimiento
        """
        df = pd.read_sql_query(query, conn, params=(empleado_id,))
    else:
        query = """
            SELECT a.id, e.nombre as empleado, e.cedula as cedula,
                   cu.nombre as curso, cl.nombre as cliente, cu.url as url_curso,
                   a.fecha_asignacion, a.fecha_vencimiento, a.estado
            FROM asignaciones a
            JOIN empleados e ON a.empleado_id = e.id
            JOIN cursos cu ON a.curso_id = cu.id
            JOIN clientes cl ON cu.cliente_id = cl.id
            ORDER BY e.nombre, a.fecha_vencimiento
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --------------------- LÓGICA DE ESTADO Y RENOVACIÓN ---------------------

def clasificar_estado(fecha_vencimiento, hoy, dias_alerta=30):
    """
    Clasifica una asignación según la fecha de vencimiento (verdad absoluta).
    Vigente = fecha no vencida. Vencido = fecha pasada. Punto.
    """
    if fecha_vencimiento.year >= 9999:
        return 'sin_vencimiento'
    if fecha_vencimiento < hoy:
        return 'vencido'
    if fecha_vencimiento <= hoy + timedelta(days=dias_alerta):
        return 'proximo'
    return 'vigente'

def necesita_renovacion(estado_bd, fecha_vencimiento, hoy, dias_alerta=30):
    """
    True si es un curso completado cuya certificación ya venció o vence pronto.
    """
    if estado_bd != 'completado':
        return False
    if fecha_vencimiento.year >= 9999:
        return False
    return fecha_vencimiento < hoy or fecha_vencimiento <= hoy + timedelta(days=dias_alerta)
def obtener_indicadores_empleado(empleado_id):
    hoy = date.today()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT estado, fecha_vencimiento FROM asignaciones WHERE empleado_id = ?", (empleado_id,))
    rows = cursor.fetchall()

    total = len(rows)
    completados = 0
    sin_ejecucion = 0
    vencidos = 0
    proximos = 0
    vigentes = 0
    sin_vencimiento = 0
    por_renovar = 0

    for estado_bd, fecha_venc_str in rows:
        fecha_venc = datetime.fromisoformat(fecha_venc_str).date()
        cat = clasificar_estado(fecha_venc, hoy)

        if estado_bd == 'completado':
            completados += 1
            if necesita_renovacion(estado_bd, fecha_venc, hoy):
                por_renovar += 1
        elif estado_bd == 'sin_ejecucion':
            sin_ejecucion += 1

        if cat == 'vencido':
            vencidos += 1
        elif cat == 'proximo':
            proximos += 1
        elif cat == 'vigente':
            vigentes += 1
        elif cat == 'sin_vencimiento':
            sin_vencimiento += 1

    porcentaje = (completados / total * 100) if total > 0 else 0
    conn.close()
    return {
        "total": total,
        "completados": completados,
        "porcentaje": round(porcentaje, 2),
        "vigentes": vigentes,
        "vencidos": vencidos,
        "proximos": proximos,
        "sin_ejecucion": sin_ejecucion,
        "sin_vencimiento": sin_vencimiento,
        "por_renovar": por_renovar
    }

@st.cache_data(ttl=300)
def obtener_indicadores_resumen():
    conn = get_connection()
    query = """
        SELECT 
            e.id AS empleado_id,
            e.nombre,
            e.rol,
            COUNT(a.id) AS total,
            SUM(CASE WHEN a.estado = 'completado' THEN 1 ELSE 0 END) AS completados,
            SUM(CASE WHEN a.estado = 'sin_ejecucion' THEN 1 ELSE 0 END) AS sin_ejecucion,
            SUM(CASE WHEN date(a.fecha_vencimiento) < date('now') AND a.estado != 'completado' THEN 1 ELSE 0 END) AS vencidos,
            SUM(CASE WHEN date(a.fecha_vencimiento) BETWEEN date('now') AND date('now', '+30 days') AND a.estado != 'completado' THEN 1 ELSE 0 END) AS proximos,
            SUM(CASE WHEN date(a.fecha_vencimiento) >= date('now') AND a.estado != 'completado' THEN 1 ELSE 0 END) AS vigentes,
            SUM(CASE WHEN a.estado = 'completado' AND (date(a.fecha_vencimiento) < date('now') OR date(a.fecha_vencimiento) <= date('now', '+30 days')) THEN 1 ELSE 0 END) AS por_renovar
        FROM empleados e
        LEFT JOIN asignaciones a ON e.id = a.empleado_id
        GROUP BY e.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Calcular porcentaje
    df['porcentaje'] = (df['completados'] / df['total'] * 100).round(2).fillna(0)
    # Asegurar que no haya valores nulos
    df = df.fillna(0)
    return df

def actualizar_vigencias_cursos(conn=None, cursor=None):
    """
    Actualiza las vigencias de los cursos según el mapeo definido.
    Si no se pasan conn y cursor, crea su propia conexión (para usos externos).
    """
    cerrar_al_final = False
    if conn is None or cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        cerrar_al_final = True

    try:
        mapeo_vigencias = {
            "COMPETENCIA TCT - BAJA": 1080,
            "COMPETENCIA TCT - MEDIA": 1080,
            "COORDINADOR EN ALTURAS": -1,
            "CURSO RIESGO ELÉCTRICO 40 HRS": 360,
            "CURSOS CLAP": -1,
            "ECOEDUCATE": 360,
            "ESTÁNDAR VIAL": 720,
            "AVAL PRE-BOMBEROS": 360,
            "FASE III  PRODUCCIÓN - VRO": 720,
            "FASE III PRODUCCIÓN - PPU": 720,
            "FASE III PRODUCCIÓN - VRC": 720,
            "FASE III SUBSUELO": 720,
            "FUNDAMENTOS PMM": -1,
            "H2S": 720,
            "INDUCCIÓN HSEQ FRONTERA": 360,
            "INDUCCIÓN HSEQ GEOPARK": 180,
            "INDUCCIÓN HSEQ PAREX": 180,
            "INSTRUCTIVO MEDICIÓN GASES": 720,
            "MANEJO DEFENSIVO": 720,
            "MANUAL CONTROL TRABAJO": 720,
            "MASE PARA ELECTRICISTAS": 360,
            "MEDIDOR DE ATMOSFERAS 5X": 1080,
            "MEMORANDO TCT GDA": 360,
            "MEMORANDO TCT GDT": 360,
            "MEMORANDO TCT GLH": 360,
            "MEMORANDO TCT GOR": 360,
            "MEMORANDO TCT GPA - PPU": 360,
            "MEMORANDO TCT VRC": 360,
            "PREVENCIÓN PMM": -1,
            "SAES ELECTRICISTAS": 360,
            "TRABAJO SEGURO EN ALTURAS": 540,
            "FASE III PRODUCCIÓN - GOR": 360
        }

        cursor.execute("SELECT id, nombre FROM cursos")
        cursos = cursor.fetchall()

        actualizados = 0
        for curso_id, nombre in cursos:
            vigencia = mapeo_vigencias.get(nombre)
            if vigencia is None:
                nombre_norm = ' '.join(nombre.strip().split())
                for key, val in mapeo_vigencias.items():
                    if ' '.join(key.strip().split()) == nombre_norm:
                        vigencia = val
                        break
            if vigencia is not None:
                cursor.execute("UPDATE cursos SET vigencia_dias = ? WHERE id = ?", (vigencia, curso_id))
                actualizados += cursor.rowcount

        conn.commit()
        if cerrar_al_final:
            conn.close()
        if actualizados > 0:
            print(f"Vigencias actualizadas para {actualizados} cursos.")
        return actualizados

    except Exception as e:
        if cerrar_al_final:
            conn.rollback()
            conn.close()
        raise e

def corregir_asignaciones_sin_vencimiento(conn=None, cursor=None):
    cerrar_al_final = False
    if conn is None or cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        cerrar_al_final = True

    try:
        cursor.execute("SELECT id FROM cursos WHERE vigencia_dias = -1")
        cursos_sin_vencimiento = [row[0] for row in cursor.fetchall()]

        if cursos_sin_vencimiento:
            placeholders = ','.join('?' * len(cursos_sin_vencimiento))
            cursor.execute(f"""
                UPDATE asignaciones 
                SET fecha_vencimiento = '9999-12-31', 
                    estado = 'pendiente'
                WHERE curso_id IN ({placeholders})
            """, cursos_sin_vencimiento)
            actualizadas = cursor.rowcount
            conn.commit()
            print(f"Asignaciones corregidas para cursos sin vencimiento: {actualizadas}")
        else:
            print("No hay cursos sin vencimiento.")

        if cerrar_al_final:
            conn.close()

    except Exception as e:
        if cerrar_al_final:
            conn.rollback()
            conn.close()
        raise e

def actualizar_urls_cursos_especiales(conn=None, cursor=None):
    cerrar_al_final = False
    if conn is None or cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        cerrar_al_final = True

    try:
        urls_especiales = {
            ("INDUCCIÓN HSEQ GEOPARK", "GEOPARK"): "https://capacitacionesgeopark.salasvirtuales.info/",
            ("MANUAL CONTROL TRABAJO", "FRONTERA"): "https://forms.office.com/pages/responsepage.aspx?id=DNU3JmDFbEOJl-vmPJZW_ZpLhxKngllFiyDSKxxg0plUM0VVTEpGRjdSVU43VFdHNzIxU0tTWklIMy4u&origin=lprLink&route=shorturl",
            ("INDUCCIÓN HSEQ FRONTERA", "FRONTERA"): "https://forms.office.com/pages/responsepage.aspx?id=DNU3JmDFbEOJl-vmPJZW_dSn9BPUc4dNgkyN2XjAfCNUQlFZTDZNMzJZTE41MFJXTDFTMFZFODk1NSQlQCN0PWcu&origin=QRCode&qrcodeorigin=presentation&route=shorturl",
            ("INDUCCIÓN HSEQ PAREX", "PAREX"): "https://controlingreso.parexresources.com/es-ES/"
        }

        for (nombre_curso, nombre_cliente), url in urls_especiales.items():
            cursor.execute("SELECT id FROM clientes WHERE nombre = ?", (nombre_cliente,))
            cliente_row = cursor.fetchone()
            if cliente_row:
                cliente_id = cliente_row[0]
                cursor.execute("SELECT id, url FROM cursos WHERE nombre = ? AND cliente_id = ?", (nombre_curso, cliente_id))
                curso_row = cursor.fetchone()
                if curso_row:
                    curso_id, url_actual = curso_row
                    if url_actual != url:
                        cursor.execute("UPDATE cursos SET url = ? WHERE id = ?", (url, curso_id))
                        print(f"✔ URL actualizada para '{nombre_curso}' de {nombre_cliente}")
                else:
                    print(f"⚠ Curso '{nombre_curso}' de {nombre_cliente} no encontrado.")

        conn.commit()
        if cerrar_al_final:
            conn.close()

    except Exception as e:
        if cerrar_al_final:
            conn.rollback()
            conn.close()
        raise e

# ===================== ROLES =====================

def obtener_roles():
    """Devuelve una lista con todos los nombres de roles ordenados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM roles ORDER BY nombre")
    roles = [row[0] for row in cursor.fetchall()]
    conn.close()
    return roles

def agregar_rol(nombre):
    """Agrega un nuevo rol a la tabla. Retorna True si éxito, False si ya existe."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        st.cache_data.clear()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False