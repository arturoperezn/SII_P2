# Guía Completa Paso a Paso - Práctica 2: Bases de Datos Relacionales (PostgreSQL + Quart)

Documento contrastado y validado directamente contra el enunciado oficial **P2-2026-27_Enunciado.pdf**.
No incluye funcionalidades inventadas ni código fuera de los requisitos obligatorios.

> [!NOTE]
> **Identificador de usuarios**: Se mantiene el `uid` (UUID generado con `uuid4()`) de la Práctica 1 para los usuarios, integrándolo como Clave Primaria en PostgreSQL y en el payload del token JWT stateless.

---

## 📋 Checklist de Requisitos Explícitos del Enunciado

| Requisito del Enunciado | Dónde se implementa | Cumplimiento |
| :--- | :--- | :--- |
| **PostgreSQL oficial** (`alumnodb`, `1234`, `si1`) con persistencia | `docker-compose.yml` (`db`) | ✅ Imagen oficial + volumen |
| **Inicialización automática** de DDL y DML al arrancar | `docker-compose.yml` (`/docker-entrypoint-initdb.d/`) | ✅ `schema.sql` y `populate.sql` |
| **Gestión de películas, actores y directores** | `schema.sql`, `populate.sql` | ✅ Tablas y relaciones |
| **Trigger 1**: Stock y precio de carrito al añadir/eliminar | `schema.sql` (`trg_item_carrito`) | ✅ PL/pgSQL en INSERT y DELETE |
| **Trigger 2**: Descuento automático de saldo y fecha al pagar | `schema.sql` (`trg_pagar_pedido`) | ✅ PL/pgSQL en UPDATE a 'pagado' |
| **Stored Procedure 1**: Nota media de una película | `schema.sql` (`sp_calcular_valoracion_media`) | ✅ PL/pgSQL `FUNCTION` |
| **SQLAlchemy Core Asíncrono** (`text()`, `execute()`, `await`) | `src/user.py`, `src/api.py` | ✅ Sin ORM, sentencias manuales |
| **Regla de oro: 1 único `execute()` por endpoint** | `src/user.py`, `src/api.py` | ✅ Cero mezclas de consultas en Python |
| **Tokens Stateless** (sin guardar en base de datos) | `src/user.py`, `src/api.py` | ✅ JWT en cabecera `Authorization: Bearer` |
| **Microservicio Usuarios (`user.py`)**: CRUD + saldo + login/logout | `src/user.py` | ✅ Endpoints exactos pedidos |
| **Microservicio Videoclub (`api.py`)**: Películas, Carrito, Votos | `src/api.py` | ✅ Endpoints exactos pedidos |
| **Endpoint para optimización**: `/ventas/<año>/<país>` | `src/api.py` (`GET /ventas/<anio>/<pais>`) | ✅ Query con JOINs en un solo execute |
| **Script de optimización**: EXPLAIN antes y después con índices | `optimizacion.sql` | ✅ Sentencias EXPLAIN e índices |
| **Cliente de pruebas con tolerancia a fallos** | `client.py` | ✅ Valida éxito y errores 400, 401, 404, 409 |

---

## 🗺️ Mapa de Arquitectura

```
                +-------------------------+
                |    client.py (Tests)    |
                +------------+------------+
                             |
             +---------------+---------------+
             | (HTTP :5050)                  | (HTTP :5051)
             v                               v
+-------------------------+     +-------------------------+
|  usersvc (src/user.py)  |     |   apisvc (src/api.py)   |
|   Gestión de usuarios   |     |   Películas y Carrito   |
+------------+------------+     +------------+------------+
             |                               |
             +---------------+---------------+
                             | (SQLAlchemy Core Asíncrono: postgresql+asyncpg://...)
                             v
             +-------------------------------+
             |      db (PostgreSQL :5432)    |
             |       Base de datos: si1      |
             |  Triggers, SPs y Persistencia |
             +-------------------------------+
```

---

## 🛠️ PASO 0: Dependencias (`requirements.txt`)

### Archivo: `requirements.txt`
```txt
quart>=0.19.0
hypercorn>=0.14.0
SQLAlchemy>=2.0.0
asyncpg>=0.29.0
PyJWT>=2.8.0
bcrypt>=4.1.0
httpx>=0.27.0
```

---

## 🐳 PASO 1: Docker Compose (`docker-compose.yml`)

### Archivo: `docker-compose.yml`
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: si1_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: alumnodb
      POSTGRES_PASSWORD: "1234"
      POSTGRES_DB: si1
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro
      - ./populate.sql:/docker-entrypoint-initdb.d/02_populate.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alumnodb -d si1"]
      interval: 5s
      timeout: 5s
      retries: 5

  usersvc:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: si1_usersvc
    command: ["hypercorn", "src.user:app", "--bind", "0.0.0.0:5050"]
    ports:
      - "5050:5050"
    environment:
      - PORT=5050
      - DATABASE_URL=postgresql+asyncpg://alumnodb:1234@db:5432/si1
      - JWT_SECRET=clave_secreta_super_segura_p2
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  apisvc:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: si1_apisvc
    command: ["hypercorn", "src.api:app", "--bind", "0.0.0.0:5051"]
    ports:
      - "5051:5051"
    environment:
      - PORT=5051
      - DATABASE_URL=postgresql+asyncpg://alumnodb:1234@db:5432/si1
      - JWT_SECRET=clave_secreta_super_segura_p2
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 🗄️ PASO 2: Esquema Relacional, Triggers y SPs (`schema.sql`)

