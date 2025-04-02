from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import json
import re

class CommandClassifier:
    def __init__(self):
        # Initialize the model and tokenizer
        print("Loading Phi-1.5 model...")
        # self.model_name = "meta-llama/Llama-3.2-1B"
        # self.tokenizer = AutoTokenizer.from_pretrained(self.model_ename
        self.pipe = pipeline("text-generation", model="google/gemma-3-1b-it", device="cuda", torch_dtype=torch.bfloat16)

        
        # Define the classification prompt template
        self.prompt_template = """You are a command classifier. Classify the following command into one of the categories: navigate, search, type, click, wait, scroll, extract, help, or exit.
                    Example:
                    Command: go to youtube and search for cats
    Response: action: search, target: youtube, value: cats, url: https://www.youtube.com

Command: {command}
Response:
"""

    
    def classify_command(self, command: str) -> dict:
        """
        Classify a natural language command using Phi-1.5
        """
        messages = [
            [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.prompt_template},]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": command},]
                },
            ],
        ]
        # prompt = self.prompt_template.format(command=command)
        # print(self.prompt_template.format(command=command))
        # Tokenize the input
        output = self.pipe(messages, max_new_tokens=500)
        assistant_content = []

        # Loop through the outer list and then the 'generated_text' list
        for outer_item in output:
            for item in outer_item:
                for entry in item['generated_text']:
                    if entry['role'] == 'assistant':
                        assistant_content.append(entry['content'])

        print(assistant_content)
        return assistant_content
                

# Test the command classifier
if __name__ == "__main__":
    classifier = CommandClassifier()
    test_commands = [
        "go to youtube and search for 3blue1brown",
        "type your name in the username field",
        "click the submit button",
        "wait for 5 seconds",
        "scroll down the page"
    ]
    for command in test_commands:
        result = classifier.classify_command(command)
        # print(f"\nTest command: {command}")
        # print (result)
        # print(f"Classification result: {json.dumps(result, indent=2)}")