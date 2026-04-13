# Testing Anti-Patterns

Common mistakes and how to avoid them. Use these "gates" to catch bad tests before writing them.

## Anti-Pattern 1: Testing Mock Behavior

### The Problem

```typescript
// ❌ BAD: Testing that the mock exists
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**Why this is wrong:**

- You verify the mock works, not the component
- Test passes when mock is present, fails when not
- Tells nothing about real behavior

### The Fix

```typescript
// ✅ GOOD: Test real component or don't mock it
test('renders sidebar', () => {
  render(<Page />);  // Don't mock sidebar
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});

// OR if sidebar MUST be mocked for isolation:
// Assert nothing on mock - test Page's behavior with sidebar present
```

### Gate Function

```
BEFORE asserting on any mock element:
  Ask: "Am I testing real component behavior or just mock existence?"

  IF testing mock existence:
    STOP - Delete the assertion or unmock the component

  Test real behavior instead
```

---

## Anti-Pattern 2: Test-Only Methods in Production

### The Problem

```python
# ❌ BAD: destroy() only used in tests
class Session:
    async def destroy(self):  # Looks like production API!
        await self._workspaceManager?.destroyWorkspace(self.id)
        # ... cleanup

# In tests
afterEach(() => session.destroy())
```

**Why this is wrong:**

- Production class polluted with test-only code
- Dangerous if accidentally called in production
- Violates YAGNI and separation of concerns
- Confuses object lifecycle with entity lifecycle

### The Fix

```python
# ✅ GOOD: Test utilities handle test cleanup
# Session has no destroy() - it's stateless in production

# test_utils.py
async def cleanup_session(session: Session):
    workspace = session.get_workspace_info()
    if workspace:
        await workspace_manager.destroy_workspace(workspace.id)

# In tests
afterEach(() => cleanup_session(session))
```

### Gate Function

```
BEFORE adding any method to production class:
  Ask: "Is this only used by tests?"

  IF yes:
    STOP - Add nothing
    Put it in test utilities instead

  Ask: "Does this class own this resource's lifecycle?"

  IF no:
    STOP - Wrong class for this method
```

---

## Anti-Pattern 3: Mocking Without Understanding

### The Problem

```typescript
// ❌ BAD: Mock breaks test logic
test('detects duplicate server', () => {
  // Mock prevents config write that test depends on!
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));

  await addServer(config);
  await addServer(config);  // Should throw - but won't!
});
```

**Why this is wrong:**

- Mocked method had side effect test depended on (writing config)
- Over-mocking to "be safe" breaks actual behavior
- Test passes for wrong reason or fails mysteriously

### The Fix

```typescript
// ✅ GOOD: Mock at correct level
test('detects duplicate server', () => {
  // Mock the slow part, preserve behavior test needs
  vi.mock('MCPServerManager'); // Just mock slow server startup

  await addServer(config);  // Config written
  await addServer(config);  // Duplicate detected ✓
});
```

### Gate Function

```
BEFORE mocking any method:
  STOP - Mock nothing yet

  1. Ask: "What side effects does real method have?"
  2. Ask: "Does this test depend on any side effects?"
  3. Ask: "Do I fully understand what this test needs?"

  IF depends on side effects:
    Mock at lower level (the actual slow/external operation)
    OR use test doubles that preserve necessary behavior
    NOT the high-level method the test depends on

  IF unsure what test depends on:
    Run test with real implementation FIRST
    Observe what actually needs to happen
    THEN add minimal mocking at the right level

  Red flags:
    - "I'll mock this to be safe"
    - "This might be slow, better mock it"
    - Mocking without understanding the dependency chain
```

---

## Anti-Pattern 4: Incomplete Mocks

### The Problem

```typescript
// ❌ BAD: Partial mock - only fields you think you need
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' }
  // Missing: metadata that downstream code uses
};

