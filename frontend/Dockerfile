# Development Frontend Dockerfile
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./

# Development stage
FROM base as development

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 3000

# Start development server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
