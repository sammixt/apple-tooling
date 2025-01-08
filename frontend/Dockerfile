FROM node:20-alpine as builder

WORKDIR /app

ARG NPM_TOKEN

COPY . .

# Set the NPM registry and authentication token
RUN npm config set @turingenterprises:registry https://npm.pkg.github.com/turingenterprises
RUN npm config set //npm.pkg.github.com/:_authToken $NPM_TOKEN

RUN npm ci

RUN npm run build

# Serve stage with Nginx
FROM nginx:alpine

# Remove the default Nginx index.html, as we'll be supplying our own content
RUN rm /usr/share/nginx/html/*

COPY --from=builder /app/dist/apples3dashboard/ /usr/share/nginx/html

COPY --from=builder /app/nginx.conf /etc/nginx/nginx.conf

# Expose port 80 for HTTP traffic
EXPOSE 80
