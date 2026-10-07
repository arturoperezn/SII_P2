from quart import Quart, jsonify, request
from uuid import uuid4, uuid5, UUID
import os
from pathlib import Path
from hashlib import sha256
import json

app = Quart(__name__)

# source .venv/bin/activate


# Comprobar si ejecutando en contenedor Docker o entorno local y establecer la ruta de datos de archivos en consecuencia
if Path("/app/data").exists() or os.path.exists("/.dockerenv"):
    user_data_path = Path("/app/data/users.json")
else:
    user_data_path = Path("data_users/users.json")
users = {}
if user_data_path.exists():
    with open(user_data_path, "r") as f:
        users = json.load(f)

# Carga o genera un UUID secreto para la aplicación, que se usará para generar tokens de usuario.
def _load_or_create_secret_uuid_env():
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

secret_uuid = _load_or_create_secret_uuid_env()

# Función aux para guardar la contraseña encriptada usando SHA-256
def hash_pwd (password: str) -> str:
    #encode lo convierte a bits (sha256 necesita bits), sha256 encripta y hexdigest lo convierte a hex
    return sha256(password.encode()).hexdigest()

# Comprueba si la petición actual trae un token válido de sesión
def check_login():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "): 
        return None
            
    token = token.replace("Bearer ", "")
    if not token:
        return None
        
    for user in users.values():
        if str(uuid5(UUID(secret_uuid), user["uid"])) == token:
            return user
    return None


# Crea un usuario nuevo con nombre, contraseña y token de acceso
@app.put('/user')
async def create_user():
    
    data = await request.get_json()
    #vacio?
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
        
    name = data.get("name")
    password = data.get("password")
    
    if not name:
        return jsonify({"error": "Falta name"}), 400
    
    if not password:
        return jsonify({"error": "Falta password"}), 400
    
    #comprobar si ya existe
    if (name in users):
        return jsonify({"error": "El usuario ya existe"}), 409
    
    #crear uid y token de este usuario
    user_uid = str(uuid4())
    pwd_hash = hash_pwd(password)
    token = str(uuid5(UUID(secret_uuid), user_uid))
    
    users[name] = {
        "uid": user_uid,
        "pwd_hash": pwd_hash
    }

    # Guardar usuario en archivo de datos
    user_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(user_data_path, "w") as f:
        json.dump(users, f, indent=4)

    return jsonify({
        "uid": user_uid,
        "token": token
    }), 201

    


# Inicia sesión comprobando nombre y contraseña y devuelve el token
@app.post("/user")
async def login():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    
    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    
    #comprobamos si el usuario existe
    user = users.get(name)
    if not user:
        return jsonify({"error": "Usuario no existe"}), 404
    
    if user["pwd_hash"] != hash_pwd(password):
        return jsonify({"error": "Password incorrecta"}), 401
    
    return jsonify({
        "uid": user["uid"],
        "token": str(uuid5(UUID(secret_uuid), user["uid"]))
    }), 200


# Cambia la contraseña del usuario
@app.patch("/user")
async def modify_user():
    #si no esta iniciada la sesion fallar
    user = check_login()
    if not user:
        return jsonify({"error": "No autorizado"}), 401
        
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    password = data.get("password")
    
    if not password:
        return jsonify ({"error": "Falta nueva password"}), 400
    
    user["pwd_hash"] = hash_pwd(password)
    with open(user_data_path, "w") as f:
        json.dump(users, f, indent=4)
    return jsonify ({"message": "Password actualizada correctamente"}), 200
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