// Later: breaks when code accesses response.metadata.requestId
```

**Why this is wrong:**

- Partial mocks hide structural assumptions
- Downstream code may depend on omitted fields
- Tests pass but integration fails
- False confidence - test proves nothing about real behavior

### The Fix

```typescript
// ✅ GOOD: Mirror real API completeness
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: {
    requestId: 'req-789',
    timestamp: 1234567890,
    version: 'v1'
  },
  links: {
    self: '/api/users/123',
    profile: '/api/users/123/profile'
  }
  // All fields real API returns
};
```

### Gate Function

```
BEFORE creating mock responses:
  Check: "What fields does the real API response contain?"

  Actions:
    1. Examine actual API response from docs/examples
    2. Include ALL fields system might consume downstream
    3. Verify mock matches real response schema completely

  Critical:
    If you're creating a mock, you must understand the ENTIRE structure
    Partial mocks fail silently when code depends on omitted fields

  If uncertain: Include all documented fields
```

---

## Anti-Pattern 5: Testing Implementation Details

### The Problem

```python
# ❌ BAD: Testing private method calls
def test_user_service_calls_validate_email():
    service._validate_email = Mock()  # Testing internal detail!
    service.create({"email": "alice@example.com", "name": "Alice"})
    service._validate_email.assert_called_once()
```

**Why this is wrong:**

- Test coupled to implementation (private method)
- Breaks when you refactor internal structure
- Doesn't test actual behavior
- Makes refactoring difficult

### The Fix

```python
# ✅ GOOD: Test public behavior
def test_user_service_rejects_invalid_email():
    with pytest.raises(ValidationError, match="Invalid email"):
        service.create({"email": "not-an-email", "name": "Alice"})
```

### Gate Function

```
BEFORE asserting on any internal/private method:
  Ask: "Am I testing public behavior or implementation detail?"

  IF testing private method/internal structure:
    STOP - Rewrite test to verify public behavior

  Rule: If test breaks when you refactor without changing behavior,
        it's testing implementation
```

---

## Anti-Pattern 6: Over-Mocking

### The Problem

```python
# ❌ BAD: Mocking everything
@patch('UserService')
@patch('EmailService')
@patch('Database')
@patch('Cache')
@patch('Logger')
def test_registration(mock_logger, mock_cache, mock_db, mock_email, mock_user):
    # Test setup is now more complex than implementation!
    mock_user.return_value = Mock(id="123")
    mock_db.return_value = Mock()
    mock_email.send = Mock()
    # ... 20 more lines of mock setup
    ...
```

**Why this is wrong:**

- Mock setup more complex than code being tested
- Not testing real component interactions
- Brittle - breaks when implementation changes
- Obscures what's actually being tested

### The Fix

```python
# ✅ GOOD: Integration test with real components
def test_registration(db_session):
    # Real service, real database, mock only external boundary
    with patch('EmailService.send') as mock_email:
        service = UserService(db_session)
        user = service.register({
            "email": "alice@example.com",
            "password": "secret123",
            "name": "Alice"
        })

        assert user.id is not None
        mock_email.assert_called_once()  # Verify email sent
```

### Gate Function

```
BEFORE adding more than 2-3 mocks to a test:
  STOP - This is probably over-mocking

  Ask: "Would an integration test be simpler?"

  Consider:
    - Integration test with real components often clearer
    - Mock only true external boundaries (APIs, email)
    - Use in-memory implementations (database, cache)

  If mock setup > test logic:
    Rewrite as integration test
```

---

## Anti-Pattern 7: Coupled Tests

### The Problem

```python
# ❌ BAD: Tests depend on execution order
class TestUserWorkflow:
    def test_1_create_user(self):
        self.user = service.create(...)  # Shared state!

    def test_2_update_user(self):
        service.update(self.user.id, ...)  # Depends on test_1

    def test_3_delete_user(self):
        service.delete(self.user.id)  # Depends on test_1 and test_2
```

**Why this is wrong:**

- Tests must run in specific order
- Cannot run single test in isolation
- One failure breaks all subsequent tests
- Impossible to parallelize
- Hard to debug

### The Fix

```python
# ✅ GOOD: Each test is independent
class TestUserWorkflow:
    def test_create_user_sets_required_fields(self):
        user = service.create({"email": "alice@example.com", "name": "Alice"})
        assert user.id is not None
        assert user.email == "alice@example.com"

    def test_update_user_changes_name(self):
        # Create user in THIS test
        user = service.create({"email": "bob@example.com", "name": "Bob"})
        # Update it
        updated = service.update(user.id, {"name": "Robert"})
        assert updated.name == "Robert"

    def test_delete_user_removes_from_database(self, db_session):
        # Create user in THIS test
        user = service.create({"email": "charlie@example.com", "name": "Charlie"})
        # Delete it
        service.delete(user.id)
        # Verify it's gone
        assert db_session.query(User).filter_by(id=user.id).first() is None
