from quart import Quart, jsonify, request
from uuid import uuid4, uuid5, UUID
import os
from pathlib import Path
from hashlib import sha256
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app = Quart(__name__)
# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@localhost:5432/si1")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Carga o genera un UUID secreto para la aplicación, que se usará para generar tokens de usuario.
def load_or_create_secret_uuid():
    if Path("/app/shared_data").exists() or os.path.exists("/.dockerenv"):
        secret_path = Path("/app/shared_data/secret_uuid.txt")
    else:
        secret_path = Path("shared_data/secret_uuid.txt")
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        secret_uuid = str(uuid4())
        with open(secret_path, "x") as f:
            f.write(secret_uuid)
        return secret_uuid
    except FileExistsError:
        with open(secret_path, "r") as f:
            secret_uuid = f.read().strip()
        return secret_uuid

secret_uuid = load_or_create_secret_uuid()

# Extrae el uid del token de usuario
def extract_uid_from_token():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "): 
        return None
    token = token.replace("Bearer ", "")
    if not token:
        return None
    if "." not in token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    user_uid = parts[0]
    hash = parts[1]
    if hash == str(uuid5(UUID(secret_uuid), user_uid)):
        return user_uid
    return None
    

# Creación de película
@app.post('/api/peliculas')
async def create_movie():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    title = data.get("title")
    year = data.get("year")
    price = data.get("price")
    genre = data.get("genre")
    stock = data.get("stock", 0)
    ids_actors = data.get("actors", [])
    ids_directors = data.get("directors", [])
    if not title or not year or not price or not genre:
        return jsonify({"error": "Faltan parámetros requeridos (title, year, price, genre)"}), 400

    async with async_session() as session:
        async with session.begin():
            try:
                query = text("INSERT INTO PELICULAS (titulo, anio, genero, precio, stock) VALUES (:title, :year, :genre, :price, :stock) RETURNING id")
                result = await session.execute(query, {"title": title, "year": year, "price": price, "genre": genre, "stock": stock})
                movie_id = result.scalar()
                for actor_id in ids_actors:
                    query = text("INSERT INTO PELICULA_ACTORES (pelicula_id, actor_id) VALUES (:movie_id, :actor_id)")
                    await session.execute(query, {"movie_id": movie_id, "actor_id": actor_id})
                for director_id in ids_directors:
                    query = text("INSERT INTO PELICULA_DIRECTORES (pelicula_id, director_id) VALUES (:movie_id, :director_id)")
                    await session.execute(query, {"movie_id": movie_id, "director_id": director_id})
                return jsonify({"message": "Movie created successfully", "movie_id": movie_id}), 201
            # Cuando un actor o director no existe, se lanza una excepción de integridad.
            except IntegrityError as e:
                await session.rollback()
                return jsonify({"error": "Error de integridad en la base de datos", "details": str(e)}), 409
            # Si ocurre algún otro error, lo manejamos aquí.
            except Exception as e:
                await session.rollback()
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

    return jsonify({"message": "Movie created successfully"}), 201

