import json
from .grammer_validation  import GrammarValidator

class RlhfImageGenValidator:
    def __init__(self, data):
        self.data = data
        self.grammar_check = GrammarValidator()
        
    def validate(self):
        errors = []  
        for entry in self.data:
            errors_list = []
            delivery_id = entry.get('deliverable_id')
            errors_list.extend(self.validate_deliverable_id(entry))
            errors_list.extend(self.validate_notes(entry))
            errors_list.extend(self.validate_messages(entry))
            if errors_list:
                errors.append({
                    "deliverableId": delivery_id,
                    "message": errors_list
                }) 
        if errors:
            filtered_data = [item for item in errors if not all(msg is None for msg in item['message'])]
            return filtered_data
        return errors
            
    def validate_deliverable_id(self, entry):
        errors = []
        if "deliverable_id" not in entry:
            errors.append("deliverable_id is missing.")
        elif not isinstance(entry["deliverable_id"], str) or not entry["deliverable_id"].strip():
            errors.append("deliverable_id must be a non-empty string.")
        return errors
    
    def validate_notes(self, entry):
        errors = []
        notes = entry.get("notes")
        if not notes:
            errors.append("notes is missing.")
            return errors
        
        # Validate task_category_list
        task_category_list = notes.get("task_category_list")
        if not isinstance(task_category_list, list) or len(task_category_list) == 0:
            errors.append("task_category_list must be a non-empty array.")
        else:
            for category in task_category_list:
                if not isinstance(category.get("category"), str) or not category.get("category").strip():
                    errors.append("category must be a non-empty string.")
                else:
                    errors.append(self.grammar_check.validate_grammer(category.get("category"),"task_category_list.category", None, None))
                    
                subcategory = category.get("subcategory")
                if not isinstance(subcategory, str) or not subcategory.strip():
                        errors.append("subcategory must be a non-empty string.")
                else:
                    errors.append(self.grammar_check.validate_grammer(category.get("subcategory"),"task_category_list.subcategory", None, None))

        # Validate annotator_ids
        annotator_ids = notes.get("annotator_ids")
        if not isinstance(annotator_ids, list) or len(annotator_ids) == 0:
            errors.append("annotator_ids must be a non-empty array.")
        elif not all(isinstance(annotator_id, str) and annotator_id.isdigit() for annotator_id in annotator_ids):
            errors.append("annotator_ids must contain only numeric strings.")
        return errors
    
    def validate_messages(self, entry):
        errors = []
        messages = entry.get("messages")
        if not isinstance(messages, list) or len(messages) == 0:
            errors.append("messages must be a non-empty array.")
            return errors

        first_message = messages[0]
        if first_message.get("role") != "user":
            errors.append("The first message must have the role 'user'.")
            return errors

        for message in messages:
            if "role" in message:
                role = message.get("role")
                if role in ["user"]:
                    content = message.get("contents")
                    errors.extend(self.validate_message_content(content, role))
               
        return errors
    
    def validate_message_content(self, content, role):
        errors = []
        # Check if content is a list
        if not isinstance(content, list):
            errors.append(f"{role} message content must be an array.")
            return  # Stop further validation if content is not a list

        # Check if the content list is empty
        if len(content) == 0:
            errors.append("{role} message content must not be an empty array.")
            return  # Stop further validation if content is empty

        # Loop through each item in the content array
        for cont in content:
            # Check if "text" key is present in each item
            if "text" in cont:
                # errors.append("Each content object must contain a 'text' property.")
                # Check if "text" is of type string
                if not isinstance(cont["text"], str):
                    errors.append("'text' property must be a string.")
                    

                # Check if the "text" string is non-empty after stripping whitespaces
                elif not cont["text"].strip():
                    errors.append("'text' property must not be an empty string after trimming.")
                else:
                    errors.append(self.grammar_check.validate_grammer(cont["text"],"content.text", None, None))

            
            
            # Check if "image" key is present in each item
            elif "image" in cont:
                image = cont.get("image")

                # Check if "url" key is present in the image object
                if "url" not in image:
                    errors.append("'image' object must contain a 'url' property.")
                    continue  # Move to the next item if URL is missing

                # Check if "url" is of type string and not null
                if not isinstance(image["url"], str) or not image["url"].strip():
                    errors.append("'url' in 'image' must be a non-empty string.")
        return errors