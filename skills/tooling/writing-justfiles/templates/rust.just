# Rust module justfile

# Show available commands
default:
    @just --list

# Install dependencies
install:
    cargo fetch

# Format code
format:
    cargo fmt

# Lint code
lint:
    cargo clippy -- -D warnings
    cargo fmt -- --check

# Run tests (optionally specify path)
test PATH="":
    cargo test {{PATH}}

# Run tests with output
test-verbose:
    cargo test -- --nocapture

# Build in debug mode
build:
    cargo build

# Build in release mode
build-release: lint test
    cargo build --release

# Run in development mode
dev:
    cargo run

# Check code without building
check:
    cargo check

# Clean build artifacts
clean:
    cargo clean
