# docker/nginx/Dockerfile
FROM nginx:1.25-alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media

# Copy static files (this will be mounted as volume in production)
VOLUME /app/staticfiles
VOLUME /app/media

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]