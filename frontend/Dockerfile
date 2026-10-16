# Etapa 1: compilar la aplicación Angular
FROM node:24-alpine AS build
WORKDIR /app

# Se copian primero los manifiestos para aprovechar la caché de capas
COPY package*.json ./
RUN npm ci

COPY . .
RUN npx ng build --configuration production

# Etapa 2: servir los archivos estáticos con Nginx
FROM nginx:1.27-alpine
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
