from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

from services.captcha_service import CaptchaService
from utils.config import settings
from utils.logger import selenium_logger

class SeleniumService:
    def __init__(self):
        self.driver = None
        self.wait = None

    def initialize_driver(self):
        """Initialize the Chrome WebDriver."""
        try:
            selenium_logger.info("Initializing Chrome WebDriver")
            chrome_options = webdriver.ChromeOptions()
            if settings.SELENIUM_CHROME_HEADLESS:
                chrome_options.add_argument('--headless')
            selenium_logger.debug("Chrome options configured: headless mode enabled")
            
            if settings.CHROME_DRIVER_PATH:
                selenium_logger.debug(f"Using custom ChromeDriver path: {settings.CHROME_DRIVER_PATH}")
                service = Service(executable_path=settings.CHROME_DRIVER_PATH)
            else:
                selenium_logger.debug("Using default ChromeDriver path")
                service = Service()
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            self.wait = WebDriverWait(self.driver, settings.SELENIUM_DEFAULT_WAIT_TIMEOUT)
            selenium_logger.info("ChromeDriver initialized successfully")
        except Exception as e:
            selenium_logger.error(f"Failed to initialize ChromeDriver: {str(e)}", exc_info=True)
            raise

    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            selenium_logger.info("Closing ChromeDriver")
            try:
                self.driver.quit()
                selenium_logger.debug("ChromeDriver closed successfully")
            except Exception as e:
                selenium_logger.error(f"Error closing ChromeDriver: {str(e)}", exc_info=True)
            
    def get_ie_number(self, cnpj: str) -> dict:
        """
        Get IE number for given CNPJ.
        
        Args:
            cnpj: CNPJ number (raw format, only digits)
            
        Returns:
            dict: Response containing IE number or error message
        """
        start_time = time.time()
        selenium_logger.info(f"Starting IE number lookup for CNPJ: {cnpj}")
        
        try:
            self.initialize_driver()
            
            # Navigate to page and wait for load
            selenium_logger.debug(f"Navigating to CADESP URL: {settings.CADESP_URL}")
            self.driver.get(settings.CADESP_URL)
            self.wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            
            # Wait for container visibility
            selenium_logger.debug("Waiting for form container")
            self.wait.until(EC.visibility_of_element_located(
                (By.ID, "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer")))

            # Select CNPJ option in dropdown
            selenium_logger.debug("Selecting CNPJ option in dropdown")
            type_select = self.wait.until(EC.element_to_be_clickable(
                (By.ID, settings.TYPE_SELECT_ID)))
            self.driver.execute_script(
                "arguments[0].value = '1'; arguments[0].dispatchEvent(new Event('change'))",
                type_select
            )
            
            # Enter CNPJ
            selenium_logger.debug("Entering CNPJ")
            try:
                cnpj_input = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, settings.CNPJ_INPUT_ID)))
                cnpj_input.clear()
                cnpj_input.send_keys(cnpj)
                selenium_logger.debug(f"CNPJ entered: {cnpj}")
            except TimeoutException:
                selenium_logger.error(f"CNPJ input field not found for CNPJ {cnpj}", exc_info=True)
                return {
                    "success": False,
                    "error": "CNPJ input field not found. The webpage structure might have changed.",
                    "cnpj": cnpj,
                    "elapsed_time": f"{time.time() - start_time:.2f}s"
                }

            # Process CAPTCHA with stability check and exponential backoff retries
            max_captcha_attempts = settings.SELENIUM_MAX_CAPTCHA_ATTEMPTS
            base_delay = settings.SELENIUM_BASE_RETRY_DELAY

            for captcha_attempt in range(max_captcha_attempts):
                # Calculate exponential backoff delay for CAPTCHA
                captcha_retry_delay = base_delay * (2 ** captcha_attempt)
                selenium_logger.debug(f"Processing CAPTCHA (attempt {captcha_attempt + 1}/{max_captcha_attempts}) with delay {captcha_retry_delay:.2f}s")
                try:
                    captcha_img = self.wait.until(EC.presence_of_element_located(
                        (By.ID, settings.CAPTCHA_IMG_ID)))
                    
                    # Get initial src to check for changes
                    initial_src = captcha_img.get_attribute("src")
                    time.sleep(settings.SELENIUM_CAPTCHA_STABILITY_WAIT)  # Wait to ensure CAPTCHA is stable
                    
                    # Verify CAPTCHA hasn't changed
                    current_src = captcha_img.get_attribute("src")
                    if initial_src != current_src:
                        selenium_logger.warning(f"CAPTCHA changed while processing, retrying in {captcha_retry_delay:.2f}s...")
                        time.sleep(captcha_retry_delay)
                        continue
                        
                    captcha_text = CaptchaService.process_captcha(captcha_img)
                    selenium_logger.debug(f"CAPTCHA processed: {captcha_text}")
                    
                    # Fill CAPTCHA
                    selenium_logger.debug("Entering CAPTCHA text")
                    try:
                        captcha_input = self.wait.until(EC.element_to_be_clickable(
                            (By.ID, settings.CAPTCHA_INPUT_ID)))
                        captcha_input.clear()
                        captcha_input.send_keys(captcha_text)
                        selenium_logger.debug("Entered new CAPTCHA text for retry.")
                    except TimeoutException:
                        if captcha_attempt < max_captcha_attempts - 1:
                            selenium_logger.warning(f"CAPTCHA input field not found, retrying in {captcha_retry_delay:.2f}s...")
                            time.sleep(captcha_retry_delay)
                            continue
                        selenium_logger.error("CAPTCHA input field not found after all retries.", exc_info=True)
                        raise Exception("CAPTCHA input field not found after all retries.")
                    break  # Successfully processed CAPTCHA, exit loop
                except TimeoutException:
                    if captcha_attempt < max_captcha_attempts - 1:
                        selenium_logger.warning(f"CAPTCHA image not found, retrying in {captcha_retry_delay:.2f}s...")
                        time.sleep(captcha_retry_delay)
                        continue
                    selenium_logger.error("CAPTCHA image not found after all retries.", exc_info=True)
                    raise Exception("CAPTCHA image not found after all retries.")
            else:
                selenium_logger.error("Failed to process stable CAPTCHA after maximum attempts.")
                return {
                    "success": False,
                    "error": "Failed to process CAPTCHA after multiple attempts.",
                    "cnpj": cnpj,
                    "elapsed_time": f"{time.time() - start_time:.2f}s"
                }

            # Try form submission with exponential backoff retries
            max_retries = settings.SELENIUM_MAX_FORM_RETRIES
            base_delay = settings.SELENIUM_BASE_RETRY_DELAY

            for attempt in range(max_retries):
                # Calculate exponential backoff delay
                retry_delay = base_delay * (2 ** attempt)
                selenium_logger.debug(f"Attempt {attempt + 1}/{max_retries} with delay {retry_delay:.2f}s")
                try:
                    # Submit form
                    selenium_logger.debug(f"Submitting form (attempt {attempt + 1}/{max_retries})")
                    search_button = self.wait.until(EC.presence_of_element_located(
                        (By.ID, settings.SEARCH_BUTTON_ID)))

                    # Use JavaScript to click to avoid potential overlay issues
                    self.driver.execute_script("arguments[0].click();", search_button)
                    
                    # Use default timeout for better reliability
                    quick_wait = WebDriverWait(self.driver, settings.SELENIUM_DEFAULT_WAIT_TIMEOUT)
                    
                    try:
                        # Wait for page to be ready after form submission
                        quick_wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                        
                        # Check for loading indicator if present
                        loading_indicators = self.driver.find_elements(By.ID, settings.LOADING_INDICATOR_ID)
                        if loading_indicators:
                            quick_wait.until_not(EC.presence_of_element_located((By.ID, settings.LOADING_INDICATOR_ID)))
                        
                        # Check each possible element
                        result = None
                        for selector in [
                            (By.XPATH, settings.RESULT_TABLE_XPATH),
                            (By.ID, settings.ERROR_MSG_ID),
                            (By.ID, settings.NOT_FOUND_MSG_ID)
                        ]:
                            try:
                                element = quick_wait.until(EC.presence_of_element_located(selector))
                                if element.is_displayed():
                                    result = element
                                    break
                            except TimeoutException:
                                continue
                        
                        if result is None:
                            raise TimeoutException("No result elements found")
                        
                        # Check which element we found (now using result from above)
                        if result.get_attribute('id') == settings.ERROR_MSG_ID:
                            error_msg = result
                            if error_msg.is_displayed() and error_msg.text.strip():
                                if "imagem de segurança" in error_msg.text and attempt < max_retries - 1:
                                    selenium_logger.warning(f"Captcha validation failed, retrying... ({attempt + 1}/{max_retries})")
                                    try:
                                        captcha_img = quick_wait.until(EC.presence_of_element_located(
                                            (By.ID, settings.CAPTCHA_IMG_ID)))
                                        captcha_text = CaptchaService.process_captcha(captcha_img)
                                        captcha_input = quick_wait.until(EC.element_to_be_clickable(
                                            (By.ID, settings.CAPTCHA_INPUT_ID)))
                                        captcha_input.clear()
                                        captcha_input.send_keys(captcha_text)
                                        selenium_logger.debug("Entered new CAPTCHA text for retry.")
                                        time.sleep(settings.SELENIUM_CAPTCHA_STABILITY_WAIT)  # Brief wait before retry
                                        continue
                                    except TimeoutException as e:
                                        selenium_logger.warning("CAPTCHA interaction failed during retry.")
                                        return {
                                            "success": False,
                                            "error": "CAPTCHA interaction failed during retry",
                                            "cnpj": cnpj,
                                            "elapsed_time": f"{time.time() - start_time:.2f}s",
                                            "validation_error": True
                                        }
                                # Return form validation error instead of raising exception
                                selenium_logger.warning(f"Form validation error: {error_msg.text}")
                                return {
                                    "success": False,
                                    "error": error_msg.text,
                                    "cnpj": cnpj,
                                    "elapsed_time": f"{time.time() - start_time:.2f}s",
                                    "validation_error": True
                                }
                        elif result.get_attribute('id') == settings.NOT_FOUND_MSG_ID:
                            not_found_msg = result
                            if not_found_msg.is_displayed() and not_found_msg.text.strip():
                                selenium_logger.info(f"CNPJ {cnpj} not found in database")
                                return {
                                    "success": False,
                                    "error": f"CNPJ {cnpj} not found in the CADESP database",
                                    "cnpj": cnpj,
                                    "elapsed_time": f"{time.time() - start_time:.2f}s",
                                    "not_found": True
                                }
                        # If we found the result table or no special messages, continue processing
                        selenium_logger.debug("Form submitted successfully, proceeding to process results.")
                        break
                    except TimeoutException:
                        if attempt == max_retries - 1:
                            selenium_logger.warning("No response received after form submission")
                            return {
                                "success": False,
                                "error": "No response received after form submission",
                                "cnpj": cnpj,
                                "elapsed_time": f"{time.time() - start_time:.2f}s",
                                "validation_error": True
                            }
                        selenium_logger.warning(f"No response after form submission, refreshing page and retrying in {retry_delay:.2f}s...")
                        self.driver.refresh()
                        time.sleep(retry_delay)
                        continue
                except Exception as e:
                    if attempt == max_retries - 1:
                        selenium_logger.warning(f"Form submission failed after {max_retries} attempts: {str(e)}")
                        return {
                            "success": False,
                            "error": f"Form submission failed after {max_retries} attempts: {str(e)}",
                            "cnpj": cnpj,
                            "elapsed_time": f"{time.time() - start_time:.2f}s",
                            "validation_error": True
                        }
                    selenium_logger.warning(f"Form submission attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay:.2f}s...")
                    time.sleep(retry_delay)
                    continue

            # Try to handle any alert that might appear
            try:
                alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                alert_text = alert.text
                selenium_logger.warning(f"Alert detected: {alert_text}")
                alert.accept()
                return {
                    "success": False,
                    "error": f"Form validation error: {alert_text}",
                    "cnpj": cnpj,
                    "elapsed_time": f"{time.time() - start_time:.2f}s",
                    "validation_error": True
                }
            except TimeoutException:
                # No alert, continue normally
                pass

            # Wait for and validate result page
            try:
                selenium_logger.debug("Waiting for result table and data")
                # Wait for main result table with exponential backoff retry
                for retry in range(settings.SELENIUM_RESULT_RETRIES):
                    # Calculate exponential backoff delay for results
                    result_retry_delay = settings.SELENIUM_BASE_RETRY_DELAY * (2 ** retry)
                    try:
                        selenium_logger.debug(f"Result table attempt {retry + 1}/{settings.SELENIUM_RESULT_RETRIES} with delay {result_retry_delay:.2f}s")
                        
                        # Wait for main result table
                        result_table = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, settings.RESULT_TABLE_XPATH)))
                        
                        # Verify all sections are present
                        sections = self.driver.find_elements(By.XPATH, settings.RESULT_SECTIONS_XPATH)
                        if len(sections) < settings.SELENIUM_MIN_RESULT_SECTIONS:
                            if retry < settings.SELENIUM_RESULT_RETRIES - 1:
                                selenium_logger.warning(f"Result sections not fully loaded, retrying in {result_retry_delay:.2f}s...")
                                time.sleep(result_retry_delay)
                                continue
                            selenium_logger.warning("Result page sections not fully loaded")
                            return {
                                "success": False,
                                "error": "Result page sections not fully loaded",
                                "cnpj": cnpj,
                                "elapsed_time": f"{time.time() - start_time:.2f}s",
                                "validation_error": True
                            }
                        
                        # Verify table has content
                        if not result_table.text.strip():
                            if retry < settings.SELENIUM_RESULT_RETRIES - 1:
                                selenium_logger.warning(f"Result table is empty, retrying in {result_retry_delay:.2f}s...")
                                time.sleep(result_retry_delay)
                                continue
                            selenium_logger.warning("Result table is empty")
                            return {
                                "success": False,
                                "error": "Result table is empty",
                                "cnpj": cnpj,
                                "elapsed_time": f"{time.time() - start_time:.2f}s",
                                "validation_error": True
                            }
                            
                        break  # If we got here, everything is loaded
                        
                    except TimeoutException as e:
                        if retry == settings.SELENIUM_RESULT_RETRIES - 1:
                            raise
                        selenium_logger.warning(f"Timeout waiting for result table (attempt {retry + 1}/{settings.SELENIUM_RESULT_RETRIES}), retrying in {result_retry_delay:.2f}s...")
                        time.sleep(result_retry_delay)
                
                # Extract IE number
                ie_number = self._get_field_value('IE:')
                
                elapsed_time = time.time() - start_time
                
                if ie_number is None:
                    selenium_logger.error("IE number not found in result page")
                    return {
                        "success": False,
                        "error": "IE number not found in result page. The webpage structure might have changed.",
                        "cnpj": cnpj,
                        "elapsed_time": f"{elapsed_time:.2f}s"
                    }
                
                selenium_logger.info(f"IE number successfully extracted: {ie_number}. Time taken: {elapsed_time:.2f}s")
                return {
                    "success": True,
                    "ie_number": ie_number,
                    "elapsed_time": f"{elapsed_time:.2f}s"
                }
            except TimeoutException:
                selenium_logger.warning("Could not load result table. The CNPJ might be invalid or the page structure changed.")
                return {
                    "success": False,
                    "error": "Could not load result page. The CNPJ might be invalid or the page structure changed.",
                    "cnpj": cnpj,
                    "elapsed_time": f"{time.time() - start_time:.2f}s",
                    "validation_error": True
                }

        except WebDriverException as e:
            selenium_logger.error(f"WebDriver error for CNPJ {cnpj}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"WebDriver error: {str(e)}",
                "cnpj": cnpj,
                "elapsed_time": f"{time.time() - start_time:.2f}s"
            }
        except Exception as e:
            selenium_logger.error(f"Unexpected error for CNPJ {cnpj}: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "error": f"Unexpected error: {str(e)}",
                "cnpj": cnpj,
                "elapsed_time": f"{time.time() - start_time:.2f}s"
            }
        finally:
            self.close_driver()
                
    def _get_field_value(self, label: str) -> str:
        """Helper method to get field value by label."""
        try:
            if label == 'IE:':
                # Try each XPath pattern in order for IE field
                xpaths = [
                    settings.IE_XPATH,
                    settings.IE_XPATH_FALLBACK1,
                    settings.IE_XPATH_FALLBACK2
                ]
                
                for xpath in xpaths:
                    try:
                        selenium_logger.debug(f"Trying XPath for IE: {xpath}")
                        value_elem = self.driver.find_element(By.XPATH, xpath)
                        value = value_elem.text.strip()
                        
                        # Validate IE number format
                        import re
                        if re.match(settings.IE_NUMBER_PATTERN, value):
                            selenium_logger.debug(f"Found valid IE number: {value}")
                            return value
                        else:
                            selenium_logger.warning(f"Found IE value but format is invalid: {value}")
                            continue
                            
                    except Exception as e:
                        selenium_logger.debug(f"XPath pattern failed: {str(e)}")
                        continue
                
                # If we get here, no valid IE was found
                selenium_logger.error("No valid IE number found with any XPath pattern")
                return None
                
            else:
                # For other fields, use the standard pattern
                xpath = f"//td[@class='{settings.DATA_CLASS}' and preceding-sibling::td[@class='{settings.LABEL_CLASS}' and contains(text(), '{label}')]]"
                selenium_logger.debug(f"Searching for field '{label}' using XPath: {xpath}")
                
                try:
                    value_elem = self.driver.find_element(By.XPATH, xpath)
                except:
                    page_source = self.driver.page_source
                    selenium_logger.debug(f"Page source when element not found:\n{page_source}")
                    raise
                
                value = value_elem.text.strip()
                selenium_logger.debug(f"Found value for {label}: {value}")
                return value
                
        except Exception as e:
            selenium_logger.error(f"Error extracting field value for label '{label}': {str(e)}", exc_info=True)
            return None
