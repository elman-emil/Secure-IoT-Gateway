CREATE TABLE vehicles (
    vehicle_id            SERIAL PRIMARY KEY,
    vehicle_name          VARCHAR(100) NOT NULL,
    model                 VARCHAR(100),
    battery_capacity_kwh  NUMERIC,
    status                VARCHAR(20)  NOT NULL DEFAULT 'active',
    registered_at         TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE telemetry (
    telemetry_id   SERIAL PRIMARY KEY,
    vehicle_id     INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
    battery_soc    NUMERIC,
    motor_temp_c   NUMERIC,
    speed_kmh      NUMERIC,
    recorded_at    TIMESTAMP NOT NULL DEFAULT NOW()
);