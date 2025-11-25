# Use Nginx to serve static files
FROM nginx:alpine

# Copy static files to Nginx html directory
COPY frontend/public /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
