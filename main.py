from interact_api import InteractAPI
import json
import os
import time

def print_help():
    print("\nAvailable commands:")
    print("1. navigate to [url] - Navigate to any website (e.g., 'navigate to https://example.com')")
    print("2. search for [query] - Search on the current page (e.g., 'search for python programming')")
    print("3. type [text] in [element] - Type text into an input field")
    print("4. click [element] - Click on an element")
    print("5. wait - Wait for 2 seconds")
    print("6. scroll - Scroll down the page")
    print("7. extract [selector] - Extract content using CSS selector (e.g., 'extract article')")
    print("8. help - Show this help message")
    print("9. exit - Close the browser and exit")
    print("\nYou can enter multiple commands separated by 'then' or 'and'")
    print("Example: 'go to youtube then search for 3blue1brown and click the first video'")

def display_extracted_content(filename: str):
    """Display the contents of an extracted JSON file"""
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            print(f"\nExtracted content from {filename}:")
            for i, item in enumerate(data, 1):
                print(f"\n{i}. {item['text']}")
                if item.get('href'):
                    print(f"   URL: {item['href']}")
                if item.get('attributes'):
                    print("   Attributes:")
                    for key, value in item['attributes'].items():
                        print(f"     {key}: {value}")
    except Exception as e:
        print(f"Error reading results: {str(e)}")

def split_commands(command: str) -> list:
    """Split a command string into individual commands"""
    # Split by 'then' or 'and'
    commands = []
    for cmd in command.lower().replace('then', ',').replace('and', ',').split(','):
        cmd = cmd.strip()
        if cmd:
            commands.append(cmd)
    return commands

def execute_commands(api: InteractAPI, commands: list) -> None:
    """Execute a list of commands"""
    for i, command in enumerate(commands, 1):
        print(f"\nExecuting command {i}/{len(commands)}: {command}")
        result, message = api.execute_command(command)
        print(f"Result: {'Success' if result else 'Failed'}")
        print(f"Message: {message}")
        
        # If the command was an extract action, show the results
        if result and command.lower().startswith('extract'):
            # Find the most recently created JSON file
            json_files = [f for f in os.listdir('.') if f.startswith('extracted_') and f.endswith('.json')]
            if json_files:
                latest_file = max(json_files, key=os.path.getctime)
                display_extracted_content(latest_file)
        
        # Add a small delay between commands
        if i < len(commands):
            time.sleep(1)

def main():
    api = InteractAPI()
    print("\nWelcome to the Interactive Browser!")
    print("Type 'help' to see available commands.")
    print("Type 'exit' to close the browser and quit.")
    
    try:
        while True:
            try:
                command = input("\nEnter command(s): ").strip()
                
                if command.lower() == 'exit':
                    print("Closing browser...")
                    break
                elif command.lower() == 'help':
                    print_help()
                    continue
                
                if not command:
                    continue
                
                # Split the command into individual commands
                commands = split_commands(command)
                if not commands:
                    print("No valid commands found. Please try again.")
                    continue
                
                # Execute all commands
                execute_commands(api, commands)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to close the browser and quit.")
            except Exception as e:
                print(f"Error executing command: {str(e)}")
    
    finally:
        api.close()

if __name__ == "__main__":
    main() 