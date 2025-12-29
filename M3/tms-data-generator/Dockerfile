# to build and run Go-based generator in a container
## Dockerfile for Go data generator
FROM golang:1.24-alpine

WORKDIR /app

# Copy go.mod and go.sum if present

# Kopiuj cały katalog generator (wraz z go.mod/go.sum jeśli są)
COPY generator ./generator
COPY cmd ./cmd

WORKDIR /app/cmd

# Default command: run generator and output to /app/output.sql
CMD ["go", "run", "main.go", "../output.sql"]
