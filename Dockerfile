FROM node:22-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci

COPY frontend ./frontend
RUN cd frontend && npm run build

WORKDIR /app/frontend
EXPOSE 4173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
