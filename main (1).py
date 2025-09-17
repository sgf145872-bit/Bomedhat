#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gmail Generator & Verifier Tool
Generate and verify random Gmail addresses with colorful output
"""

import argparse
import random
import string
import json
import time
import os
import sys
from verify_email import verify_email
from tqdm import tqdm
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

class ColorfulOutput:
    """Class for colorful terminal output"""

    @staticmethod
    def header(text):
        """Print header text"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}╔{'═' * (len(text) + 2)}╗")
        print(f"║ {text} ║")
        print(f"╚{'═' * (len(text) + 2)}╝{Style.RESET_ALL}")

    @staticmethod
    def success(text):
        """Print success text"""
        print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

    @staticmethod
    def error(text):
        """Print error text"""
        print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

    @staticmethod
    def warning(text):
        """Print warning text"""
        print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

    @staticmethod
    def info(text):
        """Print info text"""
        print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

    @staticmethod
    def progress(text):
        """Print progress text"""
        print(f"{Fore.MAGENTA}🔄 {text}{Style.RESET_ALL}")

    @staticmethod
    def email(text, status):
        """Print email with status color"""
        if status == "valid":
            print(f"{Fore.GREEN}📧 {text}{Style.RESET_ALL}")
        elif status == "invalid":
            print(f"{Fore.RED}📧 {text}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}📧 {text}{Style.RESET_ALL}")

