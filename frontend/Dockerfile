FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG SIGNAL_BACKEND_URL=http://backend:8000
ENV SIGNAL_BACKEND_URL=${SIGNAL_BACKEND_URL}
RUN npm run build
CMD ["npm", "start"]
