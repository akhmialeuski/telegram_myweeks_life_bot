# Git Hooks in the Project

This project uses git hooks for automatic code quality checks before commits.

## Installed Hooks

### Pre-commit Hook

File: `.git/hooks/pre-commit`

This hook automatically runs before each commit and performs the following checks:

1. **Black** - code formatting check
2. **isort** - import sorting check
3. **flake8** - code style check
4. **pytest** - unit tests execution
5. **coverage** - code coverage check (warning, doesn't block commit)

## How it Works

### When attempting to commit:

```bash
git commit -m "Your commit message"
```

Git will automatically run the pre-commit hook, which:

- ✅ If all checks pass - commit will be created
- ❌ If there are errors - commit will be cancelled with detailed problem description

### Example output with errors:

```
🔍 Running pre-commit checks...
📝 Checking code formatting (black)...
❌ Black found formatting issues!
⚠️  Run 'black .' to fix automatically
```

## Fixing Issues

### Automatic formatting fix:

```bash
./scripts/fix_code_style.sh
```

This script will automatically fix:
- Code formatting (black)
- Import sorting (isort)

### Manual fixing:

```bash
# Fix formatting
black .

# Fix imports
isort .

# Check code style (needs manual fixing)
flake8 .

# Run tests
pytest tests/
```

## Configuration

### Black (pyproject.toml)
- Line length: 88 characters
- Python versions: 3.8-3.11

### isort (pyproject.toml)
- Profile: black
- Line length: 88 characters
- Automatic sorting by sections

### flake8 (.flake8)
- Line length: 88 characters
- Ignores conflicts with black
- Maximum complexity: 10

### pytest (pyproject.toml)
- Tests in `tests/` folder
- Verbose output
- Markers for different test types

## Disabling Hook (not recommended)

If you need to temporarily disable the pre-commit hook:

```bash
git commit --no-verify -m "Your message"
```

⚠️ **Warning**: Use only in extreme cases!

## Adding New Checks

To add new checks to the pre-commit hook:

1. Edit the file `.git/hooks/pre-commit`
2. Add the new check in the appropriate section
3. Make sure the check returns the correct exit code

## Troubleshooting

### Hook doesn't run:
1. Check permissions: `ls -la .git/hooks/pre-commit`
2. Make sure the file is executable: `chmod +x .git/hooks/pre-commit`

### Virtual environment errors:
1. Activate virtual environment: `source .venv/bin/activate`
2. Make sure all dependencies are installed: `pip install -r requirements-dev.txt`

### Slow performance:
1. Check that unnecessary folders are excluded in configuration
2. Consider caching results

## Useful Commands

```bash
# Check all linters manually
black --check .
isort --check-only .
flake8 .

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# Quick check of only changed files
git diff --cached --name-only | xargs black --check
```