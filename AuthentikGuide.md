# M2M IoT Gateway & Identity Provider Architecture

This repository contains the architecture and configuration for securing Machine-to-Machine (M2M) communications in a Digital Twin environment. The system uses **Authentik** as an Identity Provider (IdP) to issue OAuth2 JSON Web Tokens (JWTs) via `client_credentials` and **Kong Gateway** (DB-less mode) as an API Gateway to validate requests before forwarding traffic to the upstream backend.

---

## Architecture Overview

![[Pasted image 20261005223421.png]]

1. **Authentication:** The IoT Client requests an RS256-signed JWT from Authentik using a Service Account App Password.
2. **Token Issuance:** Authentik validates credentials and issues an access token signed with its private RSA key.
3. **API Request:** The Client presents the JWT in the `Authorization: Bearer <JWT>` header to Kong Gateway.
4. **Validation & Routing:** Kong verifies the token signature against Authentik's public RSA key. Valid requests are proxied upstream to the backend service.

---

## Technical Stack

* **API Gateway:** Kong Gateway (DB-less, declarative `kong.yml`)
* **Identity Provider:** Authentik (Docker / Docker Compose)
* **Token Standard:** OAuth2 `client_credentials` with RS256 JWT signatures
* **Authentication Method:** Service Account + App Password

---

## Configuration Steps

### 1. Authentik Setup (Identity Provider)

1. **Create Service Account:**
   * Navigate to **Directory** $\rightarrow$ **Users** $\rightarrow$ **New User**.
   * Set Type to **Service Account**.
   * Name: `iot-device`
   * Copy and save the generated **App Password**.

2. **Configure OAuth2 Provider:**
   * Navigate to **Applications** $\rightarrow$ **Providers** $\rightarrow$ **Create Provider**.
   * Protocol: **OAuth2/OpenID Provider**.
   * Name: `Kong-IoT-Provider`.
   * Client Type: `Confidential`.
   * Authorization Flow: Select `default-provider-authorization-implicit-branch`.
   * Copy the generated **Client ID**.

3. **Bind Provider to Application:**
   * Navigate to **Applications** $\rightarrow$ **Applications** $\rightarrow$ **Create Application**.
   * Name: `Secure IoT Gateway`.
   * Provider: Select `Kong-IoT-Provider`.

---

### 2. Extract Public Key for Kong

Kong requires Authentik’s RSA Public Key (`-----BEGIN PUBLIC KEY-----`) to verify JWT signatures.

1. Download the certificate (`cert.pem`) from Authentik under **Crypto Certificates**.
2. Convert the certificate to an RSA Public Key using OpenSSL:
   ```bash
   openssl x509 -in cert.pem -pubkey -noout > public_key.pem
   ```

	### 2.1 Openssl issue
	- During the key conversion you might run into an issue with **openssl** not being installed in your windows PATH. Installing it is unnecessary, and you can use your Docker environment instead with a temporary **Alpine** container.
	- Run the following command to convert the key and save it into a file named **public_key.pem**
   ```powershell
   docker run --rm -v "${PWD}:/certs" -w /certs alpine/openssl x509 -in cert.pem -pubkey -noout > public_key.pem
   ```

---

### 3. Kong Declarative Configuration (`kong.yml`)

Save the following configuration as `kong.yml` in your Kong directory:

```yaml
_format_version: "3.0"
_transform: true

services:
  - name: digital-twin-backend
    url: https://jsonplaceholder.typicode.com
    routes:
      - name: test-route
        paths:
          - /test
        strip_path: true
    plugins:
      - name: jwt
        config:
          claims_to_verify:
            - exp

consumers:
  - username: iot-device
    jwt_secrets:
      - key: "http://localhost:9000/application/o/secure-iot-gateway/" 
        # Must match JWT 'iss' claim
        algorithm: RS256
        rsa_public_key: |
          -----BEGIN PUBLIC KEY-----
          <PASTE_YOUR_EXTRACTED_RSA_PUBLIC_KEY_HERE>
          -----END PUBLIC KEY-----
```

---

## Verifying the Pipeline

Run the following PowerShell script to execute an end-to-end authentication and API request flow:

```powershell
# Parameters
$authentikUrl = "http://localhost:9000/application/o/token/"
$kongUrl      = "http://localhost:8000/test"
$clientId     = "YOUR_AUTHENTIK_PROVIDER_CLIENT_ID"
$username     = "iot-device"
$appPassword  = "YOUR_SERVICE_ACCOUNT_APP_PASSWORD"

# 1. Fetch JWT Token from Authentik
$tokenResponse = Invoke-RestMethod -Uri $authentikUrl `
    -Method Post `
    -ContentType "application/x-www-form-urlencoded" `
    -Body @{
        grant_type    = "client_credentials"
        client_id     = $clientId
        username      = $username
        password      = $appPassword
        scope         = "openid"
    }

$jwt = $tokenResponse.access_token
Write-Host "Token successfully received from Authentik!" -ForegroundColor Green

# 2. Present Token to Kong Gateway
$response = Invoke-RestMethod -Uri $kongUrl `
    -Headers @{ Authorization = "Bearer $jwt" }

Write-Host "Kong successfully validated JWT and routed request!" -ForegroundColor Green
$response
```

---

## Production Security Checklist

- [ ] Transition HTTP endpoints (`http://`) to HTTPS (`https://`) using TLS certificates.
- [ ] Restrict direct network access to the Upstream Backend so it only accepts traffic originating from Kong's IP address.
- [ ] Store Client Secrets and Service Account App Passwords in a secure vault/environment variable store.