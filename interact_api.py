from typing import Dict, List, Tuple, Optional
from playwright.sync_api import sync_playwright, Page
import time
import json
from command_classifier import CommandClassifier

class InteractAPI:
    def __init__(self):
        # Initialize Playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Initialize command classifier
        self.classifier = CommandClassifier()

    def parse_command(self, command: str) -> Dict:
        """
        Parse a natural language command using the command classifier
        """
        return self.classifier.classify_command(command)

    def extract_page_content(self, selector: str, limit: int = 3) -> List[Dict]:
        """
        Extract information from any webpage using a CSS selector
        """
        try:
            # Wait for elements to load
            self.page.wait_for_selector(selector, timeout=5000)
            
            # Extract content using JavaScript
            content = self.page.evaluate("""
                (selector, limit) => {
                    const items = [];
                    const elements = document.querySelectorAll(selector);
                    for (let i = 0; i < Math.min(elements.length, limit); i++) {
                        const element = elements[i];
                        items.push({
                            text: element.textContent.trim(),
                            href: element.href || null,
                            attributes: Object.fromEntries(
                                Array.from(element.attributes).map(attr => [attr.name, attr.value])
                            )
                        });
                    }
                    return items;
                }
            """, selector, limit)
            
            return content
            
        except Exception as e:
            print(f"Error extracting content: {str(e)}")
            return []

    def execute_command(self, command: str) -> Tuple[bool, str]:
        """
        Execute a natural language command in the browser
        Returns (success, message)
        """
        try:
            parsed_command = self.parse_command(command)
            print(f"Parsed command: {parsed_command}")  # Debug output
            
            # Validate parsed command
            if not parsed_command["action"]:
                return False, "Could not determine action from command"
            
            if parsed_command["action"] == "navigate":
                if not parsed_command["url"]:
                    return False, "No URL provided for navigation"
                self.page.goto(parsed_command["url"])
                return True, f"Navigated to {parsed_command['url']}"
                
            elif parsed_command["action"] == "click":
                if not parsed_command["target"]:
                    return False, "No target element found for click action"
                
                # Wait for the page to load and stabilize
                time.sleep(2)
                
                # Try different selectors for YouTube videos
                if "youtube.com" in self.page.url:
                    try:
                        # Wait for video links to be visible
                        self.page.wait_for_selector("a#video-title", timeout=10000)
                        
                        # Try to find and click the first video
                        if "first" in parsed_command["target"].lower():
                            try:
                                # Click the first video link
                                self.page.click("a#video-title")
                                time.sleep(2)  # Wait for video to start loading
                                return True, "Clicked the first video"
                            except Exception as e:
                                print(f"Error clicking first video: {e}")
                        
                        # Try to find video by title text
                        try:
                            # Find all video titles
                            video_titles = self.page.query_selector_all("a#video-title")
                            for title in video_titles:
                                if title.is_visible():
                                    title.click()
                                    time.sleep(2)  # Wait for video to start loading
                                    return True, "Clicked a video"
                        except Exception as e:
                            print(f"Error clicking video by title: {e}")
                    
                    except Exception as e:
                        print(f"Error with YouTube video selection: {e}")
                
                # Fallback to general click selectors
                selectors = [
                    f"button:has-text('{parsed_command['target']}')",
                    f"a:has-text('{parsed_command['target']}')",
                    f"[role='button']:has-text('{parsed_command['target']}')",
                    f"[type='submit']",
                    f"button[type='submit']",
                    f"input[type='submit']",
                    f"button",
                    f"a[href*='{parsed_command['target'].lower()}']",
                    f"a[title*='{parsed_command['target'].lower()}']"
                ]
                
                for selector in selectors:
                    try:
                        # Wait for element to be visible
                        self.page.wait_for_selector(selector, timeout=5000)
                        # Click the element
                        self.page.click(selector)
                        time.sleep(1)  # Wait for click to register
                        return True, f"Clicked element: {parsed_command['target']}"
                    except Exception as e:
                        print(f"Error with selector {selector}: {e}")
                        continue
                        
                return False, f"Could not find clickable element: {parsed_command['target']}"
                
            elif parsed_command["action"] == "type":
                if not parsed_command["value"]:
                    return False, "No text provided for type action"
                    
                # Try different input selectors with YouTube-specific ones first
                selectors = [
                    "#search-input input",  # YouTube search box
                    "input[name='search_query']",  # Alternative YouTube search
                    "input[type='text']",
                    "input[type='search']",
                    "textarea",
                    "[role='textbox']",
                    "[contenteditable='true']",
                    "input"
                ]
                
                for selector in selectors:
                    try:
                        self.page.fill(selector, parsed_command["value"])
                        return True, f"Typed '{parsed_command['value']}' into input field"
                    except:
                        continue
                        
                return False, "Could not find input field to type into"
                
            elif parsed_command["action"] == "wait":
                time.sleep(2)  # Default wait time
                return True, "Waited for 2 seconds"
                
            elif parsed_command["action"] == "scroll":
                self.page.evaluate("window.scrollBy(0, 500)")  # Scroll down by 500px
                return True, "Scrolled down the page"
                
            elif parsed_command["action"] == "search":
                if not parsed_command["value"]:
                    return False, "No search query provided"
                
                # First navigate to the URL if provided and we're not already there
                if parsed_command.get("url"):
                    current_url = self.page.url
                    if not current_url.startswith(parsed_command["url"]):
                        self.page.goto(parsed_command["url"])
                        time.sleep(3)  # Wait longer for page to load
                    
                # Try to find and fill search box
                try:
                    # YouTube-specific selectors first
                    if parsed_command.get("url") and "youtube.com" in parsed_command["url"]:
                        # Wait for the search box to be visible
                        try:
                            self.page.wait_for_selector("input[name='search_query']", timeout=10000)
                            # Clear any existing text
                            self.page.fill("input[name='search_query']", "")
                            # Type the search query
                            self.page.fill("input[name='search_query']", parsed_command["value"])
                            # Press Enter to search
                            self.page.keyboard.press("Enter")
                            time.sleep(3)  # Wait longer for results
                            return True, f"Searched for '{parsed_command['value']}'"
                        except Exception as e:
                            print(f"Error with YouTube search: {e}")
                    
                    # Fallback to common search selectors
                    search_selectors = [
                        "input[type='search']",
                        "input[name='q']",
                        "input[name='search']",
                        "input[aria-label='Search']",
                        "input[placeholder*='search']",
                        "input[placeholder*='Search']",
                        "input[name='search_query']",
                        "#search-input input",
                        "input#search"
                    ]
                    
                    for selector in search_selectors:
                        try:
                            # Wait for the search input to be visible
                            self.page.wait_for_selector(selector, timeout=5000)
                            # Clear any existing text
                            self.page.fill(selector, "")
                            # Type the search query
                            self.page.fill(selector, parsed_command["value"])
                            # Press Enter to search
                            self.page.keyboard.press("Enter")
                            time.sleep(3)  # Wait longer for results
                            return True, f"Searched for '{parsed_command['value']}'"
                        except Exception as e:
                            print(f"Error with selector {selector}: {e}")
                            continue
                    
                    return False, "Could not find search input field"
                        
                except Exception as e:
                    return False, f"Error performing search: {str(e)}"
            
            elif parsed_command["action"] == "extract":
                if not parsed_command["target"]:
                    return False, "No target specified for extraction"
                
                # Extract content based on target
                content = self.extract_page_content(parsed_command["target"])
                if content:
                    # Save results to a file
                    filename = f"extracted_{parsed_command['target'].replace(' ', '_')}.json"
                    with open(filename, "w") as f:
                        json.dump(content, f, indent=2)
                    return True, f"Extracted {len(content)} items and saved to {filename}"
                else:
                    return False, f"No content found for selector: {parsed_command['target']}"
            
            return False, f"Unsupported action: {parsed_command['action']}"
                    
        except Exception as e:
            return False, f"Error executing command: {str(e)}"
            
    def close(self):
        """
        Clean up browser resources
        """
        self.context.close()
        self.browser.close()
        self.playwright.stop() 