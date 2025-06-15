FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Generate Tailwind CSS
RUN npx tailwindcss -o src/tailwind.css

EXPOSE 3000

# Start the application
CMD ["npm", "start"] 