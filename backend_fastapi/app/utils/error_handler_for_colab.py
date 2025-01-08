def handle_error_for_colab_link(e: Exception, link: str) -> dict:
    """
    Helper function to process errors and return a structured error response.
    """
    # Capture and structure the error
    error_summary = {"summary": {"error_types": [], "total_errors": 0}, "errors": []}

    # Example error categorization
    if "object has no attribute" in str(e).lower():
        error_type = "Schema validation error"
    elif "Penguin Schema Validation Error" in str(e).lower():
        error_type = "Schema validation error"
    elif "file not found" in str(e).lower():
        error_type = "File not found"
    elif "invalid colab link" in str(e).lower():
        error_type = "Invalid Colab link"
    else:
        error_type = "General error"

    # Add error to summary and details
    error_summary["summary"]["error_types"].append({"error_type": error_type, "count": 1})
    error_summary["summary"]["total_errors"] = 1
    error_summary["errors"].append(
        {
            "error_message": str(e),
            "type": error_type,
            "link": link,
        }
    )

    return error_summary
