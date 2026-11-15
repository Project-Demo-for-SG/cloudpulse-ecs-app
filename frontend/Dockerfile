FROM nginx:1.27-alpine

COPY index.html /usr/share/nginx/html/index.html

COPY default.conf.template \
    /etc/nginx/templates/default.conf.template

ENV BACKEND_URL=http://backend:3000

ENV DNS_RESOLVER=127.0.0.11

ENV NGINX_ENVSUBST_FILTER=^(BACKEND_URL|DNS_RESOLVER)$

EXPOSE 80