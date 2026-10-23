# PRÁCTICA 2: README

# Nota: Todos los comandos deben ejecutarse en el directorio raíz del proyecto. 

# EJECUCIÓN CON DOCKER COMPOSE
# Para construir imagen y levantar ambos microservicios en los laboratorios en modo rootless:
sudo /usr/local/bin/si2setuid.sh 3000000:100000 $USER
dockerd-rootless-setuptool.sh install --skip-iptables
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
docker compose up --build
# Para detener servicios:
docker compose down

# EJECUTAR EL CLIENTE DE PRUEBA
python3 cliente.py

# EJECUTAR LA OPTIMIZACIÓN Y GUARDAR LOS DATOS EN UN FICHERO
docker compose exec -T db psql -U alumnodb -d si1 -f - < optimizacion.sql > resultado_optimizacion.txt 2>&1
Al crear la base de datos desde cero hay que ejecutar también optimizacion.sql, porque Docker solo carga inicialmente schema.sql y populate.sql.
