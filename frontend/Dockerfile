FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Install serve to run the production build
RUN npm install -g serve

# Railway uses $PORT
CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]
