import json
from jsonschema import validate, ValidationError
from jsonschema.exceptions import SchemaError
import re

class SftSchemaValidator:
    def __init__(self):
        pass

    def validate_deliverable_id(self, deliverable_id):
        if not isinstance(deliverable_id, str):
            return "Deliverable ID should be a string."
        return None

    def validate_message(self, message, index, tools, expected_id_index, is_system):
        errors = []

        if "role" in message:
            role = message.get('role')
            if index == 0 and role not in ['system', 'user']:
                errors.append("First message role should be either 'system' or 'user'.")

            if role == 'user':
                errors.extend(self.validate_user_message(message))
            elif role == 'tool':
                errors.extend(self.validate_tool_message(message))

        elif "_message_type" in message:
            msg_type_errors, expected_id_index = self.validate_message_type(message, tools, expected_id_index, is_system) 
            errors.extend(msg_type_errors)

        else:
            errors.append(f"Message {index + 1} should have a 'role' or '_message_type' field.")

        return errors, expected_id_index

    def validate_user_message(self, message):
        errors = []
        extras_user = message.get('extras_user', {})

        if 'extras_user' in message:
            if 'user_context' not in extras_user or 'user_contexts' not in extras_user:
                errors.append("First user message should have 'extras_user' with 'user_context' and 'user_contexts'.")
            elif 'foreground_app' not in extras_user.get('user_contexts', {}):
                errors.append("'user_contexts' should contain 'foreground_app'.")
        
        if 'content' in message and (message.get('content') is None or message.get('content') == ''):
            errors.append("'content' should not be null or empty.")
        
        return errors

    def validate_message_type(self, message, tools, expected_id_index, is_system):
        errors = []
        if message.get('_message_type') != 'MessageBranch':
            errors.append("The second message should have '_message_type' as 'MessageBranch'.")

        choices = message.get('choices', [])
        if not isinstance(choices, list):
            errors.append("'choices' should be an array.")
        else:
            for index, choice in enumerate(choices):
                errors.extend(self.validate_choice(choice, is_system))
                errors.extend(self.validate_tool_used(choice, tools))
                errors.extend(self.validate_error_label_model(choice, tools))  # Call this for each choice
                errors.extend(self.validate_tool_and_selection_conditions_in_choices(index, choice, choices))

        errors.extend(self.validate_last_role_is_assistant(choices))
        
        return errors, expected_id_index

    def validate_tool_and_selection_conditions_in_choices(self, i, choice, choices):
        errors = []
        if choice.get('response_source') != 'human':
            error_labels = choice.get('other_properties', {}).get('error_labels', [])
            selected_overall = choice.get('other_properties', {}).get('selected_overall', True)
            
            # Condition 1: "tool_over_triggered" error and "selected_overall" is false
            if "tool_over_triggered" in error_labels and not selected_overall:
                # Check if the next choice exists
                if i + 1 < len(choices):
                    next_choice = choices[i + 1]
                    # Check if there are "tool_calls" in the next object
                    next_tool_calls = next_choice.get('messages', [{}])[0].get('tool_calls', [])
                    if next_tool_calls:
                        errors.append(f"Condition violated: obect[{i}] has tool_over_triggered, and tool_calls is found in the next object[{next_choice}] when they shouldn't be")
                        
            # Condition 2: "no_tool_triggered" error and "selected_overall" is false
            if "no_tool_triggered" in error_labels and not selected_overall:
                # Check if the next choice exists
                if i + 1 < len(choices):
                    next_choice = choices[i + 1]
                    # Check if there are no "tool_calls" in the next object
                    next_tool_calls = next_choice.get('messages', [{}])[0].get('tool_calls', [])
                    if not next_tool_calls:
                        errors.append(f"Condition violated: obect[{i}] has no_tool_triggered, and no tool_calls found in the next object[{next_choice}] when they should be")

        return errors  # Conditions satisfied

    def validate_last_role_is_assistant(self, choices):
        errors = []
        last_choice = choices[-1]
        # Check if 'messages' exists in the last choice and has at least one message
        messages = last_choice.get('messages', [])
        if not messages:
            errors.append("Invalid JSON: 'messages' array is missing or empty in the last choice.")

        # Get the last message in the last choice
        last_message = messages[-1]

        # Check if the role of the last message is 'assistant'
        if last_message.get("role") != "assistant":
            errors.append("Invalid: The last message does not have the role 'assistant'.")
        return errors
        
    def validate_choice(self, choice, is_system):
        errors = []
        response_source = choice.get('response_source')

        if response_source != 'human':
            errors.extend(self.validate_non_human_choice(choice, is_system))
        else:
            errors.extend(self.validate_human_choice(choice))

        return errors

    def validate_non_human_choice(self, choice, is_system):
        errors = []
        other_properties = choice.get('other_properties', {})

        if not isinstance(other_properties.get('selected_overall'), bool):
            errors.append("Other properties 'selected_overall' should be a boolean.")
        
        hyperparameters = choice.get('hyperparameters', {})
        errors.extend(self.validate_hyperparameters(hyperparameters, is_system))

        messages_in_choice = choice.get('messages', [])
        errors.extend(self.validate_choice_messages(messages_in_choice))

        if other_properties.get('selected_overall') is False:
            errors.extend(self.validate_critic_comments(other_properties))

        return errors
    
    def validate_error_label_model(self, choice, tools):
        errors = []
        #print(f"Debugging validate_error_label_model")
        #print(f"Choice: {json.dumps(choice, indent=2)}")

        # Check if response_source exists and is not "human"
        if choice.get("response_source") == "human":
            #print("Response source is human, skipping")
            return errors

        # Extract other_properties
        other_properties = choice.get("other_properties", {})
        #print(f"Other properties: {other_properties}")

        # Extract error_labels and critic_comments
        error_labels = other_properties.get("error_labels", [])
        critic_comments = other_properties.get("critic_comments", "")
        #print(f"Error labels: {error_labels}")
        #print(f"Critic comments: {critic_comments}")
        
        if "wrong_tool_used" not in error_labels:
            if "wrong_param_value" in error_labels or "enum_not_respected" in error_labels:
                #print("'wrong_param_value' or 'enum_not_respected' found in error_labels")
                tool_calls = choice.get("messages", [{}])[0].get("tool_calls", [])
                for tool_call in tool_calls:
                    function_name = tool_call.get("function", {}).get("name")
                    arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                    #print(f"Function name: {function_name}")
                    #print(f"Arguments: {arguments}")
                    
                    tool = tools.get(function_name)
                    
                    if tool:
                        #print(f"Tool found: {tool['name']}")
                        schema = tool["parameters"]
                        #print(f"Schema: {json.dumps(schema, indent=2)}")
                        
                        enum_violation = False
                        wrong_param_value = False
                        extra_params = []

                        for param, value in arguments.items():
                            #print(f"Checking parameter: {param}, value: {value}")
                            if param in schema.get("properties", {}):
                                param_schema = schema["properties"][param]
                                #print(f"Parameter schema: {param_schema}")
                                if "enum" in param_schema:
                                    #print(f"Enum found for {param}: {param_schema['enum']}")
                                    if str(value).lower() not in [str(e).lower() for e in param_schema["enum"]]:
                                        enum_violation = True
                                        #print(f"Enum violation found: {param}={value} not in {param_schema['enum']}")
                                elif "type" in param_schema:
                                    if not self.check_type(value, param_schema["type"]):
                                        wrong_param_value = True
                                        #print(f"Type mismatch: {param}={value} is not of type {param_schema['type']}")
                            else:
                                extra_params.append(param)
                        
                        if enum_violation and "enum_not_respected" not in error_labels:
                            errors.append("Error label 'enum_not_respected' should be present for enum violation for tool "+function_name)
                        elif not enum_violation and "enum_not_respected" in error_labels:
                            errors.append("Error label 'enum_not_respected' is used, but no enum violation was found for tool "+function_name)
                        
                        #if wrong_param_value and "wrong_param_value" not in error_labels:
                            #errors.append("Error label 'wrong_param_value' should be present for type mismatch.")
                        #elif not wrong_param_value and "wrong_param_value" in error_labels:
                            #errors.append("Error label 'wrong_param_value' is used, but all parameter values are valid.")
                        
                        #if extra_params:
                            #if "extra_param_predicted" not in error_labels:
                                #errors.append(f"Error label 'extra_param_predicted' should be present for extra parameters: {', '.join(extra_params)}")
                        # elif "extra_param_predicted" in error_labels:
                            #errors.append("Error label 'extra_param_predicted' is used, but no extra parameters were found.")
                    else:
                        #print(f"Tool '{function_name}' not found in the tools list")
                        errors.append(f"Tool '{function_name}' not found in the tools list.")

        #print(f"Final errors: {errors}")
        return errors

    def check_type(self, value, expected_type):
        if expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        return True  # For other types, assume it's correct

    def validate_object_schema(self, schema, function_name):
        errors = set()  # Use a set instead of a list to avoid duplicates
        
        if "type" not in schema:
            errors.add(f"Schema for '{function_name}' is missing the 'type' key at the top level.")
            return errors

        if schema.get("type") == "object":
            properties = schema.get("properties")
            if properties is None:
                errors.add(f"Schema for '{function_name}' has type 'object' but is missing the 'properties' key.")
            else:
                for prop_name, prop_schema in properties.items():
                    try:
                        if prop_schema.get("type") == "object":
                            nested_errors = self.validate_object_schema(prop_schema, f"{function_name}.{prop_name}")
                            errors.update(nested_errors)
                        elif prop_schema.get("type") == "array":
                            items = prop_schema.get("items", {})
                            if items.get("type") == "object" and "properties" not in items:
                                errors.add(f"Array items in '{function_name}.{prop_name}' are of type 'object' but missing 'properties' key.")
                    except Exception as e:
                        errors.add(f"Error processing '{function_name}.{prop_name}': {str(e)}")
                        # Log the error with deliverable_id
                        self.log_error(f"Error in validate_object_schema for '{function_name}.{prop_name}': {str(e)}")
        
        return errors

    def log_error(self, error_message):
        # Assuming self.current_deliverable_id is set somewhere in the class
        deliverable_id = getattr(self, 'current_deliverable_id', 'Unknown')
        print(f"Error for deliverable_id {deliverable_id}: {error_message}")
        # You can also log to a file or use a proper logging system here

    def validate_tool_used(self, choice, tools):
        errors = []
        if choice.get("other_properties", {}).get("selected_overall"):
            choice_messages = choice.get("messages", [])
            for message in choice_messages:
                if "tool_calls" in message:
                    for tool_call in message.get("tool_calls", []):
                        function_name = tool_call.get("function", {}).get("name").strip()
                        arguments = tool_call.get("function", {}).get("arguments")
                        
                        # Check if the function name exists in the tools
                        if function_name not in tools or tools[function_name]["name"] != function_name:
                            errors.append(f"Function '{function_name}' not found in tools.")
                            continue

                        tool_properties = tools[function_name].get("parameters", {}).get("properties", {})
                        required_fields = tools[function_name].get("parameters", {}).get("required", [])
                        
                        schema = {
                            "type": "object",
                            "properties": tool_properties,
                            "required": required_fields,
                            "additionalProperties": False
                        }
                        
                        # Parse arguments if it's a string
                        if isinstance(arguments, str):
                            try:
                                arguments = json.loads(arguments)
                            except json.JSONDecodeError:
                                errors.append(f"Invalid JSON format in arguments for function '{function_name}'.")
                                continue

                        # Validate nested objects recursively
                        def validate_nested_object(arg_obj, schema_obj, path=""):
                            nested_errors = []
                            
                            # Check for additional properties
                            if schema_obj.get("type") == "object":
                                schema_props = schema_obj.get("properties", {})
                                if not isinstance(arg_obj, str):
                                    actual_props = arg_obj.keys()
                                    extra_props = set(actual_props) - set(schema_props.keys())
                                    if extra_props and schema_obj.get("additionalProperties", False) is False:
                                        error_path = f"{function_name}.{path}" if path else function_name
                                        nested_errors.append(f"Extra fields found in {error_path}: {extra_props}")
                                    
                                    # Validate each property
                                    for prop_name, prop_value in arg_obj.items():
                                        if prop_name in schema_props:
                                            prop_schema = schema_props[prop_name]
                                            new_path = f"{path}.{prop_name}" if path else prop_name
                                            
                                            if isinstance(prop_value, dict) and prop_schema.get("type") == "object":
                                                nested_errors.extend(validate_nested_object(prop_value, prop_schema, new_path))
                        
                            return nested_errors

                        # Validate the entire argument structure
                        validation_errors = validate_nested_object(arguments, schema)
                        errors.extend(validation_errors)

        return errors

    def validate_tool_call_ids(self, choice, expected_id_index):
        errors = []
        if 'response_source' in choice and choice.get("response_source") != "human":
            choice_messages = choice.get("messages", [])
            for msg in choice_messages:
                if 'tool_calls' in msg:
                    for tool_call in msg.get('tool_calls', []):
                        tool_id = tool_call.get('id')

                        if not tool_id:
                            errors.append(f"Error: Missing ID in tool_call: {tool_call}")
                            break
                        
                        match = re.match(r'call_(\d+)', tool_id)
                        if match:
                            call_index = int(match.group(1))
                            
                            if call_index != expected_id_index:
                                errors.append(f"Error: Incorrect ID increment. Expected 'call_{expected_id_index}' but got '{tool_id}'.")
                            
                            expected_id_index += 1
                        else:
                            errors.append(f"Error: Invalid ID format '{tool_id}'.")
        return errors, expected_id_index

    def stripe_quote(self, quoted_string):
        if isinstance(quoted_string, str):
            stripped_string = quoted_string.strip('"')
            try:
                json_object = json.loads(stripped_string)
                return json_object
            except json.JSONDecodeError as e:
                return quoted_string
        return quoted_string

    def check_extra_fields(self, payload, schema):
        schema_fields = schema.get('properties', {}).keys()
        payload_fields = payload.keys()
        extra_fields = set(payload_fields) - set(schema_fields)
        return extra_fields

    def validate_arguments_with_schema(self, arguments, schema):
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format in arguments: {e}"
    
        extra_fields = self.check_extra_fields(arguments, schema)
        if extra_fields:
            return False, f"Payload contains extra fields not in schema: {extra_fields}"
        
        try:
            validate(instance=arguments, schema=schema)
            return True, "Arguments are valid"
        except SchemaError as e:
            error_message = f"SchemaError: {str(e)}"
            print(f"Error for deliverable_id {self.current_deliverable_id}: {error_message}")
            return False, error_message
        except ValidationError as e:
            return False, f"Validation error: {e.message}"

    def validate_human_choice(self, choice):
        errors = []
        messages_in_choice = choice.get('messages', [])
        for message in messages_in_choice:
            if message.get('role') != 'assistant':
                errors.append("Message role in human response response_source should be 'assistant'.")
            if 'content' in message and 'extras_assistant' not in message:
                errors.append("Extras_assistant should be present in human response response_source messages.")
            if not message.get('extras_assistant'):
                errors.append("Reasoning comment should be present in human response response_source messages.")
        
        other_properties = choice.get('other_properties', {})
        if not isinstance(other_properties.get('selected_overall'), bool):
            errors.append("Other properties 'selected_overall' should be a boolean.")
        
        return errors

    def validate_hyperparameters(self, hyperparameters, is_system):
        errors = []
        if not isinstance(hyperparameters.get('model_id'), str):
            errors.append("Hyperparameters 'model_id' should be a string.")
        if not isinstance(hyperparameters.get('temperature'), float):
            errors.append("Hyperparameters 'temperature' should be a float.")
        if not isinstance(hyperparameters.get('top_p'), float):
            errors.append("Hyperparameters 'top_p' should be a float.")
        if is_system:
            if not isinstance(hyperparameters.get('system_prompt'), str):
                errors.append("Hyperparameters system prompt is required.")
        
        return errors

    def validate_choice_messages(self, messages_in_choice):
        errors = []
        if not isinstance(messages_in_choice, list):
            errors.append("Messages in choices should be an array.")
        else:
            for message in messages_in_choice:
                if message.get('role') != 'assistant':
                    errors.append("Message role should be 'assistant'.")
                if message.get('content') is None and 'tool_calls' not in message:
                    errors.append("Tool_calls should be present when content is null.")

        return errors

    def validate_critic_comments(self, other_properties):
        errors = []
        critic_comments = other_properties.get("critic_comments", "")
        error_labels = other_properties.get("error_labels", [])
        
        if len(error_labels) < 1:
            errors.append("Error labels should have a reason if selected_overall is false.")
        
        # Validate error_labels: ensure no empty or whitespace-only strings
        elif any(not self.is_valid_string(label) for label in error_labels):
            errors.append("Condition violated: error_labels contain empty or whitespace-only strings")
        elif not critic_comments.strip() and error_labels:
            errors.append("Critic comments should be present if selected_overall is false.")
        else:
            comments_split = critic_comments.split('\n') if critic_comments else []
            if len(comments_split) != len(error_labels):
                errors.append(f"Condition failed. Number of critic comments ({len(comments_split)}) does not match number of error labels ({len(error_labels)}).")
        return errors
    
    def is_valid_string(self,item):
        return item and not item.isspace()

    def validate_schema(self, obj):
        errors = set()
        delivery_id = obj.get('deliverable_id')
        self.current_deliverable_id = delivery_id  # Set the current deliverable_id

        tools = obj.get("tools", [])
        for tool in tools:
            function = tool.get("function", {})
            function_name = function.get("name", "Unknown")
            parameters = function.get("parameters", {})
            try:
                tool_errors = self.validate_object_schema(parameters, function_name)
                errors.update(tool_errors)
            except SchemaError as e:
                error_message = f"SchemaError in tool '{function_name}': {str(e)}"
                print(f"Error for deliverable_id {delivery_id}: {error_message}")
                errors.add(error_message)

        tools_dict = {tool["function"]["name"]: tool["function"] for tool in tools}
        
        error = self.validate_deliverable_id(delivery_id)
        expected_id_index = 0
        if error:
            errors.add(error)

        messages = obj.get('messages', [])
        if not isinstance(messages, list):
            errors.add("Messages should be an array.")
        else:
            is_system = messages[0].get('role') == 'system'
            for index, message in enumerate(messages):
                try:
                    message_errors, expected_id_index = self.validate_message(message, index, tools_dict, expected_id_index, is_system)
                    errors.update(message_errors)
                except SchemaError as e:
                    error_message = f"SchemaError in message {index}: {str(e)}"
                    print(f"Error for deliverable_id {delivery_id}: {error_message}")
                    errors.add(error_message)

        if errors:
            return {
                "deliverableId": delivery_id,
                "message": list(errors)
            }
        return None

    def process_schema_validation(self, data):
        errors_list = []
        for i, obj in enumerate(data):
            result = self.validate_schema(obj)
            if result:
                errors_list.append(result)
        
        return errors_list

    def validate_tool_message(self, message):
        errors = []
        content = message.get('content')
        
        if not isinstance(content, str):
            errors.append("Tool message content should be a string.")
        else:
            try:
                json.loads(content)
            except json.JSONDecodeError:
                errors.append("Tool message content should be a valid JSON string.")
        
        if 'tool_call_id' not in message:
            errors.append("Tool message should have a 'tool_call_id' field.")
        
        if 'name' not in message:
            errors.append("Tool message should have a 'name' field.")
        
        return errors