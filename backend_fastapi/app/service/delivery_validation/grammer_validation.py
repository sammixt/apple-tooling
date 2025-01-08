import language_tool_python
import re

class GrammarValidator:
    def __init__(self):
        self.tool = language_tool_python.LanguageTool('en-US')

    def validate_grammer(self, content, field, role, delivery_id):
        errors = []
        if content is not None:
            cleaned_content = re.sub(r'`[^`]*`', '', content)
             # Remove any occurrences of ", ," (consecutive commas)
            cleaned_content = re.sub(r'\s*,\s*,', ',', cleaned_content)

            # Replace multiple spaces with a single space
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
            # Trim leading and trailing spaces
            cleaned_content = cleaned_content.strip()
            matches = self.tool.check(cleaned_content)
            
            for match in matches:
                if "too many consecutive spaces" in match.message:
                    continue
                errors.append({
                    "originalContent": content,
                    "error": match.message,
                    "suggestion": ', '.join(match.replacements) if match.replacements else ""
                })
            
            if errors:
                return {
                    "deliverableId": delivery_id,
                    "field": field,
                    "role": role,
                    "spellingError": errors
                }

        return None