## Good Tests
**Integration-style**: Test through real interfaces, not mocks of internal parts.
### TypeScript
```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```
### .NET (xUnit)
```c#
// GOOD: Tests observable behavior
[Fact]
public async Task User_can_checkout_with_valid_cart()
{
    var cart = CreateCart();
    cart.Add(product);

    var result = await _checkoutService.Checkout(cart, paymentMethod);

    Assert.Equal("confirmed", result.Status);
}
```
Characteristics:
- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test
## Bad Tests
**Implementation-detail tests**: Coupled to internal structure.
### TypeScript
```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```
### .NET (xUnit + Moq)
```c#
// BAD: Tests implementation details
[Fact]
public async Task Checkout_calls_payment_service_process()
{
    var mockPayment = new Mock<IPaymentService>();
    var sut = new CheckoutService(mockPayment.Object);

    await sut.Checkout(cart, payment);

    mockPayment.Verify(p => p.Process(cart.Total), Times.Once);
}
```
Red flags:
- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface
### TypeScript
```typescript
// BAD: Bypasses interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: Verifies through interface
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```
### .NET (xUnit)
```c#
// BAD: Bypasses interface to verify
[Fact]
public async Task CreateUser_saves_to_database()
{
    await _userService.CreateUser(new CreateUserRequest("Alice"));

    using var conn = new SqlConnection(connString);
    var row = await conn.QuerySingleAsync("SELECT * FROM Users WHERE Name = @Name", new { Name = "Alice" });
    Assert.NotNull(row);
}

// GOOD: Verifies through interface
[Fact]
public async Task CreateUser_makes_user_retrievable()
{
    var user = await _userService.CreateUser(new CreateUserRequest("Alice"));

    var retrieved = await _userService.GetUser(user.Id);

    Assert.Equal("Alice", retrieved.Name);
}
```
