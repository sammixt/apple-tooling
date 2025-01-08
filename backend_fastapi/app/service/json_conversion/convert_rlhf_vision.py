import json
import re
from app.config import settings
import boto3
import logging
from app.core.s3_client import S3Client
from app.db.models import ConfigOption
from app.db.database import SessionLocal


logger = logging.getLogger(__name__)
s3 = S3Client()


class JSONProcessor:
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

    def __init__(self, s3_prefix, images_folder):
        logger.info(f"Initializing JSONProcessor with prefix: {s3_prefix}, folder: {images_folder}")
        self.s3_prefix = s3_prefix
        self.images_folder = images_folder

        try:
            logger.info("Creating S3 client...")
            db = SessionLocal()
            apple_upload = db.query(ConfigOption).filter_by(name="enable_penguin_s3_upload").first()
            apple_upload_value = apple_upload.value if apple_upload else False
            if apple_upload_value:
                s3._refresh_if_credentials_expired()
                self.s3_client = s3.s3_client
                self.s3_bucket_name = settings.AWS_BUCKET_NAME
            else:
                self.s3_bucket_name = settings.DEV_AWS_BUCKET_NAME
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.DEV_AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.DEV_AWS_SECRET_ACCESS_KEY,
                )
            logger.info("S3 client created successfully")
        except Exception as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            raise

        try:
            logger.info("Getting assets...")
            self.assets = self.get_assets()
            logger.info(f"Successfully retrieved {len(self.assets)} assets")
        except Exception as e:
            logger.error(f"Failed to get assets: {str(e)}")
            raise

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

    def get_assets(self):
        logger.info(f"Starting get_assets for bucket: {self.s3_bucket_name}")
        assets = []
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket_name, Prefix=self.images_folder)

            for page in pages:
                if "Contents" not in page:
                    logger.warning(f"No contents found for prefix: {self.images_folder}")
                    continue

                for obj in page["Contents"]:
                    image = obj["Key"].split("/")[-1]
                    assets.append(image)

            if not assets:
                logger.error(
                    f"No assets found in the specified bucket '{self.s3_bucket_name}' and prefix '{self.images_folder}'"
                )
                raise ValueError(
                    f"No assets found in the specified bucket '{self.s3_bucket_name}' and prefix '{self.images_folder}'"
                )

            logger.info(f"Retrieved {len(assets)} assets")
            return assets

        except Exception as e:
            logger.error(f"Error in get_assets: {str(e)}")
            raise

    def create_json_entry(self, rlhf, del_id, annotator_id):
        system_prompt, user_index = None, 0
        if rlhf["messages"][0].get("role") == "system":
            system_prompt = rlhf["messages"][0].get("text")
            user_index = 1

        # image_category = rlhf["messages"][user_index]["prompt_evaluation"][0].get("human_input_value")
        # image_sub_category = rlhf["messages"][user_index]["prompt_evaluation"][1].get("human_input_value")
        # task_category = rlhf["messages"][user_index]["prompt_evaluation"][2].get("human_input_value")
        # task_category_list = [{"category": "Multimodal:Image", "subcategory": task_category}]

        task_category_list = []
        image_distribution = []
        temp_image_data = {}
        difficulty_distribution = []

        for msg in rlhf["messages"]:
            if msg.get("role") == "user":
                for prompt_eval in msg["prompt_evaluation"]:
                    if prompt_eval["question"] == "Prompt type":
                        task_category_list.append(
                            {"category": "Multimodal:Image", "subcategory": prompt_eval["human_input_value"]}
                        )
                    elif prompt_eval["question"] == "Image category":
                        temp_image_data["category"] = prompt_eval["human_input_value"]
                    elif prompt_eval["question"] == "Image type":
                        temp_image_data["subcategory"] = prompt_eval["human_input_value"]
                    elif prompt_eval["question"] == "Prompt Difficulty level":
                        difficulty_distribution.append(prompt_eval["human_input_value"])
                    if "category" in temp_image_data and "subcategory" in temp_image_data:
                        image_distribution.append(temp_image_data.copy())
                        temp_image_data = {}

        main_branch = {
            "deliverable_id": del_id,
            "language": {"overall": "en_US"},
            "notes": {
                "task_category_list": task_category_list,
                # "image_distribution": {
                #     "category": image_category,
                #     "subcategory": image_sub_category,
                # },
                "image_distribution": image_distribution,
                "difficulty_distribution": difficulty_distribution,
                "annotator_ids": [str(annotator_id)],
            },
            "messages": [],
        }

        if system_prompt:
            main_branch["messages"].append({"role": "system", "contents": [{"text": system_prompt}]})

        return main_branch, user_index

    def add_one_turn(self, main_branch, rlhf, user_index, del_id):
        image_name = self.get_image_name_with_extension(del_id)
        final_image_file_name = f"{self.s3_prefix}/{image_name}"
        user_message_text = rlhf["messages"][user_index].get("text")
        for prompt_eval in rlhf["messages"][user_index]["prompt_evaluation"]:
            if prompt_eval["question"] == "Prompt type":
                subcategory = prompt_eval["human_input_value"]
            # elif prompt_eval["question"] == "Prompt Difficulty level":
            #     difficulty = prompt_eval["human_input_value"]

        main_branch["messages"].append(
            {
                "role": "user",
                "prompt_type": subcategory,
                # "difficulty_level": difficulty,
                "contents": [
                    {"image": {"url": final_image_file_name}},
                    {"text": user_message_text},
                ],
            }
        )

        raw_preference_signal = rlhf["messages"][user_index + 1]["signal"].get("raw_preference_signal", 1)
        selected_model = "A" if 1 <= raw_preference_signal <= 4 else "B"

        main_branch["messages"].append(
            {
                "_message_type": "MessageBranch",
                "choices": [],
                "misc_properties": {"ranking_overall": self.score_cat_map.get(raw_preference_signal)},
            }
        )

        response_options = rlhf["messages"][user_index + 1]["response_options"]
        evaluations = rlhf["messages"][user_index + 1]["signal"]["human_evals"]
        ideal_response = rlhf["messages"][user_index + 1]["signal"].get("ideal_response", "")

        for i, response in enumerate(response_options[:2]):
            model_id = f"model_{chr(65 + i)}"
            human_eval = evaluations[i]
            try:
                # Map the evaluation values from the human evaluation form into a dictionary (eval_map)
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

    @staticmethod
    def load_json(file_path):
        with open(file_path, "r") as file:
            return json.load(file)

    @staticmethod
    def clean_rating_value(value):
        if " - " in value:
            return value.split(" - ", 1)[1]
        return value

    @staticmethod
    def extract_uuid(turing_task_url):
        match = re.search(r"([a-f0-9\-]{36})", turing_task_url)
        return match.group(0) if match else None

    def get_image_name_with_extension(self, deliverable_id):
        for filename in self.assets:
            if filename.startswith(deliverable_id):
                return filename
        print("Not found:", deliverable_id)

    def to_title_case(self, s):
        """
        Convert a string to Title Case, where each word starts with an uppercase letter.
        :param s: The input string (e.g., "make a string titlecase")
        :return: The string converted to Title Case (e.g., "Make A String Titlecase")
        """
        # Split the string into words and capitalize each one
        title_case = " ".join(word.capitalize() for word in s.split())

        return title_case

    def map_evaluation_values(self, evaluation_form):
        eval_map = {}
        for item in evaluation_form:
            question = item["question"].lower()
            value = self.clean_rating_value(item["human_input_value"])
            value = self.to_title_case(value)
            if value != "Okay":
                value = value.replace("Ok", "Okay")

            if "image" in question:
                eval_map["rating_image_understanding"] = value
            elif "instruction" in question:
                eval_map["rating_instruction_following"] = value
            elif "truthfulness" in question:
                eval_map["rating_truthfulness"] = value
            elif "verbosity" in question or "concision" in question:
                eval_map["rating_verbosity"] = value
            elif "harmlessness" in question:
                eval_map["rating_harmlessness"] = value
            elif "overall" in question:
                satisfaction_map = {
                    "Major Issues": "Not at all",
                    "Minor Issues": "Partially",
                    "No Issues": "Completely",
                }
                eval_map["rating_overall_satisfaction"] = satisfaction_map.get(value, value)

        return eval_map