```

### Gate Function

```
BEFORE using self.* or class variables in tests:
  Ask: "Does another test depend on this state?"

  IF yes:
    STOP - Tests are coupled
    Each test should create its own data

  Use fixtures or setup methods to create fresh state per test
```

---

## Anti-Pattern 8: Testing Multiple Behaviors

### The Problem

```python
# ❌ BAD: One test doing too much
def test_user_crud_operations():
    # Create
    user = service.create({...})
    assert user.id is not None

    # Read
    found = service.get(user.id)
    assert found.email == user.email

    # Update
    updated = service.update(user.id, {"name": "Bob"})
    assert updated.name == "Bob"

    # Delete
    service.delete(user.id)
    assert service.get(user.id) is None
```

**Why this is wrong:**

- Which behavior failed? Have to read entire test
- Testing 4 different behaviors in one test
- If first assertion fails, rest don't run
- Hard to understand test intent

### The Fix

```python
# ✅ GOOD: One behavior per test
def test_create_user_generates_unique_id():
    user = service.create({"email": "alice@example.com", "name": "Alice"})
    assert user.id is not None

def test_get_user_by_id_returns_correct_user():
    user = service.create({"email": "bob@example.com", "name": "Bob"})
    found = service.get(user.id)
    assert found.email == "bob@example.com"

def test_update_user_changes_name():
    user = service.create({"email": "charlie@example.com", "name": "Charlie"})
    updated = service.update(user.id, {"name": "Charles"})
    assert updated.name == "Charles"

def test_delete_user_removes_from_database(db_session):
    user = service.create({"email": "david@example.com", "name": "David"})
    service.delete(user.id)
    assert db_session.query(User).filter_by(id=user.id).first() is None
```

### Gate Function

```
BEFORE writing assertions:
  Count behaviors being tested

  IF > 1 unrelated behavior:
    STOP - Split into separate tests

  Exception: Multiple assertions verifying SAME behavior are OK
  Example: assert user.id, assert user.email, assert user.name
           (all verify "user creation populates fields")
```

---

## Anti-Pattern 9: Slow Unit Tests

### The Problem

```python
# ❌ BAD: Unit test hitting real database
def test_validate_email_format():
    # Test takes 100ms because it hits database!
    user = User(email="invalid-email")
    db.session.add(user)
    with pytest.raises(IntegrityError):
        db.session.commit()
```

**Why this is wrong:**

- Unit test should be < 10ms (this is 100ms)
- Unit test shouldn't need database
- Slow tests = slow feedback loop
- Tests run less frequently if they're slow

### The Fix

```python
# ✅ GOOD: Pure validation logic
def test_validate_email_format():
    # Test takes < 1ms - no database needed
    with pytest.raises(ValidationError, match="Invalid email format"):
        validate_email("invalid-email")
```

### Gate Function

```
BEFORE running unit tests:
  Time them: pytest --durations=10

  IF any unit test > 50ms:
    STOP - Investigate why it's slow
    - Hitting database? → Extract logic or make it integration test
    - Hitting network? → Mock external API
    - Complex computation? → Optimize or make it integration test

  Target: Unit tests < 10ms each
```

---

## Anti-Pattern 10: Test Duplication Across Levels

### The Problem

```python
# ❌ BAD: Same flow tested at all three levels

# Unit test
def test_user_registration_works():
    user = register_user({"email": "alice@example.com", "password": "secret123"})
    assert user.id is not None

# Integration test
def test_user_registration_works(db_session):
    user = register_user({"email": "alice@example.com", "password": "secret123"})
    assert db_session.query(User).filter_by(email=user.email).first() is not None

# E2E test
def test_user_registration_works(browser):
    browser.goto('/register')
    browser.fill('[name=email]', 'alice@example.com')
    browser.fill('[name=password]', 'secret123')
    browser.click('text=Register')
    assert browser.is_visible('text=Welcome')
```

**Why this is wrong:**

- Testing same flow three times
- Maintenance burden (change one thing, update three tests)
- Wastes time (slow tests running redundant checks)
- Doesn't add value

### The Fix

```python
# ✅ GOOD: Different aspects at each level

