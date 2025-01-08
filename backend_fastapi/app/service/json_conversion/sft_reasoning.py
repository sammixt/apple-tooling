import json
from typing import Any
import uuid
from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import nbformat
import re
from googleapiclient.discovery import build
import io
from nbconvert import PythonExporter
from app.routers.convert import string_to_id
from difflib import get_close_matches
from app.db.enums import ClientEnum

def authenticate_drive():
    """Authenticate with Google Drive API using a service account."""
    credentials = service_account.Credentials.from_service_account_file(
        "turing-gpt.json", scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=credentials)


def extract_file_id(link):
    """Extract file ID from a Colab link."""
    match = re.search(r"/drive/([a-zA-Z0-9_-]+)", link)
    if not match:
        raise ValueError("Invalid Colab link.")
    return match.group(1)


def download_ipynb(drive_service, file_id):
    """Download the notebook (.ipynb) from Google Drive."""
    request = drive_service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return file_content.getvalue().decode("utf-8")


def convert_ipynb_to_py(ipynb_content):
    """Convert a Colab notebook (.ipynb) to Python script (.py)."""
    nb = nbformat.reads(ipynb_content, as_version=4)
    exporter = PythonExporter()
    script, _ = exporter.from_notebook_node(nb)
    return script

# Function to clean the text
def clean_text_from_comments(comment_block):
    cleaned = re.sub(r"^#\s?", "", comment_block, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned

# def get_category_from_enum(category):
#     # List of categories (enum or predefined list)
#     categories = [
#         "Brainstorming",
#         "Chatbot",
#         "Classification",
#         "Closed Q&A",
#         "Coding",
#         "Creative Writing",
#         "Extraction",
#         "Analytical Reasoning",
#         "Math",
#         "Open Q&A",
#         "Rewriting",
#         "Structured Data Generation",
#         "Summarization",
#         "Tool Usage",
#         "Other",
#         "Multimodal:Image"
#     ]
#     matches = get_close_matches(category, categories, n=1, cutoff=0.4)
#     return matches[0] if matches else "Other"

def get_category_from_enum(category):
    categories = [
        "Brainstorming",
        "Chatbot",
        "Classification",
        "Closed Q&A",
        "Coding",
        "Creative Writing",
        "Extraction",
        "Analytical Reasoning",
        "Math",
        "Open Q&A",
        "Rewriting",
        "Structured Data Generation",
        "Summarization",
        "Tool Usage",
        "Other",
        "Multimodal:Image"
    ]

    # Define specific mappings for exact terms
    specific_mappings = {
        "mathematics": "Math",
        "code": "Coding",
        "creative": "Creative Writing",
        "reasoning": "Analytical Reasoning",
        "closedqa": "Closed Q&A",
        "openqa": "Open Q&A",
        "datagen": "Structured Data Generation",
        "image": "Multimodal:Image"
    }

    # Normalize input for case-insensitive comparison
    category_lower = category.lower()

    # Check for specific mappings first
    if category_lower in specific_mappings:
        return specific_mappings[category_lower]

    # Check in categories list (case insensitive)
    for item in categories:
        if item.lower() == category_lower:
            return item

    # Return "Other" if no match is found
    return "Other"

def parse_functions_from_code(mock_code):
    func_impl = []
    lines = mock_code.splitlines()
    function_code = []
    function_name = None

    for line in lines:
        stripped_line = line.strip()

        # Detect function definition
        if stripped_line.startswith("def "):
            if function_name:
                func_impl.append(
                    {
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "code": function_code,
                        },
                    }
                )

            function_name = re.match(r"def ([a-zA-Z_]\w*)", stripped_line).group(1)
            function_code = [line]

        elif function_name:
            function_code.append(line)

    # Save the last function if it exists
    if function_name:
        func_impl.append(
            {
                "type": "function",
                "function": {
                    "name": function_name,
                    "code": function_code,
                },
            }
        )

    return func_impl


def validate_type(value: Any, expected_type: str) -> bool:
    type_map = {"string": str, "object": dict, "array": list, "number": (int, float), "boolean": bool}
    return isinstance(value, type_map.get(expected_type, object))


