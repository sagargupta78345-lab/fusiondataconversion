#!/usr/bin/env bash
# Generates a sample X.509 key pair and a signed JWT (RS256) for
# Oracle Fusion SaaS REST/SOAP API authentication, following the
# steps documented in ../README.md.
#
# Usage:
#   ./generate_jwt.sh
#
# Outputs (in this folder):
#   private.key          - RSA private key (KEEP SECRET, do not commit real keys)
#   publickey.cer         - self-signed X.509 certificate (upload the real one to Oracle Fusion)
#   header.json            - JWT header
#   payload.json            - JWT payload (claims)
#   sample_jwt_token.txt    - the signed JWT, ready to use as: Authorization: Bearer <token>
#
# Edit ISSUER and PRINCIPAL below to match your Trusted Issuer name
# (configured in Fusion Security Console) and target Fusion user.

set -euo pipefail

ISSUER="testapplication"
PRINCIPAL="fusion_userA"
TOKEN_TTL_SECONDS=3600

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

# Step 1: X.509 key pair (skip if already generated)
if [[ ! -f private.key ]]; then
  openssl genrsa -out private.key 2048
fi
if [[ ! -f publickey.cer ]]; then
  openssl req -new -x509 -key private.key -out publickey.cer -days 3650 \
    -subj "/CN=${ISSUER}/O=FusionDataConversion/C=US"
fi

# x5t: base64-encoded SHA-1 fingerprint of the certificate (DER form)
X5T=$(openssl x509 -in publickey.cer -outform der | openssl dgst -sha1 -binary | base64)

cat > header.json <<EOF
{"alg":"RS256","typ":"JWT","x5t":"${X5T}"}
EOF

IAT=$(date +%s)
EXP=$((IAT + TOKEN_TTL_SECONDS))
cat > payload.json <<EOF
{"iss":"${ISSUER}","prn":"${PRINCIPAL}","iat":${IAT},"exp":${EXP}}
EOF

HEADER_B64=$(tr -d '\n' < header.json | b64url)
PAYLOAD_B64=$(tr -d '\n' < payload.json | b64url)
SIGNING_INPUT="${HEADER_B64}.${PAYLOAD_B64}"

SIGNATURE_B64=$(printf '%s' "${SIGNING_INPUT}" | openssl dgst -sha256 -sign private.key | b64url)

echo "${SIGNING_INPUT}.${SIGNATURE_B64}" > sample_jwt_token.txt

echo "x5t: ${X5T}"
echo "JWT: $(cat sample_jwt_token.txt)"
