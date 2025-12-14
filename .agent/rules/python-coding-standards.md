---
trigger: glob
globs: **/*.py
---

# Python Coding Standards

## Language Requirements
- **NEVER use Russian in code comments** - only English
- **ALWAYS use English** for all code documentation, comments, and strings
- **Use clear, professional English terminology** in all code elements

## Type Annotations
- **ALWAYS use type hints** for function parameters and return values
- **Use explicit typing** for all variables where possible
- **Import typing modules** when needed (List, Dict, Optional, etc.)

## Function Definition Format
```python
def function_name(
    param1: Type1,
    param2: Type2,
    optional_param: Optional[Type3] = None
) -> ReturnType:
```

## Documentation Standards (reST Style)
- **ALWAYS write comprehensive docstrings** in reST format
- **Include all parameters, return type, and exceptions**
- **Use proper reST syntax** with colons and type information

### Required Docstring Format:
```python
"""Function description.

Detailed explanation of what the function does, its purpose,
and any important implementation details.

:param param_name: Description of the parameter
:type param_name: ParameterType
:param optional_param: Description of optional parameter
:type optional_param: Optional[ParameterType]
:returns: Description of what is returned
:rtype: ReturnType
:raises ExceptionType: When and why this exception is raised
:raises AnotherException: Another possible exception
"""
```

### Example:
```python
def generate_message_registration_success(
    user_info: TelegramUser,
    birth_date: str
) -> str:
    """Generate registration success message for the user.

    This function creates a localized success message when the user
    successfully registers with their birth date. It includes calculated
    life statistics to show the user what they can expect.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :param birth_date: User's birth date as formatted string
    :type birth_date: str
    :returns: Localized registration success message with statistics
    :rtype: str
    :raises ValueError: If user profile is not found
    :raises KeyError: If required statistics are missing from calculator output
    """
```

## Named Parameters
- **ALWAYS use named parameters** wherever possible in function calls
- **Prefer explicit parameter names** over positional arguments
- **Use keyword arguments** for clarity and maintainability

### Example:
```python
return get_message(
    message_key="command_subscription",
    sub_key="already_active",
    language=user_lang,
    subscription_type=subscription_type,
)
```

## Python 3.13+ Best Practices
- **Use Python 3.13+ syntax** and features when available
- **Prefer built-in functions** and modern Python idioms
- **Use type union syntax** (Type1 | Type2) instead of Union[Type1, Type2]
- **Use match-case statements** where appropriate
- **Use dataclasses** for data structures
- **Use pathlib** for file operations
- **Use asyncio** for asynchronous operations

## Constants and Configuration
- **ALWAYS define constants** instead of magic numbers and strings
- **Use UPPER_CASE** for constant names
- **Group related constants** in configuration modules
- **Use enums** for categorical constants
- **Import constants** from main code in tests

### Example:
```python
# Instead of magic numbers
if age < 18:
    return False

# Use constants
if age < MIN_AGE_FOR_REGISTRATION:
    return False
```

## Testing Standards (pytest)
- **ALWAYS use pytest** for all testing
- **Write comprehensive test descriptions** in docstrings
- **Group tests by classes** - one class per function/module
- **Use descriptive test names** that explain what is being tested
- **Use constants and enums** from main code in tests
- **Mock external dependencies** properly
- **Test edge cases** and error scenarios

### Test Class Structure:
```python
class TestFunctionName:
    """Test class for function_name function.

    This class contains all tests for the function_name function,
    including success cases, error cases, and edge cases.
    """

    def test_success_case(self):
        """Test successful execution of function_name.

        This test verifies that function_name works correctly
        with valid input parameters and returns expected results.
        """

    def test_error_case(self):
        """Test error handling in function_name.

        This test verifies that function_name properly handles
        invalid input and raises appropriate exceptions.
        """

    def test_edge_case(self):
        """Test edge case handling in function_name.

        This test verifies that function_name handles boundary
        conditions and edge cases correctly.
        """
```

### Test Example:
```python
class TestGenerateMessageRegistrationSuccess:
    """Test class for generate_message_registration_success function.

    This class contains all tests for the registration success message
    generation function, including various input scenarios and error cases.
    """

    def test_success_with_valid_input(self):
        """Test successful message generation with valid user data.

        This test verifies that the function correctly generates
        a localized success message when given valid user information
        and birth date.
        """
        # Test implementation

    def test_user_not_found_error(self):
        """Test error handling when user profile is not found.

        This test verifies that the function raises ValueError
        when the user profile cannot be retrieved from the database.
        """
        # Test implementation
```

## Code Quality Standards
- **Follow PEP 8** style guidelines strictly
- **Use meaningful variable and function names**
- **Keep functions small and focused**
- **Handle exceptions properly**
- **Use proper logging** instead of print statements
- **Write self-documenting code**
- **Avoid code duplication**
- **Use list comprehensions** and generator expressions where appropriate
- **Prefer context managers** for resource management

## Import Organization
- **Group imports** in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- **Use absolute imports** when possible
- **Avoid wildcard imports** (from module import *)
- **Use specific imports** (from module import specific_function)

## Error Handling
- **Use specific exception types** for different error scenarios
- **Provide meaningful error messages**
- **Log errors** with sufficient context
- **Use proper exception hierarchy**
- **Handle exceptions at appropriate levels**

## Performance Considerations
- **Use generators** for large data processing
- **Avoid unnecessary object creation**
- **Use appropriate data structures**
- **Profile code** when performance is critical
- **Use caching** where appropriate

## Security Best Practices
- **Validate all user inputs**
- **Use parameterized queries** for database operations
- **Sanitize data** before processing
- **Follow security best practices** for the specific domain
- **Never commit sensitive data** (API keys, passwords, etc.)

---
description: Python coding standards for all Python files including tests
globs: ["**/*.py", "**/*.pyi"]
alwaysApply: true