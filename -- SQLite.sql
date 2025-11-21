-- SQLite
--INSERT INTO usuarios_modo_operador 
    --(complet_name, codigo_institucional, contacto, estado) 
--VALUES 
    --('Gustavo Adrián Cerati', '240457390383527892', 'ceratistereo.dynamo65@gmail.com', 'PENDIENTE');

INSERT INTO usuarios_modo_general
    (complet_name, contacto, estado) 
VALUES 
    ('Manuel López Chicoya', 'chicoLop.prueba.77@gmail.com', 'PENDIENTE');

    DELETE FROM usuarios_modo_general WHERE contacto = 'mauricioalejandro.sets64@gmail.com';