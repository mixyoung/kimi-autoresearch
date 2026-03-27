# Scenario Mode Protocol

Scenario mode is an autonomous scenario exploration engine that generates comprehensive test scenarios, edge cases, and use cases from a seed scenario.

## Quick Start

```
$kimi-autoresearch:scenario
Seed: User checkout flow
Depth: deep
Iterations: 25
```

## Overview

Takes a seed scenario and iteratively generates situations across **12 dimensions**:

1. **Happy paths** - Normal, expected usage
2. **Error cases** - Expected failures and error handling
3. **Edge cases** - Boundary conditions and extremes
4. **Abuse cases** - Malicious or unintended usage
5. **Scale cases** - High volume, concurrency, load
6. **Concurrency** - Race conditions, simultaneous access
7. **Temporal** - Time-based scenarios (delays, timeouts, scheduling)
8. **Data variation** - Different data types, sizes, formats
9. **Permissions** - Authorization, access control scenarios
10. **Integrations** - External system interactions
11. **Recovery** - Failure recovery, rollback scenarios
12. **State transitions** - Complex multi-step workflows

## Usage

```
$kimi-autoresearch:scenario
Seed: User attempts to checkout with multiple payment methods
Iterations: 25
```

## Process

### Phase 1: Seed Analysis

Analyze the seed scenario:

1. **Identify actors**: Who is involved?
2. **Identify actions**: What are they doing?
3. **Identify objects**: What data/systems are involved?
4. **Identify context**: When/where is this happening?

Example:
```
Seed: "User attempts to checkout with multiple payment methods"

Actors: User, Payment Gateway, System
Actions: Select payment, Enter details, Process payment, Handle failure
Objects: Shopping cart, Payment methods, Orders
Context: E-commerce checkout flow
```

### Phase 2: Dimension Decomposition

For each of the 12 dimensions, generate relevant scenarios:

#### Happy Paths

| # | Scenario |
|---|----------|
| 1 | User successfully pays with single credit card |
| 2 | User splits payment between two cards |
| 3 | User pays with saved payment method |
| 4 | User applies discount code and pays |

#### Error Cases

| # | Scenario |
|---|----------|
| 1 | First card declined, second succeeds |
| 2 | Both cards declined |
| 3 | Payment gateway timeout |
| 4 | Invalid CVV entered |
| 5 | Expired card used |

#### Edge Cases

| # | Scenario |
|---|----------|
| 1 | Split payment with $0.01 on one card |
| 2 | 100 items in cart with split payment |
| 3 | Payment with exactly card limit amount |
| 4 | International card with currency conversion |

#### Abuse Cases

| # | Scenario |
|---|----------|
| 1 | Rapid-fire payment attempts (DoS) |
| 2 | Stolen card testing multiple amounts |
| 3 | Man-in-the-middle payment interception |
| 4 | Replay attack with captured payment token |

#### Scale Cases

| # | Scenario |
|---|----------|
| 1 | 1000 simultaneous checkouts |
| 2 | Black Friday traffic spike |
| 3 | Payment processing queue backup |
| 4 | Database connection pool exhaustion |

#### Concurrency

| # | Scenario |
|---|----------|
| 1 | Same card used in two simultaneous checkouts |
| 2 | Cart modified during payment processing |
| 3 | Double-submit button click |
| 4 | Session expires during payment |

#### Temporal

| # | Scenario |
|---|----------|
| 1 | Payment during maintenance window |
| 2 | Retry after 30-second timeout |
| 3 | Session timeout mid-checkout |
| 4 | Rate limit hit, retry after cooldown |

#### Data Variation

| # | Scenario |
|---|----------|
| 1 | Unicode characters in cardholder name |
| 2 | Very long (100 char) email address |
| 3 | Special characters in shipping address |
| 4 | Null/empty optional fields |

#### Permissions

| # | Scenario |
|---|----------|
| 1 | Guest checkout vs authenticated |
| 2 | Corporate account with spending limits |
| 3 | Parental control blocks payment |
| 4 | Region-restricted payment method |

#### Integrations

| # | Scenario |
|---|----------|
| 1 | Payment gateway API down |
| 2 | Webhook delivery failure |
| 3 | Tax calculation service timeout |
| 4 | Inventory system out of sync |

#### Recovery

| # | Scenario |
|---|----------|
| 1 | Payment succeeds but order fails to create |
| 2 | Network error during payment confirmation |
| 3 | Partial payment processed, retry needed |
| 4 | Refund after successful payment |

