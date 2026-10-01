# Usa una imagen base de Python
FROM python:3.9-slim

# Install MySQL client for healthcheck
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Copy and make entrypoint executable (sanitizing CRLF line endings for Linux compatibility)
COPY docker-entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh && chmod +x /usr/local/bin/docker-entrypoint.sh

# Expone el puerto en el que corre la aplicación
EXPOSE 5000

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Comando para correr la aplicación
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
