from quart import Quart, jsonify, request
from uuid import uuid4, uuid5, UUID
import os
from pathlib import Path
from hashlib import sha256
import json

app = Quart(__name__)

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