# Refactoring Reference

## Overview

Refactoring means changing code structure without changing behavior. Tests prove behavior is unchanged.

**Golden Rule:** Refactor only when all tests are green. If tests fail during refactoring, revert immediately.

## When to Refactor

### Code Smell Checklist

Run through this checklist during the REFACTOR phase of TDD. Each smell has a suggested pattern.

#### Duplication Smells

- [ ] **Duplicated Code** - Same logic in multiple places
  - → See: Extract Method, Extract Class, Pull Up Method

- [ ] **Magic Numbers** - Unexplained numbers throughout code
  - → See: Replace Magic Number with Named Constant

- [ ] **Duplicated Conditional Logic** - Same if/switch in multiple places
  - → See: Replace Conditional with Polymorphism, Extract Method

#### Size Smells

- [ ] **Long Method** - Method > 20 lines
  - → See: Extract Method, Replace Temp with Query

- [ ] **Large Class** - Class > 300 lines or > 10 methods
  - → See: Extract Class, Extract Subclass

- [ ] **Long Parameter List** - Method takes > 3 parameters
  - → See: Introduce Parameter Object, Preserve Whole Object

#### Responsibility Smells

- [ ] **Feature Envy** - Method uses another class more than its own
  - → See: Move Method, Extract Method

- [ ] **Divergent Change** - Class changes for multiple reasons (violates SRP)
  - → See: Extract Class, Extract Interface

- [ ] **Shotgun Surgery** - One change requires many small changes in many classes
  - → See: Move Method, Move Field, Inline Class

#### Data Smells

- [ ] **Data Clumps** - Same group of data items appear together repeatedly
  - → See: Introduce Parameter Object, Extract Class

- [ ] **Primitive Obsession** - Using primitives (strings, numbers) instead of domain objects
  - → See: Replace Data Value with Object, Extract Class

- [ ] **Temporary Field** - Field only used in certain circumstances
  - → See: Extract Class, Replace Method with Method Object

#### Clarity Smells

- [ ] **Comments Explaining Code** - Comments describing what code does (not why)
  - → See: Extract Method, Rename Method, Introduce Assertion

- [ ] **Unclear Names** - Variables/methods/classes with vague names
  - → See: Rename Variable, Rename Method, Rename Class (IDE-assisted)

- [ ] **Dead Code** - Unused variables, methods, classes, parameters
  - → Delete it immediately

#### Conditional Smells

- [ ] **Complex Conditional** - Nested if/switch statements > 2 levels
  - → See: Decompose Conditional, Replace Conditional with Polymorphism

- [ ] **Null Checks** - Checking for null throughout codebase
  - → See: Introduce Null Object, Use Optional/Maybe types

- [ ] **Type Code** - Using strings/enums for behavior that varies by type
  - → See: Replace Type Code with Polymorphism

## Common Refactoring Patterns

### Extract Method

**Smell:** Long method, duplicated code
**When:** Code fragment can be grouped together with clear purpose

**Before:**

```typescript
function printOwing(invoice: Invoice) {
  printBanner();

  // Print details
  console.log(`Name: ${invoice.customer}`);
  console.log(`Amount: ${invoice.getOutstanding()}`);
}
```

**After:**

```typescript
function printOwing(invoice: Invoice) {
  printBanner();
  printDetails(invoice);
}

function printDetails(invoice: Invoice) {
  console.log(`Name: ${invoice.customer}`);
  console.log(`Amount: ${invoice.getOutstanding()}`);
}
```

**Steps:**

1. Create new method with descriptive name
2. Copy code to new method
3. Scan for local variables (become parameters)
4. Replace old code with method call
5. Run tests

### Extract Class

**Smell:** Large class, divergent change, data clumps
**When:** Class has too many responsibilities

**Before:**

```typescript
class Person {
  name: string;
  officeAreaCode: string;
  officeNumber: string;

  getTelephoneNumber(): string {
    return `(${this.officeAreaCode}) ${this.officeNumber}`;
  }
}
```

**After:**

```typescript
class Person {
  name: string;
  officeTelephone: TelephoneNumber;

  getTelephoneNumber(): string {
    return this.officeTelephone.toString();
  }
}

class TelephoneNumber {
  constructor(
    public areaCode: string,
    public number: string
  ) {}

  toString(): string {
    return `(${this.areaCode}) ${this.number}`;
  }
}
```

**Steps:**

1. Create new class for responsibilities
2. Copy fields to new class
3. Update original class to reference new class
4. Move methods to new class
5. Run tests after each move

### Introduce Parameter Object

**Smell:** Long parameter list, data clumps
**When:** Multiple parameters naturally belong together

**Before:**

```typescript
function amountInvoiced(
  startDate: Date,
  endDate: Date,
  customerId: string
): number {
  // ...
}
```