def validate_notebook_json(data):
    errors = []

    # Validate func_impl functions in tools list
    tool_functions = {tool["function"]["name"] for tool in data.get("tools", [])}
    for func in data.get("notes", {}).get("func_impl", []):
        func_name = func.get("function", {}).get("name")
        if func_name not in tool_functions:
            errors.append(f"Function '{func_name}' in func_impl is not in the tools list.")

    # Validate tool_call and tool_output matching
    for section in data.get("messages", []):
        if section.get("role") == "assistant":
            for process_step in section.get("reasoning", {}).get("process", []):
                if isinstance(process_step, dict):
                    thoughts = process_step.get("thoughts", [])
                    for i, thought in enumerate(thoughts):
                        if "tool_call" in thought:
                            if "tool_output" not in thought:
                                raise HTTPException(
                                    status_code=400, detail=f"Tool output is missing for tool call at index {i}."
                                )
                            if isinstance(thought.get("tool_output"), dict) and isinstance(thought.get("tool_call"), dict):
                                if (
                                    thought["tool_output"]["tool_call_id"] != thought["tool_call"]["id"]
                                    or thought["tool_output"]["name"] != thought["tool_call"]["function"]["name"]
                                ):
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"Tool output at index {i} does not match the tool call in the same thought.",
                                    )
                            else:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Expected 'tool_output' and 'tool_call' to be valid JSON.",
                                )

    # Validate tool_call functions in tools list
    for section in data.get("messages", []):
        if section.get("role") == "assistant":
            for process_step in section.get("reasoning", {}).get("process", []):
                if isinstance(process_step, dict):
                    for thought in process_step.get("thoughts", []):
                        tool_calls = thought.get("tool_call", [])
                        if isinstance(tool_calls, dict):
                            tool_calls = [tool_calls]
                        for tool_call in tool_calls:
                            tool_call_func = tool_call["function"]["name"]
                            if tool_call_func not in tool_functions:
                                errors.append(f"Tool call function '{tool_call_func}' is not in the tools list.")

    # Validate tool call parameters
    tool_params = {tool["function"]["name"]: tool["function"]["parameters"] for tool in data.get("tools", [])}
    for section in data.get("messages", []):
        if section.get("role") == "assistant":
            for process_step in section.get("reasoning", {}).get("process", []):
                if isinstance(process_step, dict):
                    for thought in process_step.get("thoughts", []):
                        tool_calls = thought.get("tool_call", [])
                        if isinstance(tool_calls, dict):
                            tool_calls = [tool_calls]
                        for tool_call in tool_calls:
                            func_name = tool_call["function"]["name"]

                            if func_name not in tool_params:
                                continue

                            params_def = tool_params[func_name]
                            required_params = params_def.get("required", [])
                            optional_params = set(params_def.get("properties", {}).keys()) - set(required_params)

                            # Validate required parameters
                            for param in required_params:
                                if param not in tool_call["function"].get("arguments", {}):
                                    errors.append(f"Required parameter '{param}' missing in tool call '{func_name}'.")

                            # Validate parameter types and structure
                            for param, value in tool_call["function"].get("arguments", {}).items():
                                if param in params_def.get("properties", {}):
                                    expected_type = params_def["properties"][param]["type"]

                                    if not validate_type(value, expected_type):
                                        errors.append(
                                            f"Parameter '{param}' in tool call '{func_name}' has an invalid type. Expected: {expected_type}."
                                        )
                                else:
                                    # Extra parameter found
                                    errors.append(f"Extra parameter '{param}' found in tool call '{func_name}'.")

    # Validate section count
    # if data.get("notes", {}).get("notebook_metadata", {}).get("Sections", 0) < 3:
    #     errors.append("The JSON must contain at least three sections.")

    return errors or None


