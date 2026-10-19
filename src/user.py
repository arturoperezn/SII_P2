import asyncio
import os
from pathlib import Path
from uuid import uuid4, uuid5, UUID
import bcrypt
from quart import Quart, jsonify, request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from hmac import compare_digest
from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import DataError

app = Quart(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@localhost:5432/si1")
engine = create_async_engine(DATABASE_URL, echo=False)

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

async def hash_pwd(password: str) -> str:
    hashed = await asyncio.to_thread(bcrypt.hashpw, password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


async def check_pwd(password: str, stored_hash: str) -> bool:
    return await asyncio.to_thread(bcrypt.checkpw, password.encode("utf-8"), stored_hash.encode("utf-8"))

def generate_token(user_uid: str) -> str:
    token_hash = str(uuid5(UUID(secret_uuid), user_uid))
    return f"{user_uid}.{token_hash}"

# Comprueba si la petición actual trae un token válido de sesión
def check_login():
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    parts = token.split(".")

    if len(parts) != 2:
        return None

    user_uid = parts[0]

    try:
        UUID(user_uid)
    except ValueError:
        return None

    expected_token = generate_token(user_uid)

    if not compare_digest(token.encode("utf-8"), expected_token.encode("utf-8")):
        return None

    return user_uid


@app.put("/user")
async def create_user():
    data = await request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    name = data.get("name")
    password = data.get("password")
    pais = data.get("pais")

    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        return jsonify({"error": "Name debe tener entre 1 y 100 caracteres"}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"error": "Falta password válida"}), 400

    if len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Password no puede superar 72 bytes"}), 400

    if not isinstance(pais, str) or not pais.strip() or len(pais) > 100:
        return jsonify({"error": "Pais debe tener entre 1 y 100 caracteres"}), 400

    user_uid = str(uuid4())
    pwd_hash = await hash_pwd(password)

    query = text("""
        INSERT INTO USUARIOS (uid, username, password_hash, pais)
        VALUES (:uid, :username, :password_hash, :pais)
        ON CONFLICT (username) DO NOTHING
        RETURNING uid
    """)

    async with engine.begin() as conn:
        result = await conn.execute(query, {
            "uid": user_uid,
            "username": name,
            "password_hash": pwd_hash,
            "pais": pais
        })
        created_uid = result.scalar()

    if created_uid is None:
        return jsonify({"error": "El usuario ya existe"}), 409

    return jsonify({
        "uid": created_uid,
        "token": generate_token(created_uid)
    }), 201
    

@app.post("/user")
async def login():
    data = await request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    name = data.get("name")
    password = data.get("password")

    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        return jsonify({"error": "Name no válido"}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"error": "Falta password válida"}), 400

    if len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Password no puede superar 72 bytes"}), 400

    query = text("""
        SELECT uid, password_hash
        FROM USUARIOS
        WHERE username = :username
    """)

    async with engine.connect() as conn:
        result = await conn.execute(query, {"username": name})
        user = result.mappings().first()

    if user is None:
        return jsonify({"error": "Usuario no existe"}), 404

    try:
        correcta = await check_pwd(password, user["password_hash"])
    except ValueError:
        correcta = False

    if not correcta:
        return jsonify({"error": "Password incorrecta"}), 401

    return jsonify({
        "uid": user["uid"],
        "token": generate_token(user["uid"])
    }), 200


@app.patch("/user")
async def modify_user():
    user_uid = check_login()

    if user_uid is None:
        return jsonify({"error": "No autorizado"}), 401

    data = await request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    password = data.get("password")

    if not isinstance(password, str) or not password:
        return jsonify({"error": "Falta nueva password válida"}), 400

    if len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Password no puede superar 72 bytes"}), 400

    pwd_hash = await hash_pwd(password)

    query = text("""
        UPDATE USUARIOS
        SET password_hash = :password_hash
        WHERE uid = :uid
        RETURNING uid
    """)

    async with engine.begin() as conn:
        result = await conn.execute(query, {
            "password_hash": pwd_hash,
            "uid": user_uid
        })
        updated_uid = result.scalar()

    if updated_uid is None:
        return jsonify({"error": "Usuario no existe"}), 404

    return jsonify({"message": "Password actualizada correctamente"}), 200

@app.delete("/user")
async def delete_user():
    user_uid = check_login()

    if user_uid is None:
        return jsonify({"error": "No autorizado"}), 401

    query = text("""
        DELETE FROM USUARIOS
        WHERE uid = :uid
        RETURNING uid
    """)

    async with engine.begin() as conn:
        result = await conn.execute(query, {"uid": user_uid})
        deleted_uid = result.scalar()

    if deleted_uid is None:
        return jsonify({"error": "Usuario no existe"}), 404

    return jsonify({"message": "Usuario eliminado correctamente"}), 200

@app.patch("/user/saldo")
async def recharge_balance():
    user_uid = check_login()

    if user_uid is None:
        return jsonify({"error": "No autorizado"}), 401

    data = await request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un objeto JSON"}), 400

    value = data.get("saldo")

    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return jsonify({"error": "Saldo debe ser un importe numérico"}), 400

    try:
        amount = Decimal(str(value))

        if not amount.is_finite():
            raise ValueError()

        if amount <= 0 or amount > Decimal("99999999.99"):
            raise ValueError()

        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError()

    except (InvalidOperation, ValueError):
        return jsonify({
            "error": "La recarga debe ser positiva, con máximo dos decimales y hasta 99999999.99"
        }), 400

    query = text("""
        UPDATE USUARIOS
        SET saldo = saldo + :amount
        WHERE uid = :uid
        RETURNING saldo
    """)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(query, {
                "amount": amount,
                "uid": user_uid
            })
            new_balance = result.scalar()
    except DataError:
        return jsonify({"error": "El saldo resultante supera el límite permitido"}), 409

    if new_balance is None:
        return jsonify({"error": "Usuario no existe"}), 404

    return jsonify({
        "message": "Saldo recargado correctamente",
        "saldo": str(new_balance)
    }), 200
    
@app.post("/user/logout")
async def logout():
    user_uid = check_login()

    if user_uid is None:
        return jsonify({"error": "No autorizado"}), 401

    query = text("SELECT uid FROM USUARIOS WHERE uid = :uid")

    async with engine.connect() as conn:
        result = await conn.execute(query, {"uid": user_uid})
        existing_uid = result.scalar()

    if existing_uid is None:
        return jsonify({"error": "Usuario no existe"}), 404

    return jsonify({
        "message": "Sesion cerrada; elimina el token del cliente"
    }), 200
    
@app.after_serving
async def close_engine():
    await engine.dispose()
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)