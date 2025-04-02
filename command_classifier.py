from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import json
import re

class CommandClassifier:
    def __init__(self):
        # Initialize the model and tokenizer
        print("Loading Gemma-1b-it model...")
        # self.model_name = "google/gemma-1b-it"
        # self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # self.model = AutoModelForCausalLM.from_pretrained(
        #     self.model_name,
        #     torch_dtype=torch.float16,
        #     device_map="auto",
        #     trust_remote_code=True
        # )
        self.pipe = pipeline("text-generation", model="google/gemma-3-1b-it", device="cuda", torch_dtype=torch.bfloat16)
        
        # Initialize context
        self.current_url = None
        
        # Define the classification prompt template
        self.prompt_template = """
Instruction: You are a command classifier. Your task is to classify the following command and return a JSON object with the specified fields.

Categories:
1. navigate - For navigating to websites (e.g., "go to youtube", "navigate to example.com")
2. search - For searching on websites (e.g., "search for cats", "find videos about dogs")
3. type - For typing text into input fields
4. click - For clicking elements
5. wait - For waiting
6. scroll - For scrolling
7. extract - For extracting information
8. help - For showing help
9. exit - For exiting

Return a JSON object with these fields:
{
    action: category_name,
    target: element_to_interact_with,
    value: text_to_type_or_search,
    url: url_to_navigate_to
}

Examples:
1. For "go to youtube", return:
{
    action: navigate,
    target: youtube,
    value: null,
    url: https://www.youtube.com
}

2. For "search for cats on youtube", return:
{
    action: search,
    target: youtube,
    value: cats,
    url: https://www.youtube.com
}

3. For "click the submit button", return:
{
    action: click,
    target: submit button,
    value: null,
    url: null
}

4. For "type your name in the username field", return:
{
    action: type,
    target: username,
    value: your name,
    url: null
}

5. For "wait for 5 seconds", return:
{
    action: wait,
    target: null,
    value: 5,
    url: null
}

6. For "scroll down the page", return:
{
    action: scroll,
    target: page,
    value: down,
    url: null
}
"""
    
    def parse_list_to_dict(self, response_list: list) -> dict:
        """Convert the list response to a dictionary with required fields."""
        try:
            # Initialize result with default values
            result = {
                "action": None,
                "target": None,
                "value": None,
                "url": None
            }
            
            # Extract action from the first item
            if response_list and len(response_list) > 0:
                first_item = response_list[0]
                
                # Extract JSON from markdown code block if present
                json_match = re.search(r'```json\n(.*?)\n```', first_item, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        parsed_json = json.loads(json_str)
                        result.update(parsed_json)
                        
                        # Update context if this is a navigation command
                        if result["action"] == "navigate" and result["url"]:
                            self.current_url = result["url"]
                        # Use current URL for search if not specified
                        elif result["action"] == "search" and not result["url"] and self.current_url:
                            result["url"] = self.current_url
                            
                        return result
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
                        print(f"JSON string: {json_str}")
                
                # Fallback to regex parsing if no JSON found
                action_match = re.search(r'action:\s*(\w+)', first_item)
                if action_match:
                    result["action"] = action_match.group(1)
                
                target_match = re.search(r'target:\s*([^,]+)', first_item)
                if target_match:
                    result["target"] = target_match.group(1).strip()
                
                value_match = re.search(r'value:\s*([^,]+)', first_item)
                if value_match:
                    result["value"] = value_match.group(1).strip()
                
                # Special handling for wait action
                if result["action"] == "wait":
                    duration_match = re.search(r'duration:\s*(\d+)\s*seconds', first_item)
                    if duration_match:
                        result["value"] = duration_match.group(1)
                
                # Special handling for scroll action
                if result["action"] == "scroll":
                    result["target"] = "page"
                    result["value"] = "down"
                
                # Use current URL for search if not specified
                if result["action"] == "search" and not result["url"] and self.current_url:
                    result["url"] = self.current_url
            
            return result
            
        except Exception as e:
            print(f"Error parsing list to dict: {e}")
            return {
                "action": None,
                "target": None,
                "value": None,
                "url": None
            }
    
    def classify_command(self, command: str) -> dict:
        """
        Classify a natural language command using Gemma-1b-it
        """
        try:
            # Prepare the prompt
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
            output = self.pipe(messages, max_new_tokens=500)
            response = []

            # Loop through the outer list and then the 'generated_text' list
            for outer_item in output:
                for item in outer_item:
                    for entry in item['generated_text']:
                        if entry['role'] == 'assistant':
                            response.append(entry['content'])
            
            print(response)
            # Parse the response list into a dictionary
            return self.parse_list_to_dict(response)
                
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
        "click the submit button",
        "wait for 5 seconds",
        "scroll down the page"
    ]
    
    for command in test_commands:
        result = classifier.classify_command(command)
        print(f"\nTest command: {command}")
        print(f"Classification result: {json.dumps(result, indent=2)}")