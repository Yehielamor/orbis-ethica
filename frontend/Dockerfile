# Use Nginx to serve static files
FROM nginx:alpine

# Copy static files to Nginx html directory
COPY frontend/public /usr/share/nginx/html

# Copy custom Nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
