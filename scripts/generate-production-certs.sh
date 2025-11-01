#!/bin/bash
set -euo pipefail

# Production-style Certificate Generation Script
# Creates a proper CA hierarchy with intermediate certificates

CERT_DIR="${1:-./certs-production}"
DOMAIN="${2:-crank.local}"

echo "🔐 Generating Production-Style Certificate Infrastructure"
echo "   Certificate Directory: $CERT_DIR"
echo "   Domain: $DOMAIN"

# Clean and create directories
rm -rf "$CERT_DIR"
mkdir -p "$CERT_DIR"/{ca,intermediate,certs,private}
chmod 700 "$CERT_DIR/private"

cd "$CERT_DIR"

# =============================================================================
# 1. ROOT CA CERTIFICATE
# =============================================================================
echo "🏛️  Generating Root CA..."

# Root CA private key (4096-bit for security)
openssl genrsa -out ca/ca.key 4096
chmod 600 ca/ca.key

# Root CA certificate (10 years)
openssl req -new -x509 -days 3650 -key ca/ca.key -out ca/ca.crt \
  -subj "/C=US/ST=CA/L=San Francisco/O=Crank Platform Root CA/OU=Security/CN=Crank Root CA"

echo "✅ Root CA generated"

# =============================================================================
# 2. INTERMEDIATE CA CERTIFICATE
# =============================================================================
echo "🔗 Generating Intermediate CA..."

# Intermediate CA private key
openssl genrsa -out intermediate/intermediate.key 4096
chmod 600 intermediate/intermediate.key

# Intermediate CA certificate signing request
openssl req -new -key intermediate/intermediate.key -out intermediate/intermediate.csr \
  -subj "/C=US/ST=CA/L=San Francisco/O=Crank Platform/OU=Security/CN=Crank Intermediate CA"

# Sign intermediate certificate with root CA (5 years)
openssl x509 -req -in intermediate/intermediate.csr \
  -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial \
  -out intermediate/intermediate.crt -days 1825 \
  -extensions v3_intermediate_ca \
  -extfile <(echo "
[v3_intermediate_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:0
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
")

echo "✅ Intermediate CA generated"

# =============================================================================
# 3. SERVER CERTIFICATES
# =============================================================================
echo "🖥️  Generating Server Certificates..."

# Create certificate chain file
cat intermediate/intermediate.crt ca/ca.crt > ca/ca-chain.crt

# Platform server certificate
echo "   Platform server certificate..."
openssl genrsa -out private/platform.key 2048
chmod 600 private/platform.key

openssl req -new -key private/platform.key -out certs/platform.csr \
  -subj "/C=US/ST=CA/L=San Francisco/O=Crank Platform/OU=Platform/CN=platform"

# Sign with intermediate CA, include SAN for Docker networking
openssl x509 -req -in certs/platform.csr \
  -CA intermediate/intermediate.crt -CAkey intermediate/intermediate.key \
  -CAcreateserial -out certs/platform.crt -days 365 \
  -extensions v3_server \
  -extfile <(echo "
[v3_server]
basicConstraints = CA:FALSE
nsCertType = server
nsComment = \"Crank Platform Server Certificate\"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = platform
DNS.2 = crank-platform
DNS.3 = localhost
DNS.4 = *.${DOMAIN}
IP.1 = 127.0.0.1
IP.2 = ::1
")

# Worker client certificate
echo "   Worker client certificate..."
openssl genrsa -out private/client.key 2048
chmod 600 private/client.key

openssl req -new -key private/client.key -out certs/client.csr \
  -subj "/C=US/ST=CA/L=San Francisco/O=Crank Platform/OU=Workers/CN=worker-client"

# Sign with intermediate CA
openssl x509 -req -in certs/client.csr \
  -CA intermediate/intermediate.crt -CAkey intermediate/intermediate.key \
  -CAcreateserial -out certs/client.crt -days 365 \
  -extensions v3_client \
  -extfile <(echo "
[v3_client]
basicConstraints = CA:FALSE
nsCertType = client, server
nsComment = \"Crank Platform Worker Client Certificate\"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, serverAuth
")

echo "✅ Server certificates generated"

# =============================================================================
# 4. PRODUCTION DEPLOYMENT FILES
# =============================================================================
echo "📦 Creating production deployment files..."

# Copy certificates to standard locations
cp ca/ca-chain.crt ca.crt
cp certs/platform.crt platform.crt
cp private/platform.key platform.key
cp certs/client.crt client.crt
cp private/client.key client.key

# Set production permissions
chmod 644 *.crt
chmod 600 *.key

# Create certificate verification script
cat > verify-certs.sh << 'EOF'
#!/bin/bash
echo "🔍 Verifying Certificate Chain..."

echo "📋 Root CA Info:"
openssl x509 -in ca.crt -noout -subject -issuer -dates

echo "📋 Platform Certificate Info:"
openssl x509 -in platform.crt -noout -subject -issuer -dates

echo "📋 Client Certificate Info:"
openssl x509 -in client.crt -noout -subject -issuer -dates

echo "🔗 Verifying Certificate Chain:"
openssl verify -CAfile ca.crt platform.crt
openssl verify -CAfile ca.crt client.crt

echo "✅ Certificate verification complete"
EOF
chmod +x verify-certs.sh

echo "✅ Production-style certificates generated successfully!"
echo ""
echo "📁 Certificate files:"
echo "   - ca.crt          (Certificate chain for verification)"
echo "   - platform.crt    (Platform server certificate)"
echo "   - platform.key    (Platform private key - 0600 permissions)"
echo "   - client.crt      (Worker client certificate)"
echo "   - client.key      (Worker private key - 0600 permissions)"
echo ""
echo "🧪 To verify certificates: ./$CERT_DIR/verify-certs.sh"
echo "🐳 To use with Docker: Copy to Docker volume or bind mount"