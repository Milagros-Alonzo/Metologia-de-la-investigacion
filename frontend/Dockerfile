FROM nginx:alpine

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar el frontend
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
