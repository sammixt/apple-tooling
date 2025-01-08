from concurrent.futures import ThreadPoolExecutor
import json
import re
import logging
from app.config import settings
import boto3

logger = logging.getLogger(__name__)


class JSONProcessor:
    score_cat_map = {
        1: "Left (A) is much better",
        2: "Left (A) is better",
        3: "Left (A) is slightly better",
        4: "Left (A) is negligibly better",
        5: "Right (B) is negligibly better",
        6: "Right (B) is slightly better",
        7: "Right (B) is better",
        8: "Right (B) is much better",
    }

    def __init__(self, s3_prefix, images_folder):
        self.s3_prefix = s3_prefix
        self.images_folder = images_folder
        try:
            logger.info("Creating S3 client...")
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

    def get_assets(self):
        logger.info(f"Starting get_assets for bucket: {settings.DEV_AWS_BUCKET_NAME}")
        assets = []
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=settings.DEV_AWS_BUCKET_NAME, Prefix=self.images_folder)

            for page in pages:
                if "Contents" not in page:
                    logger.warning(f"No contents found for prefix: {self.images_folder}")
                    continue

                for obj in page["Contents"]:
                    image = obj["Key"].split("/")[-1]
                    assets.append(image)

            logger.info(f"Retrieved {len(assets)} assets")
            return assets

        except Exception as e:
            logger.error(f"Error in get_assets: {str(e)}")
            raise

    def process_file(self, input_array):
        output_data = []
        try:
            for input_data in input_array:
                sft_array, rlhf_array = input_data["sft"], input_data["rlhf"]
                output = []

                for rlhf in rlhf_array:
                    try:
                        turing_task_url = rlhf["metadata"].get("turing_task_url")
                        del_id = self.extract_uuid(turing_task_url)
                        print("del_id", del_id)
                        if del_id is None:
                            print(f"Invalid turing_task_url: {turing_task_url}")
                            continue  # Skip this iteration if del_id is None

                        # Initialize numeric_value here
                        numeric_value = ""
                        for msg in rlhf["messages"]:
                            if msg["role"] == "user":
                                numeric_value = self.extract_numeric_prefix(msg["text"])

                        matching_sft = next(
                            (sft for sft in sft_array if sft["colabLink"] == turing_task_url),
                            None,
                        )

                        if matching_sft:
                            annotator_id = matching_sft["humanUser"].get("id")
                            main_branch = self.create_json_entry(rlhf, del_id, annotator_id)
                            self.add_msg_branch(main_branch, rlhf, del_id, numeric_value)
                            output.append(main_branch)
                        else:
                            print(f"Matching sft not found - {del_id}")
                    except Exception as e:
                        print(f"Error in Delivery: {del_id} - {e}")

                output_data.extend(output)
            return output_data
        except Exception as e:
            print(f"Error processing JSON: {e}")

    def create_json_entry(self, rlhf, del_id, annotator_id):
        prompt = None
        if rlhf["messages"][1].get("role") == "user":
            prompt = rlhf["messages"][1].get("text")

        main_branch = {
            "deliverable_id": del_id,
            "language": {"overall": "en_US"},
            "notes": {
                "task_category_list": [{"category": "Multimodal:Image", "subcategory": "Customer Inputs"}],
                "annotator_ids": [str(annotator_id)],
            },
            "messages": [],
        }

        if prompt:
            main_branch["messages"].append({"role": "user", "contents": [{"text": prompt}]})
        else:
            print(f"prompt is not available - {del_id}")

        return main_branch

    def add_msg_branch(self, main_branch, rlhf, del_id, numeric_value):
        raw_preference_signal = rlhf["messages"][2]["signal"].get("raw_preference_signal", 1)

        main_branch["messages"].append(
            {
                "_message_type": "MessageBranch",
                "choices": [],
                "misc_properties": {"ranking_overall": self.score_cat_map.get(raw_preference_signal)},
            }
        )

        response_options = rlhf["messages"][2]["response_options"]
        evaluations = rlhf["messages"][2]["signal"]["human_evals"]

        for index, eval in enumerate(evaluations):
            if response_options[index]["text"] == "no image":
                image = response_options[index]["text"]
            else:
                model_id = eval["model_id"].replace("-", "_")

                image_name = f"{model_id}_{numeric_value}"
                image_name_with_extension = self.get_image_name_with_extension(image_name)
                image = f"{self.s3_prefix}/{image_name_with_extension}"

            choice = {
                "response_source": eval["model_id"],
                "messages": [
                    {
                        "role": "assistant",
                        "contents": [{"image": {"url": image}}],
                        "other_properties": self.process_evaluation(eval, raw_preference_signal, index),
                    }
                ],
            }

            main_branch["messages"][1]["choices"].append(choice)

    def process_evaluation(self, evaluation, raw_preference_signal, index):
        summary = {
            "selected_overall": False,
            "rating_accuracy": 0,
            "rating_creativity": 0,
            "rating_visual_appeal": 0,
            "rating_aesthetic_quality": 0,
            "rating_clarity": 0,
            "rating_coherence": 0,
            "rating_thematic_impact": 0,
            "rating_overall_score": 0,
        }

        if (index == 0 and 1 <= raw_preference_signal <= 4) or (index == 1 and 5 <= raw_preference_signal <= 8):
            summary["selected_overall"] = True

        questions_map = {
            "Accuracy": "rating_accuracy",
            "Creativity": "rating_creativity",
            "Visual Appeal": "rating_visual_appeal",
            "Aesthetic Quality": "rating_aesthetic_quality",
            "Clarity": "rating_clarity",
            "Coherence": "rating_coherence",
            "Thematic Impact": "rating_thematic_impact",
            "Overall Quality": "rating_overall_score",
        }

        overall_score = 0

        for question in evaluation["evaluation_form"]:
            if not question["question"] == "Selected Overall":
                value = int(question["human_input_value"].split()[0])
                question_key = questions_map[question["question"]]
                summary[question_key] = value
                overall_score += value

        summary["rating_overall_score"] = overall_score

        return summary

    @staticmethod
    def load_json(file_path):
        with open(file_path, "r") as file:
            return json.load(file)

    @staticmethod
    def extract_uuid(turing_task_url):
        match = re.search(r"([a-f0-9\-]{36})", turing_task_url)
        return match.group(0) if match else None

    def get_image_name_with_extension(self, deliverable_id):
        for filename in self.assets:
            if filename.startswith(deliverable_id):
                return filename
        print("Not found:", deliverable_id)

    def extract_drive_id(self, drive_link):
        pattern = r"(?:/d/|/folders/)([a-zA-Z0-9_-]+)"
        match = re.search(pattern, drive_link)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def extract_numeric_prefix(text):
        match = re.match(r"^(\d+)_", text)
        if match:
            return match.group(1)
        else:
            return None
