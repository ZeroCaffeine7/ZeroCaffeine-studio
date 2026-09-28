FROM nginx:stable-alpine

# Copy static frontend files to nginx html directory
COPY . /usr/share/nginx/html

# Ensure correct permissions
RUN chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
