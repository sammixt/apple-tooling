def count_sft(messages):
    sft_count = 0
    for message in messages:
        if "_message_type" in message and message["_message_type"] == "MessageBranch":
            choices = message.get("choices", [])
            for choice in choices:
                other_properties = choice.get("other_properties", {})
                if other_properties.get("selected_overall") and choice.get("response_source") == "human":
                    sft_count += 1
    return sft_count

def process_json_data(json_data, workstream):
    subcategory_groups = {}
    difficulty_level = {}
    main_coding_language_groups = {}
    image_distribution_groups = {}
    section_sum_sft_reasoning = 0

    if len(json_data) > 0:
        # Initialize counters and category dictionary
        total_conversations = 0
        total_user_turns = 0
        category_groups = {}
        ideal_sft = 0
        rlhf = 0

        # Helper function to count sft turns in a list of messages, only for 2410-sft-tools
        def count_sft_for_sft_tool_in_messages(messages):
            nonlocal ideal_sft
            for message in messages:
                ideal_sft += count_sft([message])

        # Helper function to count user turns in a list of messages
        def count_user_turns_in_messages(messages):
            nonlocal total_user_turns, rlhf
            for message in messages:
                if message.get("role") == "user":
                    total_user_turns += 1
                    rlhf += 1  # Increase RLHF for each user message in the choices

        # Iterate over each conversation in the JSON data
        for conversation in json_data:
            total_conversations += 1

            if workstream == '2410-sft-app-tools':
                count_sft_for_sft_tool_in_messages(conversation.get("messages", []))

            # Check if 'messages' exist in the conversation
            if "messages" in conversation:
                for message_branch in conversation["messages"]:
                    # First case: 'messageBranch' contains 'choices' with their own 'messages' arrays
                    if "choices" in message_branch:
                        for choice in message_branch["choices"]:
                            if "messages" in choice:
                                count_user_turns_in_messages(choice["messages"])
                    # Second case: Direct 'messages' array without 'choices'
                    elif message_branch.get("role") == "user":
                        total_user_turns += 1
                        rlhf += 1

                # Count original messages for ideal_sft
                for message in conversation["messages"]:
                    if message.get("_message_type") == "MessageBranch" and "choices" in message:
                        for choice in message["choices"]:
                            if choice.get("other_properties", {}).get("original_messages"):
                                ideal_sft += 1
                                total_user_turns += 1

            # Categorize the conversation based on 'task_category_list'
            task_categories = conversation.get("notes", {}).get("task_category_list", [])
            notebook_metadata = conversation.get("notes", {}).get("notebook_metadata", {})
            if workstream == '2410-sft-reasoning':
                section_sum_sft_reasoning += notebook_metadata.get("Sections") 

            for category in task_categories:
                if workstream == "2410-sft-reasoning":
                    if isinstance(category, str):
                        # Add the total sections to the category
                        category_groups[category] = category_groups.get(category, 0) + notebook_metadata.get("Sections", 0)
                        
                    elif isinstance(category, dict) and "category" in category:
                        category_name = category["category"]
                        # Add the total sections to the category name
                        category_groups[category_name] = category_groups.get(category_name, 0) +  notebook_metadata.get("Sections", 0)
                        
                else:
                    if isinstance(category, str):
                        # Increment count for the category
                        category_groups[category] = category_groups.get(category, 0) + 1
                    elif isinstance(category, dict) and "category" in category:
                        category_name = category["category"]
                        # Increment count for the category name
                        category_groups[category_name] = category_groups.get(category_name, 0) + 1

            # Dictionary to store subcategory details
            for subcategory in task_categories:
                subcategory_name = None
                subcategory_data = subcategory.get("subcategory") if isinstance(subcategory, dict) else subcategory

                if isinstance(subcategory_data, list) and len(subcategory_data) > 1:  # Ensure there are at least two elements
                    subcategory_name = subcategory_data[1]
                elif isinstance(subcategory_data, str):
                    subcategory_name = subcategory_data

                if not subcategory_name:
                    continue  # Skip to the next item if format is unexpected

                # Ensure subcategory_groups has a correctly initialized entry for subcategory_name
                subcategory_groups.setdefault(subcategory_name, {"total_rlhf_turn": 0, "total_count": 0, "sft_turn": 0, "total_turn": 0})

                # Update counts for subcategory
                if "messages" in conversation:
                    for message_branch in conversation["messages"]:
                        if "choices" in message_branch:
                            for choice in message_branch["choices"]:
                                if "messages" in choice:
                                    for message in choice["messages"]:
                                        if 'rlhf-vision' in workstream:
                                            if message.get("role") == "user" and message.get('prompt_type')==subcategory_groups[subcategory_name]:
                                                subcategory_groups[subcategory_name]["total_rlhf_turn"] += 1
                                        else:
                                            if message.get("role") == "user":
                                                subcategory_groups[subcategory_name]["total_rlhf_turn"] += 1
                        elif message_branch.get("role") == "user":
                            if 'rlhf-vision' in workstream:
                                if message.get("role") == "user" and message.get('prompt_type')==subcategory_groups[subcategory_name]:
                                    subcategory_groups[subcategory_name]["total_rlhf_turn"] += 1
                            else:
                                if message.get("role") == "user":
                                    subcategory_groups[subcategory_name]["total_rlhf_turn"] += 1

                    # Count original messages for ideal_sft
                    for message in conversation["messages"]:
                        if message.get("_message_type") == "MessageBranch" and "choices" in message:
                            for choice in message["choices"]:
                                if choice.get("other_properties", {}).get("original_messages"):
                                    subcategory_groups[subcategory_name]["sft_turn"] += 1

                if 'rlhf-vision' in workstream:
                    subcategory_groups[subcategory_name]["total_rlhf_turn"] += 1
                else:
                    subcategory_groups[subcategory_name]["total_count"] += 1
                subcategory_groups[subcategory_name]["total_turn"] = subcategory_groups[subcategory_name]["total_rlhf_turn"] + subcategory_groups[subcategory_name]["sft_turn"]

            # Handle main_coding_language details
            coding_language = conversation.get("notes", {}).get("main_coding_language", [])
            if coding_language:
                main_coding_language_groups.setdefault(coding_language, {"total_rlhf_turn": 0, "total_count": 0, "sft_turn": 0, "total_turn": 0})
                main_coding_language_groups[coding_language]["total_count"] += 1

                if "messages" in conversation:
                    for message_branch in conversation["messages"]:
                        if "choices" in message_branch:
                            for choice in message_branch["choices"]:
                                if "messages" in choice:
                                    for message in choice["messages"]:
                                        if message.get("role") == "user":
                                            main_coding_language_groups[coding_language]["total_rlhf_turn"] += 1
                        elif message_branch.get("role") == "user":
                            main_coding_language_groups[coding_language]["total_rlhf_turn"] += 1

                # Count original messages for ideal_sft
                for message in conversation["messages"]:
                    if message.get("_message_type") == "MessageBranch" and "choices" in message:
                        for choice in message["choices"]:
                            if choice.get("other_properties", {}).get("original_messages"):
                                main_coding_language_groups[coding_language]["sft_turn"] += 1

                main_coding_language_groups[coding_language]["total_turn"] = main_coding_language_groups[coding_language]["total_rlhf_turn"] + main_coding_language_groups[coding_language]["sft_turn"]

            # Handle difficulty level
            difficulty = notebook_metadata.get("Difficulty Level") or notebook_metadata.get("difficulty")
            if difficulty:
                difficulty_level.setdefault(difficulty, {"total_turn": 0, "total_count": 0})
                difficulty_level[difficulty]["total_count"] += 1

                if "messages" in conversation:
                    for message_branch in conversation["messages"]:
                        if "choices" in message_branch:
                            for choice in message_branch["choices"]:
                                if "messages" in choice:
                                    for message in choice["messages"]:
                                        if message.get("role") == "user":
                                            difficulty_level[difficulty]["total_turn"] += 1
                        elif message_branch.get("role") == "user":
                            difficulty_level[difficulty]["total_turn"] += 1

            # Handle image distribution details
            if "image_distribution" in conversation.get("notes", {}):
                image_distribution = conversation["notes"]["image_distribution"]

                for image in image_distribution:
                    sft_added_cat = False
                    sft_added_subcat = False
                    for category, subcategory in image.items():
                        # Extract category and subcategory details
                        category_name = category  # This is the key for category
                        subcategory_name = subcategory  # This would be the value for subcategory

                        # Handle category
                        # if category_name:
                        #     if category_name not in image_distribution_groups:
                        #         image_distribution_groups[category_name] = {"total_rlhf_turn": 0, "sft_turn": 0, "total_turn": 0}
                        #     image_distribution_groups[category_name]["total_rlhf_turn"] += 1

                        #     # Count original messages for ideal_sft
                        #     if not sft_added_cat:
                        #         sft_added_cat=True
                        #         for message in conversation["messages"]:
                        #             if message.get("_message_type") == "MessageBranch" and "choices" in message:
                        #                 for choice in message["choices"]:
                        #                     if choice.get("other_properties", {}).get("original_messages"):
                        #                         image_distribution_groups[category_name]["sft_turn"] += 1

                        # Handle subcategory
                        if subcategory_name:
                            if subcategory_name not in image_distribution_groups:
                                image_distribution_groups[subcategory_name] = {"total_rlhf_turn": 0, "sft_turn": 0, "total_turn": 0}
                            image_distribution_groups[subcategory_name]["total_rlhf_turn"] += 1

                            if not sft_added_subcat:
                                sft_added_subcat=True
                                # Count original messages for ideal_sft
                                for message in conversation["messages"]:
                                    if message.get("_message_type") == "MessageBranch" and "choices" in message:
                                        for choice in message["choices"]:
                                            if choice.get("other_properties", {}).get("original_messages"):
                                                image_distribution_groups[subcategory_name]["sft_turn"] += 1

            # Calculate total_turn for image distribution
            for category, data in image_distribution_groups.items():
                total_rlhf_turn = data.get("total_rlhf_turn", 0)
                sft_turn = data.get("sft_turn", 0)
                data["total_turn"] = total_rlhf_turn + sft_turn

        if workstream == '2410-sft-app-tools':
            total_user_turns += ideal_sft
 
        if workstream == '2410-sft-reasoning':
            ideal_sft = rlhf
            rlhf = 0

        # Prepare the response
        response = {
            "totalConversations": total_conversations,
            "totalUserTurns": total_user_turns,
            "ideal_sft": rlhf if "code" in workstream.lower() else ideal_sft,
            "rlhf": ideal_sft if "code" in workstream.lower() else rlhf,
            "categoryGroups": category_groups,
            "subcategoryGroups": subcategory_groups,
            "difficultyLevel": difficulty_level,
            "mainCodingLanguageGroups": main_coding_language_groups,
            "image_distribution_groups": image_distribution_groups,
        }
        # Add 'section_sum' only if the workstream matches
        if workstream == '2410-sft-reasoning':
            response["section_sum"] = section_sum_sft_reasoning

        return response
    else:
        return "Data is not available"