#### State Transitions

| # | Scenario |
|---|----------|
| 1 | Cart → Shipping → Payment → Confirmation |
| 2 | Payment pending → Processing → Completed |
| 3 | Payment → Failed → Retry → Success |
| 4 | Multi-step: Auth → Capture → Settlement |

### Phase 3: Iterative Generation

Each iteration:

1. **Select dimension**: Round-robin or priority-based
2. **Generate scenario**: Create specific, detailed scenario
3. **Classify**: Is this new, variant, or duplicate?
4. **Expand**: For edge cases, expand to sub-scenarios
5. **Log**: Record in scenario log

### Phase 4: Classification

| Classification | Criteria |
|---------------|----------|
| **New** | Entirely new situation |
| **Variant** | Similar to existing but different parameters |
| **Duplicate** | Already covered by existing scenario |

### Phase 5: Output Generation

Generate output based on `--format`:

#### Use Cases Format

```markdown
## UC-001: Successful Single Card Payment

**Actor**: Registered User  
**Precondition**: User has items in cart, valid saved card  
**Postcondition**: Order created, payment processed  

**Flow**:
1. User navigates to checkout
2. System displays saved payment methods
3. User selects card ending in 4242
4. User confirms payment
5. System processes payment via Stripe
6. System creates order
7. System sends confirmation email

**Extensions**:
- 5a. Payment declined → Display error, allow retry
```

#### Test Scenarios Format

```markdown
## TS-001: Single Card Payment Success

**Priority**: P1  
**Type**: Happy Path  

**Setup**:
- User: registered_customer_1
- Cart: 3 items, total $150.00
- Payment: Visa ending in 4242

**Steps**:
1. Navigate to /checkout
2. Select saved card
3. Click "Pay Now"
4. Wait for processing

**Expected**:
- Redirect to /order-confirmation
- Order status: paid
- Email received
- Inventory decremented

**Cleanup**:
- Refund order
- Clear test data
```

#### Threat Scenarios Format

```markdown
## TH-001: Payment DoS Attack

**Threat**: Availability  
**Severity**: High  

**Attack**: Attacker scripts rapid payment attempts  

**Impact**:
- Payment gateway rate limited
- Legitimate users cannot checkout
- Revenue loss

**Mitigation**:
- Rate limiting per IP
- CAPTCHA after 3 failures
- Alert on anomaly detection
```

## Commands

### Basic Usage

```
$kimi-autoresearch:scenario
Seed: User registration flow
```

### With Options

```
$kimi-autoresearch:scenario
Seed: API authentication
Depth: deep
Format: test-scenarios
Focus: security
Iterations: 50
```

### Options

| Option | Description | Values |
|--------|-------------|--------|
| `--depth` | Exploration depth | shallow(10), standard(25), deep(50+) |
| `--format` | Output format | use-cases, test-scenarios, threat-scenarios, user-stories |
| `--focus` | Prioritize areas | edge-cases, failures, security, scale |
| `--domain` | Domain context | software, product, business, security, marketing |
| `--scope` | Limit scope | file glob pattern |

## Domain-Specific Adaptations

### Software Domain

Focus: API, data flow, error handling
- Input validation scenarios
- API versioning scenarios
- Database transaction scenarios

### Product Domain

Focus: User journey, feature interaction
- Onboarding flows
- Feature discovery
- Upgrade/downgrade paths

### Business Domain

Focus: Processes, compliance, operations
- Approval workflows
- Audit trail scenarios
- Regulatory compliance

### Security Domain

Focus: Threats, vulnerabilities, controls
- Authentication bypass
- Privilege escalation
- Data exfiltration

### Marketing Domain

Focus: Campaigns, channels, conversion
- A/B test scenarios
- Multi-channel attribution
- Funnel drop-off

## Chaining with Other Modes

Scenario → Debug:
```
$kimi-autoresearch:scenario --focus edge-cases
# ...generates scenarios...
$kimi-autoresearch:debug --from-scenario
# ...hunts bugs in edge cases...
```

Scenario → Security:
```
$kimi-autoresearch:scenario --format threat-scenarios
$kimi-autoresearch:security --threats from-scenario
```

## Output Files

- `scenario-exploration-{timestamp}.md` - All scenarios
- `scenario-summary.json` - Statistics and coverage
- `scenarios/*.md` - Individual scenario files by category