# Unit - Validation logic only
def test_registration_validates_email_format():
    with pytest.raises(ValidationError):
        validate_email("invalid-email")

def test_registration_hashes_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)

# Integration - Service + database
def test_user_service_creates_user_in_database(db_session):
    service = UserService(db_session)
    user = service.register({"email": "alice@example.com", "password": "secret123"})
    # Verify persistence and password hashing
    db_user = db_session.query(User).filter_by(id=user.id).first()
    assert db_user.password != "secret123"

# E2E - Complete user flow
def test_user_can_register_and_login(browser):
    # Full journey: register → logout → login
    browser.goto('/register')
    browser.fill('[name=email]', 'alice@example.com')
    browser.fill('[name=password]', 'secret123')
    browser.click('text=Register')
    browser.click('text=Logout')
    browser.fill('[name=email]', 'alice@example.com')
    browser.fill('[name=password]', 'secret123')
    browser.click('text=Login')
    assert browser.is_visible('text=Welcome back')
```

### Gate Function

```
BEFORE writing a test:
  Ask: "Is this behavior already tested at another level?"

  IF yes:
    Ask: "Am I testing a DIFFERENT aspect of this behavior?"

    IF no:
      STOP - You're duplicating tests
      Remove duplicate or test different aspect

  Guidelines:
    - Unit: Logic correctness
    - Integration: Component interactions
    - E2E: User experience
```

---

## Anti-Pattern 11: Testing the Framework

### The Problem

```python
# ❌ BAD: Testing that pytest works
def test_fixture_works(db_session):
    assert db_session is not None
    assert isinstance(db_session, Session)

# ❌ BAD: Testing that SQLAlchemy works
def test_orm_saves_data(db_session):
    user = User(email="alice@example.com")
    db_session.add(user)
    db_session.commit()
    assert db_session.query(User).count() == 1  # Testing ORM!

# ❌ BAD: Testing that React renders
test('component renders', () => {
  const { container } = render(<Button />);
  expect(container.firstChild).toBeInTheDocument();  // Testing React!
});
```

**Why this is wrong:**

- Framework is already tested by its maintainers
- Wastes time and adds no value
- Gives false sense of test coverage

### The Fix

```python
# ✅ GOOD: Test YOUR business logic
def test_user_service_validates_duplicate_email(db_session):
    service = UserService(db_session)
    service.create({"email": "alice@example.com", "name": "Alice"})

    with pytest.raises(ValidationError, match="Email already exists"):
        service.create({"email": "alice@example.com", "name": "Bob"})

# ✅ GOOD: Test YOUR component behavior
test('button shows loading state when clicked', async () => {
  render(<SubmitButton />);
  fireEvent.click(screen.getByRole('button'));
  expect(screen.getByText('Loading...')).toBeInTheDocument();
});
```

### Gate Function

```
BEFORE writing a test:
  Ask: "Am I testing MY code or the framework?"

  If testing:
    - That fixtures work → Delete test
    - That ORM saves data → Delete test
    - That framework renders → Delete test
    - Standard library functions → Delete test

  Test YOUR logic using the framework
```

---

## Red Flags Summary

Watch for these warning signs:

| Red Flag | What It Means | Fix |
|----------|---------------|-----|
| Assertion on `*-mock` | Testing mock behavior | Test real component or unmock |
| Methods only in test files | Test-only production methods | Move to test utilities |
| Mock setup > test logic | Over-mocking | Use integration test |
| Test breaks on refactor | Testing implementation | Test behavior instead |
| Tests run in order | Coupled tests | Make independent |
| One failure causes cascade | Shared state | Use fixtures |
| Can't explain mock | Mocking without understanding | Understand first, then mock |
| Test takes seconds | Wrong test level | Move to integration/e2e |
| Testing framework features | Not testing your code | Test your logic |
| Same test at all levels | Duplication | Test different aspects |

---

## When Mocks Become Too Complex

**Warning signs:**

- Mock setup longer than test logic
- Mocking everything to make test pass
- Mocks missing methods real components have
- Test breaks when mock changes
- Need mocks for mocks

**Solution:**
Consider integration tests with real components - often simpler than complex mocks.

---

**See [SKILL.md](SKILL.md) for core principles and [examples.md](examples.md) for comprehensive code examples.**
