import json

class SftCodeIntValidation:

    def __init__(self, data):
        self.json_data = data

    def validate(self):
        records_to_be_removed = []
        print('sft code int validation started')
        for record in self.json_data:
            try:
                delivery_id = record['deliverable_id']
                
                # Check task category list count matches user message count
                task_category_list_count = len(record["notes"]["task_category_list"])
                user_message_count = sum(1 for message in record["messages"] if message.get("role") == "user")

                if task_category_list_count != user_message_count:
                    records_to_be_removed.append({
                        "deliverableId": delivery_id,
                        "message": f"Task category list count ({task_category_list_count}) does not match user message count ({user_message_count})."
                    })

                # Build sequence list
                sequence_list = []
                for message in record['messages']:
                    if message['role'] == 'user':
                        sequence_list.append('User')
                    elif message['role'] == 'assistant' and message.get('contents') is not None:
                        sequence_list.append('Assistant')
                    elif message['role'] == 'assistant' and message.get('content') is None:
                        sequence_list.append('Code Block')
                    elif message['role'] == 'tool':
                        sequence_list.append('Code Output')

                # Check task sequence
                is_success, message = self.check_task_sequence(sequence_list)
                if not is_success:
                    records_to_be_removed.append({
                        "deliverableId": delivery_id,
                        "message": message
                    })

            except Exception as e:
                print(f"Exception occurred: {e} - FAILED_VALIDATION:")
        return records_to_be_removed

    def check_task_sequence(self, task_sequence):
        # Define the expected sequences for turn types 1 and 2
        type_1 = ["User", "Assistant", "Code Block", "Code Output", "Assistant"]
        type_2 = ["User", "Assistant", "Assistant", "Code Block", "Code Output", "Assistant"]

        message = ""
        turns, index, sequence_count = [], 0, len(task_sequence)

        while index < sequence_count:
            # Check for Type 2 turn first
            if task_sequence[index:index + len(type_2)] == type_2:
                turns.append(type_2)
                index += len(type_2)
            # Check for Type 1 turn
            elif task_sequence[index:index + len(type_1)] == type_1:
                turns.append(type_1)
                index += len(type_1)
            else:
                # Mark invalid turns
                message += f"Invalid turn starting at position {index + 1}: Does not match type 1 or type 2 format."
                break

        # Validate each turn
        for i, turn in enumerate(turns, start=1):
            if turn != type_1 and turn != type_2:
                message += f" Turn {i}: Invalid order or missing block."
                if len(turn) != len(type_1) and len(turn) != len(type_2):
                    message += f"Error: Turn {i} has incorrect number of blocks."
                else:
                    message += f"Error: Turn {i} does not match the expected order of type 1 or type 2."
                return False, message

        return True, ""