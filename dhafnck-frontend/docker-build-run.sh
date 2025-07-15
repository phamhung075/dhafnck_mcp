#!/bin/bash

# Build and run the frontend container

echo "Building dhafnck-frontend Docker image..."
docker build -t dhafnck-frontend:latest .

if [ $? -eq 0 ]; then
    echo "Build successful!"
    
    # Stop and remove existing container if it exists
    docker stop dhafnck-frontend 2>/dev/null
    docker rm dhafnck-frontend 2>/dev/null
    
    echo "Starting dhafnck-frontend container on port 3800..."
    docker run -d \
        --name dhafnck-frontend \
        -p 3800:80 \
        --restart unless-stopped \
        dhafnck-frontend:latest
    
    if [ $? -eq 0 ]; then
        echo "✅ Frontend is running at http://localhost:3800"
        echo "Container name: dhafnck-frontend"
        echo ""
        echo "Useful commands:"
        echo "  View logs:    docker logs dhafnck-frontend"
        echo "  Stop:         docker stop dhafnck-frontend"
        echo "  Start:        docker start dhafnck-frontend"
        echo "  Remove:       docker rm dhafnck-frontend"
    else
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi