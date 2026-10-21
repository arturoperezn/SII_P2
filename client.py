import requests
from pathlib import Path
import os
import uuid

USER_URL = "http://127.0.0.1:5050"
API_URL = "http://127.0.0.1:5051"

def run_tests():
    print("Iniciando pruebas de la API de usuario\n")

    # Usuario inexistente para pruebas
    uid_inexistente = str(uuid.uuid4())
    if Path("/app/shared_data").exists() or os.path.exists("/.dockerenv"):
        secret_path = Path("/app/shared_data/secret_uuid.txt")
    else:
        secret_path = Path("shared_data/secret_uuid.txt")
    if secret_path.exists():
        with open(secret_path, "r") as f:
            secret_uuid = f.read().strip()
        token_inexistente = f"{uid_inexistente}.{uuid.uuid5(uuid.UUID(secret_uuid), uid_inexistente)}"

    # 1. Crear usuario Alicia
    r = requests.put(f"{USER_URL}/user", json={"name": "alicia", "password": "pwd", "pais": "España"})
    if r.status_code == 201:
        print("[OK] Crear usuario Alicia (HTTP 201)")
        data = r.json()
        uid_alicia = data["uid"]
        token_alicia = data["token"]
    else:
        print(f"[FAIL] Crear usuario Alicia - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 2. Crear usuario Alicia que ya existe 
    r = requests.put(f"{USER_URL}/user", json={"name": "alicia", "password": "pwd2", "pais": "España"})
    if r.status_code == 409:
        print("[OK] Crear usuario Alicia que ya existe (HTTP 409)")
    else:
        print(f"[FAIL] Crear usuario Alicia que ya existe - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 3. Crear usuario Alicia sin password 
    r = requests.put(f"{USER_URL}/user", json={"name": "alicia", "pais": "España"})
    if r.status_code == 400:
        print("[OK] Crear usuario Alicia sin password (HTTP 400)")
    else:
        print(f"[FAIL] Crear usuario Alicia sin password - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 4. Crear usuario sin nombre 
    r = requests.put(f"{USER_URL}/user", json={"password": "pwd", "pais": "España"})
    if r.status_code == 400:
        print("[OK] Crear usuario sin nombre (HTTP 400)")
    else:
        print(f"[FAIL] Crear usuario sin nombre - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 5. Crear usuario sin pais
    r = requests.put(f"{USER_URL}/user", json={"name": "alicia", "password": "pwd"})
    if r.status_code == 400:
        print("[OK] Crear usuario sin pais (HTTP 400)")
    else:
        print(f"[FAIL] Crear usuario sin pais - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 6. Crear usuario sin datos 
    r = requests.put(f"{USER_URL}/user", json={})
    if r.status_code == 400:
        print("[OK] Crear usuario sin datos (HTTP 400)")
    else:
        print(f"[FAIL] Crear usuario sin datos - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 7. Iniciar sesión con usuario Alicia
    r = requests.post(f"{USER_URL}/user", json={"name": "alicia", "password": "pwd"})
    if r.status_code == 200:
        print("[OK] Iniciar sesión con usuario Alicia (HTTP 200)")
        data = r.json()
        if data.get("token") == token_alicia:
            print("[OK] Token recibido coincide con el token esperado")
        else:
            print(f"[FAIL] Token recibido no coincide - Esperado: {token_alicia}, Obtenido: {data.get('token')}")
    else:
        print(f"[FAIL] Iniciar sesión con usuario Alicia - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    headers_alicia = {"Authorization": f"Bearer {token_alicia}"}

    # 8. Iniciar sesión con usuario Alicia con contraseña incorrecta
    r = requests.post(f"{USER_URL}/user", json={"name": "alicia", "password": "wrongpwd"})
    if r.status_code == 401:
        print("[OK] Iniciar sesión con usuario Alicia con contraseña incorrecta (HTTP 401)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario Alicia con contraseña incorrecta - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 9. Iniciar sesión con usuario que no existe
    r = requests.post(f"{USER_URL}/user", json={"name": "sergio", "password": "pwd"})
    if r.status_code == 404:
        print("[OK] Iniciar sesión con usuario que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 10. Iniciar sesión con usuario sin datos
    r = requests.post(f"{USER_URL}/user", json={})
    if r.status_code == 400:
        print("[OK] Iniciar sesión con usuario sin datos (HTTP 400)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario sin datos - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 11. Iniciar sesión con usuario sin password
    r = requests.post(f"{USER_URL}/user", json={"name": "alicia"})
    if r.status_code == 400:
        print("[OK] Iniciar sesión con usuario sin password (HTTP 400)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario sin password - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 12. Iniciar sesión con usuario sin nombre
    r = requests.post(f"{USER_URL}/user", json={"password": "pwd"})
    if r.status_code == 400:
        print("[OK] Iniciar sesión con usuario sin nombre (HTTP 400)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario sin nombre - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 13. Cambiar contraseña de Alicia
    r = requests.patch(
        f"{USER_URL}/user",
        json={"password": "newpwd"},
        headers=headers_alicia
    )
    if r.status_code == 200:
        print("[OK] Cambiar contraseña de Alicia (HTTP 200)")
    else:
        print(f"[FAIL] Cambiar contraseña de Alicia - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 14. Iniciar sesión con usuario Alicia con la nueva contraseña
    r = requests.post(f"{USER_URL}/user", json={"name": "alicia", "password": "newpwd"})
    if r.status_code == 200:
        print("[OK] Iniciar sesión con usuario Alicia con la nueva contraseña (HTTP 200)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario Alicia con la nueva contraseña - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 15. Iniciar sesión con usuario Alicia con la contraseña antigua
    r = requests.post(f"{USER_URL}/user", json={"name": "alicia", "password": "pwd"})
    if r.status_code == 401:
        print("[OK] Iniciar sesión con usuario Alicia con la contraseña antigua (HTTP 401)")
    else:
        print(f"[FAIL] Iniciar sesión con usuario Alicia con la contraseña antigua - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 16. Cambiar contraseña de Alicia sin estar logueada (sin token) 
    r = requests.patch(
        f"{USER_URL}/user",
        json={"password": "anotherpwd"}
    )
    if r.status_code == 401:
        print("[OK] Cambiar contraseña de Alicia sin estar logueada (sin token) (HTTP 401)")
    else:
        print(f"[FAIL] Cambiar contraseña de Alicia sin estar logueada - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")
        return

    # 17. Cambiar contraseña de Alicia con token pero sin nueva contraseña
    r = requests.patch(
        f"{USER_URL}/user",
        json={},
        headers=headers_alicia
    )
    if r.status_code == 400:
        print("[OK] Cambiar contraseña de Alicia con token pero sin nueva contraseña (HTTP 400)")
    else:
        print(f"[FAIL] Cambiar contraseña de Alicia con token pero sin nueva contraseña - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 18. Cambiar contraseña de un usuario que no existe
    r = requests.patch(
        f"{USER_URL}/user",
        json={"password": "newpwd"},
        headers={"Authorization": f"Bearer {token_inexistente}"}
    )
    if r.status_code == 404:
        print("[OK] Cambiar contraseña de un usuario que no existe con token válido (HTTP 404)")
    else:
        print(f"[FAIL] Cambiar contraseña de un usuario que no existe con token válido - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 19. Eliminar usuario nuevo
    # Creamos un nuevo usuario para eliminarlo
    r = requests.put(f"{USER_URL}/user", json={"name": "eliminar", "password": "pwd", "pais": "España"})
    if r.status_code == 201:
        data = r.json()
        token_eliminar= data["token"]
        r = requests.delete(
            f"{USER_URL}/user",
            headers={"Authorization": f"Bearer {token_eliminar}"}
        )
        if r.status_code == 200:
            print("[OK] Eliminar usuario nuevo (HTTP 200)")
        else:
            print(f"[FAIL] Eliminar usuario nuevo - Esperado: 200, Obtenido: {r.status_code}")
            print(f"       Respuesta: {r.text}")
    else: 
        print(f"[FAIL] Crear usuario para eliminarlo - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 20. Eliminar usuario sin token
    r = requests.delete(f"{USER_URL}/user")
    if r.status_code == 401:
        print("[OK] Eliminar usuario sin token (HTTP 401)")
    else:
        print(f"[FAIL] Eliminar usuario sin token - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 21. Eliminar usuario que no existe
    r = requests.delete(
        f"{USER_URL}/user",
        headers={"Authorization": f"Bearer {token_inexistente}"}
    )
    if r.status_code == 404:
        print("[OK] Eliminar usuario que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Eliminar usuario que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 22. Recargar saldo de Alicia
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": 120.00},
        headers=headers_alicia
    )
    if r.status_code == 200:
        print("[OK] Recargar saldo de Alicia (HTTP 200)")
    else:
        print(f"[FAIL] Recargar saldo de Alicia - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 23. Recargar saldo de Alicia con saldo negativo
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": -50.00},
        headers=headers_alicia
    )
    if r.status_code == 400:
        print("[OK] Recargar saldo de Alicia con saldo negativo (HTTP 400)")
    else:
        print(f"[FAIL] Recargar saldo de Alicia con saldo negativo - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 24. Recargar saldo de Alicia con 3 decimales
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": 10.123},
        headers=headers_alicia
    )
    if r.status_code == 400:
        print("[OK] Recargar saldo de Alicia con 3 decimales (HTTP 400)")
    else:
        print(f"[FAIL] Recargar saldo de Alicia con 3 decimales - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 25. Recargar saldo de Alicia con saldo mayor a 99999999.99
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": 100000000.00},
        headers=headers_alicia
    )
    if r.status_code == 400:
        print("[OK] Recargar saldo de Alicia con saldo mayor a 99999999.99 (HTTP 400)")
    else:
        print(f"[FAIL] Recargar saldo de Alicia con saldo mayor a 99999999.99 - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 26. Recargar saldo de Alicia con saldo no numérico
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": "abc"},
        headers=headers_alicia
    )
    if r.status_code == 400:
        print("[OK] Recargar saldo de Alicia con saldo no numérico (HTTP 400)")
    else:
        print(f"[FAIL] Recargar saldo de Alicia con saldo no numérico - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 27. Recargar saldo de Alicia sin token
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": 50.00}
    )
    if r.status_code == 401:
        print("[OK] Recargar saldo de Alicia sin token (HTTP 401)")
    else:
        print(f"[FAIL] Recargar saldo de Alicia sin token - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 28. Recargar saldo de usuario que no existe
    r = requests.patch(
        f"{USER_URL}/user/saldo",
        json={"saldo": 50.00},
        headers={"Authorization": f"Bearer {token_inexistente}"}
    )
    if r.status_code == 404:
        print("[OK] Recargar saldo de usuario que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Recargar saldo de usuario que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 29. Cerrar sesión de Alicia
    r = requests.post(
        f"{USER_URL}/user/logout",
        headers=headers_alicia
    )
    if r.status_code == 200:
        print("[OK] Cerrar sesión de Alicia (HTTP 200)")
    else:
        print(f"[FAIL] Cerrar sesión de Alicia - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")
    token_alicia = None  # Invalidamos el token de Alicia para futuras pruebas

    # 30. Cerrar sesión de Alicia sin token
    r = requests.post(
        f"{USER_URL}/user/logout"
    )
    if r.status_code == 401:
        print("[OK] Cerrar sesión de Alicia sin token (HTTP 401)")
    else:
        print(f"[FAIL] Cerrar sesión de Alicia sin token - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 31. Cerrar sesión de usuario que no existe
    r = requests.post(
        f"{USER_URL}/user/logout",
        headers={"Authorization": f"Bearer {token_inexistente}"}
    )
    if r.status_code == 404:
        print("[OK] Cerrar sesión de usuario que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Cerrar sesión de usuario que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    print("\nIniciando pruebas de la API principal\n")

    # 32. Crear director
    r = requests.post(
        f"{API_URL}/api/directores",
        json={"name": "Director 1"}
    )
    if r.status_code == 201:
        print("[OK] Crear director (HTTP 201)")
        data = r.json()
        director_id = data["director_id"]
    else:
        print(f"[FAIL] Crear director - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 33. Crear director con nombre vacío
    r = requests.post(
        f"{API_URL}/api/directores",
        json={"name": ""}
    )
    if r.status_code == 400:
        print("[OK] Crear director con nombre vacío (HTTP 400)")
    else:
        print(f"[FAIL] Crear director con nombre vacío - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 34. Crear director sin datos
    r = requests.post(
        f"{API_URL}/api/directores",
        json={}
    )
    if r.status_code == 400:
        print("[OK] Crear director sin datos (HTTP 400)")
    else:
        print(f"[FAIL] Crear director sin datos - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 35. Crear actor
    r = requests.post(
        f"{API_URL}/api/actores",
        json={"name": "Actor 1"}
    )
    if r.status_code == 201:
        print("[OK] Crear actor (HTTP 201)")
        data = r.json()
        actor_id = data["actor_id"]
    else:
        print(f"[FAIL] Crear actor - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 36. Crear actor con nombre vacío
    r = requests.post(
        f"{API_URL}/api/actores",
        json={"name": ""}
    )
    if r.status_code == 400:
        print("[OK] Crear actor con nombre vacío (HTTP 400)")
    else:
        print(f"[FAIL] Crear actor con nombre vacío - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 37. Crear actor sin datos
    r = requests.post(
        f"{API_URL}/api/actores",
        json={}
    )
    if r.status_code == 400:
        print("[OK] Crear actor sin datos (HTTP 400)")
    else:
        print(f"[FAIL] Crear actor sin datos - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 38. Crear una película
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 1", "year": 2010, "price": 19.99, "genre": "Accion", "stock": 10, "directors": [director_id], "actors": [actor_id]}
    )
    if r.status_code == 201:
        print("[OK] Crear una película (HTTP 201)")
        data = r.json()
        pelicula_id = data["movie_id"]
    else:
        print(f"[FAIL] Crear una película - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 39. Crear una película sin título
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"year": 2023, "price": 19.99, "genre": "Accion", "stock": 10, "directors": [director_id], "actors": [actor_id]}
    )
    if r.status_code == 400:
        print("[OK] Crear una película sin título (HTTP 400)")
    else:
        print(f"[FAIL] Crear una película sin título - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 40. Crear una película sin año
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 2", "price": 19.99, "genre": "Accion", "stock": 10, "directors": [director_id], "actors": [actor_id]}
    )
    if r.status_code == 400:
        print("[OK] Crear una película sin año (HTTP 400)")
    else:
        print(f"[FAIL] Crear una película sin año - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 41. Crear una película sin precio
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 3", "year": 2023, "genre": "Accion", "stock": 10, "directors": [director_id], "actors": [actor_id]}
    )
    if r.status_code == 400:
        print("[OK] Crear una película sin precio (HTTP 400)")
    else:
        print(f"[FAIL] Crear una película sin precio - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 42. Crear una película sin género
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 4", "year": 2023, "price": 19.99, "stock": 10, "directors": [director_id], "actors": [actor_id]}
    )
    if r.status_code == 400:
        print("[OK] Crear una película sin género (HTTP 400)")
    else:
        print(f"[FAIL] Crear una película sin género - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 43. Crear una película sin stock
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 5", "year": 2023, "price": 19.99, "genre": "Accion", "directors": [director_id], "actors": [actor_id]}
    )
    if r.status_code == 201:
        print("[OK] Crear una película sin stock (HTTP 201) - Se asume stock=0 por defecto")
    else:
        print(f"[FAIL] Crear una película sin stock - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 44. Crear una película con director que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 6", "year": 2023, "price": 19.99, "genre": "Accion", "stock": 10, "directors": [999], "actors": [actor_id]}
    )
    if r.status_code == 409:
        print("[OK] Crear una película con director que no existe (HTTP 409)")
    else:
        print(f"[FAIL] Crear una película con director que no existe - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 45. Crear una película con actor que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula 7", "year": 2023, "price": 19.99, "genre": "Accion", "stock": 10, "directors": [director_id], "actors": [999]}
    )
    if r.status_code == 409:
        print("[OK] Crear una película con actor que no existe (HTTP 409)")
    else:
        print(f"[FAIL] Crear una película con actor que no existe - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 46. Añadir actor a la película
    # Creamos un nuevo actor
    r = requests.post(
        f"{API_URL}/api/actores",
        json={"name": "Actor 2"}
    )
    if r.status_code == 201:
        data = r.json()
        actor2_id = data["actor_id"]
        r = requests.post(
            f"{API_URL}/api/peliculas/{pelicula_id}/actores/{actor2_id}"
        )
        if r.status_code == 201:
            print("[OK] Añadir actor a la película (HTTP 201)")
        else:
            print(f"[FAIL] Añadir actor a la película - Esperado: 201, Obtenido: {r.status_code}")
            print(f"       Respuesta: {r.text}")
    else:
        print(f"[FAIL] Crear actor para añadirlo a la película - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 47. Añadir actor que no existe a la película
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/actores/999"
    )
    if r.status_code == 409:
        print("[OK] Añadir actor que no existe a la película (HTTP 409)")
    else:
        print(f"[FAIL] Añadir actor que no existe a la película - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 48. Añadir actor a película que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas/999/actores/{actor2_id}"
    )
    if r.status_code == 409:
        print("[OK] Añadir actor a película que no existe (HTTP 409)")
    else:
        print(f"[FAIL] Añadir actor a película que no existe - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 49. Añadir director a la película
    # Creamos un nuevo director
    r = requests.post(
        f"{API_URL}/api/directores",
        json={"name": "Director 2"}
    )
    if r.status_code == 201:
        data = r.json()
        director2_id = data["director_id"]
        r = requests.post(
            f"{API_URL}/api/peliculas/{pelicula_id}/directores/{director2_id}"
        )
        if r.status_code == 201:
            print("[OK] Añadir director a la película (HTTP 201)")
        else:
            print(f"[FAIL] Añadir director a la película - Esperado: 201, Obtenido: {r.status_code}")
            print(f"       Respuesta: {r.text}")
    else:
        print(f"[FAIL] Crear director para añadirlo a la película - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 50. Añadir director que no existe a la película
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/directores/999"
    )
    if r.status_code == 409:
        print("[OK] Añadir director que no existe a la película (HTTP 409)")
    else:
        print(f"[FAIL] Añadir director que no existe a la película - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 51. Añadir director a película que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas/999/directores/{director2_id}"
    )
    if r.status_code == 409:
        print("[OK] Añadir director a película que no existe (HTTP 409)")
    else:
        print(f"[FAIL] Añadir director a película que no existe - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 52. Añadir stock de la película
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": 5}
    )
    if r.status_code == 200:
        print("[OK] Añadir stock de la película (HTTP 200)")
    else:
        print(f"[FAIL] Añadir stock de la película - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 53. Reducir stock de la película
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": -5}
    )
    if r.status_code == 200:
        print("[OK] Reducir stock de la película (HTTP 200)")
    else:
        print(f"[FAIL] Reducir stock de la película - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 54. Reducir stock de la película a negativo
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": -100}
    )
    if r.status_code == 409:
        print("[OK] Reducir stock de la película a negativo (HTTP 409)")
    else:
        print(f"[FAIL] Reducir stock de la película a negativo - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 55. Añadir stock de la película con cantidad no numérica entera
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": "abc"}
    )
    if r.status_code == 400:
        print("[OK] Añadir stock de la película con cantidad no numérica (HTTP 400)")
    else:
        print(f"[FAIL] Añadir stock de la película con cantidad no numérica - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 56. Añadir stock de la película con cantidad no entera (decimal)
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": 5.5}
    )
    if r.status_code == 400:
        print("[OK] Añadir stock de la película con cantidad no entera (HTTP 400)")
    else:
        print(f"[FAIL] Añadir stock de la película con cantidad no entera - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 57. Añadir stock de la película con cantidad 0
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": 0}
    )
    if r.status_code == 400:
        print("[OK] Añadir stock de la película con cantidad 0 (HTTP 400)")
    else:
        print(f"[FAIL] Añadir stock de la película con cantidad 0 - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 58. Añadir stock sin especificar cantidad
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": None}
    )
    if r.status_code == 400:
        print("[OK] Añadir stock sin especificar cantidad (HTTP 400)")
    else:
        print(f"[FAIL] Añadir stock sin especificar cantidad - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 59. Añadir stock a película sin datos
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={}
    )
    if r.status_code == 400:
        print("[OK] Añadir stock a película sin datos (HTTP 400)")
    else:
        print(f"[FAIL] Añadir stock a película sin datos - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 60. Añadir stock a película que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas/999/stock",
        json={"stock": 5}
    )
    if r.status_code == 404:
        print("[OK] Añadir stock a película que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Añadir stock a película que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 61. Establecer stock de la película
    r = requests.put(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": 10}
    )
    if r.status_code == 200:
        print("[OK] Establecer stock de la película (HTTP 200)")
    else:
        print(f"[FAIL] Establecer stock de la película - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 62. Establecer stock de la película a negativo
    r = requests.put(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": -10}
    )
    if r.status_code == 400:
        print("[OK] Establecer stock de la película a negativo (HTTP 400)")
    else:
        print(f"[FAIL] Establecer stock de la película a negativo - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 63. Establecer stock de la película con cantidad no numérica entera
    r = requests.put(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": "abc"}
    )
    if r.status_code == 400:
        print("[OK] Establecer stock de la película con cantidad no numérica (HTTP 400)")
    else:
        print(f"[FAIL] Establecer stock de la película con cantidad no numérica - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 64. Establecer stock de la película con cantidad no entera (decimal)
    r = requests.put(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": 5.5}
    )
    if r.status_code == 400:
        print("[OK] Establecer stock de la película con cantidad no entera (HTTP 400)")
    else:
        print(f"[FAIL] Establecer stock de la película con cantidad no entera - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 65. Establecer stock de la película sin especificar cantidad
    r = requests.put(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={"stock": None}
    )
    if r.status_code == 400:
        print("[OK] Establecer stock de la película sin especificar cantidad (HTTP 400)")
    else:
        print(f"[FAIL] Establecer stock de la película sin especificar cantidad - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 66. Establecer stock de película sin datos
    r = requests.put(
        f"{API_URL}/api/peliculas/{pelicula_id}/stock",
        json={}
    )
    if r.status_code == 400:
        print("[OK] Establecer stock de película sin datos (HTTP 400)")
    else:
        print(f"[FAIL] Establecer stock de película sin datos - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 67. Establecer stock de película que no existe
    r = requests.put(
        f"{API_URL}/api/peliculas/999/stock",
        json={"stock": 5}
    )
    if r.status_code == 404:
        print("[OK] Establecer stock de película que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Establecer stock de película que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 68. Obtener lista de películas por un criterio especifico (titulo, genero y año)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"titulo": "Pelicula 1", "genero": "Accion", "anio": 2010}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio especifico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio especifico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 69. Obtener lista de películas por un criterio específico (genero y año)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"genero": "Accion", "anio": 2010}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 70. Obtener lista de películas por un criterio específico (titulo y año)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"titulo": "Pelicula 1", "anio": 2010}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 71. Obtener lista de películas por un criterio específico (titulo y genero)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"titulo": "Pelicula 1", "genero": "Accion"}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 72. Obtener lista de películas por un criterio específico (solo titulo)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"titulo": "Pelicula 1"}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 73. Obtener lista de películas por un criterio específico (solo genero)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"genero": "Accion"}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 74. Obtener lista de películas por un criterio específico (solo año)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"anio": 2010}
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas que cumplen con el criterio")
        else:
            print("[FAIL] No se encontraron películas que cumplan con el criterio")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 75. Obtener lista de películas por un criterio específico (año no numérico entero)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"anio": "abc"}
    )
    if r.status_code == 400:
        print("[OK] Obtener lista de películas por un criterio específico (año no numérico entero) (HTTP 400)")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico (año no numérico entero) - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 76. Obtener lista de películas por un criterio específico (año no entero)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"anio": 2010.5}
    )
    if r.status_code == 400:
        print("[OK] Obtener lista de películas por un criterio específico (año no entero) (HTTP 400)")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico (año no entero) - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 77. Obtener lista de películas por un criterio específico (año negativo)
    r = requests.get(
        f"{API_URL}/api/peliculas",
        params={"anio": -2010}
    )
    if r.status_code == 400:
        print("[OK] Obtener lista de películas por un criterio específico (año negativo) (HTTP 400)")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico (año negativo) - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 78. Obtener lista de películas por un criterio específico (sin criterios)
    r = requests.get(
        f"{API_URL}/api/peliculas"
    )
    if r.status_code == 200:
        print("[OK] Obtener lista de películas por un criterio específico (sin criterios) (HTTP 200)")
        data = r.json()
        if len(data["Movies"]) > 0:
            print(f"[OK] Se encontraron {len(data['Movies'])} películas")
        else:
            print("[FAIL] No se encontraron películas")
    else:
        print(f"[FAIL] Obtener lista de películas por un criterio específico (sin criterios) - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 79. Añadir película al carrito de Alicia
    # Primero iniciamos sesión de Alicia nuevamente para obtener un token válido
    r = requests.post(
        f"{USER_URL}/user",
        json={"name": "alicia", "password": "newpwd"}
    )
    if r.status_code == 200:
        data = r.json()
        token_alicia = data["token"]
        headers_alicia = {"Authorization": f"Bearer {token_alicia}"}
        r = requests.post(
            f"{API_URL}/api/carrito",
            headers=headers_alicia,
            json={"movie_id": pelicula_id, "quantity": 2}
        )
        if r.status_code == 201:
            print("[OK] Añadir película al carrito de Alicia (HTTP 201)")
        else:
            print(f"[FAIL] Añadir película al carrito de Alicia - Esperado: 201, Obtenido: {r.status_code}")
            print(f"       Respuesta: {r.text}")
    else:
        print(f"[FAIL] Iniciar sesión de Alicia - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 80. Añadir película al carrito de Alicia con cantidad negativa
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": pelicula_id, "quantity": -1}
    )
    if r.status_code == 400:
        print("[OK] Añadir película al carrito de Alicia con cantidad negativa (HTTP 400)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia con cantidad negativa - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 81. Añadir película al carrito de Alicia con cantidad no numérica
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": pelicula_id, "quantity": "abc"}
    )
    if r.status_code == 400:
        print("[OK] Añadir película al carrito de Alicia con cantidad no numérica (HTTP 400)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia con cantidad no numérica - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 82. Añadir película al carrito de Alicia con cantidad no entera (decimal)
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": pelicula_id, "quantity": 1.5}
    )
    if r.status_code == 400:
        print("[OK] Añadir película al carrito de Alicia con cantidad no entera (HTTP 400)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia con cantidad no entera - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 83. Añadir película al carrito de Alicia sin especificar película
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"quantity": 1}
    )
    if r.status_code == 400:
        print("[OK] Añadir película al carrito de Alicia sin especificar película (HTTP 400)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia sin especificar película - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 84. Añadir película al carrito de Alicia sin especificar cantidad
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": pelicula_id}
    )
    if r.status_code == 201:
        print("[OK] Añadir película al carrito de Alicia sin especificar cantidad (HTTP 201) - Se asume cantidad 1 por defecto")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia sin especificar cantidad - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 85. Añadir película al carrito de Alicia que no existe
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": 999, "quantity": 1}
    )
    if r.status_code == 404:
        print("[OK] Añadir película al carrito de Alicia que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 86. Añadir película al carrito de Alicia sin suficiente stock
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": pelicula_id, "quantity": 1000}
    )
    if r.status_code == 409:
        print("[OK] Añadir película al carrito de Alicia sin suficiente stock (HTTP 409)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia sin suficiente stock - Esperado: 409, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 87. Añadir película al carrito de Alicia sin token
    r = requests.post(
        f"{API_URL}/api/carrito",
        json={"movie_id": pelicula_id, "quantity": 1}
    )
    if r.status_code == 401:
        print("[OK] Añadir película al carrito de Alicia sin token (HTTP 401)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia sin token - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 88. Añadir película al carrito de un usuario que no existe con token de usuario que no existe
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers={"Authorization": f"Bearer {token_inexistente}"},
        json={"movie_id": pelicula_id, "quantity": 1}
    )
    if r.status_code == 404:
        print("[OK] Añadir película al carrito de Alicia con token de usuario que no existe (HTTP 401)")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia con token de usuario que no existe - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 89. Pagar carrito de Alicia con token válido
    r = requests.post(
        f"{API_URL}/api/carrito/pagar",
        headers=headers_alicia
    )
    if r.status_code == 200:
        print("[OK] Pagar carrito de Alicia con token válido (HTTP 200)")
    else:
        print(f"[FAIL] Pagar carrito de Alicia con token válido - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 90. Pagar carrito de Alicia sin token
    r = requests.post(
        f"{API_URL}/api/carrito/pagar"
    )
    if r.status_code == 401:
        print("[OK] Pagar carrito de Alicia sin token (HTTP 401)")
    else:
        print(f"[FAIL] Pagar carrito de Alicia sin token - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 91. Pagar carrito de Alicia de nuevo (sin items en el carrito)
    r = requests.post(
        f"{API_URL}/api/carrito/pagar",
        headers=headers_alicia
    )
    if r.status_code == 404:
        print("[OK] Pagar carrito de Alicia de nuevo (sin items en el carrito) (HTTP 404)")
    else:
        print(f"[FAIL] Pagar carrito de Alicia de nuevo (sin items en el carrito) - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 92. Pagar carrito de un usuario que no existe con token de usuario que no existe
    r = requests.post(
        f"{API_URL}/api/carrito/pagar",
        headers={"Authorization": f"Bearer {token_inexistente}"}
    )
    if r.status_code == 404:
        print("[OK] Pagar carrito de un usuario que no existe con token de usuario que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Pagar carrito de un usuario que no existe con token de usuario que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 93. Pagar carrito Alicia sin suficiente saldo
    # Primero añadimos una película al carrito de Alicia con cantidad suficiente para que el total supere su saldo
    r = requests.post(
        f"{API_URL}/api/carrito",
        headers=headers_alicia,
        json={"movie_id": pelicula_id, "quantity": 6}
    )
    if r.status_code == 201:
        r = requests.post(
            f"{API_URL}/api/carrito/pagar",
            headers=headers_alicia
        )
        if r.status_code == 402:
            print("[OK] Pagar carrito Alicia sin suficiente saldo (HTTP 402)")
        else:
            print(f"[FAIL] Pagar carrito Alicia sin suficiente saldo - Esperado: 402, Obtenido: {r.status_code}")
            print(f"       Respuesta: {r.text}")
    else:
        print(f"[FAIL] Añadir película al carrito de Alicia para prueba de pago sin saldo - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 94. Votar película por Alicia con token válido
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers=headers_alicia,
        json={"vote": 5}
    )
    if r.status_code == 200:
        print("[OK] Votar película por Alicia con token válido (HTTP 200)")
    else:
        print(f"[FAIL] Votar película por Alicia con token válido - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 95. Votar película por Alicia con voto negativo
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers=headers_alicia,
        json={"vote": -1}
    )
    if r.status_code == 422:
        print("[OK] Votar película por Alicia con voto negativo (HTTP 422)")
    else:
        print(f"[FAIL] Votar película por Alicia con voto negativo - Esperado: 422, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 96. Votar película por Alicia con voto mayor a 10
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers=headers_alicia,
        json={"vote": 11}
    )
    if r.status_code == 422:
        print("[OK] Votar película por Alicia con voto mayor a 10 (HTTP 422)")
    else:
        print(f"[FAIL] Votar película por Alicia con voto mayor a 10 - Esperado: 422, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 97. Votar película por Alicia con voto no numérico entero
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers=headers_alicia,
        json={"vote": "abc"}
    )
    if r.status_code == 400:
        print("[OK] Votar película por Alicia con voto no numérico (HTTP 400)")
    else:
        print(f"[FAIL] Votar película por Alicia con voto no numérico - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 98. Votar película por Alicia con voto no entero (decimal)
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers=headers_alicia,
        json={"vote": 5.5}
    )
    if r.status_code == 400:
        print("[OK] Votar película por Alicia con voto no entero (HTTP 400)")
    else:
        print(f"[FAIL] Votar película por Alicia con voto no entero - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 99. Votar película por Alicia sin especificar voto
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers=headers_alicia,
        json={}
    )
    if r.status_code == 400:
        print("[OK] Votar película por Alicia sin especificar voto (HTTP 400)")
    else:
        print(f"[FAIL] Votar película por Alicia sin especificar voto - Esperado: 400, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 100. Votar película por Alicia que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas/999/votar",
        headers=headers_alicia,
        json={"vote": 5}
    )
    if r.status_code == 404:
        print("[OK] Votar película por Alicia que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Votar película por Alicia que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 101. Votar película por un usuario que no existe con token de usuario que no existe
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        headers={"Authorization": f"Bearer {token_inexistente}"},
        json={"vote": 5}
    )
    if r.status_code == 404:
        print("[OK] Votar película por un usuario que no existe con token de usuario que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Votar película por un usuario que no existe con token de usuario que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 102. Votar película por Alicia sin token
    r = requests.post(
        f"{API_URL}/api/peliculas/{pelicula_id}/votar",
        json={"vote": 5}
    )
    if r.status_code == 401:
        print("[OK] Votar película por Alicia sin token (HTTP 401)")
    else:
        print(f"[FAIL] Votar película por Alicia sin token - Esperado: 401, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 103. Obtener el promedio de votos de la película
    r = requests.get(
        f"{API_URL}/api/peliculas/{pelicula_id}/votos"
    )
    if r.status_code == 200:
        print("[OK] Obtener el promedio de votos de la película (HTTP 200)")
        data = r.json()
        print(f"[OK] Promedio de votos: {data['average']}")
    else:
        print(f"[FAIL] Obtener el promedio de votos de la película - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 104. Obtener el promedio de votos de una película que no existe
    r = requests.get(
        f"{API_URL}/api/peliculas/999/votos"
    )
    if r.status_code == 404:
        print("[OK] Obtener el promedio de votos de una película que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Obtener el promedio de votos de una película que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 105. Obtener el promedio de votos de una película sin votos
    # Creamos una nueva película sin votos
    r = requests.post(
        f"{API_URL}/api/peliculas",
        json={"title": "Pelicula sin votos", "genre": "Drama", "year": 2020, "price": 10.0}
    )
    if r.status_code == 201:
        data = r.json()
        pelicula_sin_votos_id = data["movie_id"]
        r = requests.get(
            f"{API_URL}/api/peliculas/{pelicula_sin_votos_id}/votos"
        )
        if r.status_code == 200:
            print("[OK] Obtener el promedio de votos de una película sin votos (HTTP 200)")
            data = r.json()
            print(f"[OK] Promedio de votos: {data['average']}")
        else:
            print(f"[FAIL] Obtener el promedio de votos de una película sin votos - Esperado: 200, Obtenido: {r.status_code}")
            print(f"       Respuesta: {r.text}")
    else:
        print(f"[FAIL] Crear película sin votos - Esperado: 201, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 106. Obtener el historial de ventas en un año dado para los clientes pertenecientes a un país específico
    r = requests.get(
        f"{API_URL}/api/ventas/2026/España"
    )
    if r.status_code == 200:
        print("[OK] Obtener el historial de ventas en un año dado para los clientes pertenecientes a un país específico (HTTP 200)")
    else:
        print(f"[FAIL] Obtener el historial de ventas en un año dado para los clientes pertenecientes a un país específico - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 107. Obtener el historial de ventas en un año dado para los clientes pertenecientes a un país específico sin ventas
    r = requests.get(
        f"{API_URL}/api/ventas/2019/España"
    )
    if r.status_code == 200:
        print("[OK] Obtener el historial de ventas en un año dado para los clientes pertenecientes a un país específico sin ventas (HTTP 200)")
    else:
        print(f"[FAIL] Obtener el historial de ventas en un año dado para los clientes pertenecientes a un país específico sin ventas - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 108. Eliminar una película
    r = requests.delete(
        f"{API_URL}/api/peliculas/{pelicula_id}"
    )
    if r.status_code == 200:
        print("[OK] Eliminar una película (HTTP 200)")
    else:
        print(f"[FAIL] Eliminar una película - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 109. Eliminar una película que no existe
    r = requests.delete(
        f"{API_URL}/api/peliculas/999"
    )
    if r.status_code == 404:
        print("[OK] Eliminar una película que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Eliminar una película que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 110. Eliminar un director
    r = requests.delete(
        f"{API_URL}/api/directores/{director_id}"
    )
    if r.status_code == 200:
        print("[OK] Eliminar un director (HTTP 200)")
    else:
        print(f"[FAIL] Eliminar un director - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 111. Eliminar un director que no existe
    r = requests.delete(
        f"{API_URL}/api/directores/999"
    )
    if r.status_code == 404:
        print("[OK] Eliminar un director que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Eliminar un director que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 112. Eliminar un actor
    r = requests.delete(
        f"{API_URL}/api/actores/{actor_id}"
    )
    if r.status_code == 200:
        print("[OK] Eliminar un actor (HTTP 200)")
    else:
        print(f"[FAIL] Eliminar un actor - Esperado: 200, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

    # 113. Eliminar un actor que no existe
    r = requests.delete(
        f"{API_URL}/api/actores/999"
    )
    if r.status_code == 404:
        print("[OK] Eliminar un actor que no existe (HTTP 404)")
    else:
        print(f"[FAIL] Eliminar un actor que no existe - Esperado: 404, Obtenido: {r.status_code}")
        print(f"       Respuesta: {r.text}")

if __name__ == "__main__":
    run_tests()