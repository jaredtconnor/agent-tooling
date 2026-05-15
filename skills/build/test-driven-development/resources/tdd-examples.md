# TDD Examples

This document provides extended examples of applying TDD in different scenarios: bug fixes, new features, and refactoring.

## Example 1: Bug Fix

**Bug:** Empty email accepted when it shouldn't be

### RED - Write Failing Test

```typescript
test('rejects empty email', async () => {
  const result = await submitForm({ email: '' });
  expect(result.error).toBe('Email required');
});
```

**Why this test:**

- Tests the specific bug (empty email)
- Clear expected behavior (rejection with error message)
- Tests behavior, not implementation

### Verify RED - Watch It Fail

```bash
$ just test
FAIL: expected 'Email required', got undefined
```

**Confirmation:**

- Test fails (not errors)
- Fails because validation is missing (not a typo)
- Error message shows what's wrong

### GREEN - Minimal Code

```typescript
function submitForm(data: FormData) {
  if (!data.email?.trim()) {
    return { error: 'Email required' };
  }
  // ... rest of existing code
}
```

**Why this is minimal:**

- Only adds missing validation
- Uses simple check (empty or whitespace)
- Doesn't add other validations (email format, etc.)

### Verify GREEN - Watch It Pass

```bash
$ just test
PASS
```

**Confirmation:**

- New test passes
- All existing tests still pass
- No warnings or errors

### REFACTOR - Clean Up

Check for code smells:

- Is there duplicated validation logic elsewhere? -> Extract validation function
- Are there multiple validation checks in submitForm? -> Extract validation module
- Is the error message duplicated? -> Extract constant

**If no smells, done. If smells present:**

```typescript
const ERROR_MESSAGES = {
  EMAIL_REQUIRED: 'Email required',
  EMAIL_INVALID: 'Email must be valid',
};

function validateEmail(email: string | undefined): string | null {
  if (!email?.trim()) {
    return ERROR_MESSAGES.EMAIL_REQUIRED;
  }
  // Future validations go here
  return null;
}

function submitForm(data: FormData) {
  const emailError = validateEmail(data.email);
  if (emailError) {
    return { error: emailError };
  }
  // ... rest of code
}
```

**Run tests again:**

```bash
$ just test
PASS
```

**Commit:**

```bash
git add .
git commit -m "Fix: reject empty email addresses

Adds validation to reject empty or whitespace-only emails.

- Added validateEmail function
- Extracted error message constants
- All tests passing"
```

## Example 2: New Feature (Retry Logic)

**Feature:** Automatically retry failed network operations up to 3 times

### RED - Write First Test

Start with simplest case: successful retry after failures

```typescript
test('retries failed operations up to 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

### Verify RED

```bash
$ just test
ERROR: retryOperation is not defined
```

Fix: Add empty function

```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  throw new Error('not implemented');
}
```

Run again:

```bash
$ just test
FAIL: expected 'success', got Error: not implemented
```

**Now we have proper failure.**

### GREEN - Minimal Implementation

```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```

### Verify GREEN

```bash
$ just test
PASS
```

### RED - Next Test (Max Retries Exhausted)

```typescript
test('throws error after 3 failed attempts', async () => {
  const operation = () => {
    throw new Error('always fails');
  };

  await expect(retryOperation(operation))
    .rejects
    .toThrow('always fails');
});
```

### Verify RED

```bash
$ just test
PASS  retries failed operations up to 3 times
PASS  throws error after 3 failed attempts
```

**Wait - test passed immediately!**

This is good - our implementation already handles this case. But we needed to write the test to verify it.

### RED - Next Test (Succeeds First Time)

```typescript
test('returns immediately on success', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(1);
});
```

### Verify RED

```bash
$ just test
PASS (all tests)
```

Again, implementation already handles this. Test still needed to verify behavior.

### REFACTOR - Review

Check code smells:

- Magic number 3 -> Consider named constant
- No configurability -> YAGNI (not requested)

```typescript
const DEFAULT_MAX_RETRIES = 3;

async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < DEFAULT_MAX_RETRIES; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === DEFAULT_MAX_RETRIES - 1) throw e;
    }
  }
  throw new Error('unreachable');
}
```

Run tests:

```bash
$ just test
PASS (all tests)
```

Commit and done.

## Example 3: Bug Fix with Edge Cases

**Bug:** User registration fails silently when username contains spaces

### RED - Test Current Bug

```typescript
test('rejects username with spaces', async () => {
  const result = await registerUser({ username: 'john doe' });
  expect(result.error).toBe('Username cannot contain spaces');
});
```

### Verify RED

```bash
$ just test
FAIL: expected error, got { success: true, userId: 123 }
```

**Bug confirmed - username with spaces is accepted.**

### GREEN - Fix Bug

```typescript
function registerUser(data: UserData) {
  if (data.username.includes(' ')) {
    return { error: 'Username cannot contain spaces' };
  }
  // ... rest of registration
}
```

### Verify GREEN

```bash
$ just test
PASS
```

### RED - Test Related Edge Cases

Now that we're touching username validation, test other edge cases:

```typescript
test('rejects username with leading whitespace', async () => {
  const result = await registerUser({ username: ' john' });
  expect(result.error).toBe('Username cannot contain spaces');
});

