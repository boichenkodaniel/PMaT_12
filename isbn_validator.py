import re
from typing import List, Tuple

ISBN_PATTERN = re.compile(
    r"""
    ^
    (
        (?:
            (?:\d-?){9}
            [\dXx]
        )
        |
        (?:
            (?:97[89]-?)
            (?:\d-?){9}
            \d
        )
    )
    $
    """,
    re.VERBOSE
)


def validate_isbn(isbn: str) -> Tuple[bool, str]:

    if not isbn:
        return False, "Empty string"

    if not ISBN_PATTERN.fullmatch(isbn):
        return False, f"Does not match ISBN format: '{isbn}'"

    isbn_clean = isbn.replace('-', '')

    if len(isbn_clean) == 10:
        return _validate_isbn10_checksum(isbn_clean)
    elif len(isbn_clean) == 13:
        return _validate_isbn13_checksum(isbn_clean)
    else:
        return False, f"Invalid length: {len(isbn_clean)} (expected 10 or 13)"


def _validate_isbn10_checksum(isbn: str) -> Tuple[bool, str]:

    if len(isbn) != 10:
        return False, f"ISBN-10 must be 10 chars, got {len(isbn)}"

    total = 0
    for i, char in enumerate(isbn):
        weight = 10 - i  # weights: 10, 9, 8, ..., 1

        if char.upper() == 'X':
            if i != 9:
                return False, "'X' allowed only as check digit (last position)"
            value = 10
        elif char.isdigit():
            value = int(char)
        else:
            return False, f"Invalid character '{char}' at position {i}"

        total += value * weight

    if total % 11 != 0:
        return False, f"Invalid ISBN-10 checksum (sum={total})"

    return True, "ISBN-10 is valid"


def _validate_isbn13_checksum(isbn: str) -> Tuple[bool, str]:

    if len(isbn) != 13:
        return False, f"ISBN-13 must be 13 chars, got {len(isbn)}"

    if not (isbn.startswith('978') or isbn.startswith('979')):
        return False, f"ISBN-13 must start with 978 or 979, got '{isbn[:3]}'"

    total = 0
    for i, char in enumerate(isbn):
        if not char.isdigit():
            return False, f"Invalid character '{char}' at position {i}"

        value = int(char)
        # weights alternate: 1 for even indices (0, 2, 4...), 3 for odd
        weight = 1 if i % 2 == 0 else 3
        total += value * weight

    if total % 10 != 0:
        return False, f"Invalid ISBN-13 checksum (sum={total})"

    return True, "ISBN-13 is valid"


def validate_isbn_list(isbn_list: List[str]) -> None:

    print("=" * 75)
    print(f"{'Status':<12} | {'ISBN':<35} | {'Result'}")
    print("=" * 75)

    valid_count = 0
    invalid_count = 0

    for isbn in isbn_list:
        is_valid, message = validate_isbn(isbn)
        status = "VALID" if is_valid else "INVALID"
        print(f"{status:<12} | {isbn:<35} | {message}")

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    print("=" * 75)
    print(f"Total: {valid_count} valid, {invalid_count} invalid")
    print("=" * 75)


TEST_ISBNS: List[Tuple[str, bool]] = [
    ("0-306-40615-2", True),      
    ("0306406152", True),        
    ("0-943396-04-2", True),     
    ("043942089X", True),         
    ("0-439-42089-X", True),      
    ("1-56619-909-3", True),      

    ("978-0-306-40615-7", True),  
    ("9780306406157", True),      
    ("979-0-306-40615-6", True),  
    ("9790306406156", True),      
    ("978-0-13-110362-7", True), 
    ("978-5-699-12014-7", True),  

    ("0-306-40615-3", False),    
    ("030640615A", False),       
    ("X306406152", False),        
    ("1234567890", False),        
    ("03064061552", False),       

    ("977-0-306-40615-7", False), 
    ("978-0-306-40615-8", False),
    ("978030640615", False),     
    ("97803064061578", False),   
    ("978-0-306-ABC15-7", False), 

    ("", False),                        
    ("ISBN 978-0-306-40615-7", False), 
    ("978 0 306 40615 7", False),       
    ("978--0--306--40615--7", False),  
    ("abcdefghij", False),             
]


if __name__ == "__main__":
    test_strings = [isbn for isbn, _ in TEST_ISBNS]
    validate_isbn_list(test_strings)

    print("\n\nCross-check with expected results:")
    print("=" * 75)

    errors: List[Tuple[str, bool, bool]] = []
    for isbn, expected_valid in TEST_ISBNS:
        is_valid, _ = validate_isbn(isbn)
        if is_valid != expected_valid:
            errors.append((isbn, expected_valid, is_valid))
            print(f"MISMATCH: {isbn:<35} | expected={expected_valid}, got={is_valid}")

    if not errors:
        print("All tests passed successfully!")
    else:
        print(f"\nFound {len(errors)} mismatch(es)")