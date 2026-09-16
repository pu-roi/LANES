# ==============================================================================
# LANES Frontend - Production Dockerfile for Google Cloud Run
# ==============================================================================
FROM node:20-alpine

WORKDIR /app

# Set production environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8080

# Install dependencies based on package-lock.json
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code
COPY . .

# Set the public backend API endpoint (passed at build time)
ARG NEXT_PUBLIC_API_URL=https://lanes-api-557679867071.asia-east1.run.app/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build Next.js application with webpack
RUN npx next build --webpack

# Expose default Cloud Run port
EXPOSE 8080

# Start Next.js on port 8080 bound to 0.0.0.0
CMD ["sh", "-c", "npx next start -p ${PORT:-8080} -H 0.0.0.0"]
