#!/usr/bin/env python3
"""
Captcha Calibration Script

This script is designed to test and calibrate the captcha recognition settings by:
1. Capturing multiple captcha images from the CADESP website
2. Testing different image enhancement configurations
3. Trying various Tesseract OCR PSM modes
4. Saving debug images showing both original and processed versions
5. Recording OCR results for each configuration

The script will:
- Create a 'calibration_output' directory
- Save original captcha images as 'original_N.png'
- Save debug images as 'debug_N_config_M.png' showing:
  * Original image
  * Processed image
  * OCR results for each PSM mode

Usage:
    python captcha_calibration.py

Requirements:
    - Python 3.6+
    - Selenium WebDriver
    - Tesseract OCR
    - Pillow (PIL)
    - Chrome WebDriver
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from services.captcha_service import CaptchaService
from utils.config import settings

def create_debug_image(original_img: Image.Image, processed_img: Image.Image, results: list) -> Image.Image:
    """Create a debug image showing original, processed, and OCR results."""
    # Create a new image with space for original, processed, and text
    width = max(original_img.width * 2, 400)
    height = original_img.height + 150  # Extra space for text
    debug_img = Image.new('RGB', (width, height), 'white')
    
    # Paste original and processed images
    debug_img.paste(original_img, (0, 0))
    debug_img.paste(processed_img, (original_img.width, 0))
    
    # Add text results
    draw = ImageDraw.Draw(debug_img)
    y_pos = original_img.height + 10
    
    draw.text((10, y_pos), "Original", fill='black')
    draw.text((original_img.width + 10, y_pos), "Processed", fill='black')
    
    y_pos += 20
    for psm, text in results:
        draw.text((10, y_pos), f"PSM {psm}: {text}", fill='black')
        y_pos += 20
        
    return debug_img

def calibrate_captcha():
    """Run captcha calibration tests."""
    print("Starting captcha calibration...")
    
    # Initialize Chrome driver
    chrome_options = webdriver.ChromeOptions()
    if settings.CHROME_DRIVER_PATH:
        driver = webdriver.Chrome(executable_path=settings.CHROME_DRIVER_PATH, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)
    
    wait = WebDriverWait(driver, 20)
    
    try:
        # Create output directory for debug images
        os.makedirs('calibration_output', exist_ok=True)
        
        # Navigate to page
        print(f"Accessing {settings.CADESP_URL}")
        driver.get(settings.CADESP_URL)
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        # Test different enhancement settings
        enhancement_configs = [
            # Base configuration
            {'stronger': False, 'contrast': 2.0, 'threshold': 128},
            # Higher contrast
            {'stronger': True, 'contrast': 2.5, 'threshold': 120},
            # Lower threshold for darker images
            {'stronger': True, 'contrast': 2.0, 'threshold': 100},
            # Higher contrast with median threshold
            {'stronger': True, 'contrast': 3.0, 'threshold': 128},
            # Extreme processing for difficult cases
            {'stronger': True, 'contrast': 4.0, 'threshold': 140},
        ]
        
        for i in range(5):  # Test 5 different captchas
            print(f"\nTesting captcha {i+1}/5:")
            
            # Get captcha image
            captcha_img = wait.until(EC.presence_of_element_located(
                (By.ID, settings.CAPTCHA_IMG_ID)))
            
            # Take screenshot of captcha
            print("Taking screenshot of captcha...")
            original_img = CaptchaService._process_screenshot(captcha_img)
            
            # Save original image
            original_path = f'calibration_output/original_{i+1}.png'
            original_img.save(original_path)
            print(f"Saved original image to {original_path}")
            
            for config_idx, config in enumerate(enhancement_configs):
                print(f"\nTesting enhancement config {config_idx + 1}:")
                print(f"Contrast: {config['contrast']}, Threshold: {config['threshold']}, Stronger: {config['stronger']}")
                
                # Create a copy of the original image for processing
                test_img = original_img.copy()
                
                # Process image with current configuration
                test_img = test_img.convert('L')
                test_img = ImageEnhance.Contrast(test_img).enhance(config['contrast'])
                test_img = test_img.point(lambda x: 0 if x < config['threshold'] else 255, '1')
                
                if config['stronger']:
                    test_img = test_img.filter(ImageFilter.MedianFilter(size=3))
                    if test_img.size[0] < 100 or test_img.size[1] < 30:
                        width = int(test_img.size[0] * 1.5)
                        height = int(test_img.size[1] * 1.5)
                        test_img = test_img.resize((width, height), Image.LANCZOS)
                
                # Test each PSM mode
                results = []
                for psm in CaptchaService.PSM_MODES:
                    config_str = f'--psm {psm} --oem 3'
                    text = pytesseract.image_to_string(test_img, config=config_str)
                    result = ''.join(filter(str.isalnum, text))
                    results.append((psm, result))
                    print(f"PSM {psm}: {result}")
                
                # Create and save debug image
                debug_img = create_debug_image(original_img, test_img, results)
                debug_path = f'calibration_output/debug_{i+1}_config_{config_idx+1}.png'
                debug_img.save(debug_path)
                print(f"Saved debug image to {debug_path}")
            
            # Wait a bit before getting next captcha
            time.sleep(2)
            
            # Refresh page to get new captcha
            driver.refresh()
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            
    finally:
        driver.quit()
        
    print("\nCalibration complete! Check the 'calibration_output' directory for results.")

if __name__ == '__main__':
    calibrate_captcha()
