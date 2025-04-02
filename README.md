# Browser Automation Agent

A Python-based browser automation agent that accepts natural language commands to control browser actions. This project uses Playwright for browser automation and spaCy for basic natural language processing.

## Features

- Natural language command parsing
- Browser automation using Playwright
- Support for common browser actions:
  - Navigation
  - Clicking elements
  - Typing text
  - Scrolling
  - Searching
  - Waiting

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
3. Install Playwright browsers:
```bash
playwright install
```

## Usage

Run the example script:
```bash
python main.py
```

The example script demonstrates basic usage with commands like:
- "go to https://www.google.com"
- "type 'python programming' in the search box"
- "click the search button"
- "wait for 2 seconds"
- "scroll down the page"

## Supported Commands

The agent supports the following types of commands:

1. Navigation:
   - "go to [URL]"
   - "visit [URL]"
   - "navigate to [URL]"

2. Clicking:
   - "click [element]"
   - "press [element]"
   - "tap [element]"

3. Typing:
   - "type [text] in [element]"
   - "enter [text] in [element]"
   - "input [text] in [element]"

4. Waiting:
   - "wait"
   - "pause"

5. Scrolling:
   - "scroll down"
   - "scroll up"
   - "move down"
   - "move up"

6. Searching:
   - "search for [query]"
   - "find [query]"
   - "look for [query]"

## Error Handling

The agent includes error handling for common scenarios:
- Invalid commands
- Missing required parameters
- Element not found
- Navigation errors
- Input field not found

## Limitations

- The natural language processing is rule-based and may not handle complex or ambiguous commands
- Element selection is based on common patterns and may need adjustment for specific websites
- Some websites may have anti-automation measures that could prevent certain actions

## Contributing

Feel free to submit issues and enhancement requests! 