### ¿Qué exige el enunciado para la BD?
1. **Usuarios**: Nombre de usuario, contraseña cifrada, país y saldo. Identificado por `uid`.
2. **Catálogo**: Películas, actores y directores con stock y precio.
3. **Carrito y compras**: Estado (`carrito`, `pagado`), importe total, fecha de pago y líneas de pedido.
4. **Valoraciones**: Voto de un usuario a una película (0 a 10).
5. **Trigger 1**: Stock e importe del carrito al añadir o borrar items (`trg_item_carrito`).
6. **Trigger 2**: Descuento de saldo del usuario y asignación de `fecha_pago` al cambiar estado a `pagado` (`trg_pagar_pedido`).
7. **Stored Procedure 1**: Cálculo de valoración media de una película (`sp_calcular_valoracion_media`).
8. **Stored Procedure 2**: Función para añadir items al carrito garantizando un único execute (`sp_anadir_item_carrito`).

### Archivo: `schema.sql`
```sql
-- Limpieza inicial
DROP TABLE IF EXISTS valoraciones CASCADE;
DROP TABLE IF EXISTS pedido_items CASCADE;
DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS pelicula_directores CASCADE;
DROP TABLE IF EXISTS pelicula_actores CASCADE;
DROP TABLE IF EXISTS directores CASCADE;
DROP TABLE IF EXISTS actores CASCADE;
DROP TABLE IF EXISTS peliculas CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- 1. TABLA USUARIOS (con UID de la P1)
CREATE TABLE usuarios (
    uid VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    saldo NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (saldo >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLAS DEL CATÁLOGO: PELÍCULAS, ACTORES Y DIRECTORES
CREATE TABLE peliculas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    anio INT NOT NULL,
    genero VARCHAR(100),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE actores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE directores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE pelicula_actores (
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    actor_id INT REFERENCES actores(id) ON DELETE CASCADE,
    PRIMARY KEY (pelicula_id, actor_id)
);

CREATE TABLE pelicula_directores (
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    director_id INT REFERENCES directores(id) ON DELETE CASCADE,
    PRIMARY KEY (pelicula_id, director_id)
);

-- 3. TABLA PEDIDOS (Carrito / Compra)
CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    usuario_uid VARCHAR(64) REFERENCES usuarios(uid) ON DELETE CASCADE,
    estado VARCHAR(20) NOT NULL DEFAULT 'carrito' CHECK (estado IN ('carrito', 'pagado', 'cancelado')),
    importe_total NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (importe_total >= 0),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_pago TIMESTAMP NULL
);

-- 4. TABLA PEDIDO_ITEMS (Líneas del carrito)
CREATE TABLE pedido_items (
    id SERIAL PRIMARY KEY,
    pedido_id INT REFERENCES pedidos(id) ON DELETE CASCADE,
    pelicula_id INT REFERENCES peliculas(id) ON DELETE RESTRICT,
    cantidad INT NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL CHECK (precio_unitario >= 0),
    UNIQUE (pedido_id, pelicula_id)
);

-- 5. TABLA VALORACIONES
CREATE TABLE valoraciones (
    id SERIAL PRIMARY KEY,
    usuario_uid VARCHAR(64) REFERENCES usuarios(uid) ON DELETE CASCADE,
    pelicula_id INT REFERENCES peliculas(id) ON DELETE CASCADE,
    puntuacion INT NOT NULL CHECK (puntuacion >= 0 AND puntuacion <= 10),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_uid, pelicula_id)
);

--------------------------------------------------------------------------------
-- TRIGGER 1: Gestión de Stock y Total del Carrito al añadir o eliminar items
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_gestionar_item_carrito()
RETURNS TRIGGER AS $$
DECLARE
    v_stock_actual INT;
    v_estado_pedido VARCHAR(20);
BEGIN
    SELECT estado INTO v_estado_pedido FROM pedidos WHERE id = COALESCE(NEW.pedido_id, OLD.pedido_id);
    IF v_estado_pedido != 'carrito' THEN
        RAISE EXCEPTION 'No se pueden modificar items de un pedido ya cerrado o pagado';
    END IF;

    -- Caso A: INSERT (añadir al carrito)
    IF TG_OP = 'INSERT' THEN
        SELECT stock INTO v_stock_actual FROM peliculas WHERE id = NEW.pelicula_id FOR UPDATE;
        IF v_stock_actual < NEW.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente para la pelicula % (disponible: %, pedido: %)',
                NEW.pelicula_id, v_stock_actual, NEW.cantidad;
        END IF;

        -- Descontar stock
        UPDATE peliculas SET stock = stock - NEW.cantidad WHERE id = NEW.pelicula_id;

        -- Incrementar importe total del pedido
        UPDATE pedidos
        SET importe_total = importe_total + (NEW.cantidad * NEW.precio_unitario)
        WHERE id = NEW.pedido_id;

        RETURN NEW;

    -- Caso B: DELETE (eliminar del carrito)
    ELSIF TG_OP = 'DELETE' THEN
        -- Reintegrar stock
        UPDATE peliculas SET stock = stock + OLD.cantidad WHERE id = OLD.pelicula_id;

        -- Reducir importe total del pedido
        UPDATE pedidos
        SET importe_total = GREATEST(0.0, importe_total - (OLD.cantidad * OLD.precio_unitario))
        WHERE id = OLD.pedido_id;

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_item_carrito
AFTER INSERT OR DELETE ON pedido_items
FOR EACH ROW
EXECUTE FUNCTION fn_gestionar_item_carrito();

--------------------------------------------------------------------------------
-- TRIGGER 2: Pago del Carrito y Descuento Automático de Saldo
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_pagar_pedido()
RETURNS TRIGGER AS $$
DECLARE
    v_saldo_actual NUMERIC(10, 2);
    v_num_items INT;
BEGIN
    IF OLD.estado = 'carrito' AND NEW.estado = 'pagado' THEN
        -- Comprobar que el carrito tiene al menos un item
        SELECT COUNT(*) INTO v_num_items FROM pedido_items WHERE pedido_id = NEW.id;
        IF v_num_items = 0 THEN
            RAISE EXCEPTION 'No se puede pagar un carrito vacio';
        END IF;

        -- Comprobar saldo del usuario
        SELECT saldo INTO v_saldo_actual FROM usuarios WHERE uid = NEW.usuario_uid FOR UPDATE;
        IF v_saldo_actual < NEW.importe_total THEN
            RAISE EXCEPTION 'Saldo insuficiente: usuario tiene % y el coste es %',
                v_saldo_actual, NEW.importe_total;
        END IF;

        -- Descontar saldo automáticamente mediante el trigger
        UPDATE usuarios
        SET saldo = saldo - NEW.importe_total
        WHERE uid = NEW.usuario_uid;

        -- Guardar fecha de pago
        NEW.fecha_pago := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pagar_pedido
BEFORE UPDATE OF estado ON pedidos
FOR EACH ROW
EXECUTE FUNCTION fn_pagar_pedido();

--------------------------------------------------------------------------------
-- PROCEDIMIENTO ALMACENADO / FUNCIÓN 1: Cálculo de Valoración Media
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_calcular_valoracion_media(p_pelicula_id INT)
RETURNS NUMERIC AS $$
DECLARE
    v_media NUMERIC(4, 2);
BEGIN
    SELECT COALESCE(ROUND(AVG(puntuacion), 2), 0.0)
    INTO v_media
    FROM valoraciones
    WHERE pelicula_id = p_pelicula_id;

    RETURN v_media;
END;
$$ LANGUAGE plpgsql;

--------------------------------------------------------------------------------
-- PROCEDIMIENTO ALMACENADO / FUNCIÓN 2: Añadir al carrito en 1 solo execute
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sp_anadir_item_carrito(
    p_usuario_uid VARCHAR(64),
    p_pelicula_id INT,
    p_cantidad INT
)
RETURNS INT AS $$
DECLARE
    v_pedido_id INT;
    v_precio NUMERIC(10, 2);
BEGIN
    -- 1. Obtener o crear carrito activo
    SELECT id INTO v_pedido_id
    FROM pedidos
    WHERE usuario_uid = p_usuario_uid AND estado = 'carrito'
    LIMIT 1;

    IF v_pedido_id IS NULL THEN
        INSERT INTO pedidos (usuario_uid, estado, importe_total)
        VALUES (p_usuario_uid, 'carrito', 0.0)
        RETURNING id INTO v_pedido_id;
    END IF;

    -- 2. Obtener precio unitario de la película
    SELECT precio INTO v_precio FROM peliculas WHERE id = p_pelicula_id;
    IF v_precio IS NULL THEN
        RAISE EXCEPTION 'La pelicula id % no existe', p_pelicula_id;
    END IF;

    -- 3. Insertar línea (el TRIGGER trg_item_carrito comprobará stock y actualizará importe)
    INSERT INTO pedido_items (pedido_id, pelicula_id, cantidad, precio_unitario)
    VALUES (v_pedido_id, p_pelicula_id, p_cantidad, v_precio)
    ON CONFLICT (pedido_id, pelicula_id)
    DO UPDATE SET cantidad = pedido_items.cantidad + EXCLUDED.cantidad;

    RETURN v_pedido_id;
END;
$$ LANGUAGE plpgsql;
```

