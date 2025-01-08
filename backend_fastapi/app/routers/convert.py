from fastapi import APIRouter,HTTPException
import zlib

router = APIRouter()

# Helper methods
def string_to_id(input_string: str) -> str:
    """
    Convert a string to a compact ID (5-10 characters).
    """
    numeric_value = zlib.crc32(input_string.encode())
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base62 = ""
    while numeric_value:
        numeric_value, rem = divmod(numeric_value, 62)
        base62 = alphabet[rem] + base62
    return base62


def id_to_string(base62_id: str, string_lookup: dict) -> str:
    """
    Convert an ID back to its original string using a lookup dictionary.
    """
    for original_string, encoded_id in string_lookup.items():
        if encoded_id == base62_id:
            return original_string
    raise ValueError("ID not found in lookup dictionary")


# In-memory storage for demonstration purposes
string_lookup = {}


# Routes
@router.post("/convert/string-to-id")
def convert_string_to_id(input_string: str):
    """
    Convert a string to an ID.
    """
    if not input_string:
        raise HTTPException(status_code=400, detail="Input string cannot be empty.")

    generated_id = string_to_id(input_string)
    string_lookup[input_string] = generated_id  # Store in lookup for decoding
    return {"input": input_string, "id": generated_id}


@router.post("/convert/id-to-string")
def convert_id_to_string(id: str):
    """
    Convert an ID back to the original string.
    """
    if not id:
        raise HTTPException(status_code=400, detail="ID cannot be empty.")

    try:
        original_string = id_to_string(id, string_lookup)
        return {"id": id, "original_string": original_string}
    except ValueError:
        raise HTTPException(status_code=404, detail="ID not found.")
