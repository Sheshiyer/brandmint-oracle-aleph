```markdown
# brandmint-oracle-aleph Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `brandmint-oracle-aleph` Python codebase. You'll learn how to structure files, write imports and exports, follow commit message conventions, and understand the project's approach to testing and workflows.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `data_processor.py`, `user_service.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import calculate_total
    from ..models import User
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['MyClass', 'my_function']
    ```

### Commit Messages
- Follow the **Conventional Commits** standard.
- Use the `feat` prefix for new features.
  - Example:
    ```
    feat: add support for user authentication
    ```

## Workflows

### Feature Development
**Trigger:** When adding a new feature  
**Command:** `/feature-development`

1. Create a new Python file using snake_case if needed.
2. Write code using relative imports and named exports.
3. Commit changes using the `feat` prefix and a concise message.
   - Example: `feat: implement transaction validation`
4. (Optional) Add or update test files as needed.

### Code Organization
**Trigger:** When structuring or refactoring code  
**Command:** `/organize-code`

1. Ensure all files follow snake_case naming.
2. Refactor imports to use relative paths.
3. Explicitly define exports with `__all__` in modules.

## Testing Patterns

- **Framework:** Unknown (not detected)
- **Test File Pattern:** Files end with `.test.ts`
  - Example: `user_service.test.ts`
- Tests may be written in TypeScript, indicating possible cross-language testing or legacy files.
- No specific Python testing framework detected.

## Commands
| Command                | Purpose                                      |
|------------------------|----------------------------------------------|
| /feature-development   | Steps to add a new feature                   |
| /organize-code         | Ensure code organization and conventions     |
```
