# Coding Standards and Approach

## Core Coding Rules (Always True)

1. **Make all functions as small and simple as possible**
2. **One task per function, preferably one function per file**
3. **All code is written in TDD in pairs** - one LLM is the test creator and the other writes the code to pass the test - the test creator validates the answers from the test taker and presents it to the person in charge of them for their approval
4. **Files must be read first before edited or erased**
5. **Never solve problems I did not ask for**
6. **Always know why**

## TDD Process

### Test-Driven Development Workflow
1. **Test Creator** writes failing tests
2. **Code Writer** writes minimal code to pass tests
3. **Test Creator** validates the code passes tests
4. **Approval** from supervisor before moving forward
5. **Refactor** if needed while keeping tests green

### Pair Programming Rules
- One LLM creates tests
- Another LLM writes code to pass tests
- Test creator validates answers
- Present to supervisor for approval
- No code without tests
- No tests without clear requirements

## Function Design Principles

### Size and Scope
- Functions should do ONE thing only
- If a function has "and" in its description, it's too big
- Prefer many small functions over few large ones
- Each function should fit on one screen
- Complex logic should be broken into smaller helper functions

### File Organization
- One function per file when possible
- Related functions can share a file if they're very small
- Clear, descriptive file names
- Consistent directory structure

## Problem-Solving Approach

### What NOT to Do
- Don't solve problems that weren't asked for
- Don't add "helpful" features not requested
- Don't optimize prematurely
- Don't assume requirements

### What TO Do
- Solve exactly what was requested
- Ask clarifying questions if unclear
- Understand the WHY behind each requirement
- Keep solutions simple and direct

## Code Quality Standards

### Readability
- Clear, descriptive variable names
- Meaningful function names that describe what they do
- Comments explain WHY, not WHAT
- Consistent formatting and style

### Maintainability
- Small, focused functions
- Clear separation of concerns
- Minimal dependencies between components
- Easy to test and modify

### Safety
- Always read files before modifying them
- Validate inputs and handle edge cases
- Fail fast with clear error messages
- Don't make assumptions about data

## Architecture Principles

### Simplicity First
- Choose the simplest solution that works
- 5 small steps are better than 3 big ones
- Always ask: "Is there a simpler way?"
- Avoid over-engineering

### Incremental Development
- Build in small, testable increments
- Each step should be fully functional
- Don't move forward until current step is complete
- Validate each increment before proceeding

### Context Awareness
- Always understand the bigger picture
- Know how your code fits into the overall system
- Consider the impact of changes on other components
- Maintain consistency with existing patterns