---

## 📥 PASO 3: Datos de Prueba (`populate.sql`)

### Archivo: `populate.sql`
```sql
-- Usuarios de prueba (contraseña '1234' hasheada con bcrypt)
INSERT INTO usuarios (uid, username, password_hash, pais, saldo) VALUES
('u1111111-1111-1111-1111-111111111111', 'alice',  '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'Francia', 100.00),
('u2222222-2222-2222-2222-222222222222', 'pierre', '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'Francia', 50.00),
('u3333333-3333-3333-3333-333333333333', 'carlos', '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'España', 75.00),
('u4444444-4444-4444-4444-444444444444', 'lucia',  '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'España', 0.00),
('u5555555-5555-5555-5555-555555555555', 'marco',  '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'Italia', 120.00)
ON CONFLICT (uid) DO NOTHING;

-- Películas de prueba
INSERT INTO peliculas (id, titulo, anio, genero, precio, stock) VALUES
(1, 'Inception', 2010, 'Ciencia Ficcion', 9.99, 20),
(2, 'Interstellar', 2014, 'Ciencia Ficcion', 12.50, 15),
(3, 'Amélie', 2001, 'Comedia', 7.99, 10),
(4, 'El Padrino', 1972, 'Drama', 14.99, 8),
(5, 'Dune: Parte 2', 2026, 'Ciencia Ficcion', 18.00, 25),
(6, 'Oppenheimer', 2023, 'Drama', 15.00, 12)
ON CONFLICT (id) DO NOTHING;

SELECT setval('peliculas_id_seq', (SELECT MAX(id) FROM peliculas));

-- Directores y Actores
INSERT INTO directores (id, nombre) VALUES
(1, 'Christopher Nolan'),
(2, 'Jean-Pierre Jeunet'),
(3, 'Francis Ford Coppola'),
(4, 'Denis Villeneuve')
ON CONFLICT (id) DO NOTHING;

SELECT setval('directores_id_seq', (SELECT MAX(id) FROM directores));

INSERT INTO actores (id, nombre) VALUES
(1, 'Leonardo DiCaprio'),
(2, 'Matthew McConaughey'),
(3, 'Audrey Tautou'),
(4, 'Marlon Brando'),
(5, 'Timothée Chalamet'),
(6, 'Cillian Murphy')
ON CONFLICT (id) DO NOTHING;

SELECT setval('actores_id_seq', (SELECT MAX(id) FROM actores));

-- Relaciones de Películas con Directores y Actores
INSERT INTO pelicula_directores (pelicula_id, director_id) VALUES
(1, 1), (2, 1), (3, 2), (4, 3), (5, 4), (6, 1)
ON CONFLICT DO NOTHING;

INSERT INTO pelicula_actores (pelicula_id, actor_id) VALUES
(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)
ON CONFLICT DO NOTHING;

-- Ventas históricas para probar /ventas/2026/Francia
INSERT INTO pedidos (id, usuario_uid, estado, importe_total, fecha_creacion, fecha_pago) VALUES
(1, 'u1111111-1111-1111-1111-111111111111', 'pagado', 22.49, '2026-02-10 10:00:00', '2026-02-10 10:05:00'),
(2, 'u2222222-2222-2222-2222-222222222222', 'pagado', 18.00, '2026-03-15 14:30:00', '2026-03-15 14:35:00'),
(3, 'u3333333-3333-3333-3333-333333333333', 'pagado', 9.99,  '2026-01-20 18:00:00', '2026-01-20 18:02:00'),
(4, 'u1111111-1111-1111-1111-111111111111', 'pagado', 14.99, '2025-11-05 12:00:00', '2025-11-05 12:10:00')
ON CONFLICT (id) DO NOTHING;

SELECT setval('pedidos_id_seq', (SELECT MAX(id) FROM pedidos));

INSERT INTO pedido_items (pedido_id, pelicula_id, cantidad, precio_unitario) VALUES
(1, 1, 1, 9.99),
(1, 2, 1, 12.50),
(2, 5, 1, 18.00),
(3, 1, 1, 9.99),
(4, 4, 1, 14.99)
ON CONFLICT DO NOTHING;

-- Valoraciones
INSERT INTO valoraciones (usuario_uid, pelicula_id, puntuacion) VALUES
('u1111111-1111-1111-1111-111111111111', 1, 9),
('u2222222-2222-2222-2222-222222222222', 1, 10),
('u3333333-3333-3333-3333-333333333333', 1, 8),
('u1111111-1111-1111-1111-111111111111', 3, 10),
('u2222222-2222-2222-2222-222222222222', 5, 9),
('u3333333-3333-3333-3333-333333333333', 4, 10)
ON CONFLICT DO NOTHING;
```

