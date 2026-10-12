-- Tabela principal para armazenamento das leituras dos sensores IoT
CREATE TABLE IF NOT EXISTS temperature_readings (
    id VARCHAR(100) PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    out_in VARCHAR(10) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    temperature NUMERIC(5, 2) NOT NULL,
    noted_date TIMESTAMP NOT NULL
);

-- Índices para otimização de consultas e agregação das views
CREATE INDEX IF NOT EXISTS idx_temp_readings_device ON temperature_readings(device_id);
CREATE INDEX IF NOT EXISTS idx_temp_readings_date ON temperature_readings(noted_date);
