import pytest
from pydantic import ValidationError

from app.schemas.machine import MachineRustdeskUpdate


@pytest.fixture(autouse=True)
def clean_database():
    """No database needed for schema unit tests."""
    pass


@pytest.mark.parametrize(
    "valid_id",
    [
        "12345",          # 5 digits (min)
        "123456789",      # 9 digits
        "123456789012",   # 12 digits (max)
    ],
)
def test_machine_rustdesk_update_accepts_valid_numeric_ids(valid_id: str):
    schema = MachineRustdeskUpdate(rustdesk_id=valid_id)
    assert schema.rustdesk_id == valid_id


def test_machine_rustdesk_update_accepts_none_and_default():
    assert MachineRustdeskUpdate(rustdesk_id=None).rustdesk_id is None
    assert MachineRustdeskUpdate().rustdesk_id is None


@pytest.mark.parametrize(
    "invalid_id",
    [
        "",                 # Empty string
        "1",                # Too short (< 5 digits)
        "1234",             # 4 digits (< 5 digits)
        "1234567890123",    # 13 digits (> 12 digits)
        "12345a",           # Alphanumeric with letters
        "abcdef",           # Letters only
        "12345-6789",       # Special characters (hyphen)
        "12345 6789",       # Whitespace
        "12345\n",          # Newline
        "<script>alert(1)</script>", # Injection attempt
    ],
)
def test_machine_rustdesk_update_rejects_invalid_ids(invalid_id: str):
    with pytest.raises(ValidationError):
        MachineRustdeskUpdate(rustdesk_id=invalid_id)
