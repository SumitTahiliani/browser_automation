from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import re

class CommandClassifier:
    def __init__(self):
        # Initialize the model and tokenizer
        print("Loading Phi-1.5 model...")
        self.model_name = "microsoft/phi-1_5"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Define the classification prompt template
        self.prompt_template = """Instruction: You are a command classifier. Your task is to classify the following command and return a JSON object with the specified fields.

Categories:
1. navigate - For navigating to websites
2. search - For searching on websites
3. type - For typing text into input fields
4. click - For clicking elements
5. wait - For waiting
6. scroll - For scrolling
7. extract - For extracting information
8. help - For showing help
9. exit - For exiting

Return a JSON object with these fields:
{
    "action": "category_name",
    "target": "element_to_interact_with",
    "value": "text_to_type_or_search",
    "url": "url_to_navigate_to"
}

For example, for the command "go to youtube and search for cats", return:
{
    "action": "search",
    "target": "youtube",
    "value": "cats",
    "url": "https://www.youtube.com"
}

Command to classify: {command}

Response: Let me classify that command into a JSON object:
"""
    
    def clean_json_string(self, json_str: str) -> str:
        """Clean the JSON string by removing any non-JSON content and fixing common issues."""
        # Remove any text before the first {
        json_str = json_str[json_str.find('{'):]
        
        # Remove any text after the last }
        json_str = json_str[:json_str.rfind('}')+1]
        
        # Fix common JSON formatting issues
        json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
        json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
        json_str = re.sub(r'}\s*{', '},{', json_str)  # Fix multiple objects
        
        return json_str
    
    def extract_json_from_response(self, response: str) -> dict:
        """Extract and parse JSON from the model response."""
        try:
            # Find all JSON objects in the response
            json_matches = re.finditer(r'\{[^{}]*\}', response)
            json_objects = []
            
            for match in json_matches:
                try:
                    json_str = self.clean_json_string(match.group(0))
                    obj = json.loads(json_str)
                    if isinstance(obj, dict) and "action" in obj:
                        json_objects.append(obj)
                except json.JSONDecodeError:
                    continue
            
            if not json_objects:
                raise ValueError("No valid JSON objects found in response")
            
            # Use the first valid JSON object
            result = json_objects[0]
            
            # Ensure all required fields are present
            required_fields = ["action", "target", "value", "url"]
            for field in required_fields:
                if field not in result:
                    result[field] = None
            
            return result
            
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            print(f"Raw response: {response}")
            return {
                "action": None,
                "target": None,
                "value": None,
                "url": None
            }
    
    def classify_command(self, command: str) -> dict:
        """
        Classify a natural language command using Phi-1.5
        """
        try:
            # Prepare the prompt
            prompt = self.prompt_template.format(command=command)
            
            # Tokenize the input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,  # Low temperature for more deterministic output
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.2  # Add repetition penalty to avoid loops
            )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"Raw response: {response}")  # Debug log
            
            # Extract and parse the JSON
            return self.extract_json_from_response(response)
                
        except Exception as e:
            print(f"Error classifying command: {e}")
            return {
                "action": None,
                "target": None,
                "value": None,
                "url": None
            }

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
        print(f"\nTest command: {command}")
        print(f"Classification result: {json.dumps(result, indent=2)}")