**After:**

```typescript
interface DateRange {
  start: Date;
  end: Date;
}

function amountInvoiced(
  range: DateRange,
  customerId: string
): number {
  // ...
}
```

**Steps:**

1. Create parameter object class/interface
2. Change function signature
3. Update all callers
4. Run tests
5. Consider moving methods to parameter object

### Replace Conditional with Polymorphism

**Smell:** Complex conditionals, type checking
**When:** Behavior varies by type

**Before:**

```typescript
function getSpeed(bird: Bird): number {
  switch (bird.type) {
    case 'European':
      return getBaseSpeed();
    case 'African':
      return getBaseSpeed() - getLoadFactor() * bird.numberOfCoconuts;
    case 'Norwegian':
      return bird.isNailed ? 0 : getBaseSpeed();
  }
}
```

**After:**

```typescript
abstract class Bird {
  abstract getSpeed(): number;
}

class European extends Bird {
  getSpeed(): number {
    return this.getBaseSpeed();
  }
}

class African extends Bird {
  constructor(public numberOfCoconuts: number) {
    super();
  }

  getSpeed(): number {
    return this.getBaseSpeed() - this.getLoadFactor() * this.numberOfCoconuts;
  }
}

class Norwegian extends Bird {
  constructor(public isNailed: boolean) {
    super();
  }

  getSpeed(): number {
    return this.isNailed ? 0 : this.getBaseSpeed();
  }
}
```

**Steps:**

1. Create subclass for each conditional branch
2. Move conditional logic to subclass methods
3. Replace conditional with polymorphic call
4. Run tests after each subclass

### Replace Magic Number with Named Constant

**Smell:** Unexplained numbers in code
**When:** Number has business meaning

**Before:**

```typescript
function potentialEnergy(mass: number, height: number): number {
  return mass * 9.81 * height;
}
```

**After:**

```typescript
const GRAVITATIONAL_CONSTANT = 9.81; // m/s²

function potentialEnergy(mass: number, height: number): number {
  return mass * GRAVITATIONAL_CONSTANT * height;
}
```

**Steps:**

1. Declare constant with descriptive name
2. Replace number with constant
3. Run tests
4. Repeat for all occurrences

### Decompose Conditional

**Smell:** Complex conditional expressions
**When:** Conditions are hard to understand

**Before:**

```typescript
if (date.before(SUMMER_START) || date.after(SUMMER_END)) {
  charge = quantity * winterRate + winterServiceCharge;
} else {
  charge = quantity * summerRate;
}
```

**After:**

```typescript
function isWinter(date: Date): boolean {
  return date.before(SUMMER_START) || date.after(SUMMER_END);
}

if (isWinter(date)) {
  charge = quantity * winterRate + winterServiceCharge;
} else {
  charge = quantity * summerRate;
}
```

**Steps:**

1. Extract condition into method with clear name
2. Extract then-branch into method if complex
3. Extract else-branch into method if complex
4. Run tests after each extraction

### Move Method

**Smell:** Feature envy, shotgun surgery
**When:** Method uses another class more than its own

**Before:**

```typescript
class Account {
  overdraftCharge(): number {
    if (this.type.isPremium()) {
      return this.daysOverdrawn > 7 ? 10 : 0;
    }
    return this.daysOverdrawn * 1.75;
  }
}
```

**After:**

```typescript
class Account {
  overdraftCharge(): number {
    return this.type.overdraftCharge(this.daysOverdrawn);
  }
}

class AccountType {
  overdraftCharge(daysOverdrawn: number): number {
    if (this.isPremium()) {
      return daysOverdrawn > 7 ? 10 : 0;
    }
    return daysOverdrawn * 1.75;
  }
}
```

**Steps:**

1. Copy method to target class
2. Adjust method to work in new class
3. Change original to delegate to new method
4. Run tests
5. Remove original method if appropriate

### Replace Temp with Query

**Smell:** Temporary variable computed once and used multiple times
**When:** Calculation can be extracted to method

**Before:**

```typescript
function getPrice(): number {
  const basePrice = quantity * itemPrice;
  const discountFactor = 0.98;

  if (basePrice > 1000) {
    return basePrice * discountFactor;
  }
  return basePrice;
}
```

**After:**

```typescript
function getPrice(): number {
  if (basePrice() > 1000) {
    return basePrice() * 0.98;
  }
  return basePrice();
}

function basePrice(): number {
  return quantity * itemPrice;
}
```

**Steps:**

1. Extract temp calculation to method
2. Replace temp variable with method calls
3. Run tests
4. Consider inlining constant if used once

### Introduce Null Object

**Smell:** Null checks throughout code
**When:** Null represents absence of object

**Before:**

