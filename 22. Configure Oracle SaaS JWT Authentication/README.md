# 22. Configure Oracle SaaS JWT Authentication

## Introduction

JSON Web Token (JWT) is a compact token format used to authorize a client application against Oracle Fusion Cloud Applications. A JWT carries the username and an expiration period, and is passed by the client application when calling Oracle Fusion SOAP/REST services.

## Usage

You may already use single sign-on (SSO) to log in to Oracle SaaS interactively. However, REST or SOAP APIs used to integrate Oracle Fusion with a third-party system still need their own authentication (not SSO).

The simplest option is **Basic Authentication** (username/password), but it carries risk:

- With a username and password, the REST API can be called from any device, and data can be downloaded to any untrusted application or system.
- Risk of password compromise.
- Ongoing user/password management overhead.

## Why JWT Authentication?

Another option is **LBAC** (Location-Based Access Control) — restricting access to a specific IP range. But since Oracle SaaS is a cloud product, you may want to access it from anywhere in the world without requiring a VPN.

To avoid the issues above, **JWT authentication** can be used for REST/SOAP API calls:

- An application hosted on PaaS (or any external system) can integrate with and consume REST APIs from Oracle Cloud using a JWT token, passed as an HTTP header.
- The generated token carries encoded details such as `user_name` (the user being authenticated as), generation time, and expiration time.

## JWT Token Structure

A JWT token is an encoded string made up of three parts:

| Part | Description |
|---|---|
| **Header** | Identifies the algorithm used to generate the signature |
| **Payload** | Contains a set of claims (e.g. `iss`, `prn`, `iat`, `exp`) describing which user the token is for, when it was issued, and when it expires |
| **Signature** | The token is signed using a private/public key pair |

## Steps to Enable JWT Token Authentication

### Pre-requisite

A pair of X.509 keys (private key + public certificate) for the application that will establish the connection to Oracle Fusion.

### Step 1: Create the X.509 Key Pair

1. Generate a private key:

   ```
   openssl genrsa -out private.key 1024
   ```

2. Using the private key, create an X.509 certificate (`.cer` file) that contains the corresponding public key.

### Step 2: Upload the Certificate to Oracle Fusion

> Prior to release 20D, this required raising a Service Request (SR) with Oracle. From 20D onward, you can manage the client certificate yourself using the steps below.

1. Navigate to **Tools > Security Console > API Authentication**.
2. Click **Edit**, then set **Token Type** to `JWT`.
   - **Trusted Issuer**: free-text field — the name of the third-party system trying to access Oracle Fusion.
3. Click **Save and Close**.
4. Select **Inbound API Authentication Public Certificates**.
5. Click **Add**, then browse to and upload the `.cer` file generated in Step 1 (or received from the third party that generated it).
6. Provide a **certificate alias** and click **Done**.

### Step 3: Generate the JWT Token

With the X.509 key pair created and the public certificate uploaded to Oracle Fusion, you can now generate a token consisting of a **Header**, **Payload**, and **Signature**.

#### 3.1 Header

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "x5t": "cfctAG1vSl82cRAk+PD9M4ltxeuSAA8="
}
```

- `alg` — the signing algorithm used, e.g. RSA (RS256) or HMAC SHA256.
- `typ` — the token type, always `JWT`.
- `x5t` — the Base64-encoded fingerprint of the trusted issuer certificate, sourced from the X.509 key pair created in Step 1.

The `x5t` value can be viewed in a certificate viewer, or generated with:

```
openssl x509 -sha1 -in publickey.cer -noout -fingerprint
```

#### 3.2 Payload

Oracle HCM requires the following claims:

```json
{
  "iss": "testapplication",
  "prn": "fusion_userA",
  "iat": 15934271154,
  "exp": 19233081154
}
```

| Claim | Meaning | Description |
|---|---|---|
| `iss` | Issuer | Must match the Trusted Issuer name configured in Oracle Fusion (Step 2) |
| `prn` | Principal | The username of the user with the Fusion Applications Integration privilege (e.g. `fusion_userA`) |
| `iat` | Issued At | Unix epoch time the token was generated, e.g. `1596271154` = 08/01/2020 @ 8:39am (UTC) |
| `exp` | Expiration | Unix epoch time the token expires, e.g. `1918081154` = 10/13/2030 @ 12:19am (UTC) |

#### 3.3 Generate the Signature

The signature is created by combining the encoded header, the encoded payload, and signing them using the algorithm specified in the header together with the public/private key pair.

### Decoding the JWT

You can use [jwt.io](https://jwt.io) to decode an existing JWT token, or to encode a new one for testing.

### Test and Confirm

Once the JWT token is generated, test it against a user by calling a REST or SOAP API with the following header:

```
Authorization: Bearer <token>
```

Example:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IlpQN3pvNXdqRklkQ2kreXNteFo1RmdIMXM1bz0iLCJraWQiOiJ0ZXN0In0.eyJzdWIiO...
```

## Conclusion

JWT authentication is a widely used technology for API authentication. It is a trusted standard that ensures a secure exchange of information between servers, avoiding the basic vulnerabilities inherent in username/password-based Basic Authentication.

---
*Adapted from: [Oracle SaaS JWT Authentication – Usage and Configuration](https://fusionpractices.com/blog/configuring-oracle-saas-jwt-authentication/), Fusion Practices.*
