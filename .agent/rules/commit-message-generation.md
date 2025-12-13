---
trigger: always_on
---

# Rules for Commit Message Generation

## Commit Message Generation Rules

When generating commit messages, follow these strict guidelines:

### Language Requirements
- **ALWAYS write commit messages in English only**
- Use clear, professional English terminology
- Avoid technical jargon unless necessary
- Use present tense for actions (e.g., "Add", "Fix", "Update", not "Added", "Fixed")

### Structure Requirements
Every commit message must follow this exact structure:

```
<type>(<scope>): <short description>

<detailed description>

<functional changes>
<refactoring changes>
<test changes>
```

### Structure Breakdown

#### 1. Header Line
- **Type**: Use conventional commit types (feat, fix, refactor, test, docs, style, chore)
- **Scope**: Specify the module/component affected (bot, scheduler, handlers, database, etc.)
- **Description**: Brief, clear description of the main change

#### 2. Detailed Description
- Provide a comprehensive overview of what was changed
- Explain the motivation behind the changes
- Mention any breaking changes or important notes

#### 3. Functional Changes (Primary)
- List all **new features** and **functional improvements**
- Describe **bug fixes** and **behavioral changes**
- Include **new commands**, **handlers**, or **business logic**
- Mention **integration points** and **dependencies**

#### 4. Refactoring Changes (Secondary)
- List **code structure improvements**
- Describe **performance optimizations**
- Mention **code organization** and **architecture changes**
- Include **dependency updates** and **configuration changes**

#### 5. Test Changes (Tertiary)
- List **new test coverage** added
- Describe **test fixes** and **improvements**
- Mention **test infrastructure** changes
- Include **coverage improvements** and **test organization**

### Content Requirements

#### Accuracy and Completeness
- **Accurately reflect ALL changes** made in the commit
- Include **specific file names** and **function names** when relevant
- Mention **quantitative improvements** (e.g., "100% test coverage", "10 new tests")
- Describe **impact** of changes on functionality

#### Functional Changes Priority
- **Always prioritize functional changes** in the description
- Focus on **user-facing features** and **business logic**
- Highlight **new capabilities** and **improved functionality**
- Mention **integration** with external systems or services

#### Refactoring Details
- Describe **code quality improvements**
- Mention **performance enhancements**
- Include **maintainability improvements**
- Note **architecture changes** and **design patterns**

#### Test Coverage
- Specify **test coverage percentages**
- List **new test categories** added
- Mention **test reliability improvements**
- Include **test infrastructure** enhancements

### Examples

#### Good Example:
```
feat(scheduler): implement weekly notification system

Add comprehensive weekly notification scheduling system with individual user preferences support.

Functional Changes:
- Add weekly notification scheduler with APScheduler integration
- Implement individual user notification preferences (day, time, enabled status)
- Add send_weekly_message_to_user function for personalized notifications
- Integrate scheduler with bot application lifecycle
- Add user management functions (add_user_to_scheduler, remove_user_from_scheduler, update_user_schedule)

Refactoring Changes:
- Improve error handling with comprehensive exception management
- Add structured logging for scheduler operations
- Optimize database queries for user settings retrieval
- Enhance code organization with clear separation of concerns

Test Changes:
- Achieve 100% test coverage for scheduler module (1101 lines)
- Add comprehensive test suite for all scheduler functions
- Include edge case testing for error scenarios
- Add integration tests for scheduler-bot interaction
```

#### Bad Example:
```
fix: some bugs and add tests

Fixed some issues and added some tests.
```

### Quality Standards

#### Must Include:
- **Specific functionality** descriptions
- **Quantitative metrics** (coverage, performance, etc.)
- **File and function names** when relevant
- **Impact assessment** of changes
- **Integration details** with other components

#### Must Avoid:
- Vague descriptions like "fix bugs" or "improve code"
- Missing functional change details
- Incomplete test coverage information
- Generic refactoring descriptions
- Non-English text

### Validation Checklist
Before generating a commit message, ensure:
- [ ] Message is in English
- [ ] Structure follows the exact format
- [ ] Functional changes are listed first
- [ ] All major changes are included
- [ ] Specific details and metrics are provided
- [ ] No vague or generic descriptions
- [ ] Proper commit type and scope are used

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
- **No exceptions to quality standards**# Cursor Rules for Commit Message Generation

