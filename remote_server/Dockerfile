FROM node:16-alpine as build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY .env .

# Copy built frontend from the build stage
COPY --from=build /app/frontend/dist /app/static

# Expose port (use the one from your .env file)
EXPOSE 5163

# Run the application
CMD ["python", "app.py"]