# Eliminación de película
@app.delete('/api/peliculas/<int:movie_id>')
async def delete_movie(movie_id: int):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("DELETE FROM PELICULAS WHERE id = :movie_id")
                result = await session.execute(query, {"movie_id": movie_id})
                if result.rowcount == 0:
                    return jsonify({"error": "Movie not found"}), 404
                return jsonify({"message": "Movie deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Crear director
@app.post('/api/directores')
async def create_director():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    name = data.get("name")
    if not name:
        return jsonify({"error": "Faltan parámetros requeridos (name)"}), 400

    async with async_session() as session:
        async with session.begin():
            try:
                query = text("INSERT INTO DIRECTORES (nombre) VALUES (:name) RETURNING id")
                result = await session.execute(query, {"name": name})
                director_id = result.scalar()
                return jsonify({"message": "Director created successfully", "director_id": director_id}), 201
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Eliminar director
@app.delete('/api/directores/<int:director_id>')
async def delete_director(director_id: int):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("DELETE FROM DIRECTORES WHERE id = :director_id")
                result = await session.execute(query, {"director_id": director_id})
                if result.rowcount == 0:
                    return jsonify({"error": "Director not found"}), 404
                return jsonify({"message": "Director deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Crear actor
@app.post('/api/actores')
async def create_actor():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    name = data.get("name")
    if not name:
        return jsonify({"error": "Faltan parámetros requeridos (name)"}), 400

    async with async_session() as session:
        async with session.begin():
            try:
                query = text("INSERT INTO ACTORES (nombre) VALUES (:name) RETURNING id")
                result = await session.execute(query, {"name": name})
                actor_id = result.scalar()
                return jsonify({"message": "Actor created successfully", "actor_id": actor_id}), 201
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Eliminar actor
@app.delete('/api/actores/<int:actor_id>')
async def delete_actor(actor_id: int):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("DELETE FROM ACTORES WHERE id = :actor_id")
                result = await session.execute(query, {"actor_id": actor_id})
                if result.rowcount == 0:
                    return jsonify({"error": "Actor not found"}), 404
                return jsonify({"message": "Actor deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Añadir actor a película
@app.post('/api/peliculas/<int:movie_id>/actores/<int:actor_id>')
async def add_actor_to_movie(movie_id: int, actor_id: int):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("INSERT INTO PELICULA_ACTORES (pelicula_id, actor_id) VALUES (:movie_id, :actor_id)")
                await session.execute(query, {"movie_id": movie_id, "actor_id": actor_id})
                return jsonify({"message": "Actor added to movie successfully"}), 201
            except IntegrityError as e:
                return jsonify({"error": "Error de integridad en la base de datos", "details": str(e)}), 409
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Añadir director a película
@app.post('/api/peliculas/<int:movie_id>/directores/<int:director_id>')
async def add_director_to_movie(movie_id: int, director_id: int):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("INSERT INTO PELICULA_DIRECTORES (pelicula_id, director_id) VALUES (:movie_id, :director_id)")
                await session.execute(query, {"movie_id": movie_id, "director_id": director_id})
                return jsonify({"message": "Director added to movie successfully"}), 201
            except IntegrityError as e:
                return jsonify({"error": "Error de integridad en la base de datos", "details": str(e)}), 409
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Añadir o reducir stock a película
@app.post('/api/peliculas/<int:movie_id>/stock')
async def add_stock_to_movie(movie_id: int):
    data = await request.get_json()
    if not data or "stock" not in data:
        return jsonify({"error": "Faltan parámetros requeridos (stock)"}), 400
    stock = data["stock"]
    if not isinstance(stock, int) or stock == 0:
        return jsonify({"error": "El stock debe ser un número entero positivo o negativo no nulo"}), 400

    async with async_session() as session:
        async with session.begin():
            try:
                query = text("UPDATE PELICULAS SET stock = stock + :stock WHERE id = :movie_id")
                result = await session.execute(query, {"stock": stock, "movie_id": movie_id})
                if result.rowcount == 0:
                    return jsonify({"error": "Pelicula no encontrada"}), 404
                return jsonify({"message": "Stock added successfully"}), 200
            # Cuando el stock resultante es negativo, se lanza una excepción de integridad.
            except IntegrityError as e:
                return jsonify({"error": "Error de integridad en la base de datos", "details": str(e)}), 409
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Establecer el stock de una película
@app.put('/api/peliculas/<int:movie_id>/stock')
async def set_stock_of_movie(movie_id: int):
    data = await request.get_json()
    if not data or "stock" not in data:
        return jsonify({"error": "Faltan parámetros requeridos (stock)"}), 400
    stock = data["stock"]
    if not isinstance(stock, int) or stock < 0:
        return jsonify({"error": "El stock debe ser un número entero no negativo"}), 400

    async with async_session() as session:
        async with session.begin():
            try:
                query = text("UPDATE PELICULAS SET stock = :stock WHERE id = :movie_id")
                result = await session.execute(query, {"stock": stock, "movie_id": movie_id})
                if result.rowcount == 0:
                    return jsonify({"error": "Pelicula no encontrada"}), 404
                return jsonify({"message": "Stock set successfully"}), 200
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Obtener listado de películas por un criterio específico
@app.get('/api/peliculas')
async def get_movies():
    titulo = request.args.get("titulo")
    genero = request.args.get("genero")
    anio = request.args.get("anio")
    async with async_session() as session:
        async with session.begin():
            try:
                query = "SELECT * FROM PELICULAS"
                conditions = []
                params = {}
                if titulo:
                    conditions.append("titulo ILIKE :title")
                    params["title"] = f"%{titulo}%"
                if genero:
                    conditions.append("genero = :genre")
                    params["genre"] = genero
                if anio:
                    # Validamos que el año sea entero
                    try:
                        params["year"] = int(anio)
                        conditions.append("anio = :year")
                    except ValueError:
                        return jsonify({"error": "El parámetro 'anio' debe ser un número entero"}), 400
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                query += " ORDER BY id DESC"
                result = await session.execute(text(query), params)
                rows = result.mappings().all()
                peliculas = []
                for row in rows:
                    pelicula = {
                        "id": row["id"],
                        "title": row["titulo"],
                        "year": row["anio"],
                        "genre": row["genero"],
                        "price": float(row["precio"]),
                        "stock": row["stock"]
                    }
                    peliculas.append(pelicula)
                return jsonify({"message": "Movies found:", "Movies": peliculas}), 200
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Añadir pelicula al carrito de un usuario
@app.post ('/api/carrito')
async def add_to_cart():
    user_uid = extract_uid_from_token()
    if not user_uid:
        return jsonify({"error": "Token de usuario inválido o no proporcionado"}), 401
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos (movie_id)"}), 400
    movie_id = data.get("movie_id")
    quantity = data.get("quantity", 1)
    if not movie_id or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Faltan parámetros requeridos (movie_id) o son inválidos (quantity debe ser un número entero positivo)"}), 400
    async with async_session() as session:
        async with session.begin():
            try:
                agregar_carrito_query = text("SELECT agregar_carrito(:user_uid, :movie_id, :quantity)")
                result = await session.execute(agregar_carrito_query, {"user_uid": user_uid, "movie_id": movie_id, "quantity": quantity})
                pedido_id = result.scalar()
                # Consultamos la cantidad pedida de la película para devolverlo en la respuesta
                cantidad_query = text("SELECT cantidad FROM PEDIDO_ITEMS WHERE pedido_id = :pedido_id AND pelicula_id = :movie_id")
                result = await session.execute(cantidad_query, {"pedido_id": pedido_id, "movie_id": movie_id})
                cantidad = result.scalar()
                return jsonify({"message": "Movie added to cart successfully", "cart_id": pedido_id, "movie_id": movie_id, "quantity": cantidad}), 201
            except Exception as e:
                error_message = str(e)
                if "no existe" in error_message.lower():
                    return jsonify({"error": "Pelicula no encontrada", "details": str(e)}), 404
                if "stock" in error_message.lower():
                    return jsonify({"error": "Stock insuficiente para la pelicula solicitada", "details": str(e)}), 409
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500
            
# Pagar el carrito de un usuario
@app.post('/api/carrito/pagar')
async def pay_cart():
    user_uid = extract_uid_from_token()
    if not user_uid:
        return jsonify({"error": "Token de usuario inválido o no proporcionado"}), 401
    async with async_session() as session:
        async with session.begin():
            try:
                pagar_carrito_query = text("SELECT pagar_carrito_usuario(:user_uid)")
                result = await session.execute(pagar_carrito_query, {"user_uid": user_uid})
                pedido_id = result.scalar()
                return jsonify({"message": "Cart paid successfully", "cart_id": pedido_id}), 200
            except Exception as e:
                error_message = str(e)
                if "activo" in error_message.lower():
                    return jsonify({"error": "No hay un carrito activo para este usuario"}), 404
                if "vacio" in error_message.lower():
                    return jsonify({"error": "El carrito está vacío", "details": str(e)}), 400
                if "saldo" in error_message.lower():
                    return jsonify({"error": "Saldo insuficiente para completar el pago", "details": str(e)}), 402
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Votar una película
@app.post('/api/peliculas/<int:movie_id>/votar')
async def vote_movie(movie_id: int):
    user_uid = extract_uid_from_token()
    if not user_uid:
        return jsonify({"error": "Token de usuario inválido o no proporcionado"}), 401
    data = await request.get_json()
    if not data or "vote" not in data:
        return jsonify({"error": "Faltan parámetros requeridos (vote)"}), 400
    vote = data["vote"]
    if not isinstance(vote, int):
        return jsonify({"error": "El voto debe ser un número entero"}), 400
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("SELECT votar_pelicula(:user_uid, :movie_id, :vote)")
                await session.execute(query, {"user_uid": user_uid, "movie_id": movie_id, "vote": vote})
                return jsonify({"message": "Movie rated successfully"}), 200
            except Exception as e:
                error_message = str(e)
                if "no existe" in error_message.lower():
                    return jsonify({"error": "Pelicula no encontrada", "details": str(e)}), 404
                if "entre 0 y 10" in error_message.lower():
                    return jsonify({"error": "El voto debe estar entre 0 y 10", "details": str(e)}), 422
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Obtener el promedio de los votos de una película
@app.get('/api/peliculas/<int:movie_id>/votos')
async def get_movie_votes(movie_id: int):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("SELECT valoracion_media(:movie_id)")
                result = await session.execute(query, {"movie_id": movie_id})
                promedio = result.scalar()
                return jsonify({"message": "Average rating obtained successfully", "movie_id": movie_id, "average": float(promedio)}), 200
            except Exception as e:
                error_message = str(e)
                if "no existe" in error_message.lower():
                    return jsonify({"error": "Pelicula no encontrada", "details": str(e)}), 404
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500

# Obtener historial de ventas en un año dado para los clientes pertenecientes a un país específico
@app.get('/api/ventas/<int:anio>/<string:pais>')
async def get_sales(anio: int, pais: str):
    async with async_session() as session:
        async with session.begin():
            try:
                query = text("SELECT * FROM obtener_ventas_anio_pais(:anio, :pais)")
                result = await session.execute(query, {"anio": anio, "pais": pais})
                ventas = result.mappings().all()
                ventas_list = []
                for venta in ventas:
                    venta_dict = {
                        "sale_id": venta["pedido_id"],
                        "user_uid": venta["usuario_uid"],
                        "username": venta["username"],
                        "amount": float(venta["importe"]), 
                        "date": venta["fecha_pago"].isoformat() if venta["fecha_pago"] else None
                    }
                    ventas_list.append(venta_dict)
                return jsonify({"message": "Sales history obtained successfully", "year": anio, "country": pais, "sales": ventas_list}), 200
            except Exception as e:
                return jsonify({"error": "Error inesperado", "details": str(e)}), 500