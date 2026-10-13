# Secure-IoT-Gateway

Team members:
- Elman Emil- Scrum master
- Praful Sharma
- Waltteri Jokinen
- Aliyyu Zen-Abdeen
- Camelia Zameni

# M2M IoT Gateway & Identity Provider Architecture

This repository contains the current work-in-progress framework architecture and configuration for securing Machine-to-Machine (M2M) communications in a Digital Twin environment. The framework uses **Authentik** as an Identity Provider (IdP) to issue OAuth2 JSON Web Tokens (JWTs) via `client_credentials` and **Kong Gateway** (DB-less, declarative mode) as an API Gateway to validate requests before forwarding traffic to the upstream backend.

---

## Architecture Overview

![Framework Visualization](https://github.com/elman-emil/Secure-IoT-Gateway/blob/6eaa83c19f588858ca4a46be42169784be8dc4fd/Screenshot%202026-10-12%20180850.png)

1. **Authentication:** The IoT Client requests an RS256-signed JWT from Authentik using a Service Account App Password.
2. **Token Issuance:** Authentik validates credentials and issues an access token signed with its private RSA key.
3. **API Request:** The Client presents the JWT in the `Authorization: Bearer <JWT>` header to Kong Gateway.
4. **Validation & Routing:** Kong verifies the token signature against Authentik's public RSA key. Valid requests are proxied upstream to the backend service.
5. **MQTT Broker:** The MQTT broker ingests and sends sensor data to the backend in real-time in JSON format.

---

## Framework Components

* **API Gateway:** Kong Gateway (DB-less, declarative `kong.yml`)
* **Identity Provider:** Authentik (Docker / Docker Compose)
* **Token Standard:** OAuth2 `client_credentials` with RS256 JWT signatures
* **Authentication Method:** Service Account + App Password
* **MQTT Broker**: Work-in-Progress (10/2026)

---

## Configuration Steps

## COMING SOON
        
