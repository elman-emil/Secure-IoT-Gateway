# Secure-IoT-Gateway: Architecture, Deployment & Troubleshooting Guide

## 1. Project Overview & Architecture

The **Secure-IoT-Gateway** is an open-source API gateway system designed to sit between external client devices (such as IoT endpoints) and backend microservices. Built using **Kong Gateway OSS** in **DB-less (declarative) mode**, this system runs in a lightweight Docker environment without requiring an external database like PostgreSQL for gateway routing rules.

```
Secure-IoT-Gateway/
└── Docker/
    ├── docker-compose.yml
    └── kong.yml


```

### 2.1 Declarative Configuration (`kong.yml`)

Defines upstream services, public routing rules, consumer credentials, and active gateway policies (`key-auth` and `rate-limiting`):

```
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


```

### 2.2 Docker Compose Configuration (`docker-compose.yml`)

Defines the Kong container environment, port mappings, and config file volume bind-mounts:

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


```

## 3. Operational Workflow & Verification

### Launching / Restarting the Gateway

To start or apply changes made to `kong.yml`:

```
# Ensure terminal is inside the directory containing docker-compose.yml
cd "C:\Users\YOUR_DOCKER_LOCATION"

# Start container environment
docker compose up -d

# Restart container to pick up declarative YAML updates
docker compose restart kong


```

### Verifying Gateway Security Policies

#### 1. Unauthenticated Request Verification (Should Fail)

Executing a request without an `apikey` header triggers an immediate 401 response:

```
curl.exe -i http://localhost:8000/test


```

*Expected Output:* `HTTP/1.1 401 Unauthorized` with body `{"message":"No API key found in request"}`.

#### 2. Invalid Key Verification (Should Fail)

Executing a request with an unassigned key is blocked:

```
curl.exe -i -H "apikey: wrong-key" http://localhost:8000/test


```

*Expected Output:* `HTTP/1.1 401 Unauthorized` with body `{"message":"Invalid authentication credentials"}`.

#### 3. Authorized Request Verification (Should Succeed)

Passing the valid consumer key grants access and returns rate-limit header counters:

```
curl.exe -i -H "apikey: my-super-secret-iot-key" http://localhost:8000/test


```

*Expected Output:* `HTTP/1.1 200 OK` accompanied by headers `X-RateLimit-Limit-Minute: 5` and `X-RateLimit-Remaining-Minute: 4`.

#### 4. Rate Limit Exhaustion Test (Should Block)

Sending more than 5 requests in under a minute exhausts the allocated quota:

```
curl.exe -i -H "apikey: my-super-secret-iot-key" http://localhost:8000/test


```

*Expected Output (6th request):* `HTTP/1.1 429 Too Many Requests` with body `{"message":"API rate limit exceeded"}`.

## 4. Problem Solving & Troubleshooting Log

During initial deployment on Windows 11, several environment-specific issues were encountered and resolved.

### Issue 1: Bash Syntax Incompatibility in Windows PowerShell

* **Symptom:** Terminal threw parsing errors: `Missing file specification after redirection operator` and `The '<' operator is reserved`.

* **Root Cause:** Bash-specific Heredoc syntax (`cat << 'EOF' > kong.yml`) was executed directly inside Windows PowerShell.

* **Resolution:** File creation was transitioned directly into VS Code editors or replaced with PowerShell Here-Strings (`@' ... '@ | Set-Content -Encoding utf8 kong.yml`).

### Issue 2: Script Wrapper Pollution in YAML Files

* **Symptom:** VS Code displayed YAML syntax errors: `BAD_SCALAR_START`, `MULTILINE_IMPLICIT_KEY`, and `MISSING_CHAR`.

* **Root Cause:** PowerShell wrapper commands (`@'` and `Set-Content...`) were accidentally pasted directly inside `docker-compose.yml`.

* **Resolution:** Replaced file contents with pure, valid YAML formatting without CLI wrappers.

### Issue 3: Working Directory Mismatch (`no config file found`)

* **Symptom:** `docker compose up` threw `no configuration file found` or `docker compose ps` displayed empty headers without running services.

* **Root Cause:** The terminal prompt was operating in the root repository directory rather than the `/Docker` subfolder where `docker-compose.yml` resides.

* **Resolution:** Changed working directory to the target path prior to invoking Docker Compose commands: `cd Docker`.

### Issue 4: Windows Carriage Return Line Endings (`CRLF` vs `LF`)

* **Symptom:** Container exited immediately on startup with `Exit Code 1`. Running `docker compose ps` showed no active port bindings.

* **Root Cause:** Windows text editors default to `CRLF` line endings (`\r\n`). Linux-based containers (such as Kong) fail to parse configuration files containing carriage returns (`\r`).

* **Resolution:** Changed line sequence setting from **CRLF** to **LF** in the bottom-right status bar of Visual Studio Code for both `kong.yml` and `docker-compose.yml`, followed by container restart (`docker compose down && docker compose up -d`).

### Issue 5: PowerShell `curl` Cmdlet Collision

* **Symptom:** Unexpected output format or failed requests when running `curl`.

* **Root Cause:** Windows PowerShell aliases `curl` to its native `Invoke-WebRequest` cmdlet, which behaves differently from real cURL.

* **Resolution:** Appended the `.exe` extension (`curl.exe`) to explicitly target the native binary executable.
