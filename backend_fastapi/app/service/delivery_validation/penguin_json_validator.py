import json
import os
import jsonschema


class PenguinFormattingValidator:
    def __init__(self, data):
        self.data = data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "deliverable_v1.schema.json")
        with open(file_path, "r") as f:
            self.schema = json.loads(f.read())

    def validate(self):
        errors = []
        for task in self.data:
            delivery_id = task.get("deliverable_id")
            try:
                # schema validation
                jsonschema.validate(
                    instance=task,
                    schema=self.schema,
                )
            except jsonschema.exceptions.ValidationError as e:
                errors.append({"deliverableId": delivery_id, "message": [str(e)]})
            except Exception as e:
                errors.append({"deliverableId": delivery_id, "message": [str(e)]})
        return errors
