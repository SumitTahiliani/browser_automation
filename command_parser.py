import spacy
from typing import Dict, List, Tuple, Optional

class CommandParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
        # Define action patterns
        self.action_patterns = {
            "click": ["click", "press", "tap", "select"],
            "type": ["type", "enter", "input", "write"],
            "navigate": ["go to", "visit", "navigate to", "open"],
            "wait": ["wait", "pause"],
            "scroll": ["scroll", "move down", "move up"],
            "search": ["search", "find", "look for"]
        }
        
        # Define element patterns with more comprehensive matching
        self.element_patterns = {
            "button": ["button", "btn", "click me", "search button", "submit", "sign in", "login", "search"],
            "input": ["input", "textbox", "field", "box", "search box", "search field", "text field", "search"],
            "link": ["link", "url", "website", "href"],
            "text": ["text", "label", "heading", "title", "header"]
        }

    def parse_command(self, command: str) -> Dict:
        """
        Parse a natural language command into structured browser actions
        """
        doc = self.nlp(command.lower())
        command_lower = command.lower()
        
        # Initialize result structure
        result = {
            "action": None,
            "target": None,
            "value": None,
            "url": None
        }
        
        # Extract action
        for action, patterns in self.action_patterns.items():
            if any(pattern in command_lower for pattern in patterns):
                result["action"] = action
                break
        
        # Extract target element with improved matching
        for element, patterns in self.element_patterns.items():
            # Check for exact matches first
            if any(pattern in command_lower for pattern in patterns):
                result["target"] = element
                break
            # Check for partial matches
            for pattern in patterns:
                if pattern in command_lower:
                    result["target"] = element
                    break
            if result["target"]:
                break
        
        # Special handling for search-related elements
        if "search" in command_lower:
            if "box" in command_lower or "field" in command_lower:
                result["target"] = "input"
            elif "button" in command_lower:
                result["target"] = "button"
        
        # Extract URL if present
        for token in doc:
            if token.like_num or token.is_digit:
                result["value"] = token.text
            elif token.like_url:
                result["url"] = token.text
        
        # Extract text content for typing or searching
        if result["action"] in ["type", "search"]:
            # Look for quoted text
            for token in doc:
                if token.is_quote:
                    result["value"] = token.text.strip('"\'')
                    break
            # If no quoted text found, try to extract text between action and target
            if not result["value"]:
                words = command_lower.split()
                try:
                    action_idx = next(i for i, word in enumerate(words) 
                                    if any(pattern in word for patterns in self.action_patterns.values()))
                    target_idx = next(i for i, word in enumerate(words) 
                                    if any(pattern in word for patterns in self.element_patterns.values()))
                    if action_idx < target_idx:
                        result["value"] = " ".join(words[action_idx + 1:target_idx])
                except:
                    pass
        
        return result

    def validate_command(self, parsed_command: Dict) -> Tuple[bool, str]:
        """
        Validate the parsed command and return (is_valid, error_message)
        """
        if not parsed_command["action"]:
            return False, "No valid action found in command"
            
        if parsed_command["action"] in ["click", "type"] and not parsed_command["target"]:
            return False, f"Command requires a target element for action: {parsed_command['action']}"
            
        if parsed_command["action"] == "type" and not parsed_command["value"]:
            return False, "Type command requires text to enter"
            
        if parsed_command["action"] == "navigate" and not parsed_command["url"]:
            return False, "Navigate command requires a URL"
            
        return True, "" 