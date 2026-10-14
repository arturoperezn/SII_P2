# Guía de Estado y Plan de Trabajo - Práctica 2: Bases de Datos Relacionales (PostgreSQL + Quart)

Documento contrastado y validado directamente contra el enunciado oficial **P2-2026-27_Enunciado.pdf** y sincronizado con el estado real del repositorio Git.

> [!NOTE]
> **Última sincronización con Git**:
> - Commit `801cc1d` ("Schema terminado" por @sergiosauco): `schema.sql` completado con tablas, triggers y procedimientos almacenados (corregidas erratas de sintaxis).
> - Commit `5e2a58e` ("diagramas" por @arturopereznoves): Diagrama E-R generado y exportado en `Diagrama/diagrama.png` y `DiagramaER.uxf`.

---

## 📋 Checklist de Requisitos y Estado Actual

| Requisito del Enunciado | Dónde se implementa | Estado |
| :--- | :--- | :--- |
| **PostgreSQL oficial** (`alumnodb`, `1234`, `si1`) con persistencia | `docker-compose.yml` (`db`) | ✅ **COMPLETADO** |
| **Diseño DDL, Tablas y Relaciones** | `schema.sql` | ✅ **COMPLETADO** |
| **Trigger 1**: Stock e importe de carrito al añadir/eliminar | `schema.sql` (`tgr_actualizar_carrito_stock`) | ✅ **COMPLETADO** |
| **Trigger 2**: Descuento automático de saldo y fecha al pagar | `schema.sql` (`tgr_pagar_carrito`) | ✅ **COMPLETADO** |
| **Trigger 3**: Reposición de stock si se cancela pedido | `schema.sql` (`tgr_reponer_stock`) | ✅ **COMPLETADO** |
| **Stored Procedures**: Valoración media, carrito, pago y ventas | `schema.sql` (`valoracion_media`, `agregar_carrito`, etc.) | ✅ **COMPLETADO** |
| **Diagrama E-R (Entidad-Relación)** | `Diagrama/diagrama.png`, `DiagramaER.uxf` | ✅ **COMPLETADO** |
| **Datos de prueba coherentes (DML)** | `populate.sql` | ⏳ **PRÓXIMO PASO** |
| **Microservicio Usuarios (`user.py`)**: Core async + JWT stateless | `src/user.py` | ⏳ **PENDIENTE** |
| **Microservicio Videoclub (`api.py`)**: Películas, Carrito, Votos | `src/api.py` | ⏳ **PENDIENTE** |
| **Regla estricta: 1 único `execute()` por endpoint** | `src/user.py`, `src/api.py` | ⏳ **PENDIENTE** |
| **Endpoint para optimización**: `GET /ventas/<año>/<país>` | `src/api.py` (`obtener_ventas_anio_pais`) | ⏳ **PENDIENTE** |
| **Script de optimización**: EXPLAIN ANALYZE antes/después + índices | `optimizacion.sql` | ⏳ **PENDIENTE** |
| **Cliente de pruebas automatizadas con tolerancia a fallos** | `client.py` | ⏳ **PENDIENTE** |
| **Memoria técnica y empaquetado** | `memoria.pdf`, `README.txt`, `P2.zip` | ⏳ **PENDIENTE** |

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

## 🛠️ PASO 0: Dependencias (`requirements.txt`) [✅ COMPLETADO]

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

## 🐳 PASO 1: Docker Compose (`docker-compose.yml`) [✅ COMPLETADO]

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

## 🗄️ PASO 2: Esquema Relacional, Triggers y SPs (`schema.sql`) [✅ COMPLETADO]

El equipo ha finalizado la estructura completa en `schema.sql` con todas las tablas, triggers y procedimientos almacenados (commits `801cc1d` y `5d22cf7`).

