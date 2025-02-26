import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import base64
import json
import os
from datetime import datetime
from selenium.webdriver.remote.webelement import WebElement
from utils.config import settings
from utils.logger import captcha_logger

class CaptchaService:
    MIN_LENGTH = 4
    MAX_LENGTH = 5
    # Try multiple PSM modes in order of preference
    PSM_MODES = [7, 8, 13]  # 7=single line, 8=single word, 13=raw line
    
    # Common CAPTCHA characters to help with validation
    ALLOWED_CHARS = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    @staticmethod
    def _save_attempt(attempt_num: int, original_img: Image.Image, processed_img: Image.Image, ocr_result: str, settings_used: dict) -> str:
        """Save captcha attempt images and results to disk."""
        if not settings.CAPTCHA_SAVE_ATTEMPTS:
            return None
            
        # Create attempts directory if it doesn't exist
        os.makedirs(settings.CAPTCHA_ATTEMPTS_DIR, exist_ok=True)
        
        # Create timestamped directory for this attempt
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        attempt_dir = os.path.join(settings.CAPTCHA_ATTEMPTS_DIR, f"{timestamp}_attempt_{attempt_num}")
        os.makedirs(attempt_dir, exist_ok=True)
        
        # Save images
        original_path = os.path.join(attempt_dir, "original.png")
        processed_path = os.path.join(attempt_dir, "processed.png")
        original_img.save(original_path)
        processed_img.save(processed_path)
        
        # Save results and settings
        results = {
            "timestamp": timestamp,
            "attempt_number": attempt_num,
            "ocr_result": ocr_result,
            "settings_used": settings_used
        }
        
        results_path = os.path.join(attempt_dir, "results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        return attempt_dir
        
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and validate extracted text."""
        # Remove any non-alphanumeric characters
        text = ''.join(filter(str.isalnum, text))
        # Convert to lowercase since CAPTCHAs are case-insensitive
        text = text.lower()
        # Remove any characters that aren't typically used in CAPTCHAs
        text = ''.join(c for c in text if c in CaptchaService.ALLOWED_CHARS)
        return text

    @staticmethod
    def process_captcha(captcha_element: WebElement, max_attempts: int = 3) -> str:
        """
        Process the CAPTCHA image and return the recognized text.
        Tries different processing methods until a valid result is found.
        
        Args:
            captcha_element: Selenium WebElement containing the CAPTCHA image
            max_attempts: Maximum number of attempts to process the captcha
            
        Returns:
            str: Recognized CAPTCHA text
        """
        captcha_logger.info("Starting CAPTCHA processing")
        try:
            if settings.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
                captcha_logger.debug(f"Using Tesseract path: {settings.TESSERACT_CMD}")

            last_error = None
            for _ in range(max_attempts):
                try:
                    # Get CAPTCHA image
                    captcha_src = captcha_element.get_attribute("src")
                    captcha_logger.debug("Retrieved CAPTCHA source")
                    
                    # Process the image based on its source type
                    if "data:image" in captcha_src:
                        captcha_logger.debug("Processing base64 image")
                        image = CaptchaService._process_base64_image(captcha_src)
                    else:
                        captcha_logger.debug("Processing screenshot")
                        image = CaptchaService._process_screenshot(captcha_element)
                    
                    original_img = image
                    attempt_num = _ + 1
                    
                    # Enhance image and keep copy for saving
                    processed_img = CaptchaService._enhance_image(image.copy())
                    
                    # Try different PSM modes
                    best_result = None
                    for psm_mode in CaptchaService.PSM_MODES:
                        config = f'--psm {psm_mode} --oem 3'
                        text = pytesseract.image_to_string(processed_img, config=config)
                        result = CaptchaService._clean_text(text)
                        
                        if result and CaptchaService.MIN_LENGTH <= len(result) <= CaptchaService.MAX_LENGTH:
                            best_result = result
                            captcha_logger.debug(f"Valid result found with PSM mode {psm_mode}: {result}")
                            break
                            
                    if best_result:
                        result = best_result
                    else:
                        result = ''  # No valid result found with any PSM mode
                    
                    # Log attempt details
                    settings_used = {
                        "psm_mode": settings.CAPTCHA_PSM_MODE,
                        "contrast": settings.CAPTCHA_CONTRAST,
                        "threshold": settings.CAPTCHA_THRESHOLD,
                        "noise_reduction": settings.CAPTCHA_APPLY_NOISE_REDUCTION,
                        "resize_enabled": settings.CAPTCHA_RESIZE_SMALL_IMAGES,
                        "stronger_enhancement": False
                    }
                    
                    # Save attempt if enabled
                    attempt_dir = CaptchaService._save_attempt(
                        attempt_num, original_img, processed_img, result, settings_used)
                    
                    if attempt_dir:
                        captcha_logger.info(f"Attempt {attempt_num} saved to: {attempt_dir}")
                    captcha_logger.info(f"Attempt {attempt_num} result: {result}")
                    
                    if result:
                        captcha_logger.info(f"Successfully recognized CAPTCHA: {result}")
                        return result
                    
                    # If no valid result, try with stronger enhancement
                    settings_used["stronger_enhancement"] = True
                    processed_img = CaptchaService._enhance_image(image.copy(), stronger=True)
                    
                    # Try different PSM modes with stronger enhancement
                    best_result = None
                    for psm_mode in CaptchaService.PSM_MODES:
                        config = f'--psm {psm_mode} --oem 3'
                        text = pytesseract.image_to_string(processed_img, config=config)
                        stronger_result = CaptchaService._clean_text(text)
                        
                        if stronger_result and CaptchaService.MIN_LENGTH <= len(stronger_result) <= CaptchaService.MAX_LENGTH:
                            best_result = stronger_result
                            captcha_logger.debug(f"Valid result found with stronger enhancement and PSM mode {psm_mode}: {stronger_result}")
                            break
                            
                    stronger_result = best_result if best_result else ''
                    
                    # Save stronger attempt if enabled
                    attempt_dir = CaptchaService._save_attempt(
                        attempt_num + max_attempts, original_img, processed_img, 
                        stronger_result, settings_used)
                        
                    if attempt_dir:
                        captcha_logger.info(f"Stronger attempt {attempt_num} saved to: {attempt_dir}")
                        
                    # Check if stronger enhancement result is valid
                    if stronger_result and CaptchaService.MIN_LENGTH <= len(stronger_result) <= CaptchaService.MAX_LENGTH:
                        captcha_logger.info(f"Successfully recognized CAPTCHA with stronger enhancement: {stronger_result}")
                        return stronger_result
                    
                except Exception as e:
                    last_error = e
                    captcha_logger.warning(f"Attempt failed: {str(e)}")
                    continue
                
            if last_error:
                raise last_error
            raise Exception("Failed to process CAPTCHA after multiple attempts")
            
        except Exception as e:
            captcha_logger.error(f"Error processing CAPTCHA: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _enhance_image(image: Image.Image, stronger: bool = False) -> Image.Image:
        """
        Apply various image enhancements to improve OCR accuracy.
        When stronger=True, applies more aggressive enhancement settings.
        """
        try:
            # Convert to grayscale
            image = image.convert('L')
            
            # Apply contrast with optional stronger enhancement
            contrast_factor = settings.CAPTCHA_CONTRAST * (1.5 if stronger else 1.0)
            image = ImageEnhance.Contrast(image).enhance(contrast_factor)
            
            # Apply sharpness enhancement if using stronger mode
            if stronger:
                image = ImageEnhance.Sharpness(image).enhance(2.0)
            
            # Apply threshold with optional stronger enhancement
            threshold = settings.CAPTCHA_THRESHOLD * (0.9 if stronger else 1.0)
            image = image.point(lambda x: 0 if x < threshold else 255, '1')
            
            # Apply noise reduction with optional stronger settings
            if settings.CAPTCHA_APPLY_NOISE_REDUCTION:
                filter_size = 5 if stronger else 3
                image = image.filter(ImageFilter.MedianFilter(size=filter_size))
                if stronger:
                    image = image.filter(ImageFilter.MinFilter(size=3))
            
            # Resize with optional stronger enhancement
            if settings.CAPTCHA_RESIZE_SMALL_IMAGES:
                resize_factor = 2.0 if stronger else 1.5
                if image.size[0] < 100 or image.size[1] < 30:
                    width = int(image.size[0] * resize_factor)
                    height = int(image.size[1] * resize_factor)
                    image = image.resize((width, height), Image.LANCZOS)
            
            return image
        except Exception as e:
            captcha_logger.error(f"Error enhancing image: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _process_base64_image(captcha_src: str) -> Image.Image:
        """Process base64 encoded image and enhance it."""
        try:
            captcha_logger.debug("Processing base64 image data")
            header, encoded = captcha_src.split(",", 1)
            img_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(img_data))
            captcha_logger.debug(f"Base64 image processed. Size: {image.size}")
            return image
        except Exception as e:
            captcha_logger.error(f"Error processing base64 image: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _process_screenshot(captcha_element: WebElement) -> Image.Image:
        """Process CAPTCHA by taking a screenshot and enhance it."""
        try:
            captcha_logger.debug("Taking screenshot of CAPTCHA element")
            captcha_element.screenshot("captcha.png")
            image = Image.open("captcha.png")
            captcha_logger.debug(f"Screenshot processed. Size: {image.size}")
            return image
        except Exception as e:
            captcha_logger.error(f"Error taking screenshot: {str(e)}", exc_info=True)
            raise
