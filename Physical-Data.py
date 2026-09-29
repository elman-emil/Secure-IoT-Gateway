"""
EV / BMS Simulator
------------------
Simulates 15 electric vehicles and publishes
their telemetry data to MQTT.

Features:
- 15 EVs
- BMS simulation
- State of Charge (SOC)
- Battery Health
- Voltage & Current
- Battery Temperature
- GPS Tracking
- Driving / Parked / Charging states
- Regenerative Braking
- Charging Curves
- Estimated Range
- Battery Status
- Temperature Alerts
- Vehicle Status

MQTT Topics:
vehicle/EV001/telemetry
vehicle/EV002/telemetry
...
vehicle/EV015/telemetry
"""

import json
import time
import random
from datetime import datetime

import paho.mqtt.client as mqtt

# --------------------------------------------------
# MQTT SETTINGS
# --------------------------------------------------

#  MQTT_BROKER = "localhost"; Public MQTT broker for testing
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# --------------------------------------------------
# CREATE 15 SIMULATED VEHICLES
# --------------------------------------------------

vehicles = {}
for i in range(1, 16):
    vehicle_id = f"EV{i:03d}"
    vehicles[vehicle_id] = {

        "soc": random.uniform(60, 100),                 # Battery State Of Charge (%)
        "voltage": random.uniform(350, 420),            # Battery Voltage (V)
        "current": random.uniform(5, 40),               # Battery Current (A)
        "battery_temp": random.uniform(25, 35),         # Battery Temperature (°C)
        "speed": random.randint(0, 90),                 # Vehicle Speed (km/h)
        "previous_speed": 0,                            # Used for regenerative braking calculations
        "odometer": random.randint(1000, 50000),        # Total distance traveled

        # Starting position (Lahti area)
        "latitude": 60.9827,
        "longitude": 25.6615,

        "charging": False,                              # Vehicle currently charging
        "battery_health": random.randint(90, 100),      # Battery health (%)

        # Vehicle operating state
        "state": random.choice([
            "parked",
            "driving"
        ])
    }
# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

