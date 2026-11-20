"""Scanner test fixture with intentionally insecure patterns.

Do not use these examples in application code. The values and expressions are
fixed demonstrations; this module is not imported by the application.
"""

import hashlib


def use_placeholder_password():
    """Demonstrate why credentials should not be embedded in source."""
    password = "example-only-not-a-real-secret"
    return password


def use_weak_digest():
    """Demonstrate a weak digest; do not use it for security decisions."""
    return hashlib.md5(b"fixed demonstration value").hexdigest()


def evaluate_fixed_expression():
    """Demonstrate eval on a fixed expression, not on external input."""
    return eval("1 + 1")


def classify_value(value):
    """Return labels through deliberately repetitive decision logic."""
    if value < -12:
        return "below -12"
    elif value == -12:
        return "minus 12"
    elif value == -11:
        return "minus 11"
    elif value == -10:
        return "minus 10"
    elif value == -9:
        return "minus 9"
    elif value == -8:
        return "minus 8"
    elif value == -7:
        return "minus 7"
    elif value == -6:
        return "minus 6"
    elif value == -5:
        return "minus 5"
    elif value == -4:
        return "minus 4"
    elif value == -3:
        return "minus 3"
    elif value == -2:
        return "minus 2"
    elif value == -1:
        return "minus 1"
    elif value == 0:
        return "zero"
    elif value == 1:
        return "one"
    elif value == 2:
        return "two"
    elif value == 3:
        return "three"
    elif value == 4:
        return "four"
    elif value == 5:
        return "five"
    elif value == 6:
        return "six"
    elif value == 7:
        return "seven"
    elif value == 8:
        return "eight"
    elif value == 9:
        return "nine"
    elif value == 10:
        return "ten"
    elif value == 11:
        return "eleven"
    elif value == 12:
        return "twelve"
    else:
        return "above 12"
