Mock at **system boundaries** only:
- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)
Don't mock:
- Your own classes/modules
- Internal collaborators
- Anything you control
## Designing for Mockability
At system boundaries, design interfaces that are easy to mock:
**1. Use dependency injection**
Pass external dependencies in rather than creating them internally.
### TypeScript
```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```
### .NET
```c#
// Easy to mock — dependency is injected via constructor
public class PaymentProcessor
{
    private readonly IPaymentClient _paymentClient;

    public PaymentProcessor(IPaymentClient paymentClient)
    {
        _paymentClient = paymentClient;
    }

    public Task<PaymentResult> ProcessPayment(Order order)
        => _paymentClient.Charge(order.Total);
}

// Hard to mock — dependency is created internally
public class PaymentProcessor
{
    public Task<PaymentResult> ProcessPayment(Order order)
    {
        var client = new StripeClient(Environment.GetEnvironmentVariable("STRIPE_KEY"));
        return client.Charge(order.Total);
    }
}
```
**2. Prefer SDK-style interfaces over generic fetchers**
Create specific functions for each external operation instead of one generic function with conditional logic.
### TypeScript
```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```
### .NET
```c#
// GOOD: Each method is independently mockable via interface
public interface IUserApi
{
    Task<User> GetUser(Guid id);
    Task<IReadOnlyList<Order>> GetOrders(Guid userId);
    Task<Order> CreateOrder(CreateOrderRequest data);
}

// BAD: Generic method requires conditional setup in tests
public interface IApiClient
{
    Task<T> Send<T>(string endpoint, HttpMethod method, object? body = null);
}
```
The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint
## Mocking in .NET Tests
When you do need a mock at a system boundary, prefer thin interfaces + constructor injection:
```c#
// In test: provide a fake at the boundary
[Fact]
public async Task Notifies_user_on_successful_order()
{
    var fakeNotifier = new Mock<INotificationService>();
    var sut = new OrderService(fakeNotifier.Object);

    await sut.PlaceOrder(validOrder);

    fakeNotifier.Verify(n => n.Send(It.Is<Notification>(
        msg => msg.UserId == validOrder.UserId)), Times.Once);
}
```
Prefer **test doubles you control** (fakes, stubs) over heavy mocking frameworks when the boundary interface is simple enough:
```c#
// A hand-rolled fake is often clearer than Moq setup
public class FakeNotificationService : INotificationService
{
    public List<Notification> Sent { get; } = new();
    public Task Send(Notification notification)
    {
        Sent.Add(notification);
        return Task.CompletedTask;
    }
}
```