test('rejects username with trailing whitespace', async () => {
  const result = await registerUser({ username: 'john ' });
  expect(result.error).toBe('Username cannot contain spaces');
});

test('accepts username without spaces', async () => {
  const result = await registerUser({ username: 'johndoe' });
  expect(result.success).toBe(true);
});
```

### Verify RED

```bash
$ just test
FAIL: rejects username with leading whitespace
FAIL: rejects username with trailing whitespace
PASS: accepts username without spaces
```

**Good - found more edge cases.**

### GREEN - Fix Edge Cases

```typescript
function registerUser(data: UserData) {
  const username = data.username.trim();
  if (username.includes(' ') || username !== data.username) {
    return { error: 'Username cannot contain spaces' };
  }
  // ... rest of registration
}
```

### Verify GREEN

```bash
$ just test
PASS (all tests)
```

### REFACTOR - Extract Validation

```typescript
function validateUsername(username: string): string | null {
  const trimmed = username.trim();
  if (trimmed.includes(' ') || trimmed !== username) {
    return 'Username cannot contain spaces';
  }
  if (trimmed.length < 3) {
    return 'Username must be at least 3 characters';
  }
  if (trimmed.length > 20) {
    return 'Username must be no more than 20 characters';
  }
  return null;
}

function registerUser(data: UserData) {
  const usernameError = validateUsername(data.username);
  if (usernameError) {
    return { error: usernameError };
  }
  // ... rest of registration
}
```

Run tests:

```bash
$ just test
FAIL: Username must be at least 3 characters
```

**Oops - added validation without tests. This is wrong.**

Revert the extra validations:

```typescript
function validateUsername(username: string): string | null {
  const trimmed = username.trim();
  if (trimmed.includes(' ') || trimmed !== username) {
    return 'Username cannot contain spaces';
  }
  return null;
}
```

Run tests:

```bash
$ just test
PASS (all tests)
```

**Lesson:** Only refactor structure during REFACTOR phase. Don't add new behavior.

If you need length validation, start new RED-GREEN-REFACTOR cycle.

## Example 4: Feature with Dependencies (Payment Processing)

**Feature:** Process payment with Stripe integration

### RED - Test Core Behavior (Mock External Service)

```typescript
test('processes payment successfully', async () => {
  const mockStripeClient = {
    charges: {
      create: jest.fn().resolves({ id: 'ch_123', status: 'succeeded' })
    }
  };

  const result = await processPayment(
    { amount: 1000, currency: 'usd' },
    mockStripeClient
  );

  expect(result.success).toBe(true);
  expect(result.chargeId).toBe('ch_123');
  expect(mockStripeClient.charges.create).toHaveBeenCalledWith({
    amount: 1000,
    currency: 'usd',
  });
});
```

**Note:** Mocking external API is acceptable - Stripe is a boundary.

### Verify RED

```bash
$ just test
ERROR: processPayment is not defined
```

### GREEN - Implement

```typescript
async function processPayment(
  payment: Payment,
  stripeClient: StripeClient
): Promise<PaymentResult> {
  const charge = await stripeClient.charges.create({
    amount: payment.amount,
    currency: payment.currency,
  });

  return {
    success: charge.status === 'succeeded',
    chargeId: charge.id,
  };
}
```

### Verify GREEN

```bash
$ just test
PASS
```

### RED - Test Failure Case

```typescript
test('handles payment failure', async () => {
  const mockStripeClient = {
    charges: {
      create: jest.fn().rejects(new Error('Card declined'))
    }
  };

  const result = await processPayment(
    { amount: 1000, currency: 'usd' },
    mockStripeClient
  );

  expect(result.success).toBe(false);
  expect(result.error).toBe('Card declined');
});
```

### Verify RED

```bash
$ just test
ERROR: Unhandled promise rejection: Card declined
```

### GREEN - Handle Errors

```typescript
async function processPayment(
  payment: Payment,
  stripeClient: StripeClient
): Promise<PaymentResult> {
  try {
    const charge = await stripeClient.charges.create({
      amount: payment.amount,
      currency: payment.currency,
    });

    return {
      success: charge.status === 'succeeded',
      chargeId: charge.id,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}
```

### Verify GREEN

```bash
$ just test
PASS (all tests)
```

### REFACTOR

No obvious code smells. Function is clear, single responsibility, good separation.

Commit and done.

## Example 5: Refactoring Existing Code

**Situation:** Existing function works but has no tests. Need to refactor for clarity.

**Current code:**

```typescript
function calc(a: number, b: number, c: string): number {
  if (c === 'add') return a + b;
  if (c === 'sub') return a - b;
  if (c === 'mul') return a * b;
  if (c === 'div') return a / b;
  return 0;
}
```

**Goal:** Refactor for clarity

### First: Add Tests (Characterization Tests)

Document current behavior before changing:

```typescript
test('adds two numbers', () => {
  expect(calc(5, 3, 'add')).toBe(8);
});

test('subtracts two numbers', () => {
  expect(calc(5, 3, 'sub')).toBe(2);
});

test('multiplies two numbers', () => {
  expect(calc(5, 3, 'mul')).toBe(15);
});

test('divides two numbers', () => {
  expect(calc(6, 3, 'div')).toBe(2);
});

test('returns 0 for unknown operation', () => {
  expect(calc(5, 3, 'unknown')).toBe(0);
});
```

Run tests:

```bash
$ just test
PASS (all tests)
```

**Now we have safety net for refactoring.**

### REFACTOR - Rename Function and Parameters

```typescript
function calculate(left: number, right: number, operation: string): number {
  if (operation === 'add') return left + right;
  if (operation === 'sub') return left - right;
  if (operation === 'mul') return left * right;
  if (operation === 'div') return left / right;
  return 0;
}
```

Update tests to use new name. Run tests:

```bash
$ just test
PASS (all tests)
```

Commit: "Refactor: rename calc to calculate with clearer parameter names"

### REFACTOR - Extract Operation Type

```typescript
type Operation = 'add' | 'sub' | 'mul' | 'div';

function calculate(left: number, right: number, operation: Operation): number {
  if (operation === 'add') return left + right;
  if (operation === 'sub') return left - right;
  if (operation === 'mul') return left * right;
  if (operation === 'div') return left / right;
  return 0;
}
```

Run tests:

```bash
$ just test
FAIL: unknown operation test - TypeScript error
```

Fix test to use valid operation type or adjust signature. Run tests:

```bash
$ just test
PASS (all tests)
```

Commit: "Refactor: add Operation type for type safety"

### REFACTOR - Use Switch Statement

```typescript
function calculate(left: number, right: number, operation: Operation): number {
  switch (operation) {
    case 'add': return left + right;
    case 'sub': return left - right;
    case 'mul': return left * right;
    case 'div': return left / right;
  }
}
```

Run tests:

```bash
$ just test
PASS (all tests)
```

Commit: "Refactor: replace if-chain with switch statement"

**Done - code is clearer, tests prove behavior unchanged.**

## Key Patterns Demonstrated

### Pattern 1: Bug Fix Always Starts with Failing Test

Don't fix the bug then add test. Write test that shows bug, then fix.

### Pattern 2: Test Related Edge Cases Together

When touching validation, test all related edge cases in same cycle.

### Pattern 3: Mock Only at Boundaries

Mock external APIs (Stripe, AWS). Don't mock your own services.

### Pattern 4: Characterization Tests Enable Refactoring

Add tests to existing code first, then refactor safely.

### Pattern 5: Small Commits per Refactoring

Each refactoring step is separate commit. Easy to revert if needed.

### Pattern 6: Tests Stay Green During Refactoring

If test fails during refactoring, revert immediately.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Testing Implementation Details

**Bad:**

```typescript
test('calls validateEmail function', () => {
  const spy = jest.spyOn(validator, 'validateEmail');
  registerUser({ email: 'test@example.com' });
  expect(spy).toHaveBeenCalled();
});
```

**Why bad:** Tests how code works, not what it does. Breaks when refactoring.

**Good:**

```typescript
test('rejects invalid email', () => {
  const result = registerUser({ email: 'invalid' });
  expect(result.error).toBe('Invalid email');
});
```

### Anti-Pattern 2: Multiple Behaviors in One Test

**Bad:**

```typescript
test('user registration works', () => {
  const result = registerUser({ username: 'john', email: 'john@example.com' });
  expect(result.success).toBe(true);
  expect(result.userId).toBeDefined();
  expect(result.email).toBe('john@example.com');
  expect(result.createdAt).toBeInstanceOf(Date);
});
```

**Why bad:** Can't tell which behavior broke when test fails.

**Good:**

```typescript
test('creates user with valid data', () => {
  const result = registerUser({ username: 'john', email: 'john@example.com' });
  expect(result.success).toBe(true);
});

test('returns userId after registration', () => {
  const result = registerUser({ username: 'john', email: 'john@example.com' });
  expect(result.userId).toBeDefined();
});

test('sets createdAt timestamp', () => {
  const result = registerUser({ username: 'john', email: 'john@example.com' });
  expect(result.createdAt).toBeInstanceOf(Date);
});
```

### Anti-Pattern 3: Adding Features During Refactoring

**Bad:**

```typescript
// During refactoring, also added logging
function processPayment(payment: Payment) {
  logger.info('Processing payment', payment); // NEW FEATURE - Don't do this
  // ... existing code
}
```

**Why bad:** Mixed concerns. Can't tell if test failure is from refactoring or new feature.

**Good:**

Refactor first (commit), then add logging in separate cycle (commit).

## Summary

TDD examples demonstrate:

1. **Always start with failing test** (RED)
2. **Verify test fails correctly** (confirm RED)
3. **Write minimal code to pass** (GREEN)
4. **Verify test passes** (confirm GREEN)
5. **Clean up only structure** (REFACTOR)
6. **Test stays green during refactoring** (verify GREEN)
7. **Small commits** (one cycle = one commit)

Following this cycle catches bugs early, enables fearless refactoring, and produces maintainable code.
