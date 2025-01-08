# Stage 1: Build the application
FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -o main cmd/server/main.go

# Stage 2: Create a lightweight runtime image
FROM alpine:3.17

WORKDIR /app

# Copy only the compiled binary from the builder stage
COPY --from=builder /app/main .

# Expose port
EXPOSE 8080

# Run the executable
CMD ["./main"]
