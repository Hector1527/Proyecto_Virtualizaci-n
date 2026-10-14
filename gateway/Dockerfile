FROM nginx:alpine
# Kubernetes mounts the configured nginx.conf from its ConfigMap at runtime.
COPY gateway/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