def validate_colab_structure(data: str):
    comments = []
    valid_structure = True

    # Regex Patterns
    patterns = {
        "Category": r"(?i)\*\*Category:\*\*\s*-\s*[\w\s]+",
        "Topic": r"(?i)\*\*Topic:\*\*\s*-\s*[\w\s]+",
        "Subtopic": r"(?i)\*\*Subtopic:\*\*\s*-\s*[\w\s]+",
        "Difficulty": r"(?i)\*\*Difficulty:\*\*\s*-\s*(Easy|Medium|Hard)",
        "Languages": r"(?i)\*\*Languages:\*\*\s*-\s*[\w\s,]+",
        "Explanation": r"(?i)\*\*Explanation:\*\*\s*-\s*[\w\s,.]+",
        "User": r"(?i)\*\*\[User\]\*\*",
        "Prompt": r"(?i)\*\*\[PROMPT\]\*\*",
        "Section": r"(?i)\*\*\[SECTION_(\d+)\]\*",
        "Atomic": r"(?i)\*\*\[Atomic_(\d+)_(\d+)\]\*",
        "Response": r"(?<=\*\*\[RESPONSE\]\*\*)([\s\S]*?)(?=\*\*|\Z)",
        "Divider": r"(?i)^---$",
    }

    # Validate Metadata
    metadata_lines = []
    for line in data.splitlines():
        if re.match(patterns["User"], line.strip()):
            break
        metadata_lines.append(line.strip())

    metadata_content = "\n".join(metadata_lines)

    metadata_fields = ["Category", "Topic", "Subtopic", "Difficulty", "Explanation"]
    for field in metadata_fields:
        if not re.search(patterns[field], metadata_content, re.IGNORECASE):
            comments.append(f"Metadata '{field}' is missing or incorrectly formatted.")
            valid_structure = False

    # Validate Sections Sequence
    sections = re.findall(patterns["Section"], data)
    if not sections:
        comments.append("No valid sections found.")
        valid_structure = False
    else:
        # Ensure sections are in increasing order
        for i in range(1, len(sections)):
            if int(sections[i]) != int(sections[i - 1]) + 1:
                comments.append(f"Section_{sections[i]} out of order. Expected Section_{int(sections[i-1]) + 1}.")
                valid_structure = False

    # Validate Atomic Sequence within Sections
    atomic_cells = re.findall(patterns["Atomic"], data)
    section_atomic_mapping = {}

    for atomic in atomic_cells:
        section_number, atomic_number = map(int, atomic)
        if section_number not in section_atomic_mapping:
            section_atomic_mapping[section_number] = []
        section_atomic_mapping[section_number].append(atomic_number)

    # Ensure atomic cells within a section are in order
    for section, atomics in section_atomic_mapping.items():
        atomics.sort()
        for i in range(1, len(atomics)):
            if atomics[i] != atomics[i - 1] + 1:
                comments.append(f"Atomic_{section}_{atomics[i]} is out of order within Section_{section}.")
                valid_structure = False

    # Check for the required response section and the order of sections
    response_section = re.search(patterns["Response"], data)
    if not response_section:
        comments.append("Missing **[RESPONSE]** section.")
        valid_structure = False
    else:
        response_content = response_section.group(1).strip()
        if len(response_content) < 50:
            comments.append("**[RESPONSE]** section must be at least 50 characters long.")
            valid_structure = False

    # Final check for validation issues
    if comments:
        raise ValueError({"errors": comments})

    return True


def process_file_content(type, py_content, annotator_email, client, file_id):
    if annotator_email:
        annotator_id = string_to_id(annotator_email)
    else:
        annotator_id = None

    if type == "Agent":
        # Do Dhiraj work
        parsed_json = parse_agent_colab_notebooks(py_content, annotator_id, client, file_id)
    elif type == "Coding":
        # Do anthony work
        parsed_json = parse_code_colab_notebooks(py_content, annotator_id, client, file_id)
    else:
        # Do marko work
        parsed_json = parse_other_colab_notebooks(py_content, annotator_id, client, file_id)

    return parsed_json