### Resumen del Modelo Implementado:
1. **`USUARIOS`**: `uid` (VARCHAR(64) PK), `username`, `password_hash`, `pais`, `saldo` (CHECK >= 0).
2. **`PELICULAS`**: `id` (SERIAL PK), `titulo`, `anio`, `genero`, `precio`, `stock`.
3. **`ACTORES`** y **`DIRECTORES`**: con tablas intermedias `PELICULA_ACTORES` y `PELICULA_DIRECTORES`.
4. **`PEDIDOS`**: `id` (SERIAL PK), `usuario_uid`, `estado` ('activo', 'pagado', 'cancelado'), `importe`, `fecha_creacion`, `fecha_pago`.
5. **`PEDIDO_ITEMS`**: `id`, `pedido_id`, `pelicula_id`, `cantidad`, `precio_unitario`, UNIQUE(pedido_id, pelicula_id).
6. **`VALORACIONES`**: `id`, `pelicula_id`, `usuario_uid`, `calificacion` (CHECK 0..10), `fecha_creacion`, UNIQUE(usuario_uid, pelicula_id).

### Triggers Implementados:
- **`tgr_pagar_carrito`** (`pagar_carrito`): BEFORE UPDATE OF estado ON PEDIDOS. Verifica saldo suficiente del usuario, descuenta el importe del saldo, registra `fecha_pago = CURRENT_TIMESTAMP` y rechaza carritos vacíos o saldo insuficiente.
- **`tgr_actualizar_carrito_stock`** (`actualizar_carrito_stock`): AFTER INSERT/UPDATE/DELETE ON PEDIDO_ITEMS. Verifica y descuenta/devuelve stock de películas y recalcula el importe total del pedido.
- **`tgr_reponer_stock`** (`reponer_stock`): BEFORE UPDATE OF estado ON PEDIDOS al pasar a 'cancelado'. Devuelve las unidades al stock.

### Stored Procedures / Funciones PL/pgSQL Implementadas:
- **`valoracion_media(p_pelicula_id INT) RETURNS NUMERIC`**: Calcula el promedio de calificaciones de una película.
- **`agregar_carrito(p_usuario_uid, p_pelicula_id, p_cantidad) RETURNS INT`**: Obtiene o crea el pedido en estado 'activo', consulta el precio e inserta en `PEDIDO_ITEMS`, activando el trigger de stock. Permite ejecución en 1 solo `execute()`.
- **`pagar_carrito_usuario(p_usuario_uid) RETURNS INT`**: Busca el pedido 'activo' y actualiza a 'pagado', activando el trigger de cobro.
- **`votar_pelicula(p_usuario_uid, p_pelicula_id, p_calificacion) RETURNS VOID`**: Valida rango 0..10 y realiza UPSERT (`ON CONFLICT DO UPDATE`).
- **`obtener_ventas_anio_pais(p_anio, p_pais) RETURNS TABLE (...)`**: Consulta optimizada de ventas por año y país de usuarios.

---

## 📊 PASO 2.1: Diagrama Entidad-Relación (`Diagrama/`) [✅ COMPLETADO]

- Generado y exportado en `Diagrama/diagrama.png` y `Diagrama/DiagramaER.uxf`.
- Documentado el procedimiento de regeneración desde pgAdmin 4 en `Diagrama/diagrama-instrucciones-para-crearlo.txt`.

---

## 📥 PASO 3: Datos de Prueba (`populate.sql`) [⏳ PRÓXIMO PASO]

Debe poblar datos consistentes con los nombres de campos de `schema.sql` (`importe`, `calificacion`, `activo`, `pagado`), incluyendo usuarios de **Francia** y ventas del año **2026** para la consulta de optimización.