```typescript
const customer = site.customer;
let name: string;

if (customer === null) {
  name = "occupant";
} else {
  name = customer.name;
}
```

**After:**

```typescript
class NullCustomer extends Customer {
  get name(): string {
    return "occupant";
  }

  isNull(): boolean {
    return true;
  }
}

// Usage
const customer = site.customer; // Never returns null, returns NullCustomer
const name = customer.name; // No null check needed
```

**Steps:**

1. Create null object class
2. Add isNull() method to base class
3. Replace null returns with null object
4. Remove null checks
5. Run tests after each change

### Rename (Variable, Method, Class)

**Smell:** Unclear names
**When:** Name doesn't reveal intent

**Before:**

```typescript
function calc(a: number, b: number): number {
  const x = a * b;
  const y = x * 0.08;
  return x + y;
}
```

**After:**

```typescript
function calculateTotalWithTax(
  subtotal: number,
  quantity: number
): number {
  const baseAmount = subtotal * quantity;
  const taxAmount = baseAmount * TAX_RATE;
  return baseAmount + taxAmount;
}
```

**Steps (Use IDE rename refactoring):**

1. Select symbol to rename
2. Use IDE refactor → rename
3. Enter new descriptive name
4. IDE updates all references
5. Run tests

## Refactoring Safety

### Before Refactoring

- [ ] All tests passing (100% green)
- [ ] No pending changes (clean working directory)
- [ ] Tests cover the behavior being refactored
- [ ] Branch created if refactoring is large (multiple smells)
- [ ] Committed recent work (can revert if needed)

### During Refactoring

- [ ] One small refactoring at a time
- [ ] Run full test suite after each refactoring
- [ ] Commit after each successful refactoring
- [ ] Behavior unchanged (tests prove this)
- [ ] If tests fail, revert immediately and try smaller step
- [ ] No new functionality added during refactoring

### After Refactoring

- [ ] All tests still passing (100% green)
- [ ] Code is clearer than before
- [ ] No behavior changes (only structure changed)
- [ ] Commit with clear refactoring description
- [ ] Ready for next feature or next refactoring

### Emergency Protocol

**If tests fail during refactoring:**

1. **STOP** - Don't try to fix
2. **REVERT** - `git reset --hard` or undo changes
3. **THINK** - What went wrong? Step too big?
4. **SMALLER STEP** - Break refactoring into smaller pieces
5. **TRY AGAIN** - One tiny change at a time

**Never:**

- Fix failing tests by changing test expectations
- Continue refactoring when tests are red
- Add functionality while refactoring
- Skip running tests "because it's obvious"

## IDE-Assisted Refactorings (Safe)

Modern IDEs provide automated refactorings that are safer than manual changes.

### TypeScript/JavaScript (VS Code, WebStorm)

**Extract Method/Function:**

- Select code block
- Right-click → Refactor → Extract Method
- Name the extracted method
- IDE handles parameters and return values

**Rename:**

- Select variable/function/class
- F2 or Right-click → Rename
- IDE updates all references

**Move to File:**

- Select class/function
- Right-click → Move to new file
- IDE handles imports

**Inline Variable:**

- Select variable
- Right-click → Inline Variable
- IDE replaces all uses with expression

### Python (PyCharm, VS Code)

**Extract Method:**

- Select code
- Ctrl+Alt+M (PyCharm) or Refactor menu
- IDE preserves function behavior

**Rename:**

- Select symbol
- Shift+F6 (PyCharm) or F2 (VS Code)
- Updates all references

**Change Signature:**

- Select function
- Ctrl+F6 (PyCharm)
- Add/remove/reorder parameters safely

### Ruby (RubyMine, VS Code)

**Extract Method:**

- Select code
- Ctrl+Alt+M
- IDE handles block parameters

**Rename:**

- Select symbol
- Shift+F6
- Updates throughout project

## Manual Refactorings (Test-First)

Some refactorings require manual work. Follow this process:

### Process for Manual Refactoring

1. **Ensure tests green** - All tests passing
2. **One change** - Make one small structural change
3. **Run tests** - Verify behavior unchanged
4. **Commit** - Commit this small refactoring
5. **Repeat** - Next small change

### Extract Class (Manual Process)

```
1. Create new class (empty)
2. Run tests (should still pass)
3. Add first field to new class
4. Update original class to use new class
5. Run tests
6. Commit
7. Move first method to new class
8. Run tests
9. Commit
10. Repeat for remaining fields/methods
```

### Replace Conditional with Polymorphism (Manual Process)

```
1. Create abstract base class
2. Run tests
3. Create first subclass with one branch
4. Run tests
5. Commit
6. Update factory to return subclass for that case
7. Run tests
8. Commit
9. Repeat for remaining branches
10. Remove original conditional
11. Run tests
12. Commit
```

