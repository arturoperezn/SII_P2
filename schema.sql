-- User Tabla
CREATE TABLE usuarios (
    uid VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    saldo NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (saldo >= 0)
);

-- Peliculas Tabla
CREATE TABLE peliculas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    anio INT NOT NULL,
    genero VARCHAR(100),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
);

-- Actores, directores y relacion con pelicula Tabla
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