--Estos datos iniciales los hemos generado con ayuda de chatgpt:
-- Creamos 10 000 usuarios y 30 000 pedidos de prueba entre 2024 y 2026.
-- Son datos para medir consultas: los pedidos no tienen articulos ni cobran saldo.
-- Las contrasenas son ficticias. Conservamos los datos originales del populate.
-- Si repetimos el script, no se duplican estos usuarios y pedidos.

BEGIN;

INSERT INTO public.usuarios (uid, username, password_hash, pais, saldo)
SELECT
    md5('sii_p2_opt_usuario_' || g)::uuid::varchar,
    'user_opt_' || g,
    'solo_para_pruebas_de_consulta',
    (ARRAY['España', 'Francia', 'Estados Unidos', 'Alemania', 'Italia'])
        [1 + ((g - 1) % 5)],
    100.00
FROM generate_series(1, 10000) AS datos(g)
ON CONFLICT (uid) DO NOTHING;

-- Añadimos tres pedidos por usuario de prueba, uno por año.
INSERT INTO public.pedidos
    (usuario_uid, estado, importe, fecha_creacion, fecha_pago)
SELECT
    u.uid,
    'pagado',
    (5 + (datos.g % 50))::numeric(10, 2),
    fechas.creacion,
    fechas.creacion + INTERVAL '1 hour'
FROM generate_series(1, 10000) AS datos(g)
JOIN public.usuarios u
    ON u.uid = md5('sii_p2_opt_usuario_' || datos.g)::uuid::varchar
CROSS JOIN generate_series(2024, 2026) AS anios(anio)
CROSS JOIN LATERAL (
    SELECT make_date(anios.anio, 1, 1)
        + (datos.g % 270) * INTERVAL '1 day' AS creacion
) AS fechas
WHERE NOT EXISTS (
    SELECT 1
    FROM public.pedidos p
    WHERE p.usuario_uid = u.uid
        AND p.fecha_creacion = fechas.creacion
);

-- Quitamos nuestros indices para empezar la comparacion sin ellos.
DROP INDEX IF EXISTS public.idx_usuarios_pais;
DROP INDEX IF EXISTS public.idx_pedidos_pagados_usuario_fecha;

ANALYZE public.usuarios;
ANALYZE public.pedidos;

-- Borramos las consultas preparadas de esta sesion.
DEALLOCATE ALL;

-- Probamos la consulta original. 
PREPARE opt_original AS
SELECT
    pedido.id,
    usuario.uid,
    usuario.username,
    pedido.importe,
    pedido.fecha_pago
FROM public.pedidos pedido
JOIN public.usuarios usuario ON pedido.usuario_uid = usuario.uid
WHERE pedido.estado = 'pagado'
    AND EXTRACT(YEAR FROM pedido.fecha_pago) = 2026
    AND usuario.pais = 'Francia';

EXPLAIN (ANALYZE, BUFFERS) EXECUTE opt_original;


-- Cambiamos EXTRACT por un intervalo de fechas.
PREPARE opt_intervalo AS
SELECT
    pedido.id,
    usuario.uid,
    usuario.username,
    pedido.importe,
    pedido.fecha_pago
FROM public.pedidos pedido
JOIN public.usuarios usuario ON pedido.usuario_uid = usuario.uid
WHERE pedido.estado = 'pagado'
    AND pedido.fecha_pago >= TIMESTAMP '2026-01-01'
    AND pedido.fecha_pago < TIMESTAMP '2027-01-01'
    AND usuario.pais = 'Francia';

EXPLAIN (ANALYZE, BUFFERS) EXECUTE opt_intervalo;


-- Creamos los indices y repetimos la consulta con intervalo.
CREATE INDEX idx_usuarios_pais ON public.usuarios (pais);
CREATE INDEX idx_pedidos_pagados_usuario_fecha
ON public.pedidos (usuario_uid, fecha_pago)
WHERE estado = 'pagado';

ANALYZE public.usuarios;
ANALYZE public.pedidos;

EXPLAIN (ANALYZE, BUFFERS) EXECUTE opt_intervalo;


-- Actualizamos la funcion de ventas con el filtro por intervalo.
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
        pedido.fecha_pago
    FROM PEDIDOS pedido
    JOIN USUARIOS usuario ON pedido.usuario_uid = usuario.uid
    WHERE pedido.estado = 'pagado'
        AND pedido.fecha_pago >= make_date(p_anio, 1, 1)
        AND pedido.fecha_pago < make_date(p_anio + 1, 1, 1)
        AND usuario.pais = p_pais;
END;
$$ LANGUAGE plpgsql;


DEALLOCATE opt_original;
DEALLOCATE opt_intervalo;
COMMIT;