def parse_other_colab_notebooks(data, annotator_id, client, file_id):
    data = data.replace("\\n", "\n").replace("\\\\", "\\").replace('"""', "")

    # Define all regex patterns in a dictionary for easy management
    patterns = {
        "prompt": r"(?i)\[PROMPT\](.*?)(?=---|\[Assistant\]|$)",
        "response": r"(?i)\[RESPONSE\](.*?)\Z",
        "category": r"(?i)\*\*Category\:\*\*\s*-\s*([^\n]*)",
        "topic": r"(?i)\*\*Topic\:\*\*\s*-\s*([^\n]*)",
        "subtopic": r"(?i)\*\*Subtopic\:\*\*\s*-\s*([^\n]*)",
        "difficulty": r"(?i)\*\*Difficulty\:\*\*\s*-\s*(Easy|Medium|Hard)",
        "languages": r"(?i)\*\*Languages\:\*\*\s*-\s*([^\n]*)",
        "explanation": r"(?i)\*\*Explanation\:\*\*\s*-\s*([\s\S]+?)(?=\*\*|\[User\]|\Z)",
        "section": r"(?i)\[SECTION_\d+\](.*?)(?=---|\[SECTION_\d+\]|$)",
        "section_summary": r"(?i)(\*\*.*?\*\*)\n*\[atomic_\d+_\d+\]",
        "atomic": r"(?i)\[atomic_\d+_\d+\](.*?)(?=\[atomic_\d+_\d+\]|$)",
    }

    # Extract matches using regex patterns
    prompt = re.search(patterns["prompt"], data, re.DOTALL)
    assistant_response = re.search(patterns["response"], data, re.DOTALL)
    category = re.search(patterns["category"], data, re.DOTALL)
    topic = re.search(patterns["topic"], data, re.DOTALL)
    subtopic = re.search(patterns["subtopic"], data, re.DOTALL)
    difficulty = re.search(patterns["difficulty"], data, re.DOTALL)
    explanation = re.search(patterns["explanation"], data, re.DOTALL)
    languages = re.search(patterns["languages"], data, re.DOTALL)
    languages = languages.group(1).strip() if languages else ""
    sections = re.findall(patterns["section"], data, re.DOTALL)

    process = []
    for idx, match in enumerate(sections, 1):
        thoughts = []
        summary = re.search(patterns["section_summary"], match.strip(), re.DOTALL)

        atomics = re.findall(patterns["atomic"], match.strip(), re.DOTALL)
        atomic_content = set()
        for a_idx, a_match in enumerate(atomics, 1):
            # Check for duplicate atomic content
            if a_match.strip() in atomic_content:
                raise ValueError(f"Duplicate atomic content found in section {idx}.")
            thoughts.append({"text": clean_text_from_comments(a_match.strip().replace("**", "").strip()).strip()})

        process.append({"summary": clean_text_from_comments(summary.group(1).strip().replace("**", "").strip()).strip(), "thoughts": thoughts})

    # Ensure prompt and assistant matches are found
    if not prompt or not assistant_response or not process:
        raise ValueError("Prompt or assistant or sections not found")

    if languages:
        language_code_blocks = []
        for lang in languages.split(","):
            lang = lang.strip().lower()

            # Regex to match code block for any language (e.g., ```python, ```javascript)
            code_block_pattern = r"```" + re.escape(lang) + r"\s*([\s\S]*?)```"

            matches = re.findall(code_block_pattern, assistant_response.group(1), re.DOTALL)
            language_code_blocks.extend(matches)

        if not language_code_blocks:
            raise ValueError("No matching language code block found in response.")

    deliverable = {
        "deliverable_id": file_id, #str(uuid.uuid4()),
        "language": {"overall": "en_US"},
        "notes": {
            "notebook_metadata": {
                "Topic": topic.group(1).strip() if topic else "",
                "Subtopic": subtopic.group(1).strip() if subtopic else "",
                "Difficulty": difficulty.group(1).strip() if difficulty else "",
                "Languages": [item.strip() for item in languages.split(",")] if languages else [],
                "Explanation": clean_text_from_comments(explanation.group(1).strip()).strip() if explanation else "",
                "Sections": len(process),
            }
        },
        "messages": [
            {"role": "user", "contents": [{"text": clean_text_from_comments(prompt.group(1).strip().replace("**", "").strip()).strip()}]},
            {
                "role": "assistant",
                "contents": [{"text": clean_text_from_comments(assistant_response.group(1).strip().replace("**", "").strip()).strip()}],
                "reasoning": {"process": process},
            },
        ],
    }

    if client == ClientEnum.PENGUIN.value:
        deliverable["notes"]["annotator_ids"] = [str(annotator_id)] if annotator_id else []
        deliverable["notes"]["task_category_list"] = [
            {
                "category": get_category_from_enum(category.group(1).strip() if category else "Other"),
            }
        ]
    else:
        deliverable["notes"]["notebook_metadata"]["Category"] = category.group(1).strip() if category else ""
    return deliverable

