from interact_api import InteractAPI
import json

def print_help():
    print("\nAvailable commands:")
    print("1. navigate to [url] - Navigate to a website (e.g., 'navigate to youtube')")
    print("2. search for [query] - Search on the current page (e.g., 'search for 3blue1brown')")
    print("3. type [text] in [element] - Type text into an input field")
    print("4. click [element] - Click on an element")
    print("5. wait - Wait for 2 seconds")
    print("6. scroll - Scroll down the page")
    print("7. extract videos - Extract video information from current page")
    print("8. help - Show this help message")
    print("9. exit - Close the browser and exit")

def main():
    api = InteractAPI()
    print("\nWelcome to the Interactive Browser!")
    print("Type 'help' to see available commands.")
    print("Type 'exit' to close the browser and quit.")
    
    try:
        while True:
            try:
                command = input("\nEnter command: ").strip()
                
                if command.lower() == 'exit':
                    print("Closing browser...")
                    break
                elif command.lower() == 'help':
                    print_help()
                    continue
                
                if not command:
                    continue
                
                print(f"\nExecuting command: {command}")
                result, message = api.execute_command(command)
                print(f"Result: {'Success' if result else 'Failed'}")
                print(f"Message: {message}")
                
                # If the command was a search or extract, show the results
                if result and command.lower().startswith(('search', 'extract')):
                    try:
                        with open("youtube_results.json", "r") as f:
                            videos = json.load(f)
                            print("\nResults found:")
                            for i, video in enumerate(videos, 1):
                                print(f"\n{i}. {video['title']}")
                                print(f"   Channel: {video['channel']}")
                                print(f"   {video['metadata']}")
                                print(f"   URL: {video['url']}")
                    except Exception as e:
                        print(f"Error reading results: {str(e)}")
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to close the browser and quit.")
            except Exception as e:
                print(f"Error executing command: {str(e)}")
    
    finally:
        api.close()

if __name__ == "__main__":
    main() 