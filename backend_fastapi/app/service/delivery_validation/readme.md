
The entry class is validator = Validator(data)
expected input is a json data, which is passed when instantiating the class
The output is also a json array

```json
output =  [
    {
        "deliverableId": "c4563b8b-b966-40f5-bde7-ef9331d94064",
        "message": [
            "hyperparameters must contain valid model_id and temperature."
        ]
    },
    {
        "deliverableId": "d4c92092-afa8-4a0d-b676-6a8e3e59a90c",
        "message": [
            "For 'Right (B)' ranking, Right (B) ranking must have a better rating_overall_satisfaction than the other side."
        ]
    }
]
```
When calling the validate method, specify the file type, which should be passed as an enum, find enums below.

```json
RLHF_TEXT = "rlhfText"  //Sample file [2024-10-02] rlhf-code-python en_US.json
RLHF_IMAGE = "rlfhVision" //Sample file [2024-10-25] RLHF Vision.json
RLHF_IMAGE_GEN_PROMPT = "rlfhImageGenPrompts" //Sample file 2410-rlhf-imagegen-prompts/_raw/20241014/[2024-10-14] Image Generation Prompts.json
EVALS_IMAGE_GEN_PROMPT = "evalsResultImageGenPrompt" //sample file [2024-10-21] Evals Image Generation Prompts - Model A vs Model B en_US.json'

```

Sample implementation
```json
def main():
    rlhf_file = '/Turing/s3/2410-rlhf-text/_raw/20241002/[2024-10-02] rlhf-code-python en_US.json'
    rlfh_file_vision = '/Turing/s3/[2024-10-25] RLHF Vision.json'
    eval_file_vision = '/Turing/s3/2410-eval-results/_raw/20241021/[2024-10-21] Evals Image Generation Prompts - Model A vs Model B en_US.json'
    eval_file_vision_a_c = '/Turing/s3/2410-eval-results/_raw/20241021/[2024-10-21] Evals Image Generation Prompts - Model A vs Model C en_US.json'
    with open(rlfh_file_vision, "r") as file:
        data = json.load(file)
        validator = Validator(data)
        output = validator.validate(TaskType.RLHF_IMAGE)
        if output:
            print(json.dumps(output, indent=4))
        else:
            print("No errors found.")
         

if __name__ == "__main__":
    main()
```

requirement.txt
`setuptools`
`language-tool-python`