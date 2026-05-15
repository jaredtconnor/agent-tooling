# Root justfile - orchestrates all modules

# List of module directories
modules := "frontend backend/api backend/workers infrastructure"

# Show available commands
default:
    @just --list

# Run command in all modules
[private]
run-in-modules command:
    #!/usr/bin/env bash
    set -e
    for dir in {{modules}}; do
        if [ -f "$dir/justfile" ]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Running '{{command}}' in $dir..."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            (cd "$dir" && just {{command}}) || exit 1
        fi
    done

# Install dependencies for all modules
install:
    @just run-in-modules install

# Format all modules
format:
    @just run-in-modules format

# Lint all modules
lint:
    @just run-in-modules lint

# Test all modules
test:
    @just run-in-modules test

# Build all modules
build:
    @just run-in-modules build

# Clean all modules
clean:
    @just run-in-modules clean

# Install pre-commit hooks (if .pre-commit-config.yaml exists)
pre-commit-install:
    @if [ -f .pre-commit-config.yaml ]; then \
        pre-commit install --install-hooks; \
    else \
        echo "No .pre-commit-config.yaml found"; \
    fi

# Run pre-commit on all files
pre-commit-run:
    @if [ -f .pre-commit-config.yaml ]; then \
        pre-commit run --all-files; \
    else \
        echo "No .pre-commit-config.yaml found"; \
    fi
