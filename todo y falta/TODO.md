# Guía de Estado y Plan de Trabajo - Práctica 2: Bases de Datos Relacionales (PostgreSQL + Quart)

Documento contrastado y validado directamente contra el enunciado oficial **P2-2026-27_Enunciado.pdf** y sincronizado con el estado real del repositorio Git.

> [!NOTE]
> **Últimos hitos completados en Git**:
> - Commit `801cc1d` ("Schema terminado" por @sergiosauco): `schema.sql` completado con tablas, triggers y procedimientos almacenados.
> - Commit `5e2a58e` ("diagramas" por @arturopereznoves): Diagrama E-R generado y exportado en `Diagrama/diagrama.png` y `DiagramaER.uxf`.
> - Commit `44084e3` ("Populate terminado" por @sergiosauco): `populate.sql` completado con datos iniciales (usuarios, películas, directores, pedidos de Francia 2026 y valoraciones).
> - Configuración local: Entorno `.venv` con Python 3.11 y `.vscode/settings.json` para resolver warnings de Pylance.

---

## 👥 Reparto de Tareas del Equipo (`todo y falta/falta`)

| Integrante | Tareas Asignadas | Estado |
| :--- | :--- | :--- |
| **Arturo** | `src/user.py` (Microservicio de Usuarios)<br>`optimizacion.sql` (Análisis EXPLAIN ANALYZE e índices) | ⏳ **En progreso** (Comenzando `user.py`)<br>⏳ Pendiente |
| **Sergio** | `src/api.py` (Microservicio Principal)<br>`client.py` (Batería de pruebas automatizadas) | ⏳ Pendiente<br>⏳ Pendiente |
| **Ambos** | `memoria.pdf` (Diagrama E-R, explicación técnica, optimización) | ⏳ Pendiente |

---

## 📋 Checklist de Requisitos y Estado Actual

| Requisito del Enunciado | Dónde se implementa | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| **PostgreSQL oficial** (`alumnodb`, `1234`, `si1`) con persistencia | `docker-compose.yml` (`db`) | Ambos | ✅ **COMPLETADO** |
| **Diseño DDL, Tablas y Relaciones** | `schema.sql` | Ambos | ✅ **COMPLETADO** |
| **Triggers obligatorios (stock, cobro, reposición)** | `schema.sql` | Ambos | ✅ **COMPLETADO** |
| **Stored Procedures (media, carrito, cobro, ventas)** | `schema.sql` | Ambos | ✅ **COMPLETADO** |
| **Diagrama E-R (Entidad-Relación)** | `Diagrama/diagrama.png` | Arturo | ✅ **COMPLETADO** |
| **Datos de prueba coherentes (DML)** | `populate.sql` | Sergio | ✅ **COMPLETADO** |
| **Microservicio Usuarios (`user.py`)**: Core async + JWT stateless | `src/user.py` | Arturo | ⏳ **ACTUAL** |
| **Microservicio Videoclub (`api.py`)**: Películas, Carrito, Votos | `src/api.py` | Sergio | ⏳ Pendiente |
| **Regla estricta: 1 único `execute()` por endpoint** | `src/user.py`, `src/api.py` | Ambos | ⏳ En desarrollo |
| **Script de optimización**: EXPLAIN ANALYZE + índices | `optimizacion.sql` | Arturo | ⏳ Pendiente |
| **Cliente de pruebas con tolerancia a fallos** | `client.py` | Sergio | ⏳ Pendiente |
| **Memoria técnica y empaquetado** | `memoria.pdf`, `P2.zip` | Ambos | ⏳ Pendiente |

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
Configuradas en `requirements.txt` e instaladas en el contenedor y en el entorno `.venv` local.

---

## 🐳 PASO 1: Docker Compose (`docker-compose.yml`) [✅ COMPLETADO]
Servicios `db`, `usersvc` y `apisvc` definidos con red compartida, volumen persistente y healthcheck.

---

