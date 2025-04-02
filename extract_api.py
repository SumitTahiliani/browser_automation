from playwright.sync_api import Page
from typing import Dict, List, Optional, Any
import json

class ExtractAPI:
    def __init__(self, page: Page):
        self.page = page
        
        # Define common data extraction patterns
        self.extraction_patterns = {
            "text": {
                "selectors": [
                    "p", "h1", "h2", "h3", "h4", "h5", "h6",
                    "span", "div", "article", "section"
                ],
                "attributes": ["textContent", "innerText"]
            },
            "links": {
                "selectors": ["a"],
                "attributes": ["href", "textContent"]
            },
            "images": {
                "selectors": ["img"],
                "attributes": ["src", "alt"]
            },
            "tables": {
                "selectors": ["table"],
                "attributes": ["innerHTML"]
            },
            "forms": {
                "selectors": ["form"],
                "attributes": ["action", "method"]
            }
        }

    def extract_data(self, command: str) -> Dict[str, Any]:
        """
        Extract structured data from the current page based on the command
        """
        try:
            # Parse the extraction command
            if "text" in command.lower():
                return self._extract_text()
            elif "links" in command.lower():
                return self._extract_links()
            elif "images" in command.lower():
                return self._extract_images()
            elif "table" in command.lower():
                return self._extract_tables()
            elif "form" in command.lower():
                return self._extract_forms()
            else:
                return {"error": "Unsupported extraction command"}
                
        except Exception as e:
            return {"error": f"Extraction failed: {str(e)}"}

    def _extract_text(self) -> Dict[str, List[str]]:
        """
        Extract text content from the page
        """
        text_content = []
        for selector in self.extraction_patterns["text"]["selectors"]:
            elements = self.page.query_selector_all(selector)
            for element in elements:
                for attr in self.extraction_patterns["text"]["attributes"]:
                    try:
                        text = element.evaluate(f"el => el.{attr}")
                        if text and text.strip():
                            text_content.append(text.strip())
                    except:
                        continue
        return {"text": text_content}

    def _extract_links(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract links from the page
        """
        links = []
        elements = self.page.query_selector_all("a")
        for element in elements:
            link_data = {}
            for attr in self.extraction_patterns["links"]["attributes"]:
                try:
                    value = element.evaluate(f"el => el.{attr}")
                    if value:
                        link_data[attr] = value
                except:
                    continue
            if link_data:
                links.append(link_data)
        return {"links": links}

    def _extract_images(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract images from the page
        """
        images = []
        elements = self.page.query_selector_all("img")
        for element in elements:
            image_data = {}
            for attr in self.extraction_patterns["images"]["attributes"]:
                try:
                    value = element.evaluate(f"el => el.{attr}")
                    if value:
                        image_data[attr] = value
                except:
                    continue
            if image_data:
                images.append(image_data)
        return {"images": images}

    def _extract_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract tables from the page
        """
        tables = []
        elements = self.page.query_selector_all("table")
        for element in elements:
            table_data = {}
            for attr in self.extraction_patterns["tables"]["attributes"]:
                try:
                    value = element.evaluate(f"el => el.{attr}")
                    if value:
                        table_data[attr] = value
                except:
                    continue
            if table_data:
                tables.append(table_data)
        return {"tables": tables}

    def _extract_forms(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract forms from the page
        """
        forms = []
        elements = self.page.query_selector_all("form")
        for element in elements:
            form_data = {}
            for attr in self.extraction_patterns["forms"]["attributes"]:
                try:
                    value = element.evaluate(f"el => el.{attr}")
                    if value:
                        form_data[attr] = value
                except:
                    continue
            if form_data:
                forms.append(form_data)
        return {"forms": forms}

    def save_to_file(self, data: Dict[str, Any], filename: str) -> bool:
        """
        Save extracted data to a JSON file
        """
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return False 