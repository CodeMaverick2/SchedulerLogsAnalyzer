from playwright.sync_api import Playwright, sync_playwright, expect
import logging
from typing import Optional
import re

class AWSLoginManager:
    def __init__(self, config: dict):
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
        
    def setup_browser(self):
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(60000)  # 60 seconds timeout
        
    def login(self) -> bool:
        try:
            self.setup_browser()
            
            # First, try direct login URL
            login_url = "https://eu-west-2.quicksight.aws.amazon.com/sn/auth/signin"
            logging.info("Navigating to login URL...")
            self.page.goto(login_url)
            self.page.wait_for_load_state('networkidle')
            
            # Debug: Log page content
            logging.info("Page Title: " + self.page.title())
            logging.info("Current URL: " + self.page.url)
            
            # Account name field
            logging.info("Looking for account name field...")
            account_input = self.page.locator('input[type="text"]').first
            if not account_input.is_visible():
                raise Exception("Account input field not visible")
            
            # Move mouse to input and click before filling
            account_input.hover()
            account_input.click()
            logging.info("Filling account name...")
            account_input.fill(self.config['aws']['environment'])
            self.page.wait_for_timeout(2000)
            account_input.press("Enter")
            logging.info(f"Account name entered: {self.config['aws']['environment']}")
            
            # Wait for the next page to load
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_timeout(3000)
            
            # Username field - wait for it to appear after account name
            logging.info("Looking for username field...")
            try:
                # Wait for the sign-in button to appear first
                self.page.wait_for_selector('button[type="submit"]', state='visible', timeout=10000)
                
                # Now look for username field
                username_input = self.page.locator('input[type="text"]').first
                if not username_input.is_visible():
                    username_input = self.page.locator('input[name="username"]')
                
                logging.info("Filling username...")
                username_input.click()
                username_input.fill(self.config['aws']['username'])
                self.page.wait_for_timeout(2000)
                
                # Click the sign-in button
                sign_in_button = self.page.locator('button[type="submit"]')
                sign_in_button.click()
                logging.info("Clicked sign-in button after username")
                
                # Important: Wait for URL change and page load after username submission
                logging.info("Waiting for password page...")
                self.page.wait_for_load_state('networkidle')
                self.page.wait_for_timeout(5000) 
                
                # Password field with explicit wait
                logging.info("Looking for password field...")
                password_input = self.page.wait_for_selector('input[type="password"]', 
                                                           state='visible', 
                                                           timeout=60000)  
                
                logging.info("Filling password...")
                password_input.click()
                password_input.fill(self.config['aws']['password'])
                self.page.wait_for_timeout(2000)
                
                # Click sign-in button for password
                sign_in_button = self.page.locator('button[type="submit"]')
                sign_in_button.click()
                logging.info("Clicked sign-in button after password")
                
            except Exception as e:
                logging.error(f"Failed during login process: {str(e)}")
                self.page.screenshot(path="login_error.png")
                raise
            
            # Wait for successful login
            logging.info("Waiting for login completion...")
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_timeout(5000)
            
            # Navigate to dashboard
            logging.info("Navigating to dashboard...")
            self.page.goto(self.config['aws']['dashboard_url'])
            logging.info("Initial dashboard navigation complete")
            
            try:
                # Wait for basic page load first
                self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                logging.info("DOM content loaded")
                
                # Wait for any visible element that indicates dashboard
                visible_selectors = [
                    'div[class*="quicksight"]',
                    'div[class*="dashboard"]',
                    'div[class*="awsui"]',
                    'div[class*="analysis"]'
                ]
                
                dashboard_loaded = False
                for selector in visible_selectors:
                    try:
                        element = self.page.locator(selector).first
                        if element.is_visible(timeout=5000):
                            logging.info(f"Found visible element: {selector}")
                            dashboard_loaded = True
                            break
                    except Exception as e:
                        logging.warning(f"Selector {selector} not found: {e}")
                        continue
                
                if not dashboard_loaded:
                    logging.warning("No dashboard elements found, but continuing...")
                
                # Save current URL for debugging
                current_url = self.page.url
                logging.info(f"Current dashboard URL: {current_url}")
                
                # Wait a moment for any animations
                self.page.wait_for_timeout(5000)
                logging.info("Completed initial wait")
                
                # Move mouse to center and click
                screen_width = self.page.viewport_size['width']
                screen_height = self.page.viewport_size['height']
                center_x = screen_width / 2
                center_y = screen_height / 2
                
                logging.info(f"Moving mouse to center ({center_x}, {center_y})")
                self.page.mouse.move(center_x, center_y)
                self.page.wait_for_timeout(2000)
                
                self.page.mouse.click(center_x, center_y)
                logging.info("Clicked center of screen")
                
                # Wait after click
                self.page.wait_for_timeout(5000)

                # Check if URL changed after click
                new_url = self.page.url
                if new_url != current_url:
                    logging.info(f"URL changed after click to: {new_url}")
                
                logging.info("Dashboard navigation sequence completed")
                return True
                
            except Exception as e:
                logging.error(f"Failed during dashboard navigation: {str(e)}")
                # Take error screenshot
                self.page.screenshot(path="dashboard_error.png")
                # Save page content for debugging
                with open("page_content.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                raise
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            self.cleanup()
            return False
            
    def download_csv(self, report_name: str) -> Optional[str]:
        try:
            logging.info("Starting CSV download process...")
            
            # Wait for table and find it
            table_selectors = [
                'div[class*="TableVisualization"]',
                'div[class*="tableVisualization"]',
                'div[class*="visContainer"]',
                'div[class*="grid"]'
            ]
            
            # Try each selector
            for selector in table_selectors:
                try:
                    if self.page.locator(selector).first.is_visible(timeout=5000):
                        logging.info(f"Found table using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Click menu button
            menu_button = self.page.locator('button[aria-label*="Menu"]').first
            menu_button.click()
            logging.info("Clicked menu button")
            
            # Wait for menu to appear and try multiple download button selectors
            self.page.wait_for_timeout(2000)  # Wait for menu animation
            
            download_selectors = [
                'button:has-text("Export to CSV")',
                'button:has-text("Download CSV")',
                'button:has-text("Export")',
                'button:has-text("CSV")',
                '[aria-label*="Export to CSV"]',
                '[aria-label*="Download CSV"]',
                'text=Export to CSV',
                'text=Download CSV'
            ]
            
            for selector in download_selectors:
                try:
                    download_button = self.page.locator(selector).first
                    if download_button.is_visible(timeout=2000):
                        logging.info(f"Found download button using selector: {selector}")
                        with self.page.expect_download(timeout=30000) as download_info:
                            download_button.click()
                            logging.info("Clicked download button")
                            download = download_info.value
                            download_path = download.path()
                            logging.info(f"File downloaded to: {download_path}")
                            return download_path
                except Exception as e:
                    logging.debug(f"Failed with selector {selector}: {str(e)}")
                    continue
            
            logging.error("Could not find download button")
            self.page.screenshot(path="download_button_error.png")
            return None
            
        except Exception as e:
            logging.error(f"CSV download failed: {str(e)}")
            self.page.screenshot(path="download_process_error.png")
            return None
            
    def cleanup(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close() 