## 🗄️ PASO 2: Esquema Relacional, Triggers y SPs (`schema.sql`) [✅ COMPLETADO]
- Tablas: `USUARIOS`, `PELICULAS`, `ACTORES`, `DIRECTORES`, `PELICULA_ACTORES`, `PELICULA_DIRECTORES`, `PEDIDOS`, `PEDIDO_ITEMS`, `VALORACIONES`.
- Triggers: `tgr_actualizar_carrito_stock`, `tgr_pagar_carrito`, `tgr_reponer_stock`.
- Stored Procedures: `valoracion_media`, `agregar_carrito`, `pagar_carrito_usuario`, `votar_pelicula`, `obtener_ventas_anio_pais`.

---

## 📊 PASO 2.1: Diagrama Entidad-Relación (`Diagrama/`) [✅ COMPLETADO]
- Exportado en `Diagrama/diagrama.png` y editable en `Diagrama/DiagramaER.uxf`.

---

## 📥 PASO 3: Datos de Prueba (`populate.sql`) [✅ COMPLETADO]
- Pobla usuarios (incluyendo Francia y España), películas variadas, directores, actores, ventas de 2026 y calificaciones iniciales.

---

## 👤 PASO 4: Microservicio de Usuarios (`src/user.py`) [⏳ TAREA ACTUAL DE ARTURO]

Migrar desde la versión antigua de P1 (archivos JSON) a PostgreSQL con **SQLAlchemy Core asíncrono** y **JWT stateless**.

### Requisitos Técnicos Obligatorios:
1. **Acceso a BD**: Exclusivamente con SQLAlchemy Core asíncrono (`create_async_engine`, `text()`, `await`). Cero ORM.
2. **Regla de Oro**: Cada consulta/endpoint debe resolverse en **1 único `execute()`**.
3. **Autenticación Stateless**:
   - Generación de token JWT al registrarse o hacer login con expiración (ej. 12h).
   - No guardar tokens en BD ni en memoria.
   - Envío y validación en cabecera `Authorization: Bearer <token>`.
4. **Cifrado de Contraseñas**: Con `bcrypt` (`hashpw` y `checkpw`).

### Endpoints a Implementar en `user.py`:
1. `PUT /user`: Registro de usuario (`username`, `password`, `pais`, `saldo` inicial). Retorna `201` con `uid`, `username` y `token`. Retorna `409` si el usuario ya existe.
2. `POST /user` o `POST /user/login`: Login. Consulta el usuario por `username`, verifica hash con `bcrypt` y retorna `200` con `uid` y nuevo `token`. Retorna `404` si no existe o `401` si contraseña incorrecta.
3. `POST /user/logout` o `POST /logout`: Valida token de cabecera y retorna `200` (el cliente borra el token).
4. `DELETE /user`: Borra el usuario autenticado (`DELETE FROM USUARIOS WHERE uid = :uid`). Retorna `200` o `401`/`404`.
5. `PATCH /user/saldo` o `PATCH /user`: Incrementa o actualiza el saldo del usuario autenticado en 1 único execute. Retorna `200` con el nuevo saldo.

---

## 🎬 PASO 5: Microservicio Principal (`src/api.py`) [⏳ TAREA DE SERGIO]
Endpoints del videoclub conectando con Triggers y Stored Procedures en 1 único `execute()`.

---

## 🧪 PASO 6: Cliente de Pruebas Automatizadas (`client.py`) [⏳ TAREA DE SERGIO]
Validación de todos los flujos de éxito y códigos de error (400, 401, 404, 409).

---

## ⚡ PASO 7: Optimización (`optimizacion.sql`) [⏳ TAREA DE ARTURO]
Ejecución de `EXPLAIN ANALYZE` sobre `/ventas/<año>/<país>`, creación de índices y comparación de planes.

---

## 📄 PASO 8: Memoria y Entrega Final [⏳ AMBOS]
Memoria técnica con Diagrama E-R, descripción de triggers/SPs, análisis de optimización y empaquetado `P2.zip`.
