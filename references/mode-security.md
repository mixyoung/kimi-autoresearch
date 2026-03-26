# Security Mode Protocol

Security mode performs read-only security audits using multiple frameworks.

## Frameworks

### STRIDE Threat Modeling

| Category | Description | What to Look For |
|----------|-------------|------------------|
| **S**poofing | Impersonation | Auth bypass, weak auth, session issues |
| **T**ampering | Data modification | Input validation, integrity checks |
| **R**epudiation | Deny actions | Logging, audit trails |
| **I**nformation Disclosure | Data leakage | Sensitive data exposure, error messages |
| **D**enial of Service | System unavailability | Resource exhaustion, rate limiting |
| **E**levation of Privilege | Unauthorized access | Access control, authorization checks |

### OWASP Top 10 (2021)

1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, NoSQL, Command, etc.)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable and Outdated Components
7. Identification and Authentication Failures
8. Software and Data Integrity Failures
9. Security Logging and Monitoring Failures
10. Server-Side Request Forgery (SSRF)

### Red-Team Personas

Analyze from 4 hostile perspectives:

1. **Script Kiddie**: Automated tools, known exploits
2. **Insider Threat**: Internal access, knowledge of system
3. **Sophisticated Attacker**: Custom exploits, patience, resources
4. **Nation State**: Advanced persistent threat, unlimited resources

## Process

### Phase 1: Asset Inventory

Identify valuable assets:
- User data (PII, credentials)
- Financial data
- Authentication tokens
- API keys/secrets
- Business logic
- Infrastructure

### Phase 2: Trust Boundaries

Map trust boundaries:
- Public internet → Load balancer
- Load balancer → Application
- Application → Database
- Application → External APIs
- User input → All processing

### Phase 3: Threat Modeling

For each STRIDE category:
1. Identify potential threats
2. Map to code locations
3. Assess likelihood and impact
4. Prioritize by risk

### Phase 4: Code Analysis

Scan for patterns:

**Injection vulnerabilities:**
```javascript
// BAD: String concatenation
db.query("SELECT * FROM users WHERE id = " + userId);

// GOOD: Parameterized query
db.query("SELECT * FROM users WHERE id = ?", [userId]);
```

**Authentication issues:**
```javascript
// BAD: Weak comparison
if (token == expectedToken)  // type coercion risk

// GOOD: Strict comparison + timing-safe
if (crypto.timingSafeEqual(token, expectedToken))
```

**Path traversal:**
```javascript
// BAD: User input in path
fs.readFile(`./uploads/${req.query.file}`);

// GOOD: Path validation
const safePath = path.join('./uploads', path.basename(req.query.file));
```

### Phase 5: Iterative Deepening

Each iteration focuses on one threat:

1. **Select threat**: Highest priority from STRIDE/OWASP
2. **Locate in code**: Find all occurrences
3. **Verify exploitability**: Is it actually exploitable?
4. **Document finding**: File:line + attack scenario
5. **Rate severity**: Critical/High/Medium/Low

## Evidence Requirements

Every finding MUST include:

1. **File and line**: `src/api/auth.ts:42`
2. **Vulnerability type**: SQL Injection, XSS, etc.
3. **Attack scenario**: Step-by-step exploitation
4. **Code snippet**: Vulnerable code
5. **Remediation**: Suggested fix

**No theoretical findings** - every issue must be backed by code evidence.

## Severity Ratings

| Severity | Criteria | Example |
|----------|----------|---------|
| **Critical** | Direct exploit, no auth needed, data breach | SQL injection in public API |
| **High** | Exploitable with low privilege, significant impact | Stored XSS |
| **Medium** | Requires specific conditions, limited impact | Weak password policy |
| **Low** | Best practice violation, minimal impact | Verbose error messages |
| **Info** | Defense in depth suggestion | Missing security headers |

## Output

Security mode produces:
1. `security-audit-{date}/`
   - `findings.md`: All findings with evidence
   - `summary.md`: Executive summary
   - `remediation.md`: Prioritized fix list
   - `stride-analysis.md`: Threat model

## Read-Only by Default

Security mode does NOT modify code unless:
- User explicitly requests: `--fix`
- Only Critical/High findings are auto-fixed
- Each fix is verified before keeping

## Chaining

Security → Fix:
```
$kimi-autoresearch:security --fix
```

Auto-fix Critical/High findings after audit.