### Archivo a crear: `populate.sql`
```sql
-- Usuarios de prueba (contraseña '1234' hasheada con bcrypt)
INSERT INTO USUARIOS (uid, username, password_hash, pais, saldo) VALUES
('u1111111-1111-1111-1111-111111111111', 'alice',  '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'Francia', 100.00),
('u2222222-2222-2222-2222-222222222222', 'pierre', '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'Francia', 50.00),
('u3333333-3333-3333-3333-333333333333', 'carlos', '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'España', 75.00),
('u4444444-4444-4444-4444-444444444444', 'lucia',  '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'España', 0.00),
('u5555555-5555-5555-5555-555555555555', 'marco',  '$2b$12$e80yqR3jM4W6sW.Kk3K0e.6o1B7UfV1s1h9r9tK9.7NfC5y0YF.1C', 'Italia', 120.00)
ON CONFLICT (uid) DO NOTHING;

-- Películas de prueba
INSERT INTO PELICULAS (id, titulo, anio, genero, precio, stock) VALUES
(1, 'Inception', 2010, 'Ciencia Ficcion', 9.99, 20),
(2, 'Interstellar', 2014, 'Ciencia Ficcion', 12.50, 15),
(3, 'Amélie', 2001, 'Comedia', 7.99, 10),
(4, 'El Padrino', 1972, 'Drama', 14.99, 8),
(5, 'Dune: Parte 2', 2026, 'Ciencia Ficcion', 18.00, 25),
(6, 'Oppenheimer', 2023, 'Drama', 15.00, 12)
ON CONFLICT (id) DO NOTHING;

SELECT setval('peliculas_id_seq', (SELECT MAX(id) FROM PELICULAS));

-- Directores y Actores
INSERT INTO DIRECTORES (id, nombre) VALUES
(1, 'Christopher Nolan'),
(2, 'Jean-Pierre Jeunet'),
(3, 'Francis Ford Coppola'),
(4, 'Denis Villeneuve')
ON CONFLICT (id) DO NOTHING;

SELECT setval('directores_id_seq', (SELECT MAX(id) FROM DIRECTORES));

INSERT INTO ACTORES (id, nombre) VALUES
(1, 'Leonardo DiCaprio'),
(2, 'Matthew McConaughey'),
(3, 'Audrey Tautou'),
(4, 'Marlon Brando'),
(5, 'Timothée Chalamet'),
(6, 'Cillian Murphy')
ON CONFLICT (id) DO NOTHING;

SELECT setval('actores_id_seq', (SELECT MAX(id) FROM ACTORES));

INSERT INTO PELICULA_DIRECTORES (pelicula_id, director_id) VALUES
(1, 1), (2, 1), (3, 2), (4, 3), (5, 4), (6, 1)
ON CONFLICT DO NOTHING;

INSERT INTO PELICULA_ACTORES (pelicula_id, actor_id) VALUES
(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)
ON CONFLICT DO NOTHING;

-- Ventas históricas para probar /ventas/2026/Francia
INSERT INTO PEDIDOS (id, usuario_uid, estado, importe, fecha_creacion, fecha_pago) VALUES
(1, 'u1111111-1111-1111-1111-111111111111', 'pagado', 22.49, '2026-02-10 10:00:00', '2026-02-10 10:05:00'),
(2, 'u2222222-2222-2222-2222-222222222222', 'pagado', 18.00, '2026-03-15 14:30:00', '2026-03-15 14:35:00'),
(3, 'u3333333-3333-3333-3333-333333333333', 'pagado', 9.99,  '2026-01-20 18:00:00', '2026-01-20 18:02:00'),
(4, 'u1111111-1111-1111-1111-111111111111', 'pagado', 14.99, '2025-11-05 12:00:00', '2025-11-05 12:10:00')
ON CONFLICT (id) DO NOTHING;

SELECT setval('pedidos_id_seq', (SELECT MAX(id) FROM PEDIDOS));

INSERT INTO PEDIDO_ITEMS (pedido_id, pelicula_id, cantidad, precio_unitario) VALUES
(1, 1, 1, 9.99),
(1, 2, 1, 12.50),
(2, 5, 1, 18.00),
(3, 1, 1, 9.99),
(4, 4, 1, 14.99)
ON CONFLICT DO NOTHING;

-- Valoraciones de prueba
INSERT INTO VALORACIONES (usuario_uid, pelicula_id, calificacion) VALUES
('u1111111-1111-1111-1111-111111111111', 1, 9),
('u2222222-2222-2222-2222-222222222222', 1, 10),
('u3333333-3333-3333-3333-333333333333', 1, 8),
('u1111111-1111-1111-1111-111111111111', 3, 10),
('u2222222-2222-2222-2222-222222222222', 5, 9),
('u3333333-3333-3333-3333-333333333333', 4, 10)
ON CONFLICT DO NOTHING;
```

---

## 👤 PASO 4: Microservicio de Usuarios (`src/user.py`) [⏳ PENDIENTE]

Migrar desde la versión antigua de P1 (archivos JSON) a PostgreSQL con **SQLAlchemy Core asíncrono** y **JWT stateless**.

