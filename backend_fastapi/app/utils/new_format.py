import boto3
import json


class S3JSONHandler:
    def __init__(self, bucket_name, aws_access_key=None, aws_secret_key=None):
        """
        Initialize the S3JSONHandler with bucket details and AWS credentials.
        """
        self.bucket_name = bucket_name

        # Initialize S3 client
        session = boto3.Session(profile_name="turing-data-drops-role")
        self.s3 = session.client("s3")

    def read_json(self, key):
        """
        Read a JSON file from the S3 bucket.

        Args:
            key (str): The key (file path) in the S3 bucket.

        Returns:
            dict: Parsed JSON data from the file.
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except Exception as e:
            print(f"Error reading JSON from S3: {e}")
            return None

    def write_json(self, key, data):
        """
        Write JSON data to a file in the S3 bucket.

        Args:
            key (str): The key (file path) in the S3 bucket.
            data (dict): The JSON data to write.
        """
        try:
            # json_content = json.dumps(data, indent=4)
            with open("formatted_vision.json", "w") as file:
                json.dump(data, file, indent=4)
            # self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=json_content)
            # print(f"File {key} written successfully to S3 bucket {self.bucket_name}.")
        except Exception as e:
            print(f"Error writing JSON to S3: {e}")

    def modify_json(self, key):
        """
        Modify an existing JSON file in the S3 bucket.

        Args:
            key (str): The key (file path) in the S3 bucket.
            modifications (dict): Key-value pairs to update in the JSON file.

        Returns:
            dict: Updated JSON data.
        """
        try:
            # Read existing JSON data
            data = self.read_json(key)
            if data is None:
                return None

            modified_data = []

            # Apply modifications
            for entry in data:
                task = {}
                task["deliverable_id"] = entry["deliverable_id"]
                task["notes"] = entry["notes"]
                task["language"] = entry["language"]
                task["messages"] = []
                for msg in entry["messages"]:
                    if msg.get("role"):
                        task["messages"].append(msg)
                    else:
                        assistant_obj = {}
                        assistant_obj["_message_type"] = msg["_message_type"]
                        assistant_obj["misc_properties"] = {}
                        assistant_obj["misc_properties"]["ranking_overall"] = self.standardize_ranking(
                            msg["misc_properties"]["ranking_overall"]
                        )
                        choises = []
                        for choise in msg["choices"]:
                            if choise["other_properties"].get("original_messages"):
                                choises.append(choise)
                            else:
                                new_choise = {}
                                new_choise["messages"] = choise["messages"]
                                new_choise["hyperparameters"] = choise["hyperparameters"]
                                new_choise["response_source"] = choise["response_source"]
                                new_choise["other_properties"] = self.reformat_other_properties(
                                    choise["other_properties"]
                                )
                                choises.append(new_choise)
                        assistant_obj["choises"] = choises

                        task["messages"].append(assistant_obj)
                modified_data.append(task)

            # Write back to S3
            self.write_json(key, modified_data)
            return data
        except Exception as e:
            print(f"Error modifying JSON: {e}")
            return None

    def standardize_ranking(self, current_value):
        # Define a dictionary that maps current values to allowed values
        mapping = {
            "Left (A) is much better": "Left (A) Much Better",
            "Left (A) is better": "Left (A) Better",
            "Left (A) is slightly better": "Left (A) Slightly Better",
            "Left (A) is negligibly better": "Left (A) Negligibly Better",
            "Right (B) negligibly Better": "Right (B) Negligibly Better",
            "Right (B) is slightly better": "Right (B) Slightly Better",
            "Right (B) is better": "Right (B) Better",
            "Right (B) is much better": "Right (B) Much Better",
        }

        # Return the mapped value if it exists; otherwise, return None or raise an error
        return mapping.get(current_value, None)

    def to_title_case(self, s):
        """
        Convert a string to Title Case, where each word starts with an uppercase letter.
        :param s: The input string (e.g., "make a string titlecase")
        :return: The string converted to Title Case (e.g., "Make A String Titlecase")
        """
        # Split the string into words and capitalize each one
        title_case = " ".join(word.capitalize() for word in s.split())

        return title_case

    def standardize_rating(self, current_value):
        value = self.to_title_case(current_value)
        if value != "Okay":
            value = value.replace("Ok", "Okay")
        return value

    def reformat_other_properties(self, input_data):
        # Extract the ratings
        original_ratings = {}

        rating_fields = [
            ("rating_concision", "rating_verbosity"),
            ("rating_harmlessness", "rating_harmlessness"),
            ("rating_satisfaction", "rating_overall_satisfaction"),
            ("rating_overall_satisfaction", "rating_overall_satisfaction"),
            ("rating_truthfulness", "rating_truthfulness"),
            ("rating_image_understanding", "rating_image_understanding"),
            ("rating_instruction_following", "rating_instruction_following"),
        ]

        for input_key, output_key in rating_fields:
            rating_value = input_data.get(input_key)
            if rating_value:
                original_ratings[output_key] = self.standardize_rating(rating_value)

        # Return the reformatted dictionary
        return {
            "other_properties": {
                "original_ratings": original_ratings,
                "selected_overall": input_data.get("selected_overall", False),
            }
        }


if __name__ == "__main__":
    processor = S3JSONHandler("og82-drop-turing")
    processed_data = processor.modify_json("2410-rlhf-vision/_raw/20241209/[2024-12-09] RLHF Vision en_US.json")

    print(f"Processed data saved.")
