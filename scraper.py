# scraper.py
# Web scraper for STEMGRADS - Downloads UNESCO STEM graduates data
# Updated for new MUI-based UNESCO interface

import os
import time
import logging
import glob
import winreg
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import config

logger = logging.getLogger(__name__)


class STEMGRADSScraper:
    """Downloads STEM Graduates data from UNESCO data portal"""

    def __init__(self):
        self.driver = None
        self.logger = logger

    def get_chrome_version_from_registry(self):
        """Get installed Chrome version from Windows Registry"""

        self.logger.info("Checking Windows Registry for Chrome version...")

        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
        ]

        for hkey, path in registry_paths:
            try:
                key = winreg.OpenKey(hkey, path)
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)

                major_version = int(version.split('.')[0])
                self.logger.info(f"Found Chrome version: {version} (major: {major_version})")
                return major_version
            except (FileNotFoundError, WindowsError, OSError):
                continue

        self.logger.warning("Chrome version not found in registry")
        return None

    def setup_driver(self):
        """Initialize Chrome driver with download preferences"""

        # Ensure download directory exists
        os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)

        # Get Chrome version from registry
        chrome_version = self.get_chrome_version_from_registry()

        # Get absolute path for downloads
        download_path = os.path.abspath(config.DOWNLOADS_DIR)

        options = uc.ChromeOptions()

        # Download preferences
        prefs = {
            'download.default_directory': download_path,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'profile.default_content_settings.popups': 0,
        }
        options.add_experimental_option('prefs', prefs)

        # GPU/stability flags for headless mode
        if config.HEADLESS_MODE:
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            self.logger.info("Running in headless mode")

        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Use UC's native headless parameter (NOT --headless=new arg)
        # UC applies extra anti-detection patches when headless=True
        if chrome_version:
            self.logger.info(f"Using Chrome version {chrome_version} for driver")
            self.driver = uc.Chrome(
                options=options,
                version_main=chrome_version,
                headless=config.HEADLESS_MODE
            )
        else:
            self.logger.info("Using automatic version detection")
            self.driver = uc.Chrome(
                options=options,
                headless=config.HEADLESS_MODE
            )

        self.driver.set_page_load_timeout(config.WAIT_TIMEOUT)

        # In headless mode, maximize_window() returns 800x600 — use set_window_size instead
        if config.HEADLESS_MODE:
            self.driver.set_window_size(1920, 1080)
        else:
            self.driver.maximize_window()

        self.logger.info("Chrome driver initialized")
        self.logger.info(f"Download directory: {download_path}")

    def wait_and_click(self, locator, timeout=None, description="element"):
        """Wait for element and click it"""
        timeout = timeout or config.ELEMENT_WAIT_TIMEOUT
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            time.sleep(0.5)
            element.click()
            self.logger.info(f"Clicked: {description}")
            return True
        except TimeoutException:
            self.logger.error(f"Timeout waiting for: {description}")
            return False
        except ElementClickInterceptedException:
            self.logger.warning(f"Click intercepted for: {description}, trying JS click")
            try:
                element = self.driver.find_element(*locator)
                self.driver.execute_script("arguments[0].click();", element)
                self.logger.info(f"JS clicked: {description}")
                return True
            except Exception as e:
                self.logger.error(f"JS click failed for {description}: {e}")
                return False

    def wait_for_element(self, locator, timeout=None, description="element"):
        """Wait for element to be present"""
        timeout = timeout or config.ELEMENT_WAIT_TIMEOUT
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.debug(f"Found: {description}")
            return element
        except TimeoutException:
            self.logger.error(f"Timeout waiting for: {description}")
            return None

    def navigate_to_page(self, url):
        """Navigate to a URL"""

        self.logger.info(f"Navigating to {url}")

        try:
            self.driver.get(url)
            time.sleep(config.PAGE_LOAD_DELAY)
            self.logger.info("Page loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading page: {e}")
            return False

    def navigate_to_stem_indicator(self):
        """
        Navigate to the STEM graduates indicator and add it to selection.

        Flow:
        1. Click "Browse data" link -> /browser page
        2. Search "Percentage of graduates by field of education (tertiary education)"
        3. Click "Graduates" folder from search results
        4. Click "Distribution of graduates by field of study" accordion
        5. Find STEM indicator and click "Add" button
        6. Click "View data" link
        """

        self.logger.info("=" * 60)
        self.logger.info("NAVIGATING TO STEM INDICATOR")
        self.logger.info("=" * 60)

        try:
            # Wait for homepage to fully load
            time.sleep(3)

            # ============================================================
            # STEP 1: Click "Browse data" link
            # ============================================================
            self.logger.info("STEP 1: Clicking 'Browse data' link...")

            browse_selectors = [
                (By.XPATH, "//a[contains(text(), 'Browse data')]"),
                (By.CSS_SELECTOR, "a[href='/browser']"),
                (By.XPATH, "//a[@href='/browser']"),
            ]

            browse_clicked = False
            for selector in browse_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    if elements:
                        try:
                            elements[0].click()
                        except Exception:
                            # Headless: element found but not interactable — use JS click
                            self.driver.execute_script("arguments[0].click();", elements[0])
                        self.logger.info("Clicked 'Browse data' link")
                        browse_clicked = True
                        time.sleep(4)
                        break
                except Exception as e:
                    self.logger.debug(f"Browse selector failed: {e}")

            if not browse_clicked:
                self.logger.warning("Could not find 'Browse data' link, navigating directly...")
                self.driver.get("https://databrowser.uis.unesco.org/browser")
                time.sleep(8)  # React SPA needs time to hydrate in headless

            # ============================================================
            # STEP 2: Click "Education" then "Other Policy Relevant Indicators"
            # ============================================================
            self.logger.info("STEP 2: Clicking 'Education' category...")

            education_selectors = [
                (By.XPATH, "//div[contains(text(), 'Education')]"),
                (By.XPATH, "//h5[contains(text(), 'Education')]"),
                (By.XPATH, "//*[contains(@class, 'MuiTypography') and text()='Education']"),
            ]

            for selector in education_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    for elem in elements:
                        try:
                            text = elem.text.strip() if elem.text else ''
                        except Exception:
                            text = self.driver.execute_script("return arguments[0].textContent;", elem) or ''
                        if 'Education' in text:
                            try:
                                elem.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", elem)
                            self.logger.info("Clicked 'Education' category")
                            time.sleep(2)
                            break
                except Exception as e:
                    self.logger.debug(f"Education selector failed: {e}")

            # Click "Other Policy Relevant Indicators - Education"
            self.logger.info("Clicking 'Other Policy Relevant Indicators - Education'...")
            opri_selectors = [
                (By.XPATH, "//a[contains(text(), 'Other Policy Relevant Indicators')]"),
                (By.XPATH, "//*[contains(text(), 'Other Policy Relevant Indicators - Education')]"),
                (By.XPATH, "//div[contains(text(), 'Other Policy Relevant')]"),
            ]

            for selector in opri_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    if elements:
                        try:
                            elements[0].click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", elements[0])
                        self.logger.info("Clicked 'Other Policy Relevant Indicators - Education'")
                        time.sleep(3)
                        break
                except Exception as e:
                    self.logger.debug(f"OPRI selector failed: {e}")

            # ============================================================
            # STEP 3: Click "Graduates" from the LEFT SIDEBAR
            # ============================================================
            self.logger.info("STEP 3: Clicking 'Graduates' from left sidebar...")

            # Look for Graduates in the left sidebar menu
            graduates_selectors = [
                (By.XPATH, "//a[contains(text(), 'Graduates')]"),
                (By.XPATH, "//div[contains(@class, 'sidebar')]//a[contains(text(), 'Graduates')]"),
                (By.CSS_SELECTOR, "a[href*='graduates']"),
                (By.XPATH, "//*[contains(@class, 'MuiTypography') and contains(text(), 'Graduates')]"),
            ]

            graduates_clicked = False
            for selector in graduates_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    for elem in elements:
                        try:
                            text = elem.text if elem.text else ''
                        except Exception:
                            text = self.driver.execute_script("return arguments[0].textContent;", elem) or ''
                        if 'Graduates' in text:
                            try:
                                elem.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", elem)
                            self.logger.info("Clicked 'Graduates' from sidebar")
                            graduates_clicked = True
                            time.sleep(3)
                            break
                    if graduates_clicked:
                        break
                except Exception as e:
                    self.logger.debug(f"Graduates sidebar selector failed: {e}")

            # ============================================================
            # STEP 4: Click "Distribution of graduates by field of study" accordion
            # ============================================================
            self.logger.info("STEP 4: Expanding 'Distribution of graduates by field of study' accordion...")

            accordion_selectors = [
                (By.XPATH, "//h5[contains(text(), 'Distribution of graduates by field of study')]"),
                (By.XPATH, "//button[contains(@class, 'MuiAccordionSummary')]//h5[contains(text(), 'Distribution')]"),
                (By.XPATH, "//*[contains(text(), 'Distribution of graduates by field of study')]"),
            ]

            accordion_clicked = False
            for selector in accordion_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    if elements:
                        # Click on the accordion header/button
                        parent = elements[0]
                        # Try to find the clickable button parent
                        try:
                            button = parent.find_element(By.XPATH, "./ancestor::button")
                            button.click()
                        except:
                            parent.click()
                        self.logger.info("Clicked 'Distribution of graduates by field of study' accordion")
                        accordion_clicked = True
                        time.sleep(2)
                        break
                except Exception as e:
                    self.logger.debug(f"Accordion selector failed: {e}")

            if not accordion_clicked:
                self.logger.warning("Could not find Distribution accordion, it may already be expanded")

            # ============================================================
            # STEP 5: Navigate to page 2, then click "Add" for STEM indicator
            # The STEM indicator is on PAGE 2 of the paginated accordion list
            # ============================================================
            self.logger.info("STEP 5: Navigating to page 2 of indicator list to find STEM indicator...")

            # Wait for accordion content to render
            time.sleep(2)

            # --- Click the "next page" button to go to page 2 ---
            # The next-page button is inside: div[class*="IndicatorGroupAccordion-pagination"]
            # It contains an SVG with data-testid="ArrowForwardIcon"
            next_page_clicked = False

            # Strategy 1: JavaScript querySelector (most reliable — bypasses interception)
            self.logger.info("Attempting JS click on ArrowForwardIcon button...")
            try:
                result = self.driver.execute_script("""
                    var svgs = document.querySelectorAll('svg[data-testid="ArrowForwardIcon"]');
                    for (var i = 0; i < svgs.length; i++) {
                        var btn = svgs[i].closest('button');
                        if (btn) {
                            btn.scrollIntoView({block: 'center'});
                            btn.click();
                            return 'clicked';
                        }
                    }
                    return 'not_found';
                """)
                if result == 'clicked':
                    self.logger.info("Clicked next-page button via JS querySelector — waiting for page 2...")
                    next_page_clicked = True
                    time.sleep(3)
                else:
                    self.logger.warning("JS querySelector: ArrowForwardIcon button not found in DOM")
            except Exception as js_e:
                self.logger.warning(f"JS querySelector click failed: {js_e}")

            # Strategy 2: XPath with data-testid on SVG child (if JS failed)
            if not next_page_clicked:
                self.logger.info("Attempting XPath click on ArrowForwardIcon button...")
                xpath_strategies = [
                    "//div[contains(@class,'IndicatorGroupAccordion-pagination')]//button[.//svg[@data-testid='ArrowForwardIcon']]",
                    "//button[.//svg[@data-testid='ArrowForwardIcon']]",
                    "//svg[@data-testid='ArrowForwardIcon']/parent::button",
                    "//div[contains(@class,'IndicatorGroupAccordion-pagination')]//button[last()]",
                ]
                for xpath in xpath_strategies:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements:
                            btn = elements[0]
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)
                            # Human-like click via ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(btn).pause(0.3).click().perform()
                            self.logger.info(f"Clicked next-page button via ActionChains (xpath: {xpath[:60]})")
                            next_page_clicked = True
                            time.sleep(3)
                            break
                    except Exception as e:
                        self.logger.debug(f"XPath strategy failed ({xpath[:40]}): {e}")

            if not next_page_clicked:
                self.logger.warning("Could not navigate to page 2 — will search current page anyway")

            # --- Search for STEM indicator on current page (should now be page 2) ---
            stem_keywords = [
                "Science, Technology, Engineering and Mathematics",
                "STEM programmes",
            ]
            add_clicked = False

            for attempt in range(3):
                self.logger.info(f"Search attempt {attempt + 1} for STEM indicator...")

                for keyword in stem_keywords:
                    try:
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                        self.logger.info(f"Found {len(elements)} elements containing '{keyword[:50]}'")

                        for elem in elements:
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                time.sleep(0.5)

                                # Climb up to the row container that also holds the Add button
                                parent_row = elem.find_element(
                                    By.XPATH,
                                    "./ancestor::div[contains(@class, 'MuiBox-root') and .//button[contains(text(), 'Add')]]"
                                )
                                add_btn = parent_row.find_element(By.XPATH, ".//button[contains(text(), 'Add')]")

                                if add_btn.is_displayed():
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
                                    time.sleep(0.3)
                                    actions = ActionChains(self.driver)
                                    actions.move_to_element(add_btn).pause(0.3).click().perform()
                                    self.logger.info("Clicked 'Add' button for STEM indicator (ActionChains)")
                                    add_clicked = True
                                    time.sleep(2)
                                    break
                            except Exception as inner_e:
                                self.logger.debug(f"Could not click Add for this element: {inner_e}")

                        if add_clicked:
                            break
                    except Exception as e:
                        self.logger.debug(f"Keyword search failed: {e}")

                if add_clicked:
                    break

                if attempt < 2:
                    self.logger.info(f"STEM indicator not found yet, retrying in 2s...")
                    time.sleep(2)

            if not add_clicked:
                self.logger.error("Could not click Add button for STEM indicator!")
                return False

            # ============================================================
            # STEP 6: Click "View data" link
            # ============================================================
            self.logger.info("STEP 6: Clicking 'View data' link...")

            view_data_selectors = [
                (By.XPATH, "//a[contains(text(), 'View data')]"),
                (By.XPATH, "//*[contains(text(), 'View data')]"),
                (By.CSS_SELECTOR, "a[href*='view']"),
            ]

            view_clicked = False
            for selector in view_data_selectors:
                try:
                    elements = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located(selector)
                    )
                    if elements:
                        elements[0].click()
                        self.logger.info("Clicked 'View data' link")
                        view_clicked = True
                        time.sleep(5)  # Wait for data view to load
                        break
                except Exception as e:
                    self.logger.debug(f"View data selector failed: {e}")

            if not view_clicked:
                self.logger.warning("Could not find 'View data' link, checking if already on data view...")

            self.logger.info("STEM indicator navigation complete!")
            return True

        except Exception as e:
            self.logger.error(f"Error navigating to STEM indicator: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def expand_time_range_section(self):
        """Expand the Time range section in the left sidebar"""

        self.logger.info("Expanding Time range section...")

        try:
            # Look for Time range accordion/section
            time_range_selectors = [
                "//div[contains(text(), 'Time range')]",
                "//span[contains(text(), 'Time range')]",
                "//button[contains(text(), 'Time range')]",
                "//*[contains(@class, 'Accordion')]//*[contains(text(), 'Time range')]",
            ]

            for selector in time_range_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        # Click to expand if it's an accordion header
                        parent = elem
                        for _ in range(3):  # Look up to 3 levels
                            try:
                                parent = parent.find_element(By.XPATH, "./..")
                                if 'Accordion' in parent.get_attribute('class') or '':
                                    parent.click()
                                    time.sleep(1)
                                    self.logger.info("Expanded Time range accordion")
                                    return True
                            except:
                                pass
                        # Try clicking the element itself
                        elem.click()
                        time.sleep(1)
                        self.logger.info("Clicked Time range section")
                        return True
                except:
                    continue

            self.logger.info("Time range section may already be expanded")
            return True

        except Exception as e:
            self.logger.error(f"Error expanding time range: {e}")
            return False

    def set_time_range_by_slider(self):
        """
        Set the time range to full extent using JavaScript on the range inputs.
        Uses React's native input value setter to trigger proper state updates.
        """

        self.logger.info("Setting time range using slider...")

        try:
            time.sleep(2)

            # Find range inputs: <input type="range" min="1998" max="2025" aria-label="Year range">
            range_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range'][aria-label='Year range']")

            if not range_inputs:
                range_inputs = self.driver.find_elements(By.CSS_SELECTOR, ".MuiSlider-root input[type='range']")

            if len(range_inputs) < 2:
                self.logger.warning(f"Expected 2 range inputs, found {len(range_inputs)}")
                return False

            min_year = range_inputs[0].get_attribute('min')
            max_year = range_inputs[0].get_attribute('max')
            self.logger.info(f"Slider range from attributes: {min_year} - {max_year}")

            # Use React's native input value setter to programmatically set slider values
            # This triggers React's onChange handler properly
            result = self.driver.execute_script("""
                var inputs = document.querySelectorAll("input[type='range'][aria-label='Year range']");
                if (inputs.length < 2) return 'not_enough_inputs';

                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;

                // Set first input (start year) to min
                nativeInputValueSetter.call(inputs[0], arguments[0]);
                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                inputs[0].dispatchEvent(new Event('change', { bubbles: true }));

                // Set second input (end year) to max
                nativeInputValueSetter.call(inputs[1], arguments[1]);
                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
                inputs[1].dispatchEvent(new Event('change', { bubbles: true }));

                return 'ok';
            """, min_year, max_year)

            if result == 'ok':
                time.sleep(1)
                # Verify
                current_min = range_inputs[0].get_attribute('value')
                current_max = range_inputs[-1].get_attribute('value')
                self.logger.info(f"Time range set to: {current_min} - {current_max}")
                return True

            self.logger.warning(f"JS slider set returned: {result}")
            return False

        except Exception as e:
            self.logger.error(f"Error setting time range by slider: {e}")
            return False

    def set_time_range_by_input(self):
        """
        Fallback: Set the time range using the text input fields.
        Reads min/max dynamically from the slider's range input attributes.
        """

        self.logger.info("Setting time range using input fields (fallback)...")

        try:
            time.sleep(2)

            # Read min/max from the slider's range inputs
            # HTML: <input type="range" min="1998" max="2025" aria-label="Year range">
            range_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range'][aria-label='Year range']")

            if not range_inputs:
                range_inputs = self.driver.find_elements(By.CSS_SELECTOR, ".MuiSlider-root input[type='range']")

            min_year = None
            max_year = None

            for inp in range_inputs:
                inp_min = inp.get_attribute('min')
                inp_max = inp.get_attribute('max')
                if inp_min:
                    min_year = inp_min
                if inp_max:
                    max_year = inp_max

            if not min_year or not max_year:
                self.logger.error("Could not read year range from slider attributes!")
                return False

            self.logger.info(f"Year range from slider: {min_year} - {max_year}")

            # Find the text input fields for year
            # HTML: <input aria-label="Start year"> and <input aria-label="End year">
            start_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[aria-label='Start year']")
            end_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[aria-label='End year']")

            if start_inputs:
                start_input = start_inputs[0]
                start_input.click()
                start_input.send_keys(Keys.CONTROL + "a")
                start_input.send_keys(str(min_year))
                start_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                self.logger.info(f"Set start year input to {min_year}")

            if end_inputs:
                end_input = end_inputs[0]
                end_input.click()
                end_input.send_keys(Keys.CONTROL + "a")
                end_input.send_keys(str(max_year))
                end_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                self.logger.info(f"Set end year input to {max_year}")

            return True

        except Exception as e:
            self.logger.error(f"Error setting time range by input: {e}")
            return False

    def find_and_click_export(self):
        """Find and click the 'Download filtered data' button"""

        self.logger.info("Looking for 'Download filtered data' button...")

        try:
            time.sleep(2)

            # Look for "Download filtered data" button (at bottom right of data view)
            download_selectors = [
                (By.XPATH, "//button[contains(text(), 'Download filtered data')]"),
                (By.XPATH, "//button[contains(text(), 'Download')]"),
                (By.XPATH, "//*[contains(text(), 'Download filtered')]"),
                (By.CSS_SELECTOR, "button[data-testid='download-button']"),
                # MUI Button with download icon
                (By.XPATH, "//button[contains(@class, 'MuiButton') and contains(., 'Download')]"),
            ]

            for selector in download_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    for elem in elements:
                        if elem.is_displayed() and 'Download' in elem.text:
                            # Scroll element into view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                            time.sleep(0.5)
                            elem.click()
                            time.sleep(2)
                            self.logger.info(f"Clicked 'Download filtered data' button")
                            return True
                except Exception as e:
                    self.logger.debug(f"Download selector failed: {e}")

            # Fallback: scroll to bottom of page and look for download button
            self.logger.info("Scrolling to find download button...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Try again after scrolling
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.MuiButton-root")
            for btn in buttons:
                if 'download' in btn.text.lower():
                    btn.click()
                    time.sleep(2)
                    self.logger.info("Clicked download button (after scroll)")
                    return True

            self.logger.warning("Could not find download button")
            return False

        except Exception as e:
            self.logger.error(f"Error finding download button: {e}")
            return False

    def select_csv_format_and_download(self):
        """
        Select Excel format from the download popover and click the Download link.

        The popover contains:
          - Radio buttons: CSV (default), Excel, JSON  (name="download-format")
          - Checkboxes:    Metadata, Footnotes
          - Download link: <a class="MuiButton-root MuiButton-contained..." target="_blank">Download</a>
        """

        self.logger.info("Selecting Excel format from download popover...")

        try:
            time.sleep(2)

            # --- Step 1: Select Excel radio button ---
            # The radio <input> is visually hidden; click its parent <label> or use JS
            excel_selected = False

            # Strategy A: JS click on the hidden radio input directly
            try:
                result = self.driver.execute_script("""
                    var inputs = document.querySelectorAll('input[name="download-format"]');
                    for (var i = 0; i < inputs.length; i++) {
                        if (inputs[i].value === 'Excel') {
                            inputs[i].click();
                            return 'clicked';
                        }
                    }
                    return 'not_found';
                """)
                if result == 'clicked':
                    self.logger.info("Selected Excel radio via JS")
                    excel_selected = True
                    time.sleep(1)
            except Exception as e:
                self.logger.debug(f"JS radio click failed: {e}")

            # Strategy B: Click the <label> that wraps the Excel option
            if not excel_selected:
                try:
                    label = self.driver.find_element(
                        By.XPATH,
                        "//label[contains(@class,'MuiFormControlLabel-root') and .//input[@value='Excel']]"
                    )
                    label.click()
                    self.logger.info("Selected Excel radio via label click")
                    excel_selected = True
                    time.sleep(1)
                except Exception as e:
                    self.logger.debug(f"Label click for Excel failed: {e}")

            if not excel_selected:
                self.logger.warning("Could not select Excel — CSV may be used by default")

            # --- Step 2: Click the Download <a> link in the popover ---
            # The Download element is an <a> tag (MuiButton-contained), NOT a <button>
            time.sleep(0.5)

            download_link_selectors = [
                # Primary: <a> with MuiButton-contained class containing "Download"
                (By.XPATH, "//a[contains(@class,'MuiButton-contained') and contains(.,'Download')]"),
                # Fallback 1: any <a> with target="_blank" inside the popover
                (By.XPATH, "//div[contains(@class,'MuiPopover-paper')]//a[contains(.,'Download')]"),
                # Fallback 2: <a> with MuiButtonBase-root and Download text
                (By.XPATH, "//a[contains(@class,'MuiButtonBase-root') and contains(.,'Download')]"),
            ]

            for selector in download_link_selectors:
                try:
                    elements = self.driver.find_elements(*selector)
                    for elem in elements:
                        if elem.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                            time.sleep(0.3)
                            actions = ActionChains(self.driver)
                            actions.move_to_element(elem).pause(0.3).click().perform()
                            self.logger.info(f"Clicked Download link in popover")
                            time.sleep(2)
                            return True
                except Exception as e:
                    self.logger.debug(f"Download link selector failed: {e}")

            self.logger.warning("Could not find Download link in popover")
            return False

        except Exception as e:
            self.logger.error(f"Error selecting format and downloading: {e}")
            return False

    def wait_for_download(self, before_files=None):
        """
        Wait for a new .zip file to appear in the downloads directory.
        The UNESCO export downloads as a zip containing the Excel/CSV file.

        Args:
            before_files: set of file paths that existed BEFORE the download started.
                          Any new zip that appears is the one we are waiting for.
        """

        self.logger.info("Waiting for download to complete (expecting .zip file)...")

        if before_files is None:
            before_files = set()

        start_time = time.time()

        while time.time() - start_time < config.DOWNLOAD_WAIT_TIMEOUT:
            # Partial download files still in progress
            crdownload_files = glob.glob(os.path.join(config.DOWNLOADS_DIR, '*.crdownload'))

            # Look for zip files
            zip_files = glob.glob(os.path.join(config.DOWNLOADS_DIR, '*.zip'))

            # A new file is one that wasn't there before we clicked Download
            new_zips = [f for f in zip_files if f not in before_files]

            if new_zips and not crdownload_files:
                downloaded = max(new_zips, key=os.path.getmtime)
                self.logger.info(f"Download complete: {os.path.basename(downloaded)}")
                return downloaded

            if crdownload_files:
                self.logger.debug(f"Download in progress ({len(crdownload_files)} partial file(s))...")

            time.sleep(1)

        self.logger.error("Download timeout — no new .zip file found in downloads directory")
        return None

    def extract_from_zip(self, zip_path):
        """
        Extract the Excel/CSV file from the downloaded zip archive.
        Returns the path to the extracted file.
        """
        import zipfile

        self.logger.info(f"Extracting: {os.path.basename(zip_path)}")

        extract_dir = os.path.dirname(zip_path)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                names = zf.namelist()
                self.logger.info(f"Zip contents: {names}")

                # Find the Excel or CSV file inside
                data_file = None
                for name in names:
                    if name.endswith('.xlsx') or name.endswith('.csv') or name.endswith('.xls'):
                        data_file = name
                        break

                if not data_file:
                    # If no recognised extension, extract the first file
                    data_file = names[0] if names else None

                if data_file:
                    zf.extract(data_file, extract_dir)
                    extracted_path = os.path.join(extract_dir, data_file)
                    self.logger.info(f"Extracted: {extracted_path}")
                    return extracted_path
                else:
                    self.logger.error("Zip file is empty")
                    return None

        except Exception as e:
            self.logger.error(f"Error extracting zip: {e}")
            return None

    def download_data(self):
        """
        Main method to download the STEMGRADS data from UNESCO.

        Returns:
            str: Path to downloaded CSV file or None
        """

        try:
            self.setup_driver()

            # Navigate to UNESCO data portal
            if not self.navigate_to_page(config.BASE_URL):
                return None

            # Wait for React SPA to fully hydrate (needs longer in headless)
            wait_time = 12 if config.HEADLESS_MODE else 8
            self.logger.info(f"Waiting for page to fully load ({wait_time}s)...")
            time.sleep(wait_time)

            # Navigate to STEM indicator (may already be selected)
            self.navigate_to_stem_indicator()
            time.sleep(3)

            # Expand time range section
            self.expand_time_range_section()
            time.sleep(2)

            # Set time range to full available range
            # Try slider first, then input fields
            if not self.set_time_range_by_slider():
                self.set_time_range_by_input()

            time.sleep(3)

            # Find and click export
            if self.find_and_click_export():
                # Snapshot existing zip files BEFORE triggering the download
                before_files = set(glob.glob(os.path.join(config.DOWNLOADS_DIR, '*.zip')))
                self.logger.info(f"Zip files before download: {len(before_files)}")

                # Select Excel format and click the Download link
                self.select_csv_format_and_download()

                # Wait for the new zip to appear
                zip_file = self.wait_for_download(before_files=before_files)

                if zip_file:
                    self.logger.info(f"Zip downloaded: {zip_file}")
                    # Extract the Excel/CSV file from the zip
                    extracted = self.extract_from_zip(zip_file)
                    if extracted:
                        self.logger.info(f"Successfully extracted: {extracted}")
                        return extracted
                    # If extraction fails, still return the zip
                    return zip_file

            self.logger.error("Failed to download data")

            # Keep browser open for debugging if not headless
            if not config.HEADLESS_MODE:
                self.logger.info("Browser kept open for debugging. Press Enter to close...")
                input("Press Enter to close browser...")

            return None

        except Exception as e:
            self.logger.error(f"Error during download: {e}")

            if not config.HEADLESS_MODE:
                self.logger.info("Browser kept open for debugging. Press Enter to close...")
                input("Press Enter to close browser...")

            return None

        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")


def main():
    """Test the scraper"""
    from logger_setup import setup_logging

    setup_logging()

    scraper = STEMGRADSScraper()
    csv_file = scraper.download_data()

    if csv_file:
        print(f"\n[SUCCESS] Downloaded: {csv_file}")
    else:
        print("\n[FAILED] Could not download CSV file")


if __name__ == '__main__':
    main()
