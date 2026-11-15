# HC-AI | ticket: FDD-TOOL-CODEMAP
# Build context is the repository root:
#   docker build -f website/Dockerfile -t codebase-map-website .
FROM python:3.12-slim AS build
WORKDIR /src
RUN pip install --no-cache-dir pyyaml==6.0.2
COPY codebase_map ./codebase_map
COPY website ./website
ARG SITE_URL=""
RUN python website/build.py --site-url "$SITE_URL"

# Stable branch (even minor); the tag follows its security patches.
FROM nginx:1.30-alpine
COPY website/deploy/nginx.conf /etc/nginx/conf.d/default.conf
# Not every Docker host enables IPv6 inside containers.
RUN sed -i '/listen \[::\]:80;/d' /etc/nginx/conf.d/default.conf
COPY --from=build /src/website/dist /var/www/codebase-map
EXPOSE 80
