from typing import Dict, List, Tuple, Optional
from playwright.sync_api import sync_playwright, Page
import time
import json
from command_classifier import CommandClassifier
from bs4 import BeautifulSoup
import re

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

    def analyze_page_structure(self) -> Dict[str, List[str]]:
        """
        Analyze the current page structure using BeautifulSoup
        Returns a dictionary of element types and their selectors
        """
        try:
            # Get the page content
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Initialize result dictionary
            selectors = {
                'search_inputs': [],
                'buttons': [],
                'links': [],
                'videos': [],
                'forms': []
            }
            
            # Find search inputs
            for input_elem in soup.find_all('input'):
                if input_elem.get('type') in ['search', 'text'] or 'search' in str(input_elem).lower():
                    selector = self._generate_selector(input_elem)
                    if selector:
                        selectors['search_inputs'].append(selector)
            
            # Find buttons
            for button in soup.find_all(['button', 'input']):
                if button.get('type') == 'submit' or button.name == 'button':
                    selector = self._generate_selector(button)
                    if selector:
                        selectors['buttons'].append(selector)
            
            # Find links
            for link in soup.find_all('a'):
                selector = self._generate_selector(link)
                if selector:
                    selectors['links'].append(selector)
            
            # Find video elements (YouTube specific)
            for video in soup.find_all(['a', 'div'], {'id': re.compile(r'video|player|watch')}):
                selector = self._generate_selector(video)
                if selector:
                    selectors['videos'].append(selector)
            
            # Find forms
            for form in soup.find_all('form'):
                selector = self._generate_selector(form)
                if selector:
                    selectors['forms'].append(selector)
            
            return selectors
            
        except Exception as e:
            print(f"Error analyzing page structure: {e}")
            return {}

    def _generate_selector(self, element) -> Optional[str]:
        """
        Generate a unique CSS selector for an element
        """
        try:
            # Try ID first
            if element.get('id'):
                return f"#{element['id']}"
            
            # Try name attribute
            if element.get('name'):
                return f"[name='{element['name']}']"
            
            # Try role attribute
            if element.get('role'):
                return f"[role='{element['role']}']"
            
            # Try class names
            if element.get('class'):
                classes = ' '.join(element['class'])
                return f".{classes.replace(' ', '.')}"
            
            # Try aria-label
            if element.get('aria-label'):
                return f"[aria-label='{element['aria-label']}']"
            
            # Try placeholder
            if element.get('placeholder'):
                return f"[placeholder='{element['placeholder']}']"
            
            # Try type attribute
            if element.get('type'):
                return f"[type='{element['type']}']"
            
            # Try text content for buttons and links
            if element.name in ['button', 'a'] and element.string:
                return f"{element.name}:has-text('{element.string.strip()}')"
            
            # Fallback to element type
            return element.name
            
        except Exception as e:
            print(f"Error generating selector: {e}")
            return None

    def find_best_selector(self, element_type: str, text: str = None) -> Optional[str]:
        """
        Find the best selector for a given element type and optional text using Playwright's smart locators
        """
        try:
            if element_type == 'search_input':
                # Try form-based search first
                search_form = self.page.locator("form").filter(has=self.page.locator("input[type='search']")).first
                if search_form and search_form.is_visible():
                    search_input = search_form.locator("input").first
                    if search_input and search_input.is_visible():
                        return "form input[type='search']"
                
                # Try website-specific selectors first
                current_url = self.page.url.lower()
                if 'youtube.com' in current_url:
                    return "input[name='search_query']"
                elif 'amazon' in current_url:
                    return "#twotabsearchtextbox"
                elif 'google.com' in current_url:
                    return "input[name='q']"
                elif 'github.com' in current_url:
                    return "input[name='q']"
                
                # Try multiple search input strategies
                search_selectors = [
                    "nav input[type='search']",
                    "header input[type='search']",
                    "input[type='search']",
                    "input[placeholder*='search' i]",
                    "input[name*='search' i]",
                    "input[aria-label*='search' i]",
                    "[role='search'] input",
                    "input.search",
                    "input#search",
                    "input[type='text']"
                ]
                
                for selector in search_selectors:
                    try:
                        element = self.page.locator(selector).first
                        if element and element.is_visible():
                            return selector
                    except:
                        continue
            
            elif element_type in ['button', 'link', 'product']:
                # Try to find element by text content first
                if text:
                    text_selectors = [
                        f"button:has-text('{text}')",
                        f"a:has-text('{text}')",
                        f"[role='button']:has-text('{text}')",
                        f"[role='link']:has-text('{text}')",
                        f"[data-testid*='product']:has-text('{text}')",
                        f".product:has-text('{text}')"
                    ]
                    
                    for selector in text_selectors:
                        try:
                            element = self.page.locator(selector).first
                            if element and element.is_visible():
                                return selector
                        except:
                            continue
                
                # Try first matching element
                generic_selectors = {
                    'button': ["button", "[role='button']", "input[type='submit']"],
                    'link': ["a", "[role='link']"],
                    'product': ["[data-testid*='product']", ".product", "a[href*='product']", "a:has(img)"]
                }
                
                for selector in generic_selectors.get(element_type, []):
                    try:
                        element = self.page.locator(selector).first
                        if element and element.is_visible():
                            return selector
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"Error finding selector: {e}")
            return None

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
                time.sleep(3)  # Wait for page to load
                return True, f"Navigated to {parsed_command['url']}"
                
            elif parsed_command["action"] == "click":
                if not parsed_command["target"]:
                    return False, "No target element found for click action"
                
                # Wait for the page to load and stabilize
                time.sleep(2)
                
                # Determine element type based on target
                element_type = parsed_command.get("element_type", "button")
                if "product" in parsed_command["target"].lower():
                    element_type = "product"
                elif "link" in parsed_command["target"].lower():
                    element_type = "link"
                
                # Try to find and click the element
                selector = self.find_best_selector(element_type, parsed_command["target"])
                if selector:
                    try:
                        # Wait for element and ensure it's visible
                        element = self.page.locator(selector).first
                        if element and element.is_visible():
                            element.scroll_into_view_if_needed()
                            time.sleep(1)  # Brief pause after scrolling
                            element.click()
                            time.sleep(2)
                            return True, f"Clicked element: {parsed_command['target']}"
                    except Exception as e:
                        print(f"Error clicking element: {e}")
                        # Try alternative click methods
                        try:
                            self.page.evaluate(f"document.querySelector('{selector}').click()")
                            time.sleep(2)
                            return True, f"Clicked element using JavaScript: {parsed_command['target']}"
                        except Exception as js_e:
                            print(f"JavaScript click failed: {js_e}")
                
                return False, f"Could not find or click element: {parsed_command['target']}"
                
            elif parsed_command["action"] == "search":
                if not parsed_command["value"]:
                    return False, "No search query provided"
                
                # First navigate to the URL if provided and we're not already there
                if parsed_command.get("url"):
                    current_url = self.page.url
                    if not current_url.startswith(parsed_command["url"]):
                        self.page.goto(parsed_command["url"])
                        time.sleep(3)
                
                # Find and use the search input
                selector = self.find_best_selector("search_input")
                if selector:
                    try:
                        # Wait for element and ensure it's visible
                        element = self.page.locator(selector).first
                        if element and element.is_visible():
                            element.scroll_into_view_if_needed()
                            time.sleep(1)  # Brief pause after scrolling
                            
                            # Clear existing text and type new search
                            element.fill("")
                            element.type(parsed_command["value"], delay=100)  # Slower typing for stability
                            time.sleep(0.5)
                            
                            # Try different ways to submit the search
                            try:
                                element.press("Enter")
                            except:
                                try:
                                    # Look for a search button
                                    search_button = self.page.locator("button[type='submit'], button:has-text('Search')").first
                                    if search_button and search_button.is_visible():
                                        search_button.click()
                                except:
                                    # Fallback to form submission
                                    self.page.evaluate("document.querySelector('form').submit()")
                            
                            time.sleep(3)
                            return True, f"Searched for '{parsed_command['value']}'"
                    except Exception as e:
                        print(f"Error performing search: {e}")
                
                return False, "Could not find or use search input field"
            
            elif parsed_command["action"] == "type":
                if not parsed_command["value"]:
                    return False, "No text provided for type action"
                
                # Find and use the input field
                selector = self.find_best_selector("input", parsed_command["target"])
                if selector:
                    try:
                        element = self.page.locator(selector).first
                        if element and element.is_visible():
                            element.scroll_into_view_if_needed()
                            time.sleep(1)
                            element.fill("")
                            element.type(parsed_command["value"], delay=100)
                            return True, f"Typed '{parsed_command['value']}' into input field"
                    except Exception as e:
                        print(f"Error typing text: {e}")
                
                return False, "Could not find input field to type into"
                
            elif parsed_command["action"] == "wait":
                time.sleep(2)  # Default wait time
                return True, "Waited for 2 seconds"
                
            elif parsed_command["action"] == "scroll":
                self.page.evaluate("window.scrollBy(0, 500)")  # Scroll down by 500px
                return True, "Scrolled down the page"
                
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