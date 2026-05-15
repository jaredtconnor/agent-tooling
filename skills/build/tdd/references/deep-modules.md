From "A Philosophy of Software Design":
**Deep module** = small interface + lots of implementation
```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
│                     │
└─────────────────────┘
```
**Shallow module** = large interface + little implementation (avoid)
```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```
When designing interfaces, ask:
- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?
## Examples
### TypeScript
```typescript
// DEEP: Simple interface hides complex retry/caching/auth logic
const dataClient = {
  getReport: (id: string) => Promise<Report>,
};

// SHALLOW: Caller must orchestrate everything
const dataClient = {
  authenticate: () => Promise<Token>,
  buildQuery: (id: string) => Query,
  execute: (query: Query, token: Token) => Promise<RawData>,
  parseResponse: (data: RawData) => Report,
  handleRetry: (fn: () => Promise<any>, retries: number) => Promise<any>,
};
```
### .NET
```c#
// DEEP: One method, complex logic hidden inside
public interface IReportGenerator
{
    Task<Report> Generate(ReportRequest request);
}

// SHALLOW: Caller must orchestrate each step
public interface IReportGenerator
{
    Task<ReportData> FetchData(ReportRequest request);
    ReportLayout BuildLayout(ReportData data);
    byte[] Render(ReportLayout layout, OutputFormat format);
    Task<string> Upload(byte[] content, string destination);
    Task Notify(string reportUrl, IReadOnlyList<string> recipients);
}
```