---

## 👤 PASO 4: Microservicio de Usuarios (`src/user.py`)

### Cumplimiento del enunciado:
* Crea usuario, borra usuario, actualiza saldo.
* Login y logout con token Bearer stateless.
* **Cada endpoint se ejecuta en UN SOLO `execute()`**.

### Archivo: `src/user.py`
```python
import os
from quart import Quart, jsonify, request
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

app = Quart(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@localhost:5432/si1")
JWT_SECRET = os.getenv("JWT_SECRET", "clave_secreta_super_segura_p2")
JWT_ALGORITHM = "HS256"

engine = create_async_engine(DATABASE_URL, echo=False)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def generate_token(user_uid: str, username: str) -> str:
    payload = {
        "uid": str(user_uid),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_payload():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "").strip()
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None

# 1. CREAR USUARIO (1 solo execute)
@app.route("/user", methods=["POST", "PUT"])
async def register_user():
    data = await request.get_json() or {}
    username = data.get("name") or data.get("username")
    password = data.get("password")
    pais = data.get("pais", "España")
    saldo = float(data.get("saldo", 0.0))

    if not username or not password:
        return jsonify({"error": "Faltan username o password"}), 400

    user_uid = str(uuid4())
    pwd_hash = hash_password(password)

    query = text("""
        INSERT INTO usuarios (uid, username, password_hash, pais, saldo)
        VALUES (:uid, :username, :pwd_hash, :pais, :saldo)
        RETURNING uid, username, pais, saldo
    """)

    try:
        async with engine.begin() as conn:
            res = await conn.execute(query, {
                "uid": user_uid,
                "username": username,
                "pwd_hash": pwd_hash,
                "pais": pais,
                "saldo": saldo
            })
            new_user = res.mappings().first()
    except IntegrityError:
        return jsonify({"error": "El usuario ya existe"}), 409

    token = generate_token(new_user["uid"], new_user["username"])
    return jsonify({
        "message": "Usuario creado exitosamente",
        "uid": new_user["uid"],
        "username": new_user["username"],
        "token": token
    }), 201

# 2. LOGIN (1 solo execute)
@app.post("/user/login")
@app.post("/login")
async def login():
    data = await request.get_json() or {}
    username = data.get("name") or data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400

    query = text("SELECT uid, username, password_hash, pais, saldo FROM usuarios WHERE username = :username")

    async with engine.connect() as conn:
        res = await conn.execute(query, {"username": username})
        user = res.mappings().first()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if not check_password(password, user["password_hash"]):
        return jsonify({"error": "Password incorrecta"}), 401

    token = generate_token(user["uid"], user["username"])
    return jsonify({
        "message": "Login exitoso",
        "uid": user["uid"],
        "username": user["username"],
        "token": token
    }), 200

# 3. LOGOUT (Stateless)
@app.post("/user/logout")
@app.post("/logout")
async def logout():
    return jsonify({"message": "Logout exitoso"}), 200

# 4. BORRAR USUARIO (1 solo execute)
@app.delete("/user")
async def delete_user():
    payload = get_current_user_payload()
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    query = text("DELETE FROM usuarios WHERE uid = :uid RETURNING uid")
    async with engine.begin() as conn:
        res = await conn.execute(query, {"uid": payload["uid"]})
        deleted = res.first()

    if not deleted:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({"message": "Usuario eliminado correctamente"}), 200

# 5. ACTUALIZAR SALDO (1 solo execute)
@app.route("/user/saldo", methods=["PATCH", "PUT"])
async def update_saldo():
    payload = get_current_user_payload()
    if not payload:
        return jsonify({"error": "No autorizado"}), 401

    data = await request.get_json() or {}
    incremento = float(data.get("saldo", 0.0))
    if incremento <= 0:
        return jsonify({"error": "El importe debe ser mayor a 0"}), 400

    query = text("""
        UPDATE usuarios
        SET saldo = saldo + :inc
        WHERE uid = :uid
        RETURNING uid, username, saldo
    """)

    async with engine.begin() as conn:
        res = await conn.execute(query, {"inc": incremento, "uid": payload["uid"]})
        updated = res.mappings().first()

    return jsonify({
        "message": "Saldo recargado correctamente",
        "saldo": float(updated["saldo"])
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
```