def parse_agent_colab_notebooks(data, annotator_id, client, file_id):
    try:
        data = data.replace("\\n", "\n").replace("\\\\", "\\").replace('"""', "")
        data = clean_text_from_comments(data).strip()

        # Define regex patterns
        patterns = {
            "system_prompt": r"(?i)\*\*\[System\]\*\*\s*\*\*\[PROMPT\]\*\*\s*([\s\S]*?)(?=---|\Z)",
            "tools": r"(?i)\*\*\[Tools\]\*\*\s*```json\s*([\s\S]*?)```",
            "mock": r"(?i)\*\*\[Mock\]\*\*\s*```([\w+]*)\s*([\s\S]*?)```",
            "prompt": r"(?i)\*\*\[User\]\*\*\s*\*\*\[PROMPT\](.*?)(?=---|\[Assistant\]|$)",
            "response": r"(?i)\[RESPONSE\](.*?)\Z",
            "category": r"(?i)\*\*Category\:\*\*\s*-\s*([^\n]*)",
            "topic": r"(?i)\*\*Topic\:\*\*\s*-\s*([^\n]*)",
            "subtopic": r"(?i)\*\*Subtopic\:\*\*\s*-\s*([^\n]*)",
            "difficulty": r"(?i)\*\*Difficulty\:\*\*\s*-\s*(Easy|Medium|Hard)",
            "languages": r"(?i)\*\*Languages\:\*\*\s*-\s*([^\n]*)",
            "explanation": r"(?i)\*\*Explanation\:\*\*\s*-\s*([\s\S]+?)(?=\*\*|\[User\]|\Z)",
            "section": r"(?i)\[SECTION_\d+\](.*?)(?=---|\[SECTION_\d+\]|$)",
            "section_summary": r"(?i)(\*\*.*?\*\*)\n*\[atomic_\d+_\d+\]",
            "atomic": r"(?i)\[atomic_\d+_\d+\](.*?)(?=\[atomic_\d+_\d+\]|$)",
            # "tool_call": r"(?i)\[Tool Call\](.*?)(?=\[Tool Output\]|\[atomic_\d+_\d+\]|\Z)",
            # "tool_output": r"(?i)\[Tool Output\](.*?)(?=\[atomic_\d+_\d+\]|\Z)",
            "atomic_string": r"(?i)([\s\S]*?)\*\*\[tool_call\]\*\*",
            "tool_call": r"(?i)\*\*\[tool_call\]\*\*\s*```json\s*([\s\S]*?)```",
            "tool_output": r"(?i)\*\*\[tool_output\]\*\*\s*```json\s*([\s\S]*?)```",
        }

        # Extract matches using regex patterns
        system_prompt_match = re.search(patterns["system_prompt"], data, re.DOTALL)
        tools_match = re.search(patterns["tools"], data, re.DOTALL)
        mock_match = re.search(patterns["mock"], data, re.DOTALL)

        system_prompt_text = system_prompt_match.group(1).strip() if system_prompt_match else ""
        tools_data = tools_match.group(1).strip() if tools_match else ""
        mock_language = mock_match.group(1).strip() if mock_match else "unknown"
        mock_code = mock_match.group(2).strip() if mock_match else ""

        prompt = re.search(patterns["prompt"], data, re.DOTALL)
        assistant_response = re.search(patterns["response"], data, re.DOTALL)
        category = re.search(patterns["category"], data, re.DOTALL)
        topic = re.search(patterns["topic"], data, re.DOTALL)
        subtopic = re.search(patterns["subtopic"], data, re.DOTALL)
        difficulty = re.search(patterns["difficulty"], data, re.DOTALL)
        explanation = re.search(patterns["explanation"], data, re.DOTALL)
        languages = re.search(patterns["languages"], data, re.DOTALL)
        languages = languages.group(1).strip() if languages else ""
        sections = re.findall(patterns["section"], data, re.DOTALL)

        # Process sections
        process = []
        for idx, match in enumerate(sections, 1):
            thoughts = []
            summary = re.search(patterns["section_summary"], match.strip(), re.DOTALL)
            atomics = re.findall(patterns["atomic"], match.strip(), re.DOTALL)
            atomic_content = set()
            for a_idx, a_match in enumerate(atomics, 1):
                # Extract tool call and output if present
                tool_call_match = re.search(patterns["tool_call"], a_match.strip(), re.DOTALL)
                tool_output_match = re.search(patterns["tool_output"], a_match.strip(), re.DOTALL)
                tool_call = tool_call_match.group(1).strip() if tool_call_match else None
                tool_output = tool_output_match.group(1).strip() if tool_output_match else None

                # Check for duplicate atomic content
                if a_match.strip() in atomic_content:
                    raise ValueError(f"Duplicate atomic content found in section {idx}.")
                atomic_content.add(a_match.strip())

                if tool_call or tool_output:
                    atomic_string_match = re.search(patterns["atomic_string"], a_match.strip(), re.DOTALL)
                    thought = {
                        "text": (
                            clean_text_from_comments(atomic_string_match.group(1).strip().replace("**", "").strip()).strip()
                            if atomic_string_match
                            else None
                        )
                    }
                    try:
                        if not tool_call:
                            raise ValueError(f"Tool call is missing in section #{idx} and atomic thought #{a_idx}")
                        try:
                            thought["tool_call"] = json.loads(tool_call)
                        except json.JSONDecodeError as json_error:
                            error_msg = (
                                f"Error parsing tool_call JSON in section #{idx}, atomic thought #{a_idx}. "
                                f"Ensure the JSON is properly formatted. Input: {tool_call}. Error: {json_error}"
                            )
                            raise ValueError(error_msg) from json_error
                    except ValueError as e:
                        raise

                    try:
                        if not tool_output:
                            raise ValueError(f"Tool output is missing in section #{idx} and atomic thought #{a_idx}")
                        try:
                            thought["tool_output"] = json.loads(tool_output)
                        except json.JSONDecodeError as json_error:
                            error_msg = (
                                f"Error parsing tool_output JSON in section #{idx}, atomic thought #{a_idx}. "
                                f"Ensure the JSON is properly formatted. Input: {tool_output}. Error: {json_error}"
                            )
                            raise ValueError(error_msg) from json_error
                    except ValueError as e:
                        thought["tool_call"] = tool_call
                        thought["tool_output"] = tool_output
                else:
                    thought = {"text": clean_text_from_comments(a_match.strip().replace("**", "").strip()).strip()}
                thoughts.append(thought)

            process.append(
                {
                    "summary": clean_text_from_comments(summary.group(1).strip().replace("**", "").strip()).strip() if summary else "",
                    "thoughts": thoughts,
                }
            )

        # Ensure prompt and assistant matches are found
        if not prompt or not assistant_response or not process:
            raise ValueError("Prompt, assistant response, or sections not found")

        if languages:
            language_code_blocks = []
            for lang in languages.split(","):
                lang = lang.strip().lower()

                # Regex to match code block for any language (e.g., ```python, ```javascript)
                code_block_pattern = r"```" + re.escape(lang) + r"\s*([\s\S]*?)```"

                matches = re.findall(code_block_pattern, assistant_response.group(1), re.DOTALL)
                language_code_blocks.extend(matches)

            if not language_code_blocks:
                raise ValueError("No matching language code block found in response.")

        mock_functions = parse_functions_from_code(mock_code)

    except Exception as e:
        raise ValueError("Error occurred. Check file format and try again! " + str(e))

    if client == ClientEnum.PENGUIN.value:
        notes = {
            "task_category_list": [
                {
                    "category": get_category_from_enum(category.group(1).strip() if category else "Other"),
                }
            ],
            "annotator_ids": [str(annotator_id)] if annotator_id else [],
            "notebook_metadata": {
                "Sections": len(process),
            },
            "func_impl": mock_functions,
        }
    else:
        notes = {
            "notebook_metadata": {
                "Sections": len(process),
            },
            "func_impl": mock_functions,
        }
    final_json = {
        "deliverable_id": file_id, #str(uuid.uuid4()),
        "language": {"overall": "en_US"},
        "notes": notes,
        "tools": json.loads(tools_data),
        "messages": [
            {"role": "system", "contents": [{"text": clean_text_from_comments(system_prompt_text.replace("**", "").strip()).strip()}]},
            {"role": "user", "contents": [{"text": clean_text_from_comments(prompt.group(1).strip().replace("**", "").strip()).strip()}]},
            {
                "role": "assistant",
                "contents": [{"text": clean_text_from_comments(assistant_response.group(1).strip().replace("**", "").strip()).strip()}],
                "reasoning": {"process": process},
            },
        ],
    }

    # Iterate over each object in the "tools" array
    for obj in final_json["tools"]:
        # Ensure "type" is set to "function"
        obj["type"] = "function"

        # Check if "function" key exists and "parameters" is an empty dictionary
        if "function" in obj and isinstance(obj["function"], dict):
            parameters = obj["function"].get("parameters", {})

            if parameters == {}:  # Empty dictionary check
                obj["function"]["parameters"] = {
                    "type": "object",
                    "required": [],
                    "properties": {}
                }
            else:  # Validate existing "parameters"
                if not isinstance(parameters, dict):
                    raise ValueError(f"Invalid parameters type: {type(parameters)}. Expected a dictionary.")

                # Check for required keys and their types
                if (
                        "type" not in parameters or not isinstance(parameters["type"], str) or
                        "required" not in parameters or not isinstance(parameters["required"], list) or
                        "properties" not in parameters or not isinstance(parameters["properties"], dict)
                ):
                    raise ValueError(f"Invalid 'parameters' structure in: {parameters}")
        else:
            raise ValueError(f"Invalid 'tools' structure in: {obj}")

    errors = validate_notebook_json(final_json)
    if errors:
        raise ValueError(errors)

    return final_json

