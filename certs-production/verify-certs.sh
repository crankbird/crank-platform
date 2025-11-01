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
