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

    def analyze_page_structure(self) -> Dict[str, List[str]]:
        """
        Analyze the current page structure using JavaScript
        Returns a dictionary of element types and their selectors
        """
        try:
            # Use JavaScript to analyze the page structure
            selectors = self.page.evaluate("""
                () => {
                    const result = {
                        search_inputs: [],
                        buttons: [],
                        links: [],
                        videos: [],
                        forms: []
                    };
                    
                    // Find search inputs
                    document.querySelectorAll('input[type="search"], input[type="text"]').forEach(input => {
                        if (input.type === 'search' || input.placeholder?.toLowerCase().includes('search') || 
                            input.name?.toLowerCase().includes('search')) {
                            result.search_inputs.push(generateSelector(input));
                        }
                    });
                    
                    // Find buttons
                    document.querySelectorAll('button, input[type="submit"], [role="button"]').forEach(button => {
                        result.buttons.push(generateSelector(button));
                    });
                    
                    // Find links
                    document.querySelectorAll('a').forEach(link => {
                        result.links.push(generateSelector(link));
                    });
                    
                    // Find video elements
                    document.querySelectorAll('[id*="video"], [id*="player"], [id*="watch"]').forEach(video => {
                        result.videos.push(generateSelector(video));
                    });
                    
                    // Find forms
                    document.querySelectorAll('form').forEach(form => {
                        result.forms.push(generateSelector(form));
                    });
                    
                    function generateSelector(element) {
                        if (element.id) {
                            return `#${element.id}`;
                        }
                        if (element.name) {
                            return `[name="${element.name}"]`;
                        }
                        if (element.getAttribute('role')) {
                            return `[role="${element.getAttribute('role')}"]`;
                        }
                        if (element.className) {
                            return `.${element.className.split(' ').join('.')}`;
                        }
                        if (element.getAttribute('aria-label')) {
                            return `[aria-label="${element.getAttribute('aria-label')}"]`;
                        }
                        if (element.placeholder) {
                            return `[placeholder="${element.placeholder}"]`;
                        }
                        return element.tagName.toLowerCase();
                    }
                    
                    return result;
                }
            """)
            
            return selectors
            
        except Exception as e:
            print(f"Error analyzing page structure: {e}")
            return {}

    def find_best_selector(self, element_type: str, text: str = None) -> Optional[str]:
        """
        Find the best selector for a given element type and optional text
        """
        try:
            if text:
                # Try to find element by text content first
                text_selectors = {
                    'search_input': [
                        "input[placeholder*='search' i]",
                        "input[name*='search' i]",
                        "input[type='search']"
                    ],
                    'button': [
                        f"button:has-text('{text}')",
                        f"[role='button']:has-text('{text}')"
                    ],
                    'link': [
                        f"a:has-text('{text}')",
                        f"[role='link']:has-text('{text}')"
                    ],
                    'product': [
                        f"[data-testid*='product']:has-text('{text}')",
                        f".product:has-text('{text}')"
                    ]
                }
                
                for selector in text_selectors.get(element_type, []):
                    try:
                        element = self.page.locator(selector).first
                        if element and element.is_visible():
                            return selector
                    except:
                        continue

            # Website-specific selectors for search
            if element_type == 'search_input':
                current_url = self.page.url.lower()
                if 'youtube.com' in current_url:
                    return "input[name='search_query']"
                elif 'amazon' in current_url:
                    return "#twotabsearchtextbox"
                elif 'google.com' in current_url:
                    return "input[name='q']"
                elif 'github.com' in current_url:
                    return "input[name='q']"

            # Generic selectors
            generic_selectors = {
                'search_input': [
                    "input[type='search']",
                    "input[placeholder*='search' i]",
                    "input[name*='search' i]",
                    "[role='search'] input",
                    "input.search",
                    "input#search"
                ],
                'button': [
                    "button",
                    "[role='button']",
                    "input[type='submit']"
                ],
                'link': [
                    "a",
                    "[role='link']"
                ],
                'product': [
                    "[data-testid*='product']",
                    ".product",
                    "a[href*='product']"
                ]
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
        """
        try:
            # Parse the command
            action = self.parse_command(command)
            
            if not action:
                return False, "Could not understand the command"
            
            command_type = action.get('type')
            target = action.get('target', '')
            value = action.get('value', '')
            
            if command_type == 'navigate':
                # Handle navigation commands
                if not target.startswith(('http://', 'https://')):
                    target = f'https://{target}'
                self.page.goto(target)
                return True, f"Navigated to {target}"
            
            elif command_type == 'search':
                # Find search input and perform search
                search_selector = self.find_best_selector('search_input')
                if not search_selector:
                    return False, "Could not find search input"
                
                search_input = self.page.locator(search_selector).first
                search_input.click()
                search_input.fill(target)
                search_input.press('Enter')
                return True, f"Searched for {target}"
            
            elif command_type == 'click':
                # Handle click commands
                element_type = 'button' if 'button' in target.lower() else 'link'
                selector = self.find_best_selector(element_type, target)
                
                if not selector:
                    return False, f"Could not find {element_type} with text '{target}'"
                
                self.page.locator(selector).first.click()
                return True, f"Clicked {element_type} with text '{target}'"
            
            elif command_type == 'scroll':
                # Handle scroll commands
                if target == 'top':
                    self.page.evaluate("window.scrollTo(0, 0)")
                elif target == 'bottom':
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                else:
                    # Scroll by a specific amount
                    scroll_amount = 500 if target == 'down' else -500
                    self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                return True, f"Scrolled {target}"
            
            elif command_type == 'extract':
                # Handle data extraction
                selector = self.find_best_selector(target)
                if not selector:
                    return False, f"Could not find elements of type {target}"
                
                content = self.extract_page_content(selector)
                return True, json.dumps(content, indent=2)
            
            return False, "Unsupported command type"
            
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def close(self):
        """
        Close the browser and clean up
        """
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop() 