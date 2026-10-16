-- Reproduce localmente los permisos de la base de Bluecore:
-- usuario_a no es administrador y solo puede crear objetos en esquema_a.
CREATE ROLE usuario_a WITH LOGIN PASSWORD 'usuario_a';

CREATE SCHEMA esquema_a AUTHORIZATION usuario_a;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE demo TO usuario_a;