### Requisitos:
* `PUT /user`: Registrar usuario con `username`, `password` (hasheado con `bcrypt`), `pais` y `saldo` inicial. Devuelve `uid` y `token`.
* `POST /user/login` o `POST /login`: Valida credenciales contra `USUARIOS` y devuelve `token` JWT con `Authorization: Bearer`.
* `POST /user/logout` o `POST /logout`: Stateless (confirmación de salida en cliente).
* `DELETE /user`: Borra usuario actual (usa `Authorization: Bearer`).
* `PATCH /user/saldo` o `PATCH /user`: Incrementa o recarga el saldo en `USUARIOS`.
* **Cada endpoint se ejecuta en 1 ÚNICO `execute()`**.

---

## 🎬 PASO 5: Microservicio Principal (`src/api.py`) [⏳ PENDIENTE]

Implementar la API del videoclub conectada a los Stored Procedures y Triggers definidos en `schema.sql`.

### Requisitos:
* `POST /peliculas`: Crear película (`titulo`, `anio`, `genero`, `precio`, `stock`).
* `DELETE /peliculas/<id>`: Borrar película.
* `GET /peliculas`: Listar películas con filtros opcionales (`genero`, `anio`).
* `POST /carrito/item`: Añadir película al carrito invocando `SELECT agregar_carrito(:uid, :pid, :cant)` en **1 solo execute**.
* `DELETE /carrito/item/<id>`: Eliminar ítem del carrito activo (desencadena trigger que devuelve stock).
* `GET /carrito`: Consultar carrito activo (`estado = 'activo'`) con detalle de ítems e importe total.
* `POST /carrito/pagar`: Pagar el carrito invocando `SELECT pagar_carrito_usuario(:uid)` o actualizando estado a `'pagado'`, desencadenando `tgr_pagar_carrito`.
* `POST /peliculas/<id>/voto`: Votar película llamando a `SELECT votar_pelicula(:uid, :pid, :calificacion)`.
* `GET /peliculas/<id>/valoracion`: Consultar nota media llamando a `SELECT valoracion_media(:pid)`.
* `GET /ventas/<anio>/<pais>`: Consultar ventas del año y país llamando a `SELECT * FROM obtener_ventas_anio_pais(:anio, :pais)`.

---

## 🧪 PASO 6: Cliente de Pruebas Automatizadas (`client.py`) [⏳ PENDIENTE]

Script que ejecuta todas las pruebas funcionales y valida la tolerancia a fallos:
1. Crear usuario con saldo inicial y recibir token.
2. Comprobar error al duplicar usuario (HTTP 409).
3. Login con credenciales válidas (HTTP 200 + token).
4. Login con contraseña errónea (HTTP 401).
5. Listar catálogo de películas.
6. Añadir película al carrito.
7. Consultar carrito.
8. Intento de pago con saldo insuficiente -> Comprobar que el Trigger aborta con HTTP 400.
9. Recarga de saldo vía endpoint de usuario.
10. Pago exitoso con saldo suficiente -> Comprobar descuento de saldo y asignación de `fecha_pago`.
11. Votación de película válida (0 a 10) y error si voto > 10.
12. Consulta de valoración media vía Stored Procedure.
13. Consulta de `/ventas/2026/Francia` comprobando resultados.

---

## ⚡ PASO 7: Optimización (`optimizacion.sql`) [⏳ PENDIENTE]

1. Ejecutar `EXPLAIN ANALYZE` sobre la consulta de `obtener_ventas_anio_pais(2026, 'Francia')` antes de crear índices.
2. Crear índices funcionales y B-Tree:
   - `CREATE INDEX idx_usuarios_pais ON USUARIOS(pais);`
   - `CREATE INDEX idx_pedidos_anio_pago ON PEDIDOS (EXTRACT(YEAR FROM fecha_pago)) WHERE estado = 'pagado';`
   - Claves foráneas: `idx_pedidos_usuario_uid`, `idx_pedido_items_pedido`.
3. Ejecutar nuevamente `EXPLAIN ANALYZE` y comparar costes de planificación, ejecución y tipo de escaneo (Seq Scan vs Index Scan).

---

## 📄 PASO 8: Memoria y Entrega Final [⏳ PENDIENTE]

1. Incorporar el Diagrama E-R ya generado (`Diagrama/diagrama.png`).
2. Documentar la lógica de los triggers y Stored Procedures implementados.
3. Incluir capturas de `EXPLAIN ANALYZE` antes y después de los índices.
4. Incluir captura de la salida exitosa de `client.py`.
5. Empaquetar todo en `P2.zip` limpio de cachés y entornos virtuales.