## Language-Specific Patterns

### TypeScript/JavaScript

**Replace Loop with Pipeline:**

```typescript
// Before
const results = [];
for (const item of items) {
  if (item.active) {
    results.push(item.name);
  }
}

// After
const results = items
  .filter(item => item.active)
  .map(item => item.name);
```

**Replace Callback with Promise:**

```typescript
// Before
function getData(callback: (data: Data) => void) {
  fetchData((result) => {
    callback(result);
  });
}

// After
async function getData(): Promise<Data> {
  return await fetchData();
}
```

**Use Optional Chaining:**

```typescript
// Before
const street = user && user.address && user.address.street;

// After
const street = user?.address?.street;
```

### Python

**Replace Loop with Comprehension:**

```python
# Before
results = []
for item in items:
    if item.active:
        results.append(item.name)

# After
results = [item.name for item in items if item.active]
```

**Use Context Manager:**

```python
# Before
file = open('data.txt')
try:
    data = file.read()
finally:
    file.close()

# After
with open('data.txt') as file:
    data = file.read()
```

**Replace Type Check with Duck Typing:**

```python
# Before
if isinstance(obj, SpecificClass):
    obj.method()

# After
if hasattr(obj, 'method'):
    obj.method()
```

### Ruby

**Replace Loop with Enumerable:**

```ruby
# Before
results = []
items.each do |item|
  results << item.name if item.active
end

# After
results = items.select(&:active).map(&:name)
```

**Use Symbol to Proc:**

```ruby
# Before
items.map { |item| item.name }

# After
items.map(&:name)
```

**Extract Module for Shared Behavior:**

```ruby
# Before (duplicated in multiple classes)
class User
  def full_name
    "#{first_name} #{last_name}"
  end
end

# After
module Nameable
  def full_name
    "#{first_name} #{last_name}"
  end
end

class User
  include Nameable
end
```

## Refactoring Anti-Patterns

### DON'T: Refactor and Add Features Simultaneously

**Wrong:**

```typescript
// Started refactoring extracting method
// Then added new feature while refactoring
function processOrder(order: Order) {
  validateOrder(order); // Extracted method (refactoring)

  // Added new logging feature (new functionality!)
  logOrderToAnalytics(order); // NEW FEATURE - DON'T DO THIS

  submitOrder(order);
}
```

**Right:**

```typescript
// First: Refactor only (commit)
function processOrder(order: Order) {
  validateOrder(order); // Extracted method
  submitOrder(order);
}

// Then: Add feature (separate commit)
function processOrder(order: Order) {
  validateOrder(order);
  logOrderToAnalytics(order); // Added in separate commit
  submitOrder(order);
}
```

### DON'T: Fix Failing Tests by Changing Assertions

**Wrong:**

```typescript
// Test fails after refactoring
test('calculates total', () => {
  const result = calculateTotal(10, 2);
  // Test failed expecting 20, got 12
  // Changed assertion to make test pass
  expect(result).toBe(12); // WRONG - changed behavior
});
```

**Right:**

```typescript
// Test fails after refactoring
// REVERT the refactoring
// Fix the bug first, then refactor correctly
test('calculates total', () => {
  const result = calculateTotal(10, 2);
  expect(result).toBe(20); // Correct assertion
});
```

### DON'T: Skip Tests "Because It's Obvious"

**Wrong:**

```typescript
// "This is obviously correct, no need to run tests"
function extractedMethod() {
  // ... refactored code
}
// Commit without running tests
```

**Right:**

```typescript
// Extract method
function extractedMethod() {
  // ... refactored code
}
// ALWAYS run full test suite
// npm test
// ✓ All tests pass
// THEN commit
```

## Checklist: Am I Refactoring Correctly?

Before claiming "refactoring complete," verify:

- [ ] Started with all tests green
- [ ] Made only structural changes (no new features)
- [ ] Ran tests after each small change
- [ ] All tests still passing (100% green)
- [ ] Committed each successful refactoring
- [ ] Code is clearer than before
- [ ] Behavior is exactly the same (tests prove it)
- [ ] No "emergency fixes" mixed with refactoring
- [ ] Used IDE refactoring tools where available
- [ ] Reverted immediately when tests failed

If you can't check ALL boxes, you're not refactoring correctly.

## Resources

**Books:**

- "Refactoring" by Martin Fowler (2nd edition, includes JavaScript examples)
- "Working Effectively with Legacy Code" by Michael Feathers

**Online:**

- Refactoring.com (Fowler's catalog of refactorings)
- SourceMaking.com/refactoring (visual examples)

**Remember:**

- Refactoring is about structure, not behavior
- Tests are your safety net
- Small steps are safer than big leaps
- IDE refactorings are safer than manual changes
- When in doubt, revert and try smaller
