#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gmail Generator & Verifier Tool for Streamlit
Generate and verify random Gmail addresses with real-time console output
"""

import streamlit as st
import argparse
import random
import string
import json
import time
import os
import sys
import threading
import queue
from io import StringIO
from verify_email import verify_email
from tqdm import tqdm
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# إنشاء طابور لالتقاط output من الكونسول
console_output = queue.Queue()

# نظام لإعادة توجيه output للطابور
class StreamToQueue:
    def __init__(self, queue):
        self.queue = queue
        
    def write(self, text):
        self.queue.put(text)
        
    def flush(self):
        pass

# استبدال sys.stdout لالتقاط output
sys.stdout = StreamToQueue(console_output)
sys.stderr = StreamToQueue(console_output)

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
    def __init__(self, timeout=15):
        """
        Initialize Gmail generator and verifier

        Args:
            timeout (int): Verification timeout in seconds
        """
        self.timeout = timeout
        
        # استخدام session state لتخزين البيانات
        if 'checked_emails' not in st.session_state:
            st.session_state.checked_emails = set()
        if 'valid_emails' not in st.session_state:
            st.session_state.valid_emails = []
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'stop_process' not in st.session_state:
            st.session_state.stop_process = False

        self.checked_emails = st.session_state.checked_emails
        self.valid_emails = st.session_state.valid_emails

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
            self.checked_emails.add(email)
            st.session_state.checked_emails = self.checked_emails

            # Verify email using library
            is_valid = verify_email(emails=email)

            if is_valid:
                email_data = {
                    'email': email,
                    'checked_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'gmail'
                }
                self.valid_emails.append(email_data)
                st.session_state.valid_emails = self.valid_emails
                return True, "Valid and available"
            else:
                return False, "Invalid or unavailable"

        except Exception as e:
            # Still save the email as checked even if verification fails
            if not self.is_already_checked(email):
                self.checked_emails.add(email)
                st.session_state.checked_emails = self.checked_emails
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

        for i in range(count):
            if st.session_state.stop_process:
                ColorfulOutput.warning("Process stopped by user")
                break
                
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

            # Delay between operations
            if i < count - 1 and not st.session_state.stop_process:
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
  • Real-time console display
{Fore.YELLOW}⚡ Running on Streamlit:{Fore.WHITE}
  • Console output displayed below
  • Results stored in session memory
  • Stop/start functionality
{Fore.CYAN}──────────────────────────────────────────────────────────────{Style.RESET_ALL}
"""
    print(banner)

def process_emails(count, delay, timeout):
    """Function to process emails in a separate thread"""
    verifier = GmailGeneratorVerifier(timeout=timeout)
    print_banner()
    
    # Show current statistics
    stats = verifier.get_stats()
    ColorfulOutput.header("CURRENT STATISTICS")
    print(f"{Fore.WHITE}📊 Total Checked: {Fore.CYAN}{stats['total_checked']}")
    print(f"{Fore.WHITE}✅ Total Valid: {Fore.GREEN}{stats['total_valid']}")
    print(f"{Fore.WHITE}📈 Success Rate: {Fore.YELLOW}{stats['success_rate']:.2f}%")

    ColorfulOutput.header("STARTING VERIFICATION PROCESS")
    results = verifier.generate_and_verify_batch(count, delay)

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
    st.session_state.processing = False

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="Gmail Generator & Verifier",
        page_icon="📧",
        layout="wide"
    )
    
    st.title("📧 Gmail Generator & Verifier")
    st.markdown("Generate and verify random Gmail addresses with real-time console output")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        count = st.slider("Number of emails", 10, 1000, 100)
        delay = st.slider("Delay between emails (seconds)", 1, 10, 2)
        timeout = st.slider("Verification timeout (seconds)", 5, 30, 15)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Processing", type="primary") and not st.session_state.get('processing', False):
                st.session_state.processing = True
                st.session_state.stop_process = False
                # Start processing in a separate thread
                thread = threading.Thread(
                    target=process_emails, 
                    args=(count, delay, timeout)
                )
                thread.start()
                
        with col2:
            if st.button("Stop Processing", type="secondary"):
                st.session_state.stop_process = True
                
        # Display statistics
        st.header("Statistics")
        if 'valid_emails' in st.session_state:
            total_checked = len(st.session_state.checked_emails)
            total_valid = len(st.session_state.valid_emails)
            success_rate = (total_valid / total_checked * 100) if total_checked > 0 else 0
            
            st.metric("Total Emails Checked", total_checked)
            st.metric("Valid Emails Found", total_valid)
            st.metric("Success Rate", f"{success_rate:.2f}%")
            
            if total_valid > 0:
                st.subheader("Recent Valid Emails")
                for email_data in st.session_state.valid_emails[-5:]:
                    st.code(f"{email_data['email']} - {email_data['checked_at']}")
    
    # Console output display
    st.header("Console Output")
    console_placeholder = st.empty()
    
    # Update console output in real-time
    if st.session_state.get('processing', False):
        status_text = st.empty()
        status_text.info("🔄 Processing emails...")
        
        console_content = ""
        while st.session_state.get('processing', False):
            try:
                # Get new console output
                while not console_output.empty():
                    console_content += console_output.get_nowait()
                
                # Update console display
                with console_placeholder:
                    st.text_area("Console", console_content, height=400, key="console_output")
                
                time.sleep(0.5)
                
            except:
                break
                
        status_text.empty()
    else:
        # Display static console content when not processing
        console_content = "Console output will appear here when processing starts..."
        with console_placeholder:
            st.text_area("Console", console_content, height=400, key="console_output")
    
    # Display valid emails in main area
    if st.session_state.get('valid_emails', []):
        st.header("Valid Emails Found")
        valid_emails = [email_data['email'] for email_data in st.session_state.valid_emails]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(valid_emails, use_container_width=True)
        
        with col2:
            st.download_button(
                label="Download Valid Emails",
                data="\n".join(valid_emails),
                file_name="valid_emails.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