def parse_code_colab_notebooks(data, annotator_id, client, file_id):
    try:
        data = data.replace("\\n", "\n").replace("\\\\", "\\").replace('"""', "")

        # Define all regex patterns in a dictionary for easy management
        patterns = {
            "prompt": r"(?i)\[PROMPT\](.*?)(?=---|\[Assistant\]|$)",
            "response": r"(?i)\[RESPONSE\](.*?)\Z",
            "category": r"(?i)\*\*Category\:\*\*\s*-\s*([^\n]*)",
            "topic": r"(?i)\*\*Topic\:\*\*\s*-\s*([^\n]*)",
            "subtopic": r"(?i)\*\*Subtopic\:\*\*\s*-\s*([^\n]*)",
            "difficulty": r"(?i)\*\*Difficulty\:\*\*\s*-\s*(Easy|Medium|Hard)",
            "languages": r"(?i)\*\*Languages\:\*\*\s*-\s*([^\n]*)",
            "failed_attempts": r"(?i)\*\*Failed attempts \(corner cases, time complexity\)\:\*\*\s*-\s*([^\n]*)",
            "number_of_approaches": r"(?i)\*\*Number of Approaches\:\*\*\s*-\s*([^\n]*)",
            "explanation": r"(?i)\*\*Explanation\:\*\*\s*-\s*([\s\S]+?)(?=\*\*|\[User\]|\Z)",
            "section": r"(?i)\[CHAIN_\d+\](.*?)(?=---|\[CHAIN_\d+\]|$)",
            "section_summary": r"(?i)(\*\*.*?\*\*)\n*\[THOUGHT_\d+_\d+\]",
            "atomic": r"(?i)\[THOUGHT_\d+_\d+\](.*?)(?=\[THOUGHT_\d+_\d+\]|$)",
        }

        # Extract matches using regex patterns
        prompt = re.search(patterns["prompt"], data, re.DOTALL)
        assistant_response = re.search(patterns["response"], data, re.DOTALL)
        category = re.search(patterns["category"], data, re.DOTALL)
        topic = re.search(patterns["topic"], data, re.DOTALL)
        subtopic = re.search(patterns["subtopic"], data, re.DOTALL)
        difficulty = re.search(patterns["difficulty"], data, re.DOTALL)
        explanation = re.search(patterns["explanation"], data, re.DOTALL)
        failed_attempts = re.search(patterns["failed_attempts"], data, re.DOTALL)
        number_of_approaches = re.search(patterns["number_of_approaches"], data, re.DOTALL)
        languages = re.search(patterns["languages"], data, re.DOTALL)
        languages = languages.group(1).strip() if languages else ""
        sections = re.findall(patterns["section"], data, re.DOTALL)

        process = []
        for idx, match in enumerate(sections, 1):
            thoughts = []
            summary = re.search(patterns["section_summary"], match.strip(), re.DOTALL)

            atomics = re.findall(patterns["atomic"], match.strip(), re.DOTALL)
            atomic_content = set()
            for a_idx, a_match in enumerate(atomics, 1):
                # Check for duplicate atomic content
                if a_match.strip() in atomic_content:
                    raise ValueError(f"Duplicate atomic content found in section {idx}.")
                thoughts.append({"text": clean_text_from_comments(a_match.strip().replace("**", "").strip()).strip()})

            process.append(
                {"id": idx, "summary": clean_text_from_comments(summary.group(1).strip().replace("**", "").strip()).strip(), "thoughts": thoughts}
            )

        # Ensure prompt and assistant matches are found
        if not prompt or not assistant_response or not process:
            raise ValueError("Prompt or assistant or sections not found")

        assistant_response = clean_text_from_comments(assistant_response.group(1).strip())
        # Regular expression to match all ``` code blocks
        code_block_pattern = r"```.*?```"

        # Find all code blocks
        code_blocks = re.findall(code_block_pattern, assistant_response, re.DOTALL)

        # Replace code blocks with a placeholder
        placeholder = "<<<CODE_BLOCK_PLACEHOLDER>>>"
        data_with_placeholders = re.sub(code_block_pattern, placeholder, assistant_response, flags=re.DOTALL)

        # Replace '**' outside code blocks
        data_with_placeholders = data_with_placeholders.replace("**", "")

        # Reinsert the original code blocks in place of the placeholders
        for code_block in code_blocks:
            data_with_placeholders = data_with_placeholders.replace(placeholder, code_block, 1)

        assistant_response = data_with_placeholders


    except Exception as e:
        raise ValueError("Error occurred. Check file format and try again! " + str(e))

    deliverable = {
        "deliverable_id": file_id, #str(uuid.uuid4()),
        "language": {"overall": "en_US"},
        "notes": {
            "notebook_metadata": {
                "Topic": topic.group(1).strip() if topic else "",
                "Subtopic": json.loads(subtopic.group(1).strip()) if subtopic else "",
                "Difficulty": difficulty.group(1).strip() if difficulty else "",
                "Failed attempts (corner cases, time complexity)": (
                    failed_attempts.group(1).strip() if failed_attempts else ""
                ),
                "Number of Approaches": (
                    number_of_approaches.group(1).strip() if number_of_approaches else ""
                ),
                "Languages": [item.strip() for item in languages.split(",")] if languages else [],
                # "Explanation": explanation.group(1).strip() if explanation else "",
                "Number of Chains": len(process),
            }
        },
        "messages": [
            {"role": "user", "prompt": [{"text": clean_text_from_comments(prompt.group(1).strip().replace("**", "").strip()).strip()}]},
            {
                "role": "assistant",
                "response": [{"text": assistant_response.strip()}],
                "reasoning": {"chain": process},
            },
        ],
    }
    if client == ClientEnum.PENGUIN.value:
        deliverable["notes"]["annotator_ids"] = [str(annotator_id)] if annotator_id else []
        deliverable["notes"]["task_category_list"] = [
            {
                "category": get_category_from_enum(category.group(1).strip() if category else "Other"),
            }
        ]
    else:
        deliverable["notes"]["notebook_metadata"]["Category"] = category.group(1).strip() if category else ""
    return deliverable
