from .enums import TaskType


class S3LinkValidator:
    def __init__(self, data, assets, assets_path) -> None:
        self.data = data
        self.assets = assets
        self.assets_path = assets_path

    def validate(self, task_type):
        errors = []
        for entry in self.data:
            deliverable_id = entry["deliverable_id"]
            images = self.get_image_urls(entry, task_type)
            for image_url in images:
                self.validate_prifix_link(deliverable_id, image_url, errors)
                self.validate_image(deliverable_id, image_url, errors)
        return errors

    def validate_image(self, deliverable_id, image_url, errors):
        image_name = self.get_image_name(image_url)
        # model eval file contains "no image" which can be ignored
        if not image_name == "no image":
            if image_name not in self.assets:
                similar_images = self.find_similar_images(image_name, self.assets)
                if similar_images:
                    errors.append(
                        {
                            "deliverable_id": deliverable_id,
                            "message": f"Image link is invalid. found similar image - {similar_images}",
                        }
                    )
                else:
                    errors.append({"deliverable_id": deliverable_id, "message": "Image link is invalid."})

    def validate_prifix_link(self, deliverable_id, image_url, errors):
        prefix_link = self.get_prfix(image_url)
        if not prefix_link == self.assets_path:
            errors.append({"deliverable_id": deliverable_id, "message": "Prefix link is invalid."})

    def get_image_urls(self, entry, task_type):
        """Returns array of images"""
        match task_type:
            case TaskType.RLHF_IMAGE:
                image_url = entry["messages"][1]["contents"][0]["image"]["url"]
                return [image_url]
            case TaskType.RLHF_IMAGE_GEN_PROMPT:
                image_url_choice_0 = entry["messages"][1]["choices"][0]["messages"][0]["contents"][0]["image"]["url"]
                image_url_choice_1 = entry["messages"][1]["choices"][1]["messages"][0]["contents"][0]["image"]["url"]
                return [image_url_choice_0, image_url_choice_1]
            case TaskType.EVALS_IMAGE_GEN_PROMPT:
                image_url = entry["messages"][0]["contents"][0]["image"]["url"]
                return [image_url]
            case TaskType.CODE_INT:
                urls = []
                for chat in entry["messages"]:
                    if chat["role"] == "tool":
                        for output in chat["content"]["outputs"]:
                            if "data" in output and "image/url" in output["data"]:
                                urls.append(output["data"]["image/url"])
                    if chat["role"] == "user" and "attachments" in chat:
                        for file in chat["attachments"]:
                            urls.append(file["file_id"])
                return urls
            case _:
                return "Invalid task"

    def get_prfix(self, image_url):
        """Return path of image without image name"""
        return image_url.rpartition("/")[0] + "/"

    def get_image_name(self, image_url):
        return image_url.split("/")[-1]

    def find_similar_images(self, image_name, assets):
        # Get the base name without extension & case insensitive comparision
        base_name = image_name.split(".")[0].lower()
        matching_files = [file for file in assets if file.lower().startswith(base_name)]
        return matching_files.join(" ") if matching_files else None
