# Node.js/TypeScript module justfile
# Package manager: pnpm

# Show available commands
default:
    @just --list

# Install dependencies
install:
    pnpm install

# Format code
format:
    prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"

# Lint code
lint:
    eslint src/ --ext .ts,.tsx,.js,.jsx
    tsc --noEmit

# Fix linting issues
lint-fix:
    eslint src/ --ext .ts,.tsx,.js,.jsx --fix

# Run unit tests (optionally specify path)
test PATH="src/**/*.test.ts":
    vitest run {{PATH}}

# Run integration tests
test-integration:
    vitest run tests/integration/**/*.test.ts

# Run all tests
test-full:
    vitest run && playwright test

# Run tests in watch mode
test-watch:
    vitest

# Build for production
build: lint test
    pnpm build

# Run development server
dev:
    pnpm dev

# Type check
typecheck:
    tsc --noEmit

# Clean build artifacts
clean:
    rm -rf dist/ .next/ node_modules/.cache/ coverage/
