# Phase 4 - dbt Test Syntax Deprecation

## Context
Implementing dbt mart models with `accepted_values` tests for tier columns (safety_tier, income_quintile, amenity_tier) that should only contain values 1-5.

## Problem
dbt 1.9+ introduced a deprecation warning for generic test arguments. The old syntax:

```yaml
tests:
  - accepted_values:
      values: [1, 2, 3, 4, 5]
```

Produces deprecation warnings:
```
MissingArgumentsPropertyInGenericTestDeprecation: Arguments to generic tests should be nested under the `arguments` property.
```

## Solution
Nest test arguments under the `arguments` property:

```yaml
tests:
  - accepted_values:
      arguments:
        values: [1, 2, 3, 4, 5]
```

This applies to all generic tests with arguments, not just `accepted_values`.

## Prevention
- When writing dbt schema YAML files, always use the `arguments:` nesting for generic tests
- Run `dbt parse --no-partial-parse` to catch all deprecation warnings before they become errors
- Check dbt changelog when upgrading versions for breaking changes to test syntax

## Tags
dbt, testing, yaml, deprecation, syntax, schema
