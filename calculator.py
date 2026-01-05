#!/usr/bin/env python3
"""A simple command-line calculator."""


def add(a, b):
    """Add two numbers."""
    return a + b


def subtract(a, b):
    """Subtract b from a."""
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    return a * b


def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def power(a, b):
    """Raise a to the power of b."""
    return a ** b


def modulo(a, b):
    """Return the remainder of a divided by b."""
    if b == 0:
        raise ValueError("Cannot modulo by zero")
    return a % b


OPERATIONS = {
    '+': add,
    '-': subtract,
    '*': multiply,
    '/': divide,
    '^': power,
    '%': modulo,
}


def calculate(expression):
    """Parse and calculate a simple expression."""
    expression = expression.strip()

    for op in OPERATIONS:
        if op in expression:
            parts = expression.split(op, 1)
            if len(parts) == 2:
                try:
                    a = float(parts[0].strip())
                    b = float(parts[1].strip())
                    return OPERATIONS[op](a, b)
                except ValueError as e:
                    if "Cannot" in str(e):
                        raise
                    raise ValueError(f"Invalid numbers in expression: {expression}")

    raise ValueError(f"Invalid expression: {expression}")


def main():
    """Run the calculator in interactive mode."""
    print("Python Calculator")
    print("=" * 40)
    print("Supported operations: +, -, *, /, ^ (power), % (modulo)")
    print("Enter expressions like: 5 + 3")
    print("Type 'quit' or 'q' to exit")
    print("=" * 40)

    while True:
        try:
            expression = input("\n> ").strip()

            if expression.lower() in ('quit', 'q', 'exit'):
                print("Goodbye!")
                break

            if not expression:
                continue

            result = calculate(expression)

            if result == int(result):
                print(f"= {int(result)}")
            else:
                print(f"= {result}")

        except ValueError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
