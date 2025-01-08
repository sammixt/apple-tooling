import json
import difflib


class RlhfValidator:
    def __init__(self, data):
        self.data = data
        self.other_prop = {
            "satisfaction_levels": {
                "horrible": 1,
                "pretty bad": 2,
                "ok": 3,
                "okay": 3,
                "pretty good": 5,
                "amazing": 6,
            },
            "rating_instruction_following": {"major issues": 1, "minor issues": 2, "no issues": 3},
            "rating_truthfulness": {"major issues": 1, "minor issues": 2, "no issues": 3},
            "rating_verbosity": {"too short": 1, "too verbose": 2, "just right": 3},
            "rating_harmlessness": {"major issues": 1, "minor issues": 2, "no issues": 3},
        }
        self.valid_code_languages = {"C++", "Go", "Java", "JavaScript", "Python", "Swift"}

    def validate(self):
        errors = []
        for entry in self.data:
            errors_list = []
            delivery_id = entry.get("deliverable_id")
            errors_list.extend(self.validate_deliverable_id(entry))
            errors_list.extend(self.validate_notes(entry))
            errors_list.extend(self.validate_messages(entry))
            if errors_list:
                errors.append({"deliverableId": delivery_id, "message": errors_list})
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
        is_vision = self.is_rlhf_vision(messages)

        # Validate task_category_list
        task_category_list = notes.get("task_category_list")
        if not isinstance(task_category_list, list) or len(task_category_list) == 0:
            errors.append("task_category_list must be a non-empty array.")
        else:
            for category in task_category_list:
                if not isinstance(category.get("category"), str) or not category.get("category").strip():
                    errors.append("category must be a non-empty string.")
                subcategory = category.get("subcategory")
                if is_vision:
                    if not isinstance(subcategory, str) or not subcategory.strip():
                        errors.append("subcategory must be a non-empty string.")
                else:
                    if (
                        not isinstance(subcategory, list)
                        or len(subcategory) == 0
                        or not all(sub.strip() for sub in subcategory)
                    ):
                        errors.append("subcategory must be a non-empty array with non-empty strings.")

        # Validate annotator_ids
        annotator_ids = notes.get("annotator_ids")
        if not isinstance(annotator_ids, list) or len(annotator_ids) == 0:
            errors.append("annotator_ids must be a non-empty array.")
        elif not all(isinstance(annotator_id, str) and annotator_id.isdigit() for annotator_id in annotator_ids):
            errors.append("annotator_ids must contain only numeric strings.")

        # Validate main_coding_language
        is_vision = self.is_rlhf_vision(messages)
        if not is_vision:
            annotator_ids = notes.get("main_coding_language")
            if not notes.get("main_coding_language") or notes["main_coding_language"] not in self.valid_code_languages:
                errors.append("Invalid or missing main coding language")
        return errors

    def validate_messages(self, entry):
        errors = []
        messages = entry.get("messages")
        if not isinstance(messages, list) or len(messages) == 0:
            errors.append("messages must be a non-empty array.")
            return errors

        # first_message = messages[0]
        # if first_message.get("role") != "user":
        #     errors.append("The first message must have the role 'user'.")

        for message in messages:
            if "role" in message:
                role = message.get("role")
                if role in ["user", "system"]:
                    content = message.get("contents")
                    errors.extend(self.validate_message_content(content, role))
            elif "_message_type" in message:
                if message["_message_type"] != "MessageBranch":
                    errors.append("_message_type must be 'MessageBranch'.")

                choices = message.get("choices")
                if not isinstance(choices, list) or len(choices) == 0:
                    errors.append("choices must be a non-empty array.")
                else:
                    errors.extend(self.validate_choices(choices, message))

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

    def is_rlhf_vision(self, messages):
        is_vision = False
        for message in messages:
            contents = message.get("contents", [])
            if any("image" in content for content in contents):
                is_vision = True
                break
        return is_vision

    def validate_choices(self, choices, message):
        errors = []
        true_selected = false_selected = 0

        for i, choice in enumerate(choices):
            if not isinstance(choice.get("response_source"), str) or not choice["response_source"].strip():
                errors.append("response_source must be a non-empty string.")
            hyperparameters = choice.get("hyperparameters")
            if (
                not isinstance(hyperparameters, dict)
                or hyperparameters.get("model_id") != choice["response_source"]
                or not isinstance(hyperparameters.get("temperature"), float)
            ):
                errors.append("hyperparameters must contain valid model_id and temperature.")
            errors.extend(self.validate_nested_messages(choice))

            other_properties = choice.get("other_properties")
            if (
                not isinstance(other_properties, dict)
                or "selected_overall" not in other_properties
                or not isinstance(other_properties["selected_overall"], bool)
            ):
                errors.append("other_properties must contain 'selected_overall' as boolean.")
            else:
                if other_properties["selected_overall"]:
                    true_selected += 1
                else:
                    false_selected += 1

        if len(choices) == 2:
            model_a = choices[0]
            model_b = choices[1]

            # Validate ideal response
            errors.extend(self.validate_ideal_response(model_a, model_b))

            misc_properties = message.get("misc_properties")
            if not isinstance(misc_properties, dict) or "ranking_overall" not in misc_properties:
                errors.append("misc_properties must contain ranking_overall.")
            else:
                ranking = misc_properties.get("ranking_overall")
                if ranking:
                    errors.extend(self.validate_ranking(model_a, model_b, ranking))
        else:
            errors.append("2 choises should be available.")

        # Ensure there is exactly one choice with selected_overall as True and one as False
        if true_selected != 1 or false_selected != 1:
            errors.append(
                "Each choices array must have exactly one object with selected_overall as True and one with selected_overall as False."
            )
        return errors

    def validate_nested_messages(self, choice):
        errors = []
        messages = choice.get("messages")
        if not isinstance(messages, list) or len(messages) == 0:
            errors.append("choices must contain messages array.")
        for message in messages:
            errors.extend(self.validate_message_content_text(message))

        other_properties = choice.get("other_properties")
        if (
            not isinstance(other_properties, dict)
            or "selected_overall" not in other_properties
            or not isinstance(other_properties["selected_overall"], bool)
        ):
            errors.append("other_properties must contain 'selected_overall' as boolean.")
        current_ratings = other_properties.get("current_ratings")
        original_ratings = other_properties.get("original_ratings")
        original_messages = other_properties.get("original_messages")
        # Validate that both or neither are present
        # if (original_ratings is None) != (original_messages is None):  # XOR logic
        #     errors.append("original_ratings and original_messages must both be present or both absent.")
        if original_messages:
            for message in original_messages:
                errors.extend(self.validate_message_content_text(message))
        if original_ratings:
            errors.extend(self.validate_ratings(original_ratings))
        elif current_ratings:
            errors.extend(self.validate_ratings(current_ratings))
        else:
            errors.extend(self.validate_ratings(other_properties))
        return errors

    def validate_ratings(self, ratings):
        errors = []
        allowed_values = {
            "rating_instruction_following": ["major issues", "minor issues", "no issues"],
            "rating_truthfulness": ["major issues", "minor issues", "no issues"],
            "rating_verbosity": ["too short", "too verbose", "just right"],
            "rating_harmlessness": ["major issues", "minor issues", "no issues"],
            "rating_overall_satisfaction": ["pretty bad", "horrible", "ok", "amazing", "pretty good", "okay"],
        }
        image_value = {
            "rating_image_understanding": ["not at all", "partially", "completely"],
        }
        for key, values in allowed_values.items():
            if key not in ratings or ratings[key].lower() not in values:
                errors.append(f"{key} must have one of the following values: {', '.join(values)}.")
        if "rating_image_understanding" in ratings:
            for key, values in image_value.items():
                if key not in ratings or ratings[key].lower() not in values:
                    errors.append(f"{key} must have one of the following values: {', '.join(values)}.")
        return errors

    def get_rating_info(self, model):
        props = model.get("other_properties")
        rating = (
            props.get("rating_overall_satisfaction")
            or props.get("original_ratings", {}).get("rating_overall_satisfaction")
            or props.get("current_ratings", {}).get("rating_overall_satisfaction")
            or props.get("rating_satisfaction")
            or props.get("original_ratings", {}).get("rating_satisfaction")
        )
        selected_overall = props.get("selected_overall", props.get("original_ratings", {}).get("selected_overall"))
        satisfaction_value = self.other_prop["satisfaction_levels"].get(rating.lower(), 0) if rating else 0
        return satisfaction_value, selected_overall

    def check_satisfaction_errors(self, errors, selected, satisfaction_a, satisfaction_b, ranking_side):
        if not selected:
            errors.append(
                f"For '{ranking_side} is better' ranking, the selected choice must have 'selected_overall' as True."
            )
        elif satisfaction_a < satisfaction_b:
            errors.append(
                f"For '{ranking_side}' ranking, {ranking_side} ranking must have a better rating_overall_satisfaction than the other side."
            )

    def validate_ranking(self, model_a, model_b, ranking):
        # Initialize errors container
        errors = []

        # Get satisfaction and selection values for both models
        satisfaction_value_a, selected_overall_a = self.get_rating_info(model_a)
        satisfaction_value_b, selected_overall_b = self.get_rating_info(model_b)

        # Process ranking phrase
        phrase = ranking.lower()
        match phrase:
            case "left (a) much better" | "left (a) better" | "left (a) slightly better":
                self.check_satisfaction_errors(
                    errors, selected_overall_a, satisfaction_value_a, satisfaction_value_b, "Left (A)"
                )
            case "left (a) negligibly better":
                if selected_overall_a and satisfaction_value_a < satisfaction_value_b:
                    errors.append(
                        "For 'Left negligibly better' ranking, Left ranking must have a slightly better rating."
                    )
            case "right (b) much better" | "right (b) better" | "right (b) slightly better":
                self.check_satisfaction_errors(
                    errors, selected_overall_b, satisfaction_value_b, satisfaction_value_a, "Right (B)"
                )
            case "right (b) negligibly better":
                if selected_overall_b and satisfaction_value_b < satisfaction_value_a:
                    errors.append(
                        "For 'Right negligibly better' ranking, Right ranking must have a slightly better rating."
                    )
            case _:
                errors.append("No specific rating comparison available.")

        return errors

    def validate_message_content_text(self, message):
        """
        Validates a single message for the required structure and constraints.

        :param message: Dictionary containing message details.
        :return: List of error messages, if any.
        """
        errors = []
        if message.get("role") != "assistant":
            errors.append("Message role in choices must be 'assistant'.")

        content = message.get("contents")
        if (
            not isinstance(content, list)
            or len(content) == 0
            or not all(
                "text" in cont
                and isinstance(cont["text"], str)
                and cont["text"].strip()
                and len(cont["text"].strip()) > 10
                for cont in content
            )
        ):
            errors.append(
                "Assistant message content must be a non-empty array with text properties and content greater than 10."
            )

        return errors

    def validate_ideal_response(self, model_a, model_b):
        error = []
        other_properties_a = model_a.get("other_properties")
        other_properties_b = model_b.get("other_properties")
        original_ratings_a = other_properties_a.get("original_ratings")
        original_ratings_b = other_properties_b.get("original_ratings")
        original_messages_a = other_properties_a.get("original_messages")
        original_messages_b = other_properties_b.get("original_messages")
        if original_ratings_a and original_messages_a:
            rating_overall_satisfaction = original_ratings_a.get("rating_overall_satisfaction", "")
            satisfaction_value_a = self.other_prop["satisfaction_levels"].get(rating_overall_satisfaction.lower(), 0)
            rating_overall_satisfaction_b = original_ratings_b.get("rating_overall_satisfaction", "")
            satisfaction_value_b = self.other_prop["satisfaction_levels"].get(rating_overall_satisfaction_b.lower(), 0)
            if satisfaction_value_a not in (1, 2) and satisfaction_value_b not in (1, 2):
                error.append(
                    f"rating_overall_satisfaction should be pretty bad or horrible if original_messages and original original_ratings is present for both model, but found model a: {rating_overall_satisfaction} and model b: {rating_overall_satisfaction_b}"
                )
            if not other_properties_a.get("selected_overall"):
                error.append(
                    f"select_overall should be True if model has Ideal response (original_ratings and original_messages)"
                )
            messages = model_a.get("messages", [])
            original_message = other_properties_a.get("original_messages", [])
            message_text = self.get_text_content(messages)
            original_message_text = self.get_text_content(original_message)

            # Calculate similarity
            if message_text is None or original_message_text is None:
                error.append(
                    "Error: Either the message or the ideal response text is missing. Cannot calculate similarity."
                )
            else:
                # Calculate similarity
                similarity = self.calculate_similarity(message_text, original_message_text)
                if similarity >= 0.9:
                    error.append(
                        f"Error: The message and Ideal response are {similarity * 100:.2f}% similar, which is over 90%."
                    )

        elif original_ratings_b and original_messages_b:
            rating_overall_satisfaction = original_ratings_b.get("rating_overall_satisfaction", "")
            satisfaction_value_b = self.other_prop["satisfaction_levels"].get(rating_overall_satisfaction.lower(), 0)
            rating_overall_satisfaction_a = original_ratings_a.get("rating_overall_satisfaction", "")
            satisfaction_value_a = self.other_prop["satisfaction_levels"].get(rating_overall_satisfaction_a.lower(), 0)
            if satisfaction_value_b not in (1, 2) and satisfaction_value_a not in (1, 2):
                error.append(
                    f"rating_overall_satisfaction should be pretty bad or horrible if original_messages and original original_ratings is present for both model, but found model b: {rating_overall_satisfaction} and model a: {rating_overall_satisfaction_a}"
                )
            if not other_properties_b.get("selected_overall"):
                error.append(
                    f"select_overall should be True if model has Ideal response (original_ratings and original_messages)"
                )

            messages = model_b.get("messages", [])
            original_message = other_properties_b.get("original_messages", [])
            message_text = self.get_text_content(messages)
            original_message_text = self.get_text_content(original_message)

            # Calculate similarity
            if message_text is None or original_message_text is None:
                error.append(
                    "Error: Either the message or the ideal response text is missing. Cannot calculate similarity."
                )
            else:
                # Calculate similarity
                similarity = self.calculate_similarity(message_text, original_message_text)
                if similarity >= 0.9:
                    error.append(
                        f"Error: The message and Ideal response are {similarity * 100:.2f}% similar, which is over 90%."
                    )
        return error

    def calculate_similarity(self, text1, text2):
        """
        Calculate the similarity between two strings using SequenceMatcher from difflib.
        Returns a float between 0 and 1.
        """
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def get_text_content(self, messages):
        if messages and "contents" in messages[0] and messages[0]["contents"]:
            message_text = messages[0]["contents"][0].get("text", "")
            return message_text
        else:
            return None
