import re
import logging


logger = logging.getLogger(__name__)


class RLHFTextJSONProcessor:
    score_cat_map = {
        1: "Left (A) Much Better",
        2: "Left (A) Better",
        3: "Left (A) Slightly Better",
        4: "Left (A) Negligibly Better",
        5: "Right (B) Negligibly Better",
        6: "Right (B) Slightly Better",
        7: "Right (B) Better",
        8: "Right (B) Much Better",
    }
    language_map = {
        "c++": "C++",
        "cpp": "C++",
        "golang": "Go",
        "golan": "Go",
        "go": "Go",
        "java": "Java",
        "js": "JavaScript",
        "javascript": "JavaScript",
        "python": "Python",
        "swift": "Swift",
    }

    def map_comparison_value(self, original_string):
        labelling_tool = [
            "Model A is significantly better than Model B",
            "Model A is better than Model B",
            "Model A is slightly better than Model B",
            "Model A is negligibly better than Model B",
            "Model B is negligibly better than Model A",
            "Model B is slightly better than Model A",
            "Model B is better than Model A",
            "Model B is significantly better than Model A",
        ]
        apple = [
            "Left (A) Much Better",
            "Left (A) Better",
            "Left (A) Slightly Better",
            "Left (A) Negligibly Better",
            "Right (B) Negligibly Better",
            "Right (B) Slightly Better",
            "Right (B) Better",
            "Right (B) Much Better",
        ]

        mapping = dict(zip(labelling_tool, apple))

        return mapping.get(original_string, original_string)

    def process_file(self, input_array):
        output_data = []

        try:
            for input_data in input_array:
                sft_array, rlhf_array = input_data["sft"], input_data["rlhf"]
                output = []
                matching_sft_count = 0

                for rlhf in rlhf_array:
                    try:
                        turing_task_url = rlhf["metadata"].get("turing_task_url")
                        del_id = self.extract_uuid(turing_task_url)
                        matching_sft = next(
                            (sft for sft in sft_array if sft["colabLink"] == turing_task_url),
                            None,
                        )

                        if matching_sft:
                            matching_sft_count += 1
                            annotator_id = matching_sft["humanUser"].get("id")
                            main_branch, user_index = self.create_json_entry(rlhf, del_id, annotator_id)
                            while user_index < len(rlhf["messages"]):
                                user_index = self.add_one_turn(main_branch, rlhf, user_index, del_id)
                            output.append(main_branch)
                    except Exception as e:
                        print(f"Error processing del_id: {del_id} - {e}")

                output_data.extend(output)
            return output_data
        except Exception as e:
            print(f"Error processing JSON: {e}")

    def create_json_entry(self, rlhf, del_id, annotator_id):
        system_prompt, user_index = None, 0
        if rlhf["messages"][0].get("role") == "system":
            system_prompt = rlhf["messages"][0].get("text")
            user_index = 1

        task_category = rlhf["metadata"]["scope_requirements"].get("task_category_list", None)
        task_category_list = []
        user_role_count = sum(1 for message in rlhf["messages"] if message.get("role") == "user")
        task_category_list.extend([{"category": "Coding", "subcategory": task_category}] * user_role_count)

        main_coding_language = self.get_language_from_batch(
            rlhf["metadata"]["scope_requirements"].get("batchName", None)
        )

        main_branch = {
            "deliverable_id": del_id,
            "language": {"overall": "en_US"},
            "notes": {
                "task_category_list": task_category_list,
                "annotator_ids": [str(annotator_id)],
                "main_coding_language": main_coding_language,
            },
            "messages": [],
        }

        if system_prompt:
            main_branch["messages"].append({"role": "system", "contents": [{"text": system_prompt}]})

        return main_branch, user_index

    def add_one_turn(self, main_branch, rlhf, user_index, del_id):
        user_message_text = rlhf["messages"][user_index].get("text")

        main_branch["messages"].append(
            {
                "role": "user",
                "contents": [
                    {"text": user_message_text},
                ],
            }
        )

        raw_preference = rlhf["messages"][user_index + 1]["signal"]["raw_preference_evaluation_form"][0].get(
            "human_input_value", ""
        )
        ranking_overall = self.map_comparison_value(raw_preference)

        pattern = r"\(([AB])\)"
        selected_model = re.search(pattern, ranking_overall).group(1)

        main_branch["messages"].append(
            {
                "_message_type": "MessageBranch",
                "choices": [],
                "misc_properties": {"ranking_overall": ranking_overall},
            }
        )

        response_options = rlhf["messages"][user_index + 1]["response_options"]
        evaluations = rlhf["messages"][user_index + 1]["signal"]["human_evals"]
        ideal_response = rlhf["messages"][user_index + 1]["signal"].get("ideal_response", "")
        ideal_response = "" if len(ideal_response) < 100 else ideal_response

        for i, response in enumerate(response_options[:2]):
            model_id = f"model_{chr(65 + i)}"
            human_eval = evaluations[i]
            try:
                eval_map = self.map_evaluation_values(human_eval["evaluation_form"])
                # print(eval_map)
            except:
                eval_map = {}
                print("no eval_map")
                print(del_id)

            selected_overall = (i == 0 and selected_model == "A") or (i == 1 and selected_model == "B")
            choice = {
                "response_source": response["model_id"],
                "hyperparameters": {
                    "model_id": response["model_id"],
                    "temperature": rlhf["messages"][user_index + 1]["signal"].get(f"{model_id}_temperature", 0.7),
                },
                "messages": [{"role": "assistant", "contents": [{"text": response["text"]}]}],
            }

            if not selected_overall or (selected_overall and not ideal_response):
                choice["other_properties"] = {
                    "selected_overall": selected_overall,
                    "original_ratings": {**eval_map},
                }
            elif selected_overall and ideal_response:
                choice["other_properties"] = {
                    "selected_overall": selected_overall,
                    "original_messages": choice["messages"],
                    "original_ratings": {**eval_map},
                }
                choice["messages"] = [{"role": "assistant", "contents": [{"text": ideal_response}]}]

            main_branch["messages"][user_index + 1]["choices"].append(choice)

        return user_index + 2

    def get_language_from_batch(self, batch_name):
        """
        Extract the programming language from the batch name based on the language map.
        :params: batch_name (str): The batch name to extract the language from.
        :returns: str: The mapped programming language or None if not found.
        """
        for key in self.language_map.keys():
            if key in batch_name.lower():
                return self.language_map[key]
        return None

    @staticmethod
    def clean_rating_value(value):
        if " - " in value:
            return value.split(" - ", 1)[1]
        return value

    @staticmethod
    def extract_uuid(turing_task_url):
        match = re.search(r"([a-f0-9\-]{36})", turing_task_url)
        return match.group(0) if match else None

    def to_title_case(self, s):
        """
        Convert a string to Title Case, where each word starts with an uppercase letter.
        :params: The input string (e.g., "make a string titlecase")
        :return: The string converted to Title Case (e.g., "Make A String Titlecase")
        """
        title_case = " ".join(word.capitalize() for word in s.split())
        return title_case

    def map_evaluation_values(self, evaluation_form):
        eval_map = {}
        for item in evaluation_form:
            question = item["question"]
            value = self.clean_rating_value(item["human_input_value"])
            value = self.to_title_case(value)

            if question == "Instruction Following":
                eval_map["rating_instruction_following"] = value
            elif question == "Truthfulness":
                eval_map["rating_truthfulness"] = value
            elif question == "Conciseness":
                eval_map["rating_verbosity"] = value
            elif question == "Content Safety":
                eval_map["rating_harmlessness"] = value
            elif question == "Overall Satisfaction":
                satisfaction_map = {
                    "Major Issues": "Not at all",
                    "Minor Issues": "Partially",
                    "No Issues": "Completely",
                }
                eval_map["rating_overall_satisfaction"] = satisfaction_map.get(value, value)

        return eval_map
