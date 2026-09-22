# Carbon-Auditor: Coding Standards

## 1. Purpose

This document establishes the coding conventions, formatting rules, and structural guidelines for developers contributing to the Carbon-Auditor platform. Strict adherence ensures codebase maintainability, readability, and fewer merge conflicts.

## 2. General Principles

*   **Readability Over Cleverness**: Code is read vastly more often than it is written. Avoid overly complex one-liners.
*   **Single Source of Truth**: Do not duplicate business logic. If a calculation is needed in two places, abstract it into a shared utility or service.
*   **Fail Fast**: Validate inputs immediately at the controller layer (using Pydantic). Do not let dirty data reach the database.

## 3. Python Standards (Backend)

The backend is written in Python 3.10+. We enforce strict typing and standardized formatting.

### 3.1. Formatting and Linting
*   **Formatter**: `Black` (Line length: 88).
*   **Linter**: `Flake8` and `mypy` (for static type checking).
*   All code must pass `black --check .` and `mypy .` in the CI pipeline before merging.

### 3.2. Type Hinting
Type hints are mandatory for all function signatures (arguments and return types).

**Correct:**
```python
def calculate_emissions(consumption: float, factor: float) -> float:
    return round(consumption * factor, 2)
```

**Incorrect:**
```python
def calculate_emissions(consumption, factor):
    return round(consumption * factor, 2)
```

### 3.3. Naming Conventions
*   Variables, functions, and methods: `snake_case`
*   Classes and Exceptions: `PascalCase`
*   Constants (Module level): `UPPER_SNAKE_CASE`

### 3.4. Docstrings
Use Google-style docstrings for all modules, classes, and public functions.

```python
def process_bill(s3_key: str) -> dict:
    """
    Extracts text from a bill in S3 and returns structured data.

    Args:
        s3_key (str): The object key of the bill in the S3 uploads bucket.

    Returns:
        dict: The structured JSON data extracted by the LLM.
        
    Raises:
        OCRProcessingError: If PaddleOCR fails to read the document.
    """
```

## 4. JavaScript/Frontend Standards

If the frontend is implemented as a Vanilla JS SPA or a React app, the following apply:

### 4.1. Formatting
*   **Formatter**: `Prettier`
*   **Linter**: `ESLint`

### 4.2. ES6+ Features
*   Use `const` by default, `let` only when reassignment is necessary. Never use `var`.
*   Use arrow functions `() => {}` for callbacks and anonymous functions.
*   Use `async/await` syntax for all API calls instead of `.then()` chains to prevent callback hell.

### 4.3. DOM Manipulation (If Vanilla JS)
*   Prefix all variables holding DOM elements with a `$` to distinguish them from data variables.
    ```javascript
    const $uploadForm = document.getElementById('upload-form');
    ```

## 5. Git and Version Control

*   **Branch Naming**: `type/issue-number-short-desc`
    *   `feature/12-add-aws-s3-upload`
    *   `bugfix/34-fix-ocr-timeout`
    *   `docs/45-update-readme`
*   **Commit Messages**: Follow Conventional Commits specification.
    *   `feat: add pdf support for ocr`
    *   `fix: resolve null pointer in carbon calc engine`
*   **Pull Requests**: All PRs must have at least one approving review and pass all CI checks before merging into `main`. No direct commits to `main`.
