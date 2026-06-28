# Code Examples: OKF vs Traditional Methods

This directory contains working implementations of both approaches to demonstrate the practical differences between traditional database/API architectures and the OKF (Open Knowledge Format) approach.

## Files

### `okf_vs_traditional.py`
**Python implementation** demonstrating:
- Traditional approach: REST API client with multiple network calls
- OKF approach: File system-based semantic navigation
- Error handling and validation patterns
- Performance comparison and metrics

**Usage:**
```bash
# Run the comparison
python okf_vs_traditional.py

# Output shows:
# - API call metrics
# - Network latency measurements
# - File I/O performance
# - Relationship traversal patterns
```

**Key Classes:**
- `TraditionalCustomerRepository`: Simulates REST API with network latency
- `OKFCustomerRepository`: Demonstrates file system-based approach

**Features Demonstrated:**
- Context window assembly (multi-call vs. single-file)
- Error handling patterns (API errors vs. file I/O errors)
- Validation and data integrity
- Relationship discovery and traversal

---

### `okf_vs_traditional.ts`
**TypeScript/JavaScript implementation** demonstrating:
- Traditional approach: HTTP REST client pattern
- OKF approach: Async file system with lazy loading
- Type-safe interfaces and validation schema
- Performance metrics collection

**Usage:**
```bash
# Node.js with ES modules support
node --input-type=module okf_vs_traditional.ts

# Or build with TypeScript compiler
tsc okf_vs_traditional.ts
node okf_vs_traditional.js
```

**Key Classes:**
- `TraditionalApiClient`: REST API client simulation
- `OKFFileSystemRepository`: File system repository with caching
- `OKFValidationSchema`: Type-safe validation without database constraints

**Features Demonstrated:**
- Type-safe data structures (TypeScript interfaces)
- Async error handling patterns
- Validation without database constraints
- In-memory caching for performance

---

## Performance Metrics

All examples include timing instrumentation to measure:

| Metric | Traditional | OKF | Difference |
|--------|---|---|---|
| **Customer fetch** | 150ms (3 API calls) | 5-10ms (1 file read) | **15-30x faster** |
| **API calls** | 3 calls | 0-1 calls | **67-100% fewer** |
| **Relationship discovery** | Requires schema knowledge | Automatic via `_references` | **Built-in** |
| **Error handling** | Network-specific | File I/O specific | **Simpler** |

---

## How to Run These Examples

### Option 1: Python (Recommended for exploring)
```bash
cd code-examples/
python okf_vs_traditional.py
```

**Output:**
```
======================================================================
OKF vs Traditional Methods - Python Implementation Comparison
======================================================================

[APPROACH 1: TRADITIONAL REST API]
----------------------------------------------------------------------

[TRADITIONAL] Fetching customer cust_123...
  ✓ Made 3 API calls, 150ms latency

Customer: Acme Corp
Contracts: 2 active
Contacts: 2 people

Performance:
  - API calls: 3
  - Network latency: 150ms
  - Total fetch time: 157ms

[APPROACH 2: OKF FILE SYSTEM]
----------------------------------------------------------------------

[OKF] Fetching customer acme-corp...
  ✓ Made 1 file reads, 5.2ms I/O

Customer: Acme Corp
Relationships defined: 2
  - contracts_active
  - contacts

Performance:
  - File reads: 1
  - I/O time: 5.2ms
  - Total fetch time: 8ms

[PERFORMANCE COMPARISON]
----------------------------------------------------------------------

Traditional Approach:
  - Network latency: 150ms
  - API calls required: 3

OKF Approach:
  - I/O latency: 5ms
  - File reads required: 1

Speedup: 15.0x faster with OKF
```

### Option 2: TypeScript (Recommended for type safety)
```bash
cd code-examples/

# Install TypeScript if needed
npm install -g typescript

# Run
ts-node okf_vs_traditional.ts

# Or compile and run
tsc okf_vs_traditional.ts
node okf_vs_traditional.js
```

---

## Key Learnings from Examples

### 1. API Call Multiplier Effect
Traditional approach makes separate API calls for each data type:
```python
# Call 1: Get customer info
customer = get_customer(id)

# Call 2: Get contracts  
contracts = get_contracts(id)

# Call 3: Get contacts
contacts = get_contacts(id)

# Total: 3 × 50ms = 150ms latency
```

