# Low-level design — {{project}}

> Every section is numbered and self-contained, so a task can be briefed with only the
> sections it needs (e.g. `LLD §2.1, §4`). Each module section holds its responsibility,
> interfaces, contracts and schema in one place; it refers to other modules only by number.
> **Numbers are stable**: at milestone as-built syncs and change requests, update sections in
> place and give new sections new numbers. Never renumber; mark removed sections `(removed)`.

## §0 Overview
### §0.1 Stack
| Layer | Choice | Why | Rejected alternative |
|---|---|---|---|

### §0.2 Folder structure
```
```

### §0.3 Layer map and module dependencies
<!-- which § depends on which §; dependency direction; composition root -->

### §0.4 Packages
| Package | Version | Purpose | Alternative rejected |
|---|---|---|---|

### §0.5 Config and secrets
<!-- env vars (all in .env.example); never commit .env -->

## §1 {{Module name}}
- **Responsibility:** {{one sentence}}
- **Path(s):** `{{src/module/}}`
- **Depends on:** {{§n interfaces only, or "none"}}

### §1.1 Interfaces / signatures
```
{{class / function signatures with types}}
```

### §1.2 Contracts
| Method | Path / event | Request | Response | Errors |
|---|---|---|---|---|

### §1.3 Data / schema owned
```mermaid
erDiagram
```

### §1.4 Key sequence
```mermaid
sequenceDiagram
```

### §1.5 Errors and edge cases
-

## §2 {{Module name}}
<!-- same shape as §1; drop sub-sections that don't apply, keep the numbers of the rest -->

## Changes since last milestone
| Milestone | Section | Change | Why | Ref |
|---|---|---|---|---|
