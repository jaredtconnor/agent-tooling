# Go module justfile

# Show available commands
default:
    @just --list

# Install dependencies
install:
    go mod download
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Format code
format:
    go fmt ./...
    goimports -w .

# Lint code
lint:
    golangci-lint run
    go vet ./...

# Run unit tests (optionally specify path)
test PATH="./...":
    go test -v -race -short {{PATH}}

# Run integration tests
test-integration:
    go test -v -race -run Integration ./...

# Run all tests
test-full:
    go test -v -race ./...

# Build binary
build: lint test
    go build -o bin/app ./cmd/app

# Run in development mode
dev:
    go run ./cmd/app

# Clean build artifacts
clean:
    rm -rf bin/ coverage.out coverage.html
