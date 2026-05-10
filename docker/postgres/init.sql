-- criação de schemas
-- opcional: garantir permissões



CREATE SCHEMA IF NOT EXISTS deputados_raw;
grant all privileges on schema deputados_raw to postgres;
CREATE SCHEMA IF NOT EXISTS deputados_trusted;
grant all privileges on schema deputados_trusted to postgres;
CREATE SCHEMA IF NOT EXISTS deputados_analytics;
grant all privileges on schema deputados_analytics to postgres;