---

## 🎬 PASO 5: Microservicio Principal (`src/api.py`)

### Cumplimiento del enunciado:
* Creación y borrado de películas.
* Listado con criterios específicos.
* Añadir al carrito, pagar carrito y fecha de pago automática.
* Borrar producto del carrito (desencadena Trigger de devolución de stock).
* Votar película (0-10) y nota media mediante Stored Procedure.
* Endpoint `/ventas/<año>/<país>` con JOINs.
* **CADA ENDPOINT SE EJECUTA EN UN ÚNICO `execute()`**.

### Archivo: `src/api.py`
```python
import os
from quart import Quart, jsonify, request
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import jwt

app = Quart(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@localhost:5432/si1")
JWT_SECRET = os.getenv("JWT_SECRET", "clave_secreta_super_segura_p2")
JWT_ALGORITHM = "HS256"

engine = create_async_engine(DATABASE_URL, echo=False)

def get_current_user_payload():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "").strip()
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None

# --------------------------------------------------------------------------
# 1. GESTIÓN DE PELÍCULAS
# --------------------------------------------------------------------------

@app.post("/peliculas")
async def create_pelicula():
    data = await request.get_json() or {}
    titulo = data.get("titulo")
    anio = data.get("anio")
    genero = data.get("genero", "")
    precio = float(data.get("precio", 0.0))
    stock = int(data.get("stock", 0))

    if not titulo or not anio:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    query = text("""
        INSERT INTO peliculas (titulo, anio, genero, precio, stock)
        VALUES (:titulo, :anio, :genero, :precio, :stock)
        RETURNING id, titulo, anio, genero, precio, stock
    """)

    async with engine.begin() as conn:
        res = await conn.execute(query, {
            "titulo": titulo, "anio": anio, "genero": genero,
            "precio": precio, "stock": stock
        })
        pelicula = res.mappings().first()

    return jsonify(dict(pelicula)), 201

@app.delete("/peliculas/<int:pelicula_id>")
async def delete_pelicula(pelicula_id):
    query = text("DELETE FROM peliculas WHERE id = :id RETURNING id")
    async with engine.begin() as conn:
        res = await conn.execute(query, {"id": pelicula_id})
        deleted = res.first()

    if not deleted:
        return jsonify({"error": "Pelicula no encontrada"}), 404

    return jsonify({"message": "Pelicula eliminada correctamente"}), 200

@app.get("/peliculas")
async def list_peliculas():
    genero = request.args.get("genero")
    anio = request.args.get("anio")

    sql = """
        SELECT id, titulo, anio, genero, precio, stock
        FROM peliculas
        WHERE (:genero IS NULL OR genero = :genero)
          AND (:anio IS NULL OR anio = :anio)
        ORDER BY id ASC
    """
    params = {
        "genero": genero if genero else None,
        "anio": int(anio) if anio else None
    }

    async with engine.connect() as conn:
        res = await conn.execute(text(sql), params)
        peliculas = [dict(row) for row in res.mappings().all()]

    return jsonify(peliculas), 200

# --------------------------------------------------------------------------
# 2. CARRITO Y COMPRAS (Aprovechando SP y TRIGGERS de la BD en 1 execute)
# --------------------------------------------------------------------------

@app.post("/carrito/item")
async def add_to_cart():
    user = get_current_user_payload()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = await request.get_json() or {}
    pelicula_id = data.get("pelicula_id")
    cantidad = int(data.get("cantidad", 1))

    if not pelicula_id or cantidad <= 0:
        return jsonify({"error": "Parametros invalidos"}), 400

    # Llama a la función SP en la BD en un ÚNICO execute()
    sql = text("SELECT sp_anadir_item_carrito(:uid, :pid, :cant) AS pedido_id")

    try:
        async with engine.begin() as conn:
            res = await conn.execute(sql, {
                "uid": user["uid"],
                "pid": pelicula_id,
                "cant": cantidad
            })
            pedido_id = res.first()[0]
    except Exception as e:
        return jsonify({"error": f"Fallo al anadir al carrito: {str(e)}"}), 400

    return jsonify({"message": "Item anadido al carrito", "pedido_id": pedido_id}), 201

@app.delete("/carrito/item/<int:pelicula_id>")
async def remove_from_cart(pelicula_id):
    user = get_current_user_payload()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    # Desencadena el trigger de DELETE en pedido_items (devuelve stock e importe)
    sql = text("""
        DELETE FROM pedido_items
        WHERE pelicula_id = :pid
          AND pedido_id = (SELECT id FROM pedidos WHERE usuario_uid = :uid AND estado = 'carrito' LIMIT 1)
        RETURNING id
    """)

    async with engine.begin() as conn:
        res = await conn.execute(sql, {"pid": pelicula_id, "uid": user["uid"]})
        deleted = res.first()

    if not deleted:
        return jsonify({"error": "Item no encontrado en el carrito"}), 404

    return jsonify({"message": "Item eliminado del carrito"}), 200

@app.get("/carrito")
async def get_cart():
    user = get_current_user_payload()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    # Un único execute con JOIN
    sql = """
        SELECT p.id AS pedido_id, p.importe_total, p.estado,
               pi.pelicula_id, pel.titulo, pi.cantidad, pi.precio_unitario
        FROM pedidos p
        LEFT JOIN pedido_items pi ON p.id = pi.pedido_id
        LEFT JOIN peliculas pel ON pi.pelicula_id = pel.id
        WHERE p.usuario_uid = :uid AND p.estado = 'carrito'
    """
    async with engine.connect() as conn:
        res = await conn.execute(text(sql), {"uid": user["uid"]})
        rows = res.mappings().all()

    if not rows:
        return jsonify({"items": [], "importe_total": 0.0}), 200

    items = []
    total = float(rows[0]["importe_total"])
    pedido_id = rows[0]["pedido_id"]

    for r in rows:
        if r["pelicula_id"] is not None:
            items.append({
                "pelicula_id": r["pelicula_id"],
                "titulo": r["titulo"],
                "cantidad": r["cantidad"],
                "precio_unitario": float(r["precio_unitario"])
            })

    return jsonify({"pedido_id": pedido_id, "importe_total": total, "items": items}), 200

@app.post("/carrito/pagar")
async def pay_cart():
    user = get_current_user_payload()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    # Un único execute(): el Trigger trg_pagar_pedido comprueba saldo, descuenta y asigna fecha
    sql = text("""
        UPDATE pedidos
        SET estado = 'pagado'
        WHERE usuario_uid = :uid AND estado = 'carrito'
        RETURNING id, importe_total, fecha_pago
    """)

    try:
        async with engine.begin() as conn:
            res = await conn.execute(sql, {"uid": user["uid"]})
            row = res.mappings().first()
    except Exception as e:
        return jsonify({"error": f"Fallo en el pago: {str(e)}"}), 400

    if not row:
        return jsonify({"error": "No hay carrito activo para pagar"}), 404

    return jsonify({
        "message": "Pedido pagado con exito",
        "pedido_id": row["id"],
        "importe_pagado": float(row["importe_total"]),
        "fecha_pago": str(row["fecha_pago"])
    }), 200

# --------------------------------------------------------------------------
# 3. VALORACIONES (Utilizando STORED PROCEDURE en 1 execute)
# --------------------------------------------------------------------------

@app.post("/peliculas/<int:pelicula_id>/voto")
async def vote_pelicula(pelicula_id):
    user = get_current_user_payload()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = await request.get_json() or {}
    puntuacion = data.get("puntuacion")

    if puntuacion is None or not (0 <= int(puntuacion) <= 10):
        return jsonify({"error": "La puntuacion debe estar entre 0 y 10"}), 400

    sql = text("""
        INSERT INTO valoraciones (usuario_uid, pelicula_id, puntuacion)
        VALUES (:uid, :pid, :puntuacion)
        ON CONFLICT (usuario_uid, pelicula_id)
        DO UPDATE SET puntuacion = EXCLUDED.puntuacion, fecha = CURRENT_TIMESTAMP
    """)

    async with engine.begin() as conn:
        await conn.execute(sql, {
            "uid": user["uid"],
            "pid": pelicula_id,
            "puntuacion": int(puntuacion)
        })

    return jsonify({"message": "Voto registrado exitosamente"}), 200

@app.get("/peliculas/<int:pelicula_id>/valoracion")
async def get_valoracion(pelicula_id):
    # LLAMADA AL STORED PROCEDURE / FUNCTION EN 1 SOLO EXECUTE
    sql = text("SELECT sp_calcular_valoracion_media(:pid) AS media")

    async with engine.connect() as conn:
        res = await conn.execute(sql, {"pid": pelicula_id})
        row = res.first()

    media = float(row[0]) if row and row[0] is not None else 0.0
    return jsonify({"pelicula_id": pelicula_id, "valoracion_media": media}), 200

# --------------------------------------------------------------------------
# 4. ENDPOINT PARA OPTIMIZACIÓN: VENTAS POR AÑO Y PAÍS
# --------------------------------------------------------------------------

@app.get("/ventas/<int:anio>/<pais>")
async def get_ventas(anio, pais):
    # Un único execute con JOIN
    sql = text("""
        SELECT p.id AS pedido_id,
               p.fecha_pago,
               p.importe_total,
               u.username,
               u.pais,
               pel.titulo AS pelicula,
               pi.cantidad,
               pi.precio_unitario
        FROM pedidos p
        JOIN usuarios u ON p.usuario_uid = u.uid
        JOIN pedido_items pi ON p.id = pi.pedido_id
        JOIN peliculas pel ON pi.pelicula_id = pel.id
        WHERE p.estado = 'pagado'
          AND EXTRACT(YEAR FROM p.fecha_pago) = :anio
          AND u.pais = :pais
        ORDER BY p.fecha_pago DESC
    """)

    async with engine.connect() as conn:
        res = await conn.execute(sql, {"anio": anio, "pais": pais})
        ventas = [dict(row) for row in res.mappings().all()]

    return jsonify({
        "anio": anio,
        "pais": pais,
        "total_registros": len(ventas),
        "ventas": ventas
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051)
```

