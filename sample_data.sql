INSERT INTO vehicles (vehicle_name, model, battery_capacity_kwh)
VALUES ('Test Vehicle 1', 'Powertrain Prototype A', 75.0);

INSERT INTO telemetry (vehicle_id, battery_soc, motor_temp_c, speed_kmh)
VALUES
  (1, 80.5, 35.2, 42.0),
  (1, 79.8, 36.0, 44.5),
  (1, 79.1, 36.8, 41.0);