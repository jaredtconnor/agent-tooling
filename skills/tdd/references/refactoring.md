After TDD cycle, look for:
- **Duplication** → Extract function/class
- **Long methods** → Break into private helpers (keep tests on public interface)
- **Shallow modules** → Combine or deepen
- **Feature envy** → Move logic to where data lives
- **Primitive obsession** → Introduce value objects
- **Existing code** the new code reveals as problematic
## Examples
### TypeScript — Primitive obsession → Value object
```typescript
// BEFORE: Primitives scattered through codebase
function createOrder(userId: string, amount: number, currency: string) { ... }

// AFTER: Value object captures intent and validation
class Money {
  constructor(readonly amount: number, readonly currency: string) {
    if (amount < 0) throw new Error("Amount cannot be negative");
  }
}
function createOrder(userId: string, price: Money) { ... }
```
### .NET — Primitive obsession → Value object
```c#
// BEFORE: Raw primitives, no validation at boundaries
public OrderResult CreateOrder(string userId, decimal amount, string currency) { ... }

// AFTER: Value object enforces invariants once
public record Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        if (amount < 0) throw new ArgumentException("Amount cannot be negative");
        Amount = amount;
        Currency = currency ?? throw new ArgumentNullException(nameof(currency));
    }
}

public OrderResult CreateOrder(string userId, Money price) { ... }
```
### .NET — Feature envy → Move logic to where data lives
```c#
// BEFORE: Service reaches into Order's internals
public class InvoiceService
{
    public decimal CalculateTotal(Order order)
        => order.Items.Sum(i => i.Price * i.Quantity) - order.DiscountAmount + order.TaxAmount;
}

// AFTER: Order owns its own total calculation
public class Order
{
    public decimal Total => Items.Sum(i => i.Price * i.Quantity) - DiscountAmount + TaxAmount;
}
```
