-- View 1: Média de temperatura por dispositivo
CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT 
    device_id, 
    ROUND(AVG(temperature), 2) AS avg_temp
FROM temperature_readings
GROUP BY device_id;

-- View 2: Contagem de leituras por hora do dia (0 a 23h)
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT 
    EXTRACT(HOUR FROM noted_date)::INT AS hora,
    COUNT(*) AS contagem
FROM temperature_readings
GROUP BY hora
ORDER BY hora;

-- View 3: Temperaturas máximas e mínimas por dia
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT 
    DATE(noted_date) AS data,
    MAX(temperature) AS temp_max,
    MIN(temperature) AS temp_min
FROM temperature_readings
GROUP BY DATE(noted_date)
ORDER BY data;
