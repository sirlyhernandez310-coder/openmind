# =========================
# 1) BUILDER STAGE
# Compila la app de React (Vite) a archivos estáticos en /app/dist
# =========================
FROM node:22-alpine AS builder

WORKDIR /app

# Copiar solo package*.json primero para aprovechar la caché de Docker
COPY package*.json ./
RUN npm ci

COPY . .

# URL de la API que usará la página (se define al construir la imagen)
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


# =========================
# 2) PRODUCTION STAGE
# Nginx sirve los archivos ya compilados (no necesita Node)
# =========================
FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
