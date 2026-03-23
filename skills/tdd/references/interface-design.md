Good interfaces make testing natural:
**1. Accept dependencies, don't create them**
### TypeScript
```typescript
// Testable
function processOrder(order, paymentGateway) {}

// Hard to test
function processOrder(order) {
  const gateway = new StripeGateway();
}
```
### .NET
```c#
// Testable — gateway injected via constructor
public class OrderProcessor
{
    private readonly IPaymentGateway _gateway;
    public OrderProcessor(IPaymentGateway gateway) => _gateway = gateway;

    public Task<OrderResult> ProcessOrder(Order order)
        => _gateway.Charge(order.Total);
}

// Hard to test — gateway created internally
public class OrderProcessor
{
    public Task<OrderResult> ProcessOrder(Order order)
    {
        var gateway = new StripeGateway();
        return gateway.Charge(order.Total);
    }
}
```
**2. Return results, don't produce side effects**
### TypeScript
```typescript
// Testable
function calculateDiscount(cart): Discount {}

// Hard to test
function applyDiscount(cart): void {
  cart.total -= discount;
}
```
### .NET
```c#
// Testable — pure function, returns a result
public Discount CalculateDiscount(Cart cart)
    => new Discount(cart.Items.Count > 5 ? 0.1m : 0m);

// Hard to test — mutates input, returns nothing
public void ApplyDiscount(Cart cart)
{
    cart.Total -= discount;
}
```
**3. Small surface area**
- Fewer methods = fewer tests needed
- Fewer params = simpler test setup
**4. Prefer explicit interfaces over marker/tag patterns**
### .NET
```c#
// GOOD: Explicit, testable contract
public interface IDiscountCalculator
{
    Discount Calculate(Cart cart);
}

// AVOID: Empty marker interface with runtime discovery
public interface IDiscountRule { }
```
