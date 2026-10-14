from quart import Quart, jsonify, request
from uuid import uuid4, uuid5, UUID
import os
from pathlib import Path
from hashlib import sha256
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

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

# Creación de película
@app.post('/api/movies')
async def create_movie():
    data = await request.get_json()
    title = data.get("title")
    director = data.get("director")
    year = data.get("year")

    

    return jsonify({"message": "Movie created successfully"}), 201