## Commit Message Generation Rules

When generating commit messages, follow these strict guidelines:

### Language Requirements
- **ALWAYS write commit messages in English only**
- Use clear, professional English terminology
- Avoid technical jargon unless necessary
- Use present tense for actions (e.g., "Add", "Fix", "Update", not "Added", "Fixed")

### Structure Requirements
Every commit message must follow this exact structure:

```
<type>(<scope>): <short description>

<detailed description>

<functional changes>
<refactoring changes>
<test changes>
```

### Structure Breakdown

#### 1. Header Line
- **Type**: Use conventional commit types (feat, fix, refactor, test, docs, style, chore)
- **Scope**: Specify the module/component affected (bot, scheduler, handlers, database, etc.)
- **Description**: Brief, clear description of the main change

#### 2. Detailed Description
- Provide a comprehensive overview of what was changed
- Explain the motivation behind the changes
- Mention any breaking changes or important notes

#### 3. Functional Changes (Primary)
- List all **new features** and **functional improvements**
- Describe **bug fixes** and **behavioral changes**
- Include **new commands**, **handlers**, or **business logic**
- Mention **integration points** and **dependencies**

#### 4. Refactoring Changes (Secondary)
- List **code structure improvements**
- Describe **performance optimizations**
- Mention **code organization** and **architecture changes**
- Include **dependency updates** and **configuration changes**

#### 5. Test Changes (Tertiary)
- List **new test coverage** added
- Describe **test fixes** and **improvements**
- Mention **test infrastructure** changes
- Include **coverage improvements** and **test organization**

### Content Requirements

#### Accuracy and Completeness
- **Accurately reflect ALL changes** made in the commit
- Include **specific file names** and **function names** when relevant
- Mention **quantitative improvements** (e.g., "100% test coverage", "10 new tests")
- Describe **impact** of changes on functionality

#### Functional Changes Priority
- **Always prioritize functional changes** in the description
- Focus on **user-facing features** and **business logic**
- Highlight **new capabilities** and **improved functionality**
- Mention **integration** with external systems or services

#### Refactoring Details
- Describe **code quality improvements**
- Mention **performance enhancements**
- Include **maintainability improvements**
- Note **architecture changes** and **design patterns**

#### Test Coverage
- Specify **test coverage percentages**
- List **new test categories** added
- Mention **test reliability improvements**
- Include **test infrastructure** enhancements

### Examples

#### Good Example:
```
feat(scheduler): implement weekly notification system

Add comprehensive weekly notification scheduling system with individual user preferences support.

Functional Changes:
- Add weekly notification scheduler with APScheduler integration
- Implement individual user notification preferences (day, time, enabled status)
- Add send_weekly_message_to_user function for personalized notifications
- Integrate scheduler with bot application lifecycle
- Add user management functions (add_user_to_scheduler, remove_user_from_scheduler, update_user_schedule)

Refactoring Changes:
- Improve error handling with comprehensive exception management
- Add structured logging for scheduler operations
- Optimize database queries for user settings retrieval
- Enhance code organization with clear separation of concerns

Test Changes:
- Achieve 100% test coverage for scheduler module (1101 lines)
- Add comprehensive test suite for all scheduler functions
- Include edge case testing for error scenarios
- Add integration tests for scheduler-bot interaction
```

#### Bad Example:
```
fix: some bugs and add tests

Fixed some issues and added some tests.
```

### Quality Standards

#### Must Include:
- **Specific functionality** descriptions
- **Quantitative metrics** (coverage, performance, etc.)
- **File and function names** when relevant
- **Impact assessment** of changes
- **Integration details** with other components

#### Must Avoid:
- Vague descriptions like "fix bugs" or "improve code"
- Missing functional change details
- Incomplete test coverage information
- Generic refactoring descriptions
- Non-English text

### Validation Checklist
Before generating a commit message, ensure:
- [ ] Message is in English
- [ ] Structure follows the exact format
- [ ] Functional changes are listed first
- [ ] All major changes are included
- [ ] Specific details and metrics are provided
- [ ] No vague or generic descriptions
- [ ] Proper commit type and scope are used