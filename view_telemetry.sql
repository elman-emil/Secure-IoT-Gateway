SELECT v.vehicle_name, v.model, t.battery_soc, t.motor_temp_c, t.speed_kmh, t.recorded_at
FROM telemetry t
JOIN vehicles v ON t.vehicle_id = v.vehicle_id
ORDER BY t.recorded_at;