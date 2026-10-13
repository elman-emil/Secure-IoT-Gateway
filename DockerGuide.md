# Secure IoT Gateway: System Architecture and Installation Guide

## 1. Gateway Overview & Docker Architecture

This Secure-IoT-Gateway project is an open-source API gateway project designed to build an open-source and easily deployable API Gateway system for communication between IoT client devices and backend microservices. This iteration is built using open-source tools like **Kong Gateway OSS** in **DB-less** **(declarative)** and **Authentik (Identity Provider)** containerized using Docker.

### 2.1 Kong Setup & Declarative Configuration File (`kong.yml`)

This initial file defines the upstream services, routing rules, consumer credentials and gateway policies (API Key authentication through `key-auth` & rate-limiting through `rate-limit`) for **Kong Gateway**. These settings will update later when **Authentik** is setup along with Kong, but that's for later part of this guide:

````
_format_version: "3.0"

services:
  - name: dummy-backend
    url: https://jsonplaceholder.typicode.com
    routes:
      - name: test-route
        paths:
          - /test
    plugins:
      # 1. Require API Key for all routes on this service
      - name: key-auth
        config:
          key_names:
            - apikey
      # 2. Limit traffic to 5 requests per minute
      - name: rate-limiting
        config:
          minute: 5
          policy: local

# 3. Register a consumer (IoT Device) and assign its key
consumers:
  - username: iot-sensor-node-01
    keyauth_credentials:
      - key: my-super-secret-iot-key


````

### 2.2 Docker Compose Configuration File Setup (`docker-compose.yml`)

These settings define the **Kong Gateway** environment, port mapping and config file locations.

```
version: '3.8'

services:
  kong:
    image: kong:latest
    container_name: kong-gateway
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /usr/local/kong/declarative/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: 0.0.0.0:8001
      KONG_ADMIN_GUI_LISTEN: 0.0.0.0:8002
    volumes:
      - ./kong.yml:/usr/local/kong/declarative/kong.yml
    ports:
      - "8000:8000"
      - "8001:8001"
      - "8002:8002"

````

## 3. Booting Up Kong Gateway & Testing Request Verification

### Launching / Restarting Kong OSS

To start **Kong OSS** in Docker, proceed with the following steps.

NOTE: For the sake of simplicity, "terminal" in this guide references the terminal tool WITHIN the Docker desktop application.

```
# First ensure your terminal is operating inside the directory where your docker-compose.yml file is located

# Start the container environment
docker compose up -d

# Restart container to pull changes in the declarative kong.yml file if neccesary
docker compose restart kong
````

**NOTE: Because Kong OSS is running in DB-less, declarative mode, any changes or updates made in the kong.yml declarative file MUST be initialized by restarting the container.**

### Verifying and Testing Gateway Policies

#### 1. Testing Unauthenticated Request Verification

Lets test requesting the gateway without an API key in the request header:

```
curl.exe -i http/localhost:8000/test
````

**Expected output for the request should read**:

	`HTTP/1.1 401 Unauthorized`

With the body of the request reading:

	`{"Message":"No API key found in the request"}`

#### 2. Testing Request Verification With an Invalid Key

Now lets test requesting the gateway with an invalid or wrong key:

```
curl.exe -i -H "apikey: wrong-key" http://localhost:8000/test

````

**Expected output for the request should read:**

	`HTTP/1.1 401 Unauthorized`

With the body of the request reading:

	`{"Message":"Invalid authentication credentials"}`
	
#### 3. Testing Request Verification With a Valid Key

Now lets test requesting the gateway with a valid key:

```
curl.exe -i -H "apikey: my-super-secret-iot-key" http://localhost:8000/test

````

**Expected output for the request should read:**

	`HTTP/1.1 200 OK`

With the headers:

```
X-RateLimit-Limit-Minute: 5
````

And:

```
X-RateLimit-Remaining-Minute: 4.
````

The dummy backend should return a veritable wall of text and JSON data. NOTE: As long as the HTTP request returns `HTTP/1.1 200 OK` you can be comfortable the gateway verification is working.

#### 4. Rate Limit Exhaustion and Lockout

Sending more than 5 rapid requests within 5 minutes should cause rate limit exhaustion. Test this by sending 5 valid requests back to back. The return should read:

`HTTP/1.1 429 Too Many Requests`

With the body of the request reading:

`{"message":"API rate limit exceeded"}`.

## 4. Problem Solving Frequent Issues

### Issue 1: Wrong Working Directory (`no config file found`)

- **Issue**: `docker compose up` gave `no configuration file found` or `docker compose ps` returned empty headers and zero services.
- **Resolution**: Navigate to the directory where your `docker-compose.yml` file is located.

#### Issue 2: Visual Studio Code CRLF / LF Error

- **Issue**: Container immediately exits under `Exit Code 1` and `docker compose ps` returns no active services.
- **Resolution**: Open the `kong.yml` and `docker-compose.yml` files in Visual Studio Code and navigate to the lower right corner. Change line ending settings from **CRLF** to **LF**.
	- Linux based containers cannot parse line endings with (`\r`).

#### Issue 3: Powershell `curl` Command Collision
- **Issue**: Failed request when running `curl` in Powershell during testing due to Powershell's native web request command.
- **Resolution**: Always remember to append the `.exe` for the `curl` command.
 
