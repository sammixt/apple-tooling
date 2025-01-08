import re
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.service.json_conversion.sft_reasoning import (
    authenticate_drive,
    convert_ipynb_to_py,
    download_ipynb,
    extract_file_id,
    process_file_content,
)
from app.utils.error_handler_for_colab import handle_error_for_colab_link


router = APIRouter()


@router.post("/convert-colab-link-to-json/")
async def convert_colab_link_to_json(link: str):
    drive_service = authenticate_drive()
    try:
        file_id = extract_file_id(link)
        ipynb_content = download_ipynb(drive_service, file_id)
        py_content = convert_ipynb_to_py(ipynb_content)

        # Determine category and patterns
        category_match = re.search(r"(?i)\*\*Category\:\*\*\s*-\s*([^\n]*)", py_content)
        category = category_match.group(1).strip() if category_match else "General"

        type = "General"
        if category.lower() == "agent":
            type = "Agent"
        elif category.lower() == "coding":
            if re.search(r"(?i)\*\*\[CHAIN", py_content) and re.search(r"(?i)\*\*\[THOUGHT", py_content):
                type = "Coding"

        json_data = process_file_content(type, py_content)
        return JSONResponse(status_code=200, content=json_data)
    except Exception as e:
        error_response = handle_error_for_colab_link(e, link)
        # Return the structured error response
        return JSONResponse(status_code=400, content=error_response)
