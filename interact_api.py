import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tree import Tree
from typing import Dict, List, Tuple, Optional
from playwright.sync_api import sync_playwright, Page
import time
import re
import json
from command_classifier import CommandClassifier

class InteractAPI:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('maxent_ne_chunker')
        nltk.download('words')
        
        # Initialize Playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Initialize command classifier
        self.classifier = CommandClassifier()

    def parse_command(self, command: str) -> Dict:
        """
        Parse a natural language command using Gemini API
        """
        return self.classifier.classify_command(command)

    def extract_youtube_videos(self, limit: int = 3) -> List[Dict]:
        """
        Extract information about YouTube videos from search results
        """
        try:
            # Wait for video results to load
            self.page.wait_for_selector("ytd-video-renderer", timeout=5000)
            
            # Extract video information using JavaScript
            videos = self.page.evaluate("""
                (limit) => {
                    const videos = [];
                    const items = document.querySelectorAll('ytd-video-renderer');
                    for (let i = 0; i < Math.min(items.length, limit); i++) {
                        const item = items[i];
                        const titleElement = item.querySelector('#video-title');
                        const channelElement = item.querySelector('#channel-name');
                        const viewsElement = item.querySelector('#metadata-line');
                        
                        if (titleElement && channelElement) {
                            videos.push({
                                title: titleElement.textContent.trim(),
                                url: titleElement.href,
                                channel: channelElement.textContent.trim(),
                                metadata: viewsElement ? viewsElement.textContent.trim() : ''
                            });
                        }
                    }
                    return videos;
                }
            """, limit)
            
            return videos
            
        except Exception as e:
            print(f"Error extracting videos: {str(e)}")
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
                    # Default to YouTube if no URL specified
                    self.page.goto("https://www.youtube.com")
                    return True, "Navigated to YouTube"
                self.page.goto(parsed_command["url"])
                return True, f"Navigated to {parsed_command['url']}"
                
            elif parsed_command["action"] == "click":
                if not parsed_command["target"]:
                    return False, "No target element found for click action"
                    
                # Try different selectors
                selectors = [
                    f"button:has-text('{parsed_command['target']}')",
                    f"a:has-text('{parsed_command['target']}')",
                    f"[role='button']:has-text('{parsed_command['target']}')",
                    f"[type='submit']",
                    f"button[type='submit']",
                    f"input[type='submit']",
                    f"button"
                ]
                
                for selector in selectors:
                    try:
                        self.page.click(selector)
                        return True, f"Clicked element: {parsed_command['target']}"
                    except:
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
                    
                # Try to find and fill YouTube search box
                try:
                    # First try YouTube-specific search box
                    try:
                        self.page.fill("#search-input input", parsed_command["value"])
                    except:
                        self.page.fill("input[name='search_query']", parsed_command["value"])
                    
                    # Press Enter to search
                    self.page.keyboard.press("Enter")
                    
                    # Wait for results and extract videos
                    print("Waiting for search results to load...")
                    self.page.wait_for_selector("ytd-video-renderer", timeout=10000)  # Wait up to 10 seconds
                    time.sleep(2)  # Additional wait for dynamic content
                    videos = self.extract_youtube_videos(3)
                    
                    if videos:
                        # Save results to a file
                        with open("youtube_results.json", "w") as f:
                            json.dump(videos, f, indent=2)
                        return True, f"Found {len(videos)} videos and saved to youtube_results.json"
                    else:
                        return False, "No videos found in search results"
                        
                except Exception as e:
                    return False, f"Error performing search: {str(e)}"
            
            elif parsed_command["action"] == "extract":
                if parsed_command["target"] == "video":
                    videos = self.extract_youtube_videos(3)
                    if videos:
                        with open("youtube_results.json", "w") as f:
                            json.dump(videos, f, indent=2)
                        return True, f"Extracted {len(videos)} videos and saved to youtube_results.json"
                    else:
                        return False, "No videos found to extract"
            
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