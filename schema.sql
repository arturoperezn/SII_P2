-- Tabla usuarios
CREATE TABLE USUARIOS (
    uid VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    saldo NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (saldo >= 0)
);

-- Tabla peliculas
CREATE TABLE PELICULAS (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    anio INT NOT NULL,
    genero VARCHAR(100),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0)
);

-- Actores, directores y relacion con pelicula Tabla
CREATE TABLE ACTORES (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);
CREATE TABLE DIRECTORES (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);
CREATE TABLE PELICULA_ACTORES (
    pelicula_id INT REFERENCES PELICULAS(id) ON DELETE CASCADE,
    actor_id INT REFERENCES ACTORES(id) ON DELETE CASCADE,
    PRIMARY KEY (pelicula_id, actor_id)
);
CREATE TABLE PELICULA_DIRECTORES (
    pelicula_id INT REFERENCES PELICULAS(id) ON DELETE CASCADE,
    director_id INT REFERENCES DIRECTORES(id) ON DELETE CASCADE,
    PRIMARY KEY (pelicula_id, director_id)
);

-- Tabla pedidos (compra/carrito)
CREATE TABLE PEDIDOS (
    id SERIAL PRIMARY KEY,
    usuario_uid VARCHAR(64) REFERENCES USUARIOS(uid) ON DELETE CASCADE,
    estado VARCHAR(10) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'pagado', 'cancelado')),
    -- activo es estado carrito (sin pagar aun)
    importe NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (importe >= 0), 
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_pago TIMESTAMP NULL
);
CREATE TABLE PEDIDO_ITEMS (
    id SERIAL PRIMARY KEY,
    pedido_id INT REFERENCES PEDIDOS(id) ON DELETE CASCADE,
    pelicula_id INT REFERENCES PELICULAS(id) ON DELETE RESTRICT,
    cantidad INT NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL CHECK (precio_unitario >= 0),
    UNIQUE(pedido_id, pelicula_id)
);

-- Tabla valoraciones
CREATE TABLE VALORACIONES (
    id SERIAL PRIMARY KEY,
    pelicula_id INT REFERENCES PELICULAS(id) ON DELETE CASCADE,
    usuario_uid VARCHAR(64) REFERENCES USUARIOS(uid) ON DELETE CASCADE,
    calificacion INT NOT NULL CHECK (calificacion >= 0 AND calificacion <= 10),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_uid, pelicula_id)
);

-- DEFINICION DE TRIGGERS

-- Pago del carrito
CREATE OR REPLACE FUNCTION pagar_carrito()
RETURNS TRIGGER AS $$
DECLARE
    v_saldo NUMERIC(10, 2);
    v_num_items INT;
BEGIN
    IF NEW.estado ='pagado' AND OLD.estado != 'pagado' THEN
        SELECT COUNT(*) INTO v_num_items FROM pedido_items WHERE pedido_id = NEW.id;
        IF v_num_items = 0 THEN
            RAISE EXCEPTION 'No se puede pagar un carrito vacio';
        END IF;

        SELECT saldo INTO v_saldo
        FROM USUARIOS 
        WHERE uid = NEW.usuario_uid 
        FOR UPDATE;

        IF v_saldo < NEW.importe THEN
            RAISE EXCEPTION 'Saldo insuficiente. Saldo: %, Importe total a pagar: %', 
                v_saldo, NEW.importe;
        END IF;
        
        UPDATE USUARIOS
        SET saldo = saldo - NEW.importe
        WHERE uid = NEW.usuario_uid;

        NEW.fecha_pago := CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tgr_pagar_carrito
BEFORE UPDATE OF estado ON PEDIDOS
FOR EACH ROW
EXECUTE FUNCTION pagar_carrito();

-- Gestionar stock y carrito 
CREATE OR REPLACE FUNCTION actualizar_carrito_stock()
RETURNS TRIGGER AS $$
DECLARE
    v_estado VARCHAR(10);
    v_stock INT;
    v_dif INT;
