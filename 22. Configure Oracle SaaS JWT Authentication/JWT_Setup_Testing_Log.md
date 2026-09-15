# Oracle Fusion JWT Authentication — Setup & Testing Log

This document records the actual steps followed to configure and test JWT-based
authentication for Oracle Fusion SaaS REST APIs on the **Argo BPC** instance
(Test - Copy of Prod), including a test of behaviour when the service user
account is locked.

## 1. Generate the X.509 Key Pair and JWT Token

**Tooling:** `generate_jwt.sh` (Git Bash / OpenSSL), stored locally in:
`C:\Users\ADMIN\OneDrive\Argo Project\BPC JWT Token Approach`

**Configured values:**

| Variable | Value |
|---|---|
| `ISSUER` | `argo_service_user` |
| `PRINCIPAL` | `argo_service_user` |
| `TOKEN_TTL_SECONDS` | `3600` (1 hour) |

**Steps:**

1. Open Git Bash in the target folder.
2. Run:
   ```bash
   bash generate_jwt.sh
   ```
3. This generates (first run only for the key pair; every run for the token):
   - `private.key` — RSA private key (2048-bit). **Kept local, never uploaded/shared.**
   - `publickey.cer` — self-signed X.509 certificate (public key).
   - `header.json` — JWT header (`alg`, `typ`, `x5t` fingerprint of the cert).
   - `payload.json` — JWT claims (`iss`, `prn`, `iat`, `exp`).
   - `sample_jwt_token.txt` — the signed JWT (`header.payload.signature`, Base64url-encoded).
4. To refresh the token later (same key pair, new `iat`/`exp`):
   ```bash
   bash generate_jwt.sh
   cat sample_jwt_token.txt
   ```

## 2. Configure Oracle Fusion to Trust the Certificate

**Navigation:** Tools > Security Console > API Authentication

1. Click **Edit**.
2. Set **Trusted Issuer** = `argo_service_user` (must exactly match the `ISSUER` value used to generate the token).
3. Set **Token Type** = `JWT`.
4. **Save and Close**.
5. Go to **Inbound API Authentication Public Certificates**.
6. Click **Add New Certificate**.
7. **Certificate Alias**: `ORA_ASE_argo_bpc`
8. **Import Public Certificate**: uploaded `publickey.cer`.
9. **Save**, then **Done**.

Result: certificate registered, `Certificate Name = C=US,O=BPC,CN=argo_service_user`.

## 3. Test the Token via Postman

**Collection:** `Oracle_Fusion_JWT.postman_collection.json`

**Collection variables:**

| Variable | Value |
|---|---|
| `fusion_host` | Argo BPC Fusion test instance base URL |
| `jwt_token` | contents of `sample_jwt_token.txt` |

**Request used:** `GET {{fusion_host}}/hcmRestApi/resources/11.13.18.05/workers?limit=1`
**Header:** `Authorization: Bearer {{jwt_token}}`

**Result:** `200 OK` — worker record returned successfully.

## 4. Test API Access With the Service Account Locked

**Purpose:** verify JWT authentication does not depend on the account's
interactive-login/password state — one of the core reasons to use JWT over
Basic Authentication.

**Steps:**

1. Navigate to **Security Console > Users**, open `argo_service_user`.
2. Checked **Locked** (account locked for interactive/password login).
3. **Save and Close**.
4. Re-ran the same Postman request (same JWT token, unchanged).

**Result:** `200 OK` — API call still succeeded, worker data returned, even
though the account was locked.

**Conclusion:** JWT authentication (certificate-based trust configured in
Security Console > API Authentication) authenticates independently of the
account's password/lock state. Locking the account blocks interactive UI/SSO
login, but does **not** revoke API access obtained via the trusted
certificate.

**Operational implication:** if you need to fully revoke this integration's
access (not just interactive login), locking the user is **not sufficient**.
Instead:
- Remove/replace the certificate under **Inbound API Authentication Public
  Certificates**, or
- Change/remove the Trusted Issuer or disable JWT as the Token Type in
  **API Authentication**.

## 5. Regenerating the Token

The token expires after `TOKEN_TTL_SECONDS` (currently 1 hour). To get a new
one:

```bash
bash generate_jwt.sh
cat sample_jwt_token.txt
```

Paste the new value into the Postman `jwt_token` collection variable (or
wherever else it's consumed, e.g. an OIC connection or another client).

## 6. Note on OIC (Oracle Integration Cloud) Connections

OIC has a native **"OAuth using JWT User Assertion"** security policy that
can sign a JWT using a private key uploaded to OIC's own certificate store,
then exchange it via IDCS for an OAuth token automatically (with refresh) —
this avoids needing to manually refresh a token like in Postman.

This is a **separate authentication path** from the direct JWT/REST trust
configured in Section 2 above: it is mediated by IDCS, and may require the
IDCS/Fusion admin to register a corresponding trusted client/application in
IDCS. Whether this OIC path is equally unaffected by the Fusion user being
locked has **not yet been verified** — this should be tested the same way as
Section 4 (lock the account, click "Test Connection" in OIC) once the OIC
connection is fully configured.