while True:
    for vehicle_id, vehicle in vehicles.items():
        # ==========================================
        # VEHICLE STATE MACHINE
        # ==========================================
        vehicle["previous_speed"] = vehicle["speed"]

        # Force charging if battery is low
        if vehicle["soc"] <= 20:
            vehicle["state"] = "charging"

        # --------------------------
        # Driving State
        # --------------------------
        if vehicle["state"] == "driving":
            vehicle["speed"] = random.randint(20, 120)
            # Chance of parking
            if random.random() < 0.05:
                vehicle["state"] = "parked"

        # --------------------------
        # Parked State
        # --------------------------

        elif vehicle["state"] == "parked":
            vehicle["speed"] = 0
            # Chance of starting trip
            if random.random() < 0.10:
                vehicle["state"] = "driving"
        # --------------------------
        # Charging State
        # --------------------------

        elif vehicle["state"] == "charging":
            vehicle["speed"] = 0

        # ==========================================
        # ODOMETER UPDATE
        # ==========================================

        vehicle["odometer"] += vehicle["speed"] * 0.001

        # ==========================================
        # GPS MOVEMENT
        # ==========================================

        if vehicle["state"] == "driving":
            vehicle["latitude"] += random.uniform(
                -0.0002,
                0.0002
            )

            vehicle["longitude"] += random.uniform(
                -0.0002,
                0.0002
            )
        # ==========================================
        # BATTERY CONSUMPTION
        # ==========================================

        if vehicle["state"] == "driving":
            power_usage = vehicle["speed"] * 0.002          # Faster speed = faster battery drain
            vehicle["soc"] -= power_usage
        elif vehicle["state"] == "parked":
            vehicle["soc"] -= 0.01                          # Small idle battery usage

        # ==========================================
        # REGENERATIVE BRAKING
        # ==========================================

        if vehicle["speed"] < vehicle["previous_speed"]:
            vehicle["soc"] += random.uniform(
                0.01,
                0.03
            )

        # ==========================================
        # CHARGING LOGIC
        # ==========================================

        if vehicle["state"] == "charging":
            vehicle["charging"] = True
            # Fast charging under 80%
            if vehicle["soc"] < 80:
                vehicle["soc"] += 1.2

            # Slow charging above 80%
            else:
                vehicle["soc"] += 0.4

            # Stop charging at 95%
            if vehicle["soc"] >= 95:
                vehicle["soc"] = 95
                vehicle["charging"] = False
                vehicle["state"] = "parked"
        else:
            vehicle["charging"] = False
        # Keep SOC valid
        vehicle["soc"] = max(
            0,
            min(100, vehicle["soc"])
        )

        # ==========================================
        # VOLTAGE SIMULATION
        # SOC affects voltage
        # ==========================================

        vehicle["voltage"] = round(
            350 + (vehicle["soc"] / 100) * 70,
            2
        )

        # ==========================================
        # CURRENT SIMULATION
        # ==========================================

        if vehicle["charging"]:
            vehicle["current"] = round(
                random.uniform(30, 60),
                2
            )
        elif vehicle["state"] == "driving":
            vehicle["current"] = round(
                random.uniform(15, 45),
                2
            )
        else:
            vehicle["current"] = round(
                random.uniform(1, 10),
                2
            )
        # ==========================================
        # TEMPERATURE SIMULATION
        # ==========================================
        if vehicle["state"] == "driving":
            vehicle["battery_temp"] += random.uniform(
                0,
                0.5
            )
        elif vehicle["state"] == "charging":
            vehicle["battery_temp"] += random.uniform(
                0,
                0.3
            )
        else:
            vehicle["battery_temp"] += random.uniform(
                -0.2,
                0.2
            )
        vehicle["battery_temp"] = round(
            max(20, min(55, vehicle["battery_temp"])),
            2
        )
        # ==========================================
        # DRIVING MODE
        # ==========================================
        if vehicle["speed"] < 20:
            driving_mode = "City"
        elif vehicle["speed"] < 80:
            driving_mode = "Normal"
        else:
            driving_mode = "Highway"
        # ==========================================
        # BATTERY STATUS
        # ==========================================
        if vehicle["soc"] > 80:
            battery_status = "Excellent"
        elif vehicle["soc"] > 50:
            battery_status = "Good"
        elif vehicle["soc"] > 20:
            battery_status = "Low"
        else:
            battery_status = "Critical"
        # ==========================================
        # ESTIMATED RANGE
        # 100% SOC ≈ 400 km
        # ==========================================
        estimated_range = (
            vehicle["soc"] * 4
        ) * (
            vehicle["battery_health"] / 100
        )
        estimated_range = round(
            estimated_range,
            0
        )
        # ==========================================
        # TEMPERATURE ALERTS
        # ==========================================

        if vehicle["battery_temp"] > 45:
            temperature_alert = "OVERHEAT"
        elif vehicle["battery_temp"] < 5:
            temperature_alert = "LOW_TEMP"
        else:
            temperature_alert = "NORMAL"

        # ==========================================
        # VEHICLE STATUS
        # ==========================================

        if vehicle["soc"] < 10:
            vehicle_status = "Needs Charging"
        elif vehicle["battery_temp"] > 45:
            vehicle_status = "Temperature Warning"
        elif vehicle["charging"]:
            vehicle_status = "Charging"
        elif vehicle["state"] == "parked":
            vehicle_status = "Parked"
        else:
            vehicle_status = "Operational"

        # ==========================================
        # PAYLOAD
        # ==========================================
        payload = {
            # General Information
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now().isoformat(),

            # Vehicle Information
            "vehicle_state": vehicle["state"],
            "vehicle_status": vehicle_status,

            # Driving Information
            "speed_kmh": vehicle["speed"],
            "driving_mode": driving_mode,
            "odometer_km": round(
                vehicle["odometer"],
                2
            ),

            # Battery Information
            "soc_percent": round(
                vehicle["soc"],
                2
            ),
            "battery_status": battery_status,
            "battery_health_percent": vehicle["battery_health"],
            "estimated_range_km": estimated_range,

            # Electrical Information
            "voltage_v": vehicle["voltage"],
            "current_a": vehicle["current"],

            # Temperature Information
            "battery_temp_c": vehicle["battery_temp"],
            "temperature_alert": temperature_alert,

            # Charging Information
            "charging": vehicle["charging"],

            # GPS Information
            "latitude": round(
                vehicle["latitude"],
                6
            ),
            "longitude": round(
                vehicle["longitude"],
                6
            )
        }

        # ==========================================
        # MQTT TOPIC
        # ==========================================

        topic = f"vehicle/{vehicle_id}/telemetry"

        # Publish telemetry
        client.publish(
            topic,
            json.dumps(payload)
        )

        # Print summary
        print(
            f"[{vehicle_id}] "
            f"State={vehicle['state']} | "
            f"Speed={vehicle['speed']} km/h | "
            f"SOC={round(vehicle['soc'],2)}% | "
            f"Range={estimated_range} km | "
            f"Status={vehicle_status}"
        )

    print("-" * 100)

    # Update every 2 seconds
    time.sleep(2)