BEGIN
    SELECT estado INTO v_estado FROM PEDIDOS WHERE id = COALESCE(NEW.pedido_id, OLD.pedido_id);
    IF v_estado != 'activo' THEN
        RAISE EXCEPTION 'No se pueden modificar items de un pedido ya pagado o cancelado';
    END IF;

    IF TG_OP = 'INSERT' THEN
        SELECT stock INTO v_stock FROM PELICULAS WHERE id = NEW.pelicula_id FOR UPDATE;
        IF v_stock < NEW.cantidad THEN
            RAISE EXCEPTION 'No hay suficiente stock para la pelicula %. Stock disponible: %, Cantidad pedida: %',
                NEW.pelicula_id, v_stock, NEW.cantidad;
        END IF;
        UPDATE PELICULAS SET stock = stock - NEW.cantidad WHERE id = NEW.pelicula_id;
        UPDATE PEDIDOS 
        SET importe = (SELECT COALESCE(SUM(cantidad * precio_unitario), 0.0) FROM PEDIDO_ITEMS WHERE pedido_id = NEW.pedido_id)
        WHERE id = NEW.pedido_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_dif = NEW.cantidad - OLD.cantidad;
        -- Solo comprobamos stock si se piden mas unidades
        IF v_dif > 0 THEN
            SELECT stock INTO v_stock FROM PELICULAS WHERE id = NEW.pelicula_id FOR UPDATE;
            IF v_stock < v_dif THEN
                RAISE EXCEPTION 'No hay suficiente stock para la pelicula %. Stock disponible: %, Cantidad pedida: %',
                    NEW.pelicula_id, v_stock, v_dif;
            END IF;
        END IF;
        UPDATE PELICULAS SET stock = stock - v_dif WHERE id = NEW.pelicula_id;
        UPDATE PEDIDOS 
        SET importe = (SELECT COALESCE(SUM(cantidad * precio_unitario), 0.0) FROM PEDIDO_ITEMS WHERE pedido_id = NEW.pedido_id)
        WHERE id = NEW.pedido_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE PELICULAS SET stock = stock + OLD.cantidad WHERE id = OLD.pelicula_id;
        UPDATE PEDIDOS 
        SET importe = (SELECT COALESCE(SUM(cantidad * precio_unitario), 0.0) FROM PEDIDO_ITEMS WHERE pedido_id = OLD.pedido_id)
        WHERE id = OLD.pedido_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tgr_actualizar_carrito_stock
AFTER UPDATE OR INSERT OR DELETE ON PEDIDO_ITEMS
FOR EACH ROW
EXECUTE FUNCTION actualizar_carrito_stock();

-- Cancelar pedido, reponer stock
CREATE OR REPLACE FUNCTION reponer_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.estado = 'cancelado' AND OLD.estado != 'cancelado' THEN  
        UPDATE PELICULAS pelicula
        SET stock = pelicula.stock + item.cantidad FROM PEDIDO_ITEMS item
        WHERE item.pelicula_id = pelicula.id AND item.pedido_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tgr_reponer_stock
BEFORE UPDATE OF estado ON PEDIDOS
FOR EACH ROW
EXECUTE FUNCTION reponer_stock();

-- DEFINICION DE PROCEDIMIENTOS ALMACENADOS

-- Calcular la valoracion media de una pelicula
CREATE OR REPLACE FUNCTION valoracion_media(p_pelicula_id INT)
RETURNS NUMERIC AS $$
DECLARE
    v_media NUMERIC(4, 2);
BEGIN
    SELECT COALESCE(AVG(calificacion), 0.00) INTO v_media
    FROM VALORACIONES
    WHERE pelicula_id = p_pelicula_id;
    RETURN v_media;
END;
$$ LANGUAGE plpgsql;

-- Agregar pelicula al carrito
CREATE OR REPLACE FUNCTION agregar_carrito(p_usuario_uid VARCHAR(64), p_pelicula_id INT, p_cantidad INT)
RETURNS INT AS $$
DECLARE
    v_pedido_id INT;
    v_precio NUMERIC(10, 2);
