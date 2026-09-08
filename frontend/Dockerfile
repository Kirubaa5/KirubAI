# Frontend Dockerfile for development
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Command will be overridden by docker-compose
CMD ["npm", "run", "dev"]
