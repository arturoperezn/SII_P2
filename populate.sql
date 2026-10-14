-- Los datos de las tablas de usuarios, peliculas, actores, directores, etc... 
-- (no el codigo de inserciones) han sido generados con IA
-- Limpieza de datos
TRUNCATE TABLE VALORACIONES, PEDIDO_ITEMS, PEDIDOS, PELICULA_ACTORES, PELICULA_DIRECTORES, ACTORES, DIRECTORES, PELICULAS, USUARIOS CASCADE;

INSERT INTO USUARIOS (username, password_hash, pais, saldo) VALUES
('juan_perez', '$2b$12$e8N4y.e1gM5I9Z8QyO1gJeZ9Y3gG2K1P0Q9W8E7R6T5Y4U3I2O1P', 'España', 150.00),
('marie_curie', '$2b$12$K8xN8u1Z2Y3X4W5V6U7T8e9R0Q1P2O3N4M5L6K7J8I9H0G1F2E3D4', 'Francia', 80.50),
('john_doe', '$2b$12$P1O2N3M4L5K6J7I8H9G0F1E2D3C4B5A678901234567890123456', 'Estados Unidos', 200.00),
('pierre_dupont', '$2b$12$K8xN8u1Z2Y3X4W5V6U7T8e9R0Q1P2O3N4M5L6K7J8I9H0G1F2E3D4', 'Francia', 50.00),
('ana_garcia', '$2b$12$e8N4y.e1gM5I9Z8QyO1gJeZ9Y3gG2K1P0Q9W8E7R6T5Y4U3I2O1P', 'España', 0.00);

INSERT INTO PELICULAS (id, titulo, anio, genero, precio, stock) VALUES
(1, 'Inception', 2010, 'Ciencia Ficcion', 12.99, 20),
(2, 'The Dark Knight', 2008, 'Accion', 14.50, 15),
(3, 'Interstellar', 2014, 'Ciencia Ficcion', 15.00, 10),
(4, 'Amelie', 2001, 'Comedia Romantica', 9.99, 8),
(5, 'Pulp Fiction', 1994, 'Crimen', 11.00, 25),
(6, 'The Matrix', 1999, 'Ciencia Ficcion', 10.50, 30);
SELECT setval('peliculas_id_seq', (SELECT MAX(id) FROM PELICULAS));

INSERT INTO DIRECTORES (id, nombre) VALUES
(1, 'Christopher Nolan'),
(2, 'Jean-Pierre Jeunet'),
(3, 'Quentin Tarantino'),
(4, 'Lana Wachowski'),
(5, 'Lilly Wachowski');
SELECT setval('directores_id_seq', (SELECT MAX(id) FROM DIRECTORES));

INSERT INTO ACTORES (id, nombre) VALUES
(1, 'Leonardo DiCaprio'),
(2, 'Christian Bale'),
(3, 'Audrey Tautou'),
(4, 'John Travolta'),
(5, 'Keanu Reeves'),
(6, 'Anne Hathaway');
SELECT setval('actores_id_seq', (SELECT MAX(id) FROM ACTORES));

INSERT INTO PELICULA_DIRECTORES (pelicula_id, director_id) VALUES
(1, 1), 
(2, 1), 
(3, 1), 
(4, 2), 
(5, 3), 
(6, 4),
(6, 5);

-- Poblamos los pedidos
INSERT INTO PEDIDOS (id, usuario_uid, estado, importe, fecha_creacion) VALUES
(1, (SELECT uid FROM USUARIOS WHERE username = 'marie_curie'), 'activo', 0.00, '2026-02-10 14:30:00');
INSERT INTO PEDIDO_ITEMS (pedido_id, pelicula_id, cantidad, precio_unitario) VALUES (1, 1, 1, 12.99), (1, 3, 1, 15.00);
UPDATE PEDIDOS 
SET estado = 'pagado', fecha_pago = '2026-02-10 14:35:00' 
WHERE id = 1;

INSERT INTO PEDIDOS (id, usuario_uid, estado, importe, fecha_creacion) VALUES
(2, (SELECT uid FROM USUARIOS WHERE username = 'pierre_dupont'), 'activo', 0.00, '2026-03-01 10:00:00');
INSERT INTO PEDIDO_ITEMS (pedido_id, pelicula_id, cantidad, precio_unitario) VALUES (2, 4, 1, 9.99);
UPDATE PEDIDOS 
SET estado = 'pagado', fecha_pago = '2026-03-01 10:05:00' 
WHERE id = 2;

INSERT INTO PEDIDOS (id, usuario_uid, estado, importe, fecha_creacion) VALUES
(3, (SELECT uid FROM USUARIOS WHERE username = 'juan_perez'), 'activo', 0.00, '2026-01-15 18:20:00');
INSERT INTO PEDIDO_ITEMS (pedido_id, pelicula_id, cantidad, precio_unitario) VALUES (3, 2, 2, 14.50);
UPDATE PEDIDOS 
SET estado = 'pagado', fecha_pago = '2026-01-15 18:22:00' 
WHERE id = 3;

INSERT INTO PEDIDOS (id, usuario_uid, estado, importe, fecha_creacion) VALUES
(4, (SELECT uid FROM USUARIOS WHERE username = 'juan_perez'), 'activo', 0.00, CURRENT_TIMESTAMP);
INSERT INTO PEDIDO_ITEMS (pedido_id, pelicula_id, cantidad, precio_unitario) VALUES (4, 6, 1, 10.50); 

SELECT setval('pedidos_id_seq', (SELECT MAX(id) FROM PEDIDOS));
SELECT setval('pedido_items_id_seq', (SELECT MAX(id) FROM PEDIDO_ITEMS));

-- Poblamos las valoraciones
INSERT INTO VALORACIONES (pelicula_id, usuario_uid, calificacion) VALUES
(1, (SELECT uid FROM USUARIOS WHERE username = 'juan_perez'), 9),
(1, (SELECT uid FROM USUARIOS WHERE username = 'marie_curie'), 10),
(1, (SELECT uid FROM USUARIOS WHERE username = 'john_doe'), 8),
(2, (SELECT uid FROM USUARIOS WHERE username = 'juan_perez'), 10),
(2, (SELECT uid FROM USUARIOS WHERE username = 'john_doe'), 9),
(3, (SELECT uid FROM USUARIOS WHERE username = 'marie_curie'), 9),
(4, (SELECT uid FROM USUARIOS WHERE username = 'marie_curie'), 10),
(4, (SELECT uid FROM USUARIOS WHERE username = 'pierre_dupont'), 7);
SELECT setval('valoraciones_id_seq', (SELECT MAX(id) FROM VALORACIONES));