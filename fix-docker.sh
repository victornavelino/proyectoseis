#!/bin/bash

echo "=== Diagnóstico de Docker ==="

# 1. Verificar DNS del host
echo "1. DNS del host:"
cat /etc/resolv.conf

# 2. Probar conectividad del host
echo -e "\n2. Conectividad del host:"
ping -c 2 deb.debian.org
ping -c 2 google.com

# 3. Probar desde contenedor temporal
echo -e "\n3. Probando desde contenedor temporal:"
docker run --rm python:3.9-bullseye sh -c "cat /etc/resolv.conf && ping -c 2 google.com || echo 'Fallo en contenedor'"

# 4. Configurar DNS global de Docker
echo -e "\n4. Configurando DNS global de Docker..."
sudo mkdir -p /etc/docker
echo '{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
}' | sudo tee /etc/docker/daemon.json

# 5. Reiniciar Docker
echo -e "\n5. Reiniciando Docker..."
sudo systemctl restart docker

# 6. Esperar a que Docker reinicie
sleep 10

# 7. Probar nuevamente
echo -e "\n6. Probando después de reiniciar:"
docker run --rm python:3.9-bullseye apt-get update

echo -e "\n=== Diagnóstico completado ==="