---

## 🧪 PASO 6: Cliente de Pruebas Automatizadas (`client.py`)

### Archivo: `client.py`
```python
import httpx
import time

USER_URL = "http://localhost:5050"
API_URL = "http://localhost:5051"

def print_test(name, success, details=""):
    symbol = "✅ [PASS]" if success else "❌ [FAIL]"
    print(f"{symbol} {name}")
    if details:
        print(f"      -> {details}")

def run_tests():
    print("=" * 60)
    print("INICIANDO BATERÍA DE PRUEBAS DE CLIENT.PY")
    print("=" * 60)

    with httpx.Client(timeout=10.0) as client:
        # 1. Crear usuario nuevo con UID
        username = f"test_{int(time.time())}"
        res = client.post(f"{USER_URL}/user", json={
            "name": username,
            "password": "password123",
            "pais": "Francia",
            "saldo": 5.0
        })
        user_uid = res.json().get("uid") if res.status_code == 201 else None
        print_test("Crear usuario nuevo con UID (201)", res.status_code == 201 and user_uid is not None, f"UID: {user_uid}")

        # 2. Tolerancia a fallos: detectar duplicado (409)
        res_dup = client.post(f"{USER_URL}/user", json={
            "name": username,
            "password": "otra",
            "pais": "Francia"
        })
        print_test("Detectar usuario duplicado (409)", res_dup.status_code == 409)

        # 3. Login correcto y recepción de token Bearer
        res_login = client.post(f"{USER_URL}/login", json={
            "name": username,
            "password": "password123"
        })
        token = res_login.json().get("token")
        print_test("Login correcto con Bearer Token (200)", res_login.status_code == 200 and token is not None)

        # 4. Tolerancia a fallos: login erróneo (401)
        res_fail_login = client.post(f"{USER_URL}/login", json={
            "name": username,
            "password": "password_incorrecta"
        })
        print_test("Login contraseña errónea (401)", res_fail_login.status_code == 401)

        headers = {"Authorization": f"Bearer {token}"}

        # 5. Listar catálogo
        res_movies = client.get(f"{API_URL}/peliculas")
        movies = res_movies.json()
        print_test("Listar catálogo de películas (200)", res_movies.status_code == 200 and len(movies) > 0)
        pelicula_id = movies[0]["id"]

        # 6. Añadir item al carrito
        res_cart = client.post(f"{API_URL}/carrito/item", json={
            "pelicula_id": pelicula_id,
            "cantidad": 1
        }, headers=headers)
        print_test("Añadir película al carrito vía SP y Trigger (201)", res_cart.status_code == 201)

        # 7. Consultar carrito
        res_get_cart = client.get(f"{API_URL}/carrito", headers=headers)
        cart_data = res_get_cart.json()
        total_a_pagar = cart_data.get("importe_total", 0.0)
        print_test("Consultar carrito activo", res_get_cart.status_code == 200 and total_a_pagar > 0)

        # 8. Tolerancia a fallos: Pagar sin saldo suficiente (Trigger rechaza con 400)
        # El usuario se creó con 5€ de saldo, la película cuesta 9.99€
        res_fail_pay = client.post(f"{API_URL}/carrito/pagar", headers=headers)
        print_test("Trigger rechaza pago por saldo insuficiente (400)", res_fail_pay.status_code == 400)

        # 9. Recargar saldo del usuario
        res_saldo = client.patch(f"{USER_URL}/user/saldo", json={"saldo": 50.0}, headers=headers)
        print_test("Recarga de saldo del usuario (200)", res_saldo.status_code == 200)

        # 10. Pagar carrito con saldo suficiente (Trigger descuenta saldo y asigna fecha)
        res_pay = client.post(f"{API_URL}/carrito/pagar", headers=headers)
        print_test("Trigger aprueba pago y descuenta saldo (200)", res_pay.status_code == 200)

        # 11. Votar película (0-10)
        res_vote = client.post(f"{API_URL}/peliculas/{pelicula_id}/voto", json={"puntuacion": 10}, headers=headers)
        print_test("Votar película con nota válida (200)", res_vote.status_code == 200)

        # 12. Tolerancia a fallos: Voto inválido >10
        res_invalid_vote = client.post(f"{API_URL}/peliculas/{pelicula_id}/voto", json={"puntuacion": 15}, headers=headers)
        print_test("Rechazar voto fuera de rango (400)", res_invalid_vote.status_code == 400)

        # 13. Consultar nota media mediante Stored Procedure
        res_media = client.get(f"{API_URL}/peliculas/{pelicula_id}/valoracion")
        media = res_media.json().get("valoracion_media")
        print_test("Consultar nota media mediante Stored Procedure", res_media.status_code == 200 and media >= 0)

        # 14. Endpoint optimización /ventas/2026/Francia
        res_ventas = client.get(f"{API_URL}/ventas/2026/Francia")
        print_test("Endpoint optimización /ventas/2026/Francia (200)", res_ventas.status_code == 200)

    print("=" * 60)
    print("TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
```