OKF loads everything semantically:
```python
# Single read
customer = load("customers/2024/{id}/metadata.okf.yaml")

# Relationships known immediately
relationships = customer._references

# Lazy load only what's needed
# Total: 1 × 5ms = 5ms latency
```

### 2. Relationship Visibility
**Traditional:** Relationships are implicit (foreign keys, API docs)
```sql
SELECT * FROM customers c
LEFT JOIN contracts ct ON c.id = ct.customer_id
WHERE c.id = 'cust_123'
```
Must know schema before querying.

**OKF:** Relationships are explicit
```yaml
_references:
  - relation: "contracts_active"
    target: "/customers/2024/acme-corp/contracts/active.okf.yaml"
```
Just read `_references` to discover what's available.

### 3. Error Handling Patterns
Both examples show how error handling differs:

**Traditional (Network-level errors):**
```python
try:
    response = requests.get(api_url)
except ConnectionError:
    # Network is down, retry strategy
except Timeout:
    # Request timed out
except HTTPError as e:
    # API returned error (429, 500, etc.)
```

**OKF (File-level errors):**
```python
try:
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
except FileNotFoundError:
    # File doesn't exist
except yaml.YAMLError:
    # YAML is malformed
```

File errors are more predictable and easier to handle.

---

## Extending These Examples

### Add New Data Types
```python
# Traditional: Add new API endpoint
def get_customer_invoices(customer_id):
    return requests.get(f"/api/customers/{customer_id}/invoices").json()

# OKF: Just add a new file relationship
# /customers/2024/acme-corp/financial/invoices.okf.yaml
# No code changes needed - just add the file!
```

### Add Validation
```python
# Traditional: Application-level validation
if not customer['name']:
    raise ValueError("Customer name is required")

# OKF: Validation schema
OKFValidationSchema = {
    "name": lambda x: len(x) > 0,
    "revenue": lambda x: x > 0,
}
```

### Add Caching
```python
# Traditional: Cache at HTTP layer
@cache(ttl=300)
def get_customer_cached(customer_id):
    return requests.get(f"/api/customers/{customer_id}").json()

# OKF: Cache at file layer (built into most implementations)
file_cache.get(file_path)  # Already cached from previous read
```

---

## Real-World Adaptations

### Integration with Actual File Systems
```python
# Replace simulated file I/O with real system:
import os
import yaml

with open(f"/data/okf-repo/customers/{year}/{id}/metadata.okf.yaml") as f:
    customer = yaml.safe_load(f)
```

### Integration with Cloud Storage (S3)
```python
import boto3

s3 = boto3.client('s3')
response = s3.get_object(
    Bucket='okf-repo',
    Key=f'customers/{year}/{id}/metadata.okf.yaml'
)
customer = yaml.safe_load(response['Body'].read())
```

### Integration with HTTP (if not using filesystem)
```python
# OKF can also work over HTTP (using the same semantic paths)
response = requests.get(
    "https://api.company.com/okf/customers/2024/acme-corp/metadata"
)
customer = response.json()
```

---

## Performance Testing

Both examples include instrumentation to measure:
- **API calls / File reads**: How many I/O operations are performed
- **Network latency / I/O time**: Actual time spent in I/O
- **Total fetch time**: End-to-end time including data assembly

Run the examples multiple times to see consistency in timing.

---

## Questions & Troubleshooting

**Q: Why is OKF faster?**
A: File I/O is 10-100x faster than network I/O. One semantic lookup replaces multiple API calls.

**Q: Won't file system have hot spots?**
A: Cloud storage (S3, GCS) with CDN handles billions of files efficiently. Performance is per-file, not total-volume dependent.

**Q: How do I validate OKF data without a database schema?**
A: Use validation schemas (shown in TypeScript example) or JSON Schema files alongside your OKF files.

**Q: Can I use OKF with real-time data?**
A: Yes, but for high-frequency updates (>1000/second), use a database for that workload and export to OKF for knowledge management.

---

## Next Steps

1. **Run the examples** to see the performance differences
2. **Modify the examples** to match your data structures
3. **Review** the parent directory files for architectural context
4. **Review** [evaluation-framework.md](../evaluation-framework.md) for decision matrices
5. **Consider** a hybrid approach: database for transactions, OKF for knowledge

---

## References

- [comparison.md](../comparison.md) - Full architectural comparison
- [evaluation-framework.md](../evaluation-framework.md) - Decision matrix and quantitative metrics
- Related work: WP-1.4 (Prompt Engineering as Code), WP-2.1 (Memory Architectures)