BEGIN
    -- Obtener carrito o crear carrito
    SELECT id INTO v_pedido_id FROM PEDIDOS WHERE usuario_uid = p_usuario_uid AND estado = 'activo' LIMIT 1;
    IF v_pedido_id IS NULL THEN
        INSERT INTO PEDIDOS(usuario_uid, estado, importe)
        VALUES(p_usuario_uid, 'activo', 0.0)
        RETURNING id INTO v_pedido_id;
    END IF;

    -- Obtener precio unitario para insertar en PEDIDO_ITEMS
    SELECT precio INTO v_precio FROM PELICULAS WHERE id = p_pelicula_id;
    IF v_precio IS NULL THEN
        RAISE EXCEPTION 'La pelicula con id % no existe', p_pelicula_id;
    END IF;

    -- Agregar al carrito
    INSERT INTO PEDIDO_ITEMS(pedido_id, pelicula_id, cantidad, precio_unitario)
    VALUES (v_pedido_id, p_pelicula_id, p_cantidad, v_precio)
    ON CONFLICT(pedido_id, pelicula_id)
    DO UPDATE SET cantidad = PEDIDO_ITEMS.cantidad + EXCLUDED.cantidad;

    RETURN v_pedido_id;
END;
$$ LANGUAGE plpgsql;

-- Pagar carrito de un usuario
CREATE OR REPLACE FUNCTION pagar_carrito_usuario(p_usuario_uid VARCHAR(64))
RETURNS INT AS $$
DECLARE
    v_pedido_id INT;
BEGIN
    -- Obtener carrito
    SELECT id INTO v_pedido_id FROM PEDIDOS WHERE usuario_uid = p_usuario_uid AND estado = 'activo'
    FOR UPDATE;
    IF v_pedido_id IS NULL THEN
        RAISE EXCEPTION 'EL usuario no tiene carrito activo para pagar'
    END IF;

    UPDATE PEDIDOS SET estado = 'pagado' WHERE id = v_pedido_id;

    return v_pedido_id;
END;
$$ LANGUAGE plpgsql;

-- Votar pelicula
CREATE OR REPLACE FUNCTION votar_pelicula(p_usuario_uid VARCHAR(64), p_pelicula_id INT, p_calificacion INT)
RETURNS VOID AS $$
BEGIN
    IF p_calificacion < 0 OR p_calificacion > 10 THEN
        RAISE EXCEPTION 'La valoracion de la pelicula debe estar entre 0 y 10'
    END IF;
    IF NOT EXISTS (SELECT 1 FROM PELICULAS WHERE id = p_pelicula_id) THEN
        RAISE EXCEPTION 'La pelicula con id % no existe', p_pelicula_id;
    END IF;
    INSERT INTO VALORACIONES(pelicula_id, usuario_uid, calificacion, fecha_creacion)
    VALUES (p_pelicula_id, p_usuario_uid, p_calificacion, CURRENT_TIMESTAMP)
    ON CONFLICT(usuario_uid, pelicula_id)
    DO UPDATE SET
        calificacion = EXCLUDED.calificacion,
        fecha_creacion = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Obtener ventas por anio y pais
CREATE OR REPLACE FUNCTION obtener_ventas_anio_pais(p_anio INT, p_pais VARCHAR(100)) 
RETURNS TABLE (
    pedido_id INT,
    usuario_uid VARCHAR(64),
    username VARCHAR(100),
    importe NUMERIC(10, 2),
    fecha_pago TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pedido.id AS pedido_id,
        usuario.uid AS usuario_uid,
        usuario.username,
        pedido.importe,
        pedio.fecha_pago
    FROM PEDIDOS pedido
    JOIN USUARIOS usuario ON pedido.usuario_uid = usuario.usuario_uid 
    WHERE pedido.estado = 'pagado' AND EXTRACT(YEAR FROM pedido.fecha_pago) = p_anio AND usuario.pais = p_pais;
END;
$$ LANGUAGE plpgsql;
