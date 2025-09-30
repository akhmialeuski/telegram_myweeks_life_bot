# Git Hooks in the Project

This project uses git hooks for automatic code quality checks before commits to ensure consistent code style and prevent regressions.

## Installed Hooks

### Pre-commit Hook

File: `.git/hooks/pre-commit`

This hook automatically runs before each commit and performs comprehensive quality checks:

1. **Black** - Code formatting (PEP 8 compliant)
2. **isort** - Import sorting and organization
3. **flake8** - Code style and complexity checks
4. **pytest** - Unit and integration tests execution
5. **coverage** - Code coverage reporting (minimum 80% required)

## How it Works

### Automatic Execution

When attempting to commit:

```bash
git commit -m "feat: add new feature"
```

Git automatically runs the pre-commit hook sequence:

- ✅ **All checks pass** → Commit created successfully
- ❌ **Any check fails** → Commit cancelled with detailed error report

### Sample Output

**Success case:**
```
🔍 Running pre-commit checks...
📝 Checking code formatting (black)... ✅
📦 Checking import sorting (isort)... ✅
🔍 Checking code style (flake8)... ✅
🧪 Running tests... ✅
📊 Checking code coverage... ✅
🚀 All checks passed! Commit allowed.
```

**Error case:**
```
🔍 Running pre-commit checks...
📝 Checking code formatting (black)... ❌
❌ Black found formatting issues!
⚠️  Run 'black .' to fix automatically
```

## Fixing Issues

### Quick Fix (Recommended)

```bash
# Fix all formatting and import issues automatically
./scripts/fix_code_style.sh
```

This script automatically fixes:
- Code formatting with black
- Import organization with isort

### Manual Fixing

```bash
# Fix code formatting
black .

# Fix import organization
isort .

# Check for style issues (manual fixing required)
flake8 .

# Run complete test suite
pytest tests/

# Run tests with coverage report
pytest tests/ --cov=. --cov-report=html
```

## Configuration

### Black (pyproject.toml)
- **Line length**: 88 characters
- **Python versions**: 3.8-3.12
- **String quotes**: Double quotes preferred
- **Multi-line expressions**: Trailing comma allowed

### isort (pyproject.toml)
- **Profile**: black (compatible formatting)
- **Line length**: 88 characters
- **Sections**: FUTURE, STDLIB, THIRDPARTY, FIRSTPARTY, LOCALFOLDER
- **Multi-line imports**: 3 lines per import group

### flake8
- **Line length**: 88 characters
- **Maximum complexity**: 10 (functions with higher complexity flagged)
- **Error codes ignored**: E203, E501, W503 (conflicts with black)
- **Extensions**: flake8-bugbear, flake8-comprehensions

### pytest (pyproject.toml)
- **Test discovery**: `tests/` directory
- **Python path**: `.` and `src`
- **Markers**:
  - `slow`: Marks tests as slow (deselect with `-m "not slow"`)
  - `integration`: Marks tests as integration tests
  - `unit`: Marks tests as unit tests
- **Coverage**: Minimum 80% required for commit

## Development Workflow

### Before Committing

```bash
# 1. Make your code changes
# 2. Fix any style issues
./scripts/fix_code_style.sh

# 3. Run tests locally
pytest tests/ --cov=. --cov-report=term-missing

# 4. Commit (hooks will run automatically)
git add .
git commit -m "feat: add new feature"
```

### Working with Virtual Environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run tests in virtual environment
pytest tests/
```

## Disabling Hook (Emergency Only)

⚠️ **Warning**: Use only in extreme emergency situations!

```bash
git commit --no-verify -m "fix: emergency patch"
```

**Never disable hooks for regular development** - they prevent technical debt and ensure code quality.

## Adding New Checks

To add new quality checks:

1. Edit `.git/hooks/pre-commit`
2. Add the new check in the appropriate section
3. Ensure proper error handling and exit codes
4. Test the hook thoroughly

Example new check:
```bash
# Add security scan
echo "🔒 Checking for security issues..."
if command -v safety >/dev/null 2>&1; then
    safety check || exit 1
else
    echo "⚠️  Security scanner not available"
fi
```

## Troubleshooting

### Hook Doesn't Execute
```bash
# Check hook permissions
ls -la .git/hooks/pre-commit

# Make executable if needed
chmod +x .git/hooks/pre-commit
```

### Virtual Environment Issues
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Verify all dependencies installed
pip list | grep -E "(black|isort|flake8|pytest)"

# Check Python version
python --version  # Should be 3.12+
```

### Performance Issues
- Tests are optimized to run only changed files when possible
- Coverage excludes virtual environments and build artifacts
- Consider running tests in parallel: `pytest -n auto`

### Common Error Patterns

**Import errors in tests:**
```bash
# Ensure src/ is in Python path
export PYTHONPATH="${PYTHONPATH}:src"

# Or run tests from project root
cd /path/to/project && pytest tests/
```

**Encoding issues:**
```bash
# Ensure UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

## Quality Gates Summary

| Check | Tool | Purpose | Exit Code |
|-------|------|---------|-----------|
| Formatting | black | PEP 8 compliance | ❌ on issues |
| Imports | isort | Import organization | ❌ on issues |
| Style | flake8 | Code quality | ❌ on issues |
| Tests | pytest | Functionality | ❌ on failures |
| Coverage | coverage | Test completeness | ⚠️ on <80% |

## Integration with CI/CD

These same checks run in GitHub Actions on every push and pull request:

- **Pull Requests**: All checks must pass before merge
- **Main Branch**: Protected from direct pushes
- **Release Branches**: Additional security scanning

## Useful Commands

```bash
# Manual quality checks
black --check --diff .
isort --check-only --diff .
flake8 .

# Quick test run for changed files
git diff --name-only | grep "\.py$" | xargs pytest

# Full test suite with coverage
pytest tests/ --cov=. --cov-report=html --cov-fail-under=80

# Development mode (skip coverage check)
pytest tests/ --no-cov

# Check specific test file
pytest tests/test_bot/test_settings_handler.py -v
```

**Note**: The pre-commit hook is essential for maintaining code quality. Always fix issues before committing rather than disabling the hook.