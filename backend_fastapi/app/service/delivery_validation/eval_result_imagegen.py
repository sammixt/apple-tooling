class EvalImageGenValidator:
    def __init__(self, data):
        self.data = data
        
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
        messages = entry.get("messages")
        
        # Validate task_category_list
        task_category_list = notes.get("task_category_list")
        if not isinstance(task_category_list, list) or len(task_category_list) == 0:
            errors.append("task_category_list must be a non-empty array.")
        else:
            for category in task_category_list:
                if not isinstance(category.get("category"), str) or not category.get("category").strip():
                    errors.append("category must be a non-empty string.")
                subcategory = category.get("subcategory")
                if not isinstance(subcategory, str) or not subcategory.strip():
                    errors.append("subcategory must be a non-empty string.")
                
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

        for message in messages:
            if "role" in message:
                role = message.get("role")
                if role in ["user"]:
                    content = message.get("contents")
                    errors.extend(self.validate_message_content(content, role))
            elif "_message_type" in message:
                if message["_message_type"] != "MessageBranch":
                    errors.append("_message_type must be 'MessageBranch'.")

                choices = message.get("choices")
                if not isinstance(choices, list) or len(choices) == 0:
                    errors.append("choices must be a non-empty array.")
                else:
                   errors.extend(self.validate_choices(choices,message))
               
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
                errors.append("Each content object must contain a 'text' property.")
        return errors
    
    def validate_choices(self, choices, message):
        errors = []
        
        if len(choices) != 2:
            errors.append(f"'choices' must contain exactly 2 objects, found {len(choices)}.")
            return errors
        
        model_a = choices[0]
        model_b = choices[1]
        
        # Ensure both models are present
        if not model_a or not model_b:
            errors.append("Both model-a and model-b choices must be present.")
            return errors
        
        errors.extend(self.validate_nested_messages(model_a))
        errors.extend(self.validate_nested_messages(model_b))
        
        misc_properties = message.get("misc_properties")
        if not isinstance(misc_properties, dict) or "ranking_overall" not in misc_properties:
            errors.append("misc_properties must contain ranking_overall.")
        else:
            ranking = misc_properties.get("ranking_overall")
            if ranking:
                errors.extend(self.validate_ranking(ranking, model_a, model_b))
        return errors
    
    def validate_nested_messages(self, choice):
        errors = []
        messages = choice.get("messages")
        if not isinstance(messages, list) or len(messages) == 0:
            errors.append("choices must contain messages array.")
        for message in messages:
            if message.get("role") != "assistant":
                errors.append("Message role in choices must be 'assistant'.")
            content = message.get("contents")
            if not isinstance(content, list) or len(content) == 0:
                errors.append("Assistant message content must be a non-empty array with text properties.")
            # Check if "image" key is present in each item
            elif "image" in content[0]:
                image = content[0].get("image")
                # Check if "url" key is present in the image object
                if "url" not in image:
                    errors.append("'image' object must contain a 'url' property.")
                    continue  # Move to the next item if URL is missing

                # Check if "url" is of type string and not null
                elif not isinstance(image["url"], str) or not image["url"].strip():
                    errors.append("'url' in 'image' must be a non-empty string.")
            else: 
                errors.append("Contents must contain an image property.")
        
        other_properties = choice.get("other_properties")
        if not isinstance(other_properties, dict) or "selected_overall" not in other_properties or not isinstance(other_properties["selected_overall"], bool):
            errors.append("other_properties must contain 'selected_overall' as boolean.")
        original_ratings = other_properties.get("original_ratings")
        if original_ratings:
            errors.extend(self.validate_ratings(original_ratings))
        else:
            errors.extend(self.validate_ratings(other_properties))
        return errors
    
    def validate_ratings(self, ratings):
        ALLOWED_RATING_VALUES = [0, 1, 2, 3, 4, 5]
        RATING_FIELDS = [
            "rating_accuracy", "rating_creativity", "rating_visual_appeal",
            "rating_aesthetic_quality", "rating_clarity", "rating_coherence",
            "rating_thematic_impact"
        ]
        errors = []
        
        def validate_rating(key, value):
            if value not in ALLOWED_RATING_VALUES:
                return f"{key} must have one of the following values: {', '.join(map(str, ALLOWED_RATING_VALUES))}."
            return None

        for field in RATING_FIELDS:
            if field not in ratings:
                errors.append(f"{field} is missing.")
            else:
                error_message = validate_rating(field, ratings[field])
                if error_message:
                    errors.append(error_message)

        return errors
    
    def validate_ranking(self, ranking, model_a, model_b):
        errors = []
        # Validate based on the ranking statement
        if ranking in ["Right (B) is much better", "Right (B) is better", "Right (B) is slightly better", "Right (B) is negligibly better"]:
            # Check if model-b has a higher overall score than model-a
            if model_b["other_properties"]["rating_overall_score"] <= model_a["other_properties"]["rating_overall_score"]:
                errors.append("Model B should have a higher rating_overall_score than Model A.")

            # Check selected_overall values
            if not model_b["other_properties"]["selected_overall"] or model_a["other_properties"]["selected_overall"]:
                errors.append("Model B should be selected_overall and Model A should not be.")

        elif ranking in ["Left (A) is much better", "Left (A) is better", "Left (A) is slightly better", "Left (A) is negligibly better"]:
            # Check if model-a has a higher overall score than model-b
            if model_a["other_properties"]["rating_overall_score"] <= model_b["other_properties"]["rating_overall_score"]:
                errors.append("Model A should have a higher rating_overall_score than Model B.")

            # Check selected_overall values
            if not model_a["other_properties"]["selected_overall"] or model_b["other_properties"]["selected_overall"]:
                errors.append("Model A should be selected_overall and Model B should not be.")

        return errors
        