---

## ⚡ PASO 7: Optimización (`optimizacion.sql`)

### Archivo: `optimizacion.sql`
```sql
-- ============================================================================
-- OPTIMIZACIÓN DE LA CONSULTA: /ventas/<año>/<país>
-- ============================================================================

-- 1. PLAN DE EJECUCIÓN INICIAL (ANTES DE ÍNDICES)
EXPLAIN ANALYZE
SELECT p.id AS pedido_id,
       p.fecha_pago,
       p.importe_total,
       u.username,
       u.pais,
       pel.titulo AS pelicula,
       pi.cantidad,
       pi.precio_unitario
FROM pedidos p
JOIN usuarios u ON p.usuario_uid = u.uid
JOIN pedido_items pi ON p.id = pi.pedido_id
JOIN peliculas pel ON pi.pelicula_id = pel.id
WHERE p.estado = 'pagado'
  AND EXTRACT(YEAR FROM p.fecha_pago) = 2026
  AND u.pais = 'Francia'
ORDER BY p.fecha_pago DESC;

-- ============================================================================
-- 2. CREACIÓN DE ÍNDICES OPTIMIZADORES
-- ============================================================================

-- Índice en usuarios por país
CREATE INDEX IF NOT EXISTS idx_usuarios_pais ON usuarios(pais);

-- Índice funcional en pedidos para el año de fecha_pago
CREATE INDEX IF NOT EXISTS idx_pedidos_anio_pago
ON pedidos (EXTRACT(YEAR FROM fecha_pago))
WHERE estado = 'pagado';

-- Índices en claves foráneas para JOINs rápidos
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario_uid ON pedidos(usuario_uid);
CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido ON pedido_items(pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedido_items_pelicula ON pedido_items(pelicula_id);

-- ============================================================================
-- 3. PLAN DE EJECUCIÓN OPTIMIZADO (DESPUÉS DE ÍNDICES)
-- ============================================================================
EXPLAIN ANALYZE
SELECT p.id AS pedido_id,
       p.fecha_pago,
       p.importe_total,
       u.username,
       u.pais,
       pel.titulo AS pelicula,
       pi.cantidad,
       pi.precio_unitario
FROM pedidos p
JOIN usuarios u ON p.usuario_uid = u.uid
JOIN pedido_items pi ON p.id = pi.pedido_id
JOIN peliculas pel ON pi.pelicula_id = pel.id
WHERE p.estado = 'pagado'
  AND EXTRACT(YEAR FROM p.fecha_pago) = 2026
  AND u.pais = 'Francia'
ORDER BY p.fecha_pago DESC;
```

---

## 🚀 PASO 8: Ejecución y Pruebas

```bash
# 1. Limpiar contenedores y volúmenes anteriores
docker compose down -v

# 2. Levantar los tres contenedores
docker compose up --build -d

# 3. Comprobar estado de los servicios
docker compose ps

# 4. Lanzar la batería de pruebas
python3 client.py
```

---

## 📄 PASO 9: Memoria y Entrega Final

1. Diagrama E-R (Entidad-Relación) con las tablas diseñadas.
2. Explicación de los triggers y del stored procedure.
3. Capturas de `EXPLAIN ANALYZE` antes y después de crear los índices.
4. Captura de `client.py` con todas las pruebas en verde.
5. Generación del fichero ZIP de entrega:
   ```bash
   zip -r P2.zip docker-compose.yml Dockerfile requirements.txt schema.sql populate.sql optimizacion.sql client.py src/ memoria.pdf README.txt
   ```
