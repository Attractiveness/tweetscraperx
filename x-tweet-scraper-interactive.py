#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import os
from datetime import datetime
import argparse
import warnings
import sys

# Suppress warnings
warnings.filterwarnings("ignore", category=Warning)

class XTweetScraper:
    def __init__(self, headless=True):
        """Initialize the XTweetScraper with configuration options."""
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Set up and return a configured Chrome webdriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        # Add user agent to appear more like a regular browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        try:
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except WebDriverException as e:
            print(f"Error initializing Chrome driver: {e}")
            print("Please make sure ChromeDriver is installed and in your PATH")
            return None

    def scrape_tweets(self, username, max_tweets=None, output_file=None):
        """Scrape tweets from the specified X.com user account."""
        # Remove @ if provided
        username = username.strip('@')
        
        self.driver = self.setup_driver()
        if not self.driver:
            return []
        
        # Construct the URL for the user's profile
        url = f"https://x.com/{username}"
        print(f"Opening {url}...")
        
        tweets = []
        
        try:
            self.driver.get(url)
            
            # Wait for the page to load with a longer timeout
            wait = WebDriverWait(self.driver, 20)
            
            # First check if we can find any page content at all
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("Page loaded. Looking for tweets...")
            except TimeoutException:
                print("Timed out waiting for page to load.")
                return []
            
            # Check if account exists
            try:
                # Check for common "doesn't exist" indicators
                if "This account doesn't exist" in self.driver.page_source or "Hmm...this page doesn't exist" in self.driver.page_source:
                    print(f"Account @{username} doesn't seem to exist.")
                    return []
            except:
                pass
            
            # Wait for tweets to appear - try multiple possible selectors
            tweet_found = False
            selectors = [
                '[data-testid="tweet"]', 
                'article', 
                '[data-testid="tweetText"]',
                '.css-1dbjc4n'  # More generic X.com class
            ]
            
            for selector in selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"Found tweets using selector: {selector}")
                    tweet_selector = selector
                    tweet_found = True
                    break
                except TimeoutException:
                    print(f"Selector {selector} not found, trying next...")
                    continue
            
            if not tweet_found:
                print("Could not find any tweets on the page. The page structure may have changed.")
                
                # Save the page source for debugging
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                debug_file = os.path.join(desktop_path, f"debug_{username}_page.html")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"Saved page source to {debug_file} for debugging")
                
                return []
        
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            print("Scrolling and collecting tweets...")
            scroll_attempts = 0
            max_scroll_attempts = 15  # Limit scrolling attempts
            
            while (max_tweets is None or len(tweets) < max_tweets) and scroll_attempts < max_scroll_attempts:
                # Get all currently loaded tweet elements
                tweet_elements = []
                
                # Try different selectors for tweet elements
                for selector in selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        tweet_elements = elements
                        break
                
                # Process new tweets
                for element in tweet_elements[len(tweets):]:
                    try:
                        # Find the tweet text using multiple possible selectors
                        tweet_text = ""
                        for text_selector in ['[data-testid="tweetText"]', '.css-901oao', 'div.css-1dbjc4n span']:
                            try:
                                tweet_text_elements = element.find_elements(By.CSS_SELECTOR, text_selector)
                                if tweet_text_elements:
                                    tweet_text = " ".join([el.text for el in tweet_text_elements if el.text])
                                    if tweet_text:
                                        break
                            except:
                                continue
                        
                        if not tweet_text:
                            continue  # Skip if no text found
                        
                        # Try to get timestamp
                        timestamp = "Unknown"
                        try:
                            time_element = element.find_element(By.CSS_SELECTOR, 'time')
                            timestamp = time_element.get_attribute('datetime')
                        except NoSuchElementException:
                            # Try alternative timestamp methods
                            pass
                        
                        # Add the tweet to our collection if it's not already there
                        tweet_data = {
                            'text': tweet_text,
                            'timestamp': timestamp
                        }
                        
                        if tweet_data not in tweets:  # Avoid duplicates
                            tweets.append(tweet_data)
                            print(f"Collected tweet {len(tweets)}: {tweet_text[:50]}...")
                        
                        # Check if we've reached the desired number of tweets
                        if max_tweets is not None and len(tweets) >= max_tweets:
                            break
                            
                    except Exception as e:
                        print(f"Error processing tweet: {e}")
                        continue
                
                # Scroll down to load more tweets
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(3)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    print(f"No new content loaded. Attempt {scroll_attempts}/{max_scroll_attempts}")
                else:
                    scroll_attempts = 0  # Reset attempts if we successfully scrolled
                    
                last_height = new_height
            
            print(f"Total tweets collected: {len(tweets)}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.driver.quit()
        
        # Save the tweets
        if tweets:
            self.save_tweets_to_text(tweets, output_file, username)
        
        return tweets

    def save_tweets_to_text(self, tweets, output_file, username):
        """Save the collected tweets to a text file on Desktop."""
        # Get the path to the Desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Generate default filename if none specified
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"tweets_{username}_{timestamp}.txt"
        
        # Ensure the filename ends with .txt
        if not output_file.endswith('.txt'):
            output_file += '.txt'
        
        # Create the full path to the output file on Desktop
        full_path = os.path.join(desktop_path, output_file)
        
        print(f"Saving tweets to {full_path}...")
        try:
            with open(full_path, 'w', encoding='utf-8') as file:
                file.write(f"Tweets from @{username}\n")
                file.write(f"Retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("-" * 80 + "\n\n")
                
                for i, tweet in enumerate(tweets, 1):
                    file.write(f"Tweet #{i}:\n")
                    file.write(f"Time: {tweet['timestamp']}\n")
                    file.write(f"Text: {tweet['text']}\n")
                    file.write("\n" + "-" * 80 + "\n\n")
            
            print(f"Successfully saved {len(tweets)} tweets to {full_path}")
        except Exception as e:
            print(f"Error saving tweets: {e}")


def interactive_mode():
    """Run the scraper in interactive mode with prompts."""
    try:
        # Interactive mode - ask for username
        username = input("Enter the X.com username to scrape (with or without @ symbol): ")
        
        # Ask if they want to limit the number of tweets
        limit_response = input("Do you want to limit the number of tweets to scrape? (y/n): ").lower()
        max_tweets = None
        if limit_response.startswith('y'):
            while True:
                try:
                    max_tweets = int(input("Enter maximum number of tweets to scrape: "))
                    if max_tweets <= 0:
                        print("Please enter a positive number.")
                        continue
                    break
                except ValueError:
                    print("Please enter a valid number.")
        
        # Ask for output file
        custom_output = input("Do you want to specify an output file name? (y/n): ").lower()
        output_file = None
        if custom_output.startswith('y'):
            output_file = input("Enter output file name (will be saved as TXT on your Desktop): ")
        
        # Ask about headless mode
        headless_response = input("Run in headless mode (no visible browser)? (y/n): ").lower()
        headless = headless_response.startswith('y')
        
        # Create scraper and run
        scraper = XTweetScraper(headless=headless)
        scraper.scrape_tweets(username, max_tweets, output_file)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

def command_line_mode():
    """Run the scraper with command line arguments."""
    parser = argparse.ArgumentParser(description='Scrape tweets from an X.com user account.')
    parser.add_argument('username', help='X.com username to scrape (without the @ symbol)')
    parser.add_argument('-m', '--max-tweets', type=int, help='Maximum number of tweets to scrape')
    parser.add_argument('-o', '--output', help='Output text file name')
    parser.add_argument('--visible', action='store_true', help='Show browser window during scraping')
    
    args = parser.parse_args()
    
    # Create scraper and run
    scraper = XTweetScraper(headless=not args.visible)
    scraper.scrape_tweets(args.username, args.max_tweets, args.output)

def main():
    """Main entry point for the script."""
    print("X.com Tweet Scraper")
    print("-" * 40)
    
    # Check if arguments were provided
    if len(sys.argv) > 1:
        command_line_mode()
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
