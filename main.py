from email_client import TempEmailClient
import sys
import time
from colorama import init, Fore, Style
import os

init()  # Initialize colorama

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(f"{Fore.CYAN}╔══════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║            TempBox              ║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚══════════════════════════════════╝{Style.RESET_ALL}\n")

def print_menu():
    print(f"{Fore.GREEN}1.{Style.RESET_ALL} Create a new temporary email")
    print(f"{Fore.GREEN}2.{Style.RESET_ALL} Check messages")
    print(f"{Fore.GREEN}3.{Style.RESET_ALL} Wait for new messages")
    print(f"{Fore.GREEN}4.{Style.RESET_ALL} Search messages")
    print(f"{Fore.GREEN}5.{Style.RESET_ALL} View message details")
    print(f"{Fore.GREEN}6.{Style.RESET_ALL} Delete message")
    print(f"{Fore.GREEN}7.{Style.RESET_ALL} Save message to file")
    print(f"{Fore.GREEN}8.{Style.RESET_ALL} Exit")

def main():
    print(f"{Fore.GREEN}Welcome to TempBox!{Style.RESET_ALL}")
    client = TempEmailClient()
    
    while True:
        print_header()
        print_menu()
        
        choice = input(f"\n{Fore.YELLOW}Enter your choice (1-8):{Style.RESET_ALL} ")
        
        if choice == "1":
            print(f"\n{Fore.BLUE}Creating new temporary email...{Style.RESET_ALL}")
            if client.create_account():
                print(f"{Fore.GREEN}Account created successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to create account{Style.RESET_ALL}")
        
        elif choice == "2":
            print(f"\n{Fore.BLUE}Checking messages...{Style.RESET_ALL}")
            client.display_messages()
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            print(f"\n{Fore.BLUE}Waiting for new messages...{Style.RESET_ALL}")
            try:
                interval = int(input(f"{Fore.YELLOW}Enter check interval in seconds (default 10):{Style.RESET_ALL} ") or 10)
                max_checks = int(input(f"{Fore.YELLOW}Enter maximum number of checks (default 10):{Style.RESET_ALL} ") or 10)
                client.wait_for_new_messages(interval, max_checks)
            except ValueError:
                print(f"{Fore.RED}Invalid input. Using default values.{Style.RESET_ALL}")
                client.wait_for_new_messages()
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            query = input(f"\n{Fore.YELLOW}Enter search term:{Style.RESET_ALL} ")
            results = client.search_messages(query)
            if results:
                print(f"\n{Fore.GREEN}Found {len(results)} messages:{Style.RESET_ALL}")
                for msg in results:
                    print(f"\nID: {msg.get('id')[:8]}")
                    print(f"From: {msg.get('from', {}).get('address', 'N/A')}")
                    print(f"Subject: {msg.get('subject', 'N/A')}")
            else:
                print(f"{Fore.RED}No messages found{Style.RESET_ALL}")
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            msg_id = input(f"\n{Fore.YELLOW}Enter message ID:{Style.RESET_ALL} ")
            client.display_message_content(msg_id)
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            msg_id = input(f"\n{Fore.YELLOW}Enter message ID to delete:{Style.RESET_ALL} ")
            if client.delete_message(msg_id):
                print(f"{Fore.GREEN}Message deleted successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to delete message{Style.RESET_ALL}")
            input("\nPress Enter to continue...")
        
        elif choice == "7":
            msg_id = input(f"\n{Fore.YELLOW}Enter message ID to save:{Style.RESET_ALL} ")
            client.save_message_to_file(msg_id)
            input("\nPress Enter to continue...")
        
        elif choice == "8":
            print(f"{Fore.GREEN}Thank you for using Temporary Email System. Goodbye!{Style.RESET_ALL}")
            sys.exit()
        
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
            time.sleep(2)

if __name__ == "__main__":
    main()