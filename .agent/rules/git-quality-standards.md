---
alwaysApply: true
---

# Git and Code Quality Standards

## Git Commit Rules

### Pre-commit Hook Requirements
- **NEVER use `--no-verify` flag when committing**
- **ALWAYS ensure all pre-commit checks pass before committing**
- **NEVER skip code quality checks or formatting validation**
- **ALWAYS fix formatting issues (black, flake8) before committing**
- **NEVER bypass security or quality gates**

### Required Pre-commit Checks
Before any commit, ensure:
- [ ] Code formatting passes (black)
- [ ] Linting passes (flake8)
- [ ] All tests pass
- [ ] No security vulnerabilities detected
- [ ] Code quality standards are met

### Commit Process
1. **Always run pre-commit checks first**
2. **Fix any issues found by the checks**
3. **Only commit when all checks pass**
4. **Never use `--no-verify` to bypass checks**
5. **Maintain code quality standards at all times**

### Quality Enforcement
- **Code quality is non-negotiable**
- **All formatting and linting errors must be fixed**
- **Test failures must be resolved before committing**
- **Security issues must be addressed immediately**
- **No exceptions to quality standards**

## Code Quality Standards

### Python Code Standards
- **Always use type hints** for function parameters and return values
- **Follow PEP 8** style guidelines strictly
- **Use black formatter** for consistent code formatting
- **Use flake8** for linting and code quality checks
- **Write comprehensive docstrings** in reST format
- **Use meaningful variable and function names**
- **Keep functions small and focused**
- **Handle exceptions properly**

### Testing Requirements
- **Maintain high test coverage** (aim for 90%+)
- **Write unit tests** for all new functionality
- **Write integration tests** for complex interactions
- **Test edge cases** and error scenarios
- **Mock external dependencies** properly
- **Ensure all tests pass** before committing

### Error Handling
- **Always handle exceptions** appropriately
- **Log errors** with sufficient context
- **Provide meaningful error messages** to users
- **Use proper exception types** for different scenarios
- **Implement graceful degradation** where possible

### Security Standards
- **Never commit sensitive data** (API keys, passwords, etc.)
- **Use environment variables** for configuration
- **Validate all user inputs**
- **Sanitize data** before processing
- **Follow security best practices**

## Development Workflow

### Before Committing
1. **Run all tests**: `python -m pytest`
2. **Check formatting**: `black .`
3. **Run linting**: `flake8`
4. **Check for security issues**
5. **Review code changes**
6. **Ensure all checks pass**

### Commit Message Standards
- **Use conventional commit format**
- **Write clear, descriptive messages**
- **Include scope and type**
- **Describe functional changes first**
- **List all significant changes**

### Branch Management
- **Use feature branches** for new development
- **Keep branches focused** on single features
- **Rebase before merging** to maintain clean history
- **Delete merged branches** to keep repository clean

## Quality Gates

### Mandatory Checks
- [ ] All tests pass
- [ ] Code formatting is correct
- [ ] Linting passes without errors
- [ ] No security vulnerabilities
- [ ] Code coverage meets standards
- [ ] Documentation is updated

### Code Review Requirements
- **All code must be reviewed** before merging
- **Address all review comments**
- **Ensure code follows standards**
- **Verify functionality works as expected**

### Continuous Integration
- **All CI checks must pass**
- **No broken builds** should be merged
- **Monitor CI/CD pipeline** for issues
- **Fix failing builds** immediately