class GmailGeneratorVerifier:
    def __init__(self, timeout=15, results_file="gmail_results.json", checked_file="checked_gmails.txt"):
        """
        Initialize Gmail generator and verifier

        Args:
            timeout (int): Verification timeout in seconds
            results_file (str): File to save valid emails
            checked_file (str): File to save checked emails
        """
        self.timeout = timeout
        self.results_file = results_file
        self.checked_file = checked_file

        # Load previously checked emails
        self.checked_emails = self._load_checked_emails()
        self.valid_emails = self._load_valid_emails()

    def _load_checked_emails(self):
        """Load previously checked emails"""
        checked_emails = set()
        if os.path.exists(self.checked_file):
            try:
                with open(self.checked_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        email = line.strip()
                        if email:
                            checked_emails.add(email)
                ColorfulOutput.success(f"Loaded {len(checked_emails)} previously checked emails")
            except Exception as e:
                ColorfulOutput.error(f"Error loading checked emails: {e}")
        return checked_emails

    def _load_valid_emails(self):
        """Load valid emails"""
        valid_emails = []
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    valid_emails = data.get('valid_emails', [])
                ColorfulOutput.success(f"Loaded {len(valid_emails)} valid emails")
            except Exception as e:
                ColorfulOutput.error(f"Error loading valid emails: {e}")
        return valid_emails

    def _save_checked_email(self, email):
        """Save checked email"""
        self.checked_emails.add(email)
        try:
            with open(self.checked_file, 'a', encoding='utf-8') as f:
                f.write(f"{email}\n")
        except Exception as e:
            ColorfulOutput.error(f"Error saving checked email: {e}")

    def _save_valid_email(self, email):
        """Save valid email"""
        email_data = {
            'email': email,
            'checked_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'gmail'
        }
        self.valid_emails.append(email_data)

        data = {
            'valid_emails': self.valid_emails,
            'total_checked': len(self.checked_emails),
            'total_valid': len(self.valid_emails),
            'last_update': time.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            ColorfulOutput.error(f"Error saving valid email: {e}")

    def generate_gmail(self, username_length=8, use_numbers=True, use_dots=True):
        """
        Generate random Gmail address

        Args:
            username_length (int): Username length
            use_numbers (bool): Use numbers in username
            use_dots (bool): Use dots in username

        Returns:
            str: Generated Gmail address
        """
        chars = string.ascii_lowercase
        if use_numbers:
            chars += string.digits

        username = ''.join(random.choice(chars) for _ in range(username_length))

        # Add dots randomly if enabled
        if use_dots and len(username) > 3 and random.random() > 0.7:
            dot_position = random.randint(1, len(username) - 2)
            username = username[:dot_position] + '.' + username[dot_position:]

        return f"{username}@gmail.com"

    def is_valid_format(self, email):
        """Check email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
        return re.match(pattern, email) is not None

    def is_already_checked(self, email):
        """Check if email was already verified"""
        return email in self.checked_emails

    def verify_email(self, email):
        """
        Verify Gmail address validity

        Args:
            email (str): Email address to verify

        Returns:
            tuple: (bool, str) Result and status message
        """
        try:
            # Check format first
            if not self.is_valid_format(email):
                return False, "Invalid email format"

            # Check if already verified
            if self.is_already_checked(email):
                return None, "Already checked"

            ColorfulOutput.progress(f"Verifying: {email}")

            # Save checked email (regardless of verification result)
            self._save_checked_email(email)

            # Verify email using library
            is_valid = verify_email(emails=email)

            if is_valid:
                self._save_valid_email(email)
                return True, "Valid and available"
            else:
                return False, "Invalid or unavailable"

        except Exception as e:
            # Still save the email as checked even if verification fails
            if not self.is_already_checked(email):
                self._save_checked_email(email)
            return False, f"Verification error: {str(e)}"

    def generate_and_verify_batch(self, count=10, delay=2):
        """
        Generate and verify batch of emails

        Args:
            count (int): Number of emails to generate and verify
            delay (int): Delay between verifications in seconds
        """
        results = {
            'valid': 0,
            'invalid': 0,
            'skipped': 0,
            'errors': 0,
            'total': count
        }

        ColorfulOutput.header("GMAIL GENERATION & VERIFICATION")
        ColorfulOutput.info(f"Starting batch of {count} emails")
        ColorfulOutput.info(f"Delay: {delay}s | Timeout: {self.timeout}s")

        # Create progress bar
        with tqdm(total=count, desc=f"{Fore.CYAN}Processing emails", 
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

            for i in range(count):
                # Generate new email
                email = self.generate_gmail(
                    username_length=random.randint(6, 12),
                    use_numbers=random.choice([True, False]),
                    use_dots=random.choice([True, False])
                )

                # Verify email
                result, message = self.verify_email(email)

                # Update results
                if result is None:  # Skipped (already checked)
                    results['skipped'] += 1
                    ColorfulOutput.warning(f"Skipped: {email} ({message})")
                elif result:  # Valid
                    results['valid'] += 1
                    ColorfulOutput.success(f"Valid: {email}")
                    ColorfulOutput.email(email, "valid")
                else:  # Invalid or error
                    if "error" in message.lower():
                        results['errors'] += 1
                        ColorfulOutput.error(f"Error: {email} - {message}")
                    else:
                        results['invalid'] += 1
                        ColorfulOutput.error(f"Invalid: {email}")
                    ColorfulOutput.email(email, "invalid")

                # Update progress bar
                pbar.update(1)
                pbar.set_postfix({
                    'Valid': results['valid'],
                    'Invalid': results['invalid'],
                    'Skipped': results['skipped']
                })

                # Delay between operations
                if i < count - 1:
                    time.sleep(delay)

        return results

    def get_stats(self):
        """Get statistics"""
        total_checked = len(self.checked_emails)
        total_valid = len(self.valid_emails)
        success_rate = (total_valid / total_checked * 100) if total_checked > 0 else 0

        return {
            'total_checked': total_checked,
            'total_valid': total_valid,
            'success_rate': success_rate
        }

def print_banner():
    """Print colorful banner"""
    banner = f"""
{Fore.RED}╔══════════════════════════════════════════════════════════════╗
{Fore.RED}║{Fore.WHITE}          GMAIL GENERATOR & VERIFIER TOOL           {Fore.RED}║
{Fore.RED}║{Fore.WHITE}      Generate and Verify Random Gmail Addresses     {Fore.RED}║
{Fore.RED}╚══════════════════════════════════════════════════════════════╝
{Fore.GREEN}🌟 Features:{Fore.WHITE}
  • Random Gmail generation
  • Email validation checking
  • Progress tracking
  • Colorful output
  • Results saving
{Fore.YELLOW}⚡ Usage:{Fore.WHITE}
  python main.py -n 1000 -d 2 -t 15         {Fore.CYAN}(1000 emails)
  python main.py -c -n 1000 --batch-delay 30 {Fore.GREEN}(continuous batches)
  python main.py -c --unlimited -d 1         {Fore.RED}(unlimited mode)
{Fore.CYAN}──────────────────────────────────────────────────────────────{Style.RESET_ALL}
"""
    print(banner)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate and verify random Gmail addresses')
    parser.add_argument('-n', '--number', type=int, default=1000, 
                       help='Number of emails to generate and verify per batch (default: 1000)')
    parser.add_argument('-d', '--delay', type=int, default=2,
                       help='Delay between verifications in seconds')
    parser.add_argument('-t', '--timeout', type=int, default=15,
                       help='Verification timeout in seconds')
    parser.add_argument('--results', default='gmail_results.json',
                       help='Results file name')
    parser.add_argument('--checked', default='checked_gmails.txt',
                       help='Checked emails file name')
    parser.add_argument('-c', '--continuous', action='store_true',
                       help='Run continuously without stopping')
    parser.add_argument('--batch-delay', type=int, default=30,
                       help='Delay between batches in continuous mode (seconds)')
    parser.add_argument('--unlimited', action='store_true',
                       help='Run unlimited emails without batch limits (use with --continuous)')

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Create verifier instance
    verifier = GmailGeneratorVerifier(
        timeout=args.timeout,
        results_file=args.results,
        checked_file=args.checked
    )

    # Show current statistics
    stats = verifier.get_stats()
    ColorfulOutput.header("CURRENT STATISTICS")
    print(f"{Fore.WHITE}📊 Total Checked: {Fore.CYAN}{stats['total_checked']}")
    print(f"{Fore.WHITE}✅ Total Valid: {Fore.GREEN}{stats['total_valid']}")
    print(f"{Fore.WHITE}📈 Success Rate: {Fore.YELLOW}{stats['success_rate']:.2f}%")

    if args.continuous:
        if args.unlimited:
            ColorfulOutput.header("UNLIMITED CONTINUOUS MODE ACTIVATED")
            ColorfulOutput.warning("Running UNLIMITED emails until stopped manually!")
        else:
            ColorfulOutput.header("CONTINUOUS MODE ACTIVATED")
            ColorfulOutput.info(f"Running {args.number} emails per batch")
        
        ColorfulOutput.info(f"Delay between emails: {args.delay}s")
        if not args.unlimited:
            ColorfulOutput.info(f"Delay between batches: {args.batch_delay}s")
        ColorfulOutput.warning("Press Ctrl+C to stop the process")
        
        batch_number = 1
        total_valid_found = 0
        total_emails_processed = 0
        
        while True:
            try:
                if args.unlimited:
                    # Unlimited mode - run forever in one continuous batch
                    ColorfulOutput.header("UNLIMITED MODE - CONTINUOUS VERIFICATION")
                    ColorfulOutput.info("Processing emails continuously until stopped...")
                    
                    # Process emails one by one indefinitely
                    email_count = 0
                    while True:
                        try:
                            email_count += 1
                            
                            # Generate new email
                            email = verifier.generate_gmail(
                                username_length=random.randint(6, 12),
                                use_numbers=random.choice([True, False]),
                                use_dots=random.choice([True, False])
                            )
                            
                            # Verify email
                            result, message = verifier.verify_email(email)
                            
                            # Update counters
                            total_emails_processed += 1
                            
                            if result is None:  # Skipped (already checked)
                                ColorfulOutput.warning(f"#{email_count} Skipped: {email} ({message})")
                            elif result:  # Valid
                                total_valid_found += 1
                                ColorfulOutput.success(f"#{email_count} Valid: {email}")
                                ColorfulOutput.email(email, "valid")
                            else:  # Invalid or error
                                if "error" in message.lower():
                                    ColorfulOutput.error(f"#{email_count} Error: {email} - {message}")
                                else:
                                    ColorfulOutput.error(f"#{email_count} Invalid: {email}")
                                ColorfulOutput.email(email, "invalid")
                            
                            # Show progress every 50 emails
                            if email_count % 50 == 0:
                                stats = verifier.get_stats()
                                ColorfulOutput.header(f"PROGRESS UPDATE - {email_count} EMAILS PROCESSED")
                                print(f"{Fore.WHITE}📊 Total Checked: {Fore.CYAN}{stats['total_checked']}")
                                print(f"{Fore.WHITE}✅ Total Valid: {Fore.GREEN}{stats['total_valid']}")
                                print(f"{Fore.WHITE}📈 Success Rate: {Fore.YELLOW}{stats['success_rate']:.2f}%")
                                print(f"{Fore.MAGENTA}🎯 Session Valid: {Fore.GREEN}{total_valid_found}")
                                print(f"{Fore.MAGENTA}📈 Session Processed: {Fore.WHITE}{total_emails_processed}")
                                
                                # Show recent valid emails
                                if verifier.valid_emails:
                                    recent_emails = verifier.valid_emails[-3:]
                                    print(f"{Fore.GREEN}Recent Valid:")
                                    for email_data in recent_emails:
                                        print(f"  • {email_data['email']}")
                            
                            # Small delay between emails
                            time.sleep(args.delay)
                            
                        except KeyboardInterrupt:
                            ColorfulOutput.warning(f"\nStopping unlimited mode after {email_count} emails...")
                            raise
                        except Exception as e:
                            ColorfulOutput.error(f"Error processing email #{email_count}: {e}")
                            continue
                else:
                    # Regular batch mode
                    ColorfulOutput.header(f"BATCH #{batch_number} - STARTING VERIFICATION PROCESS")
                    results = verifier.generate_and_verify_batch(args.number, args.delay)
                    
                    total_valid_found += results['valid']
                    total_emails_processed += results['total']

                    # Show batch results
                    ColorfulOutput.header(f"BATCH #{batch_number} RESULTS")
                    print(f"{Fore.GREEN}✅ Valid: {results['valid']}")
                    print(f"{Fore.RED}❌ Invalid: {results['invalid']}")
                    print(f"{Fore.YELLOW}⏭️  Skipped: {results['skipped']}")
                    print(f"{Fore.RED}🚫 Errors: {results['errors']}")
                    print(f"{Fore.WHITE}📊 Total: {results['total']}")

                    # Show updated statistics
                    stats = verifier.get_stats()
                    ColorfulOutput.header("OVERALL STATISTICS")
                    print(f"{Fore.WHITE}📊 Total Checked: {Fore.CYAN}{stats['total_checked']}")
                    print(f"{Fore.WHITE}✅ Total Valid: {Fore.GREEN}{stats['total_valid']}")
                    print(f"{Fore.WHITE}📈 Success Rate: {Fore.YELLOW}{stats['success_rate']:.2f}%")
                    print(f"{Fore.MAGENTA}🔢 Batches Completed: {Fore.WHITE}{batch_number}")
                    print(f"{Fore.MAGENTA}🎯 Session Valid Emails: {Fore.GREEN}{total_valid_found}")
                    print(f"{Fore.MAGENTA}📈 Session Processed: {Fore.WHITE}{total_emails_processed}")

                    # Show some recent valid emails
                    if verifier.valid_emails:
                        ColorfulOutput.header("RECENT VALID EMAILS")
                        recent_emails = verifier.valid_emails[-5:]
                        for i, email_data in enumerate(recent_emails, 1):
                            print(f"{Fore.GREEN}{i}. {email_data['email']} {Fore.WHITE}({email_data['checked_at']})")

                    batch_number += 1
                    
                    # Wait before next batch
                    ColorfulOutput.info(f"Waiting {args.batch_delay} seconds before next batch...")
                    time.sleep(args.batch_delay)
                
            except KeyboardInterrupt:
                ColorfulOutput.warning("\nStopping continuous mode...")
                break
            except Exception as e:
                ColorfulOutput.error(f"Error in batch #{batch_number}: {e}")
                ColorfulOutput.warning("Continuing to next batch in 10 seconds...")
                time.sleep(10)
                if not args.unlimited:
                    batch_number += 1
                continue
        
        ColorfulOutput.success(f"Continuous mode stopped!")
        ColorfulOutput.info(f"Total valid emails found in session: {total_valid_found}")
        ColorfulOutput.info(f"Total emails processed in session: {total_emails_processed}")
        
    else:
        # Single batch mode (original behavior)
        ColorfulOutput.header("STARTING VERIFICATION PROCESS")
        results = verifier.generate_and_verify_batch(args.number, args.delay)

        # Show final results
        ColorfulOutput.header("FINAL RESULTS")
        print(f"{Fore.GREEN}✅ Valid: {results['valid']}")
        print(f"{Fore.RED}❌ Invalid: {results['invalid']}")
        print(f"{Fore.YELLOW}⏭️  Skipped: {results['skipped']}")
        print(f"{Fore.RED}🚫 Errors: {results['errors']}")
        print(f"{Fore.WHITE}📊 Total: {results['total']}")

        # Show updated statistics
        stats = verifier.get_stats()
        ColorfulOutput.header("UPDATED STATISTICS")
        print(f"{Fore.WHITE}📊 Total Checked: {Fore.CYAN}{stats['total_checked']}")
        print(f"{Fore.WHITE}✅ Total Valid: {Fore.GREEN}{stats['total_valid']}")
        print(f"{Fore.WHITE}📈 Success Rate: {Fore.YELLOW}{stats['success_rate']:.2f}%")

        # Show some valid emails
        if verifier.valid_emails:
            ColorfulOutput.header("RECENT VALID EMAILS")
            recent_emails = verifier.valid_emails[-5:]
            for i, email_data in enumerate(recent_emails, 1):
                print(f"{Fore.GREEN}{i}. {email_data['email']} {Fore.WHITE}({email_data['checked_at']})")

        ColorfulOutput.success("Process completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        ColorfulOutput.error("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        ColorfulOutput.error(f"Unexpected error: {e}")
        sys.exit(1)