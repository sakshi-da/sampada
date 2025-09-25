import os
import time
import re
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageEnhance, ImageFilter
from selenium.webdriver.common.keys import Keys
import pytesseract
from io import BytesIO


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

TEMP_CAPTCHA_IMAGE_FILE = "temp_sampada_captcha_raw.png"
PROCESSED_CAPTCHA_IMAGE_FILE = "temp_sampada_captcha_processed.png"



def preprocess_image(img):
    img = img.convert('L') # Convert to grayscale

    width, height = img.size
    img = img.resize((width * 3, height * 3), Image.LANCZOS) # Scaled up 3x for better detail

    threshold = 225
    img = img.point(lambda p: 0 if p < threshold else 255)

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.0) 
    img = img.filter(ImageFilter.SHARPEN)
    
    img = img.filter(ImageFilter.MedianFilter(size=7))

    return img

def process_and_read_captcha(driver, captcha_image_element_locator, captcha_input_field_locator):
    captcha_text = ""
    
    try:
        if os.path.exists(TEMP_CAPTCHA_IMAGE_FILE):
            os.remove(TEMP_CAPTCHA_IMAGE_FILE)
        if os.path.exists(PROCESSED_CAPTCHA_IMAGE_FILE):
            os.remove(PROCESSED_CAPTCHA_IMAGE_FILE)
        time.sleep(2) 

        captcha_element = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(captcha_image_element_locator)
        )
        base64_image_data = captcha_element.get_attribute("src")
            
        if base64_image_data and base64_image_data.startswith("data:image"):
            base64_data = base64_image_data.split(',')[1]
            img_bytes = base64.b64decode(base64_data)
            img_raw = Image.open(BytesIO(img_bytes))
        else:
            captcha_element_png = captcha_element.screenshot_as_png
            img_raw = Image.open(BytesIO(captcha_element_png))

        img_raw.save(TEMP_CAPTCHA_IMAGE_FILE)
        img_processed = preprocess_image(img_raw)
        img_processed.save(PROCESSED_CAPTCHA_IMAGE_FILE)
        tesseract_config = '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        captcha_text = pytesseract.image_to_string(img_processed, config=tesseract_config).strip()
            
        captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text) 
            
        if captcha_text:
            captcha_input_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(captcha_input_field_locator)
            )
            captcha_input_field.clear()
                
            captcha_input_field.send_keys(captcha_text.upper())
            print(f"Entered '{captcha_text.upper()}' into CAPTCHA field.")  
            return captcha_text.upper()
        else:
            print("Failed to extract any text from the CAPTCHA image after OCR.")
                
    except Exception as e:
        print(f"An error occurred during CAPTCHA processing : {e}")
        import traceback
        traceback.print_exc()


def login():
    username_field_locator = (By.ID, "username")
    password_field_locator = (By.ID, "password")
    captcha_image_locator = (By.XPATH, "//img[contains(@src, 'data:image')]") 
    captcha_input_field_locator = (By.ID, "captchaStr")
    login_button_locator = (By.XPATH, "//button[contains(., 'Login')]") 
    
    for attempt in range(1, 11):
        print(f"Login attempt {attempt}/10")
        
        try:
            # Refresh the page to get a new captcha for each attempt
            if attempt > 1:
                driver.refresh()
                WebDriverWait(driver, 20).until(EC.presence_of_element_located(username_field_locator))

            # Fill in username and password
            username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located(username_field_locator))
            username_field.send_keys("sakshi494")
            password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located(password_field_locator))
            password_field.send_keys("ballu12345@S")

            solved_text = process_and_read_captcha(driver, captcha_image_locator, captcha_input_field_locator)
            time.sleep(5)
            if solved_text:
                login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(login_button_locator))
                login_button.click()
                time.sleep(5)
                # Check if the login was successful by looking for a post-login element
                post_login_element_locator = (By.ID, 'SearchDocument')
                WebDriverWait(driver, 15).until(EC.element_to_be_clickable(post_login_element_locator))
                print("Login successful!")
                return True
            else:
                print(" Captcha could not be solved. retrying....")
                time.sleep(2)
        except Exception as e:
            print(f"An error occurred during login attempt {attempt}: {e}")
            print("Refreshing page and trying again...")
            time.sleep(2)
    print(f"Failed to log in after 10 attempts. Exiting.")
    return False
    
def other_details():
    other_details_button_locator = (By.ID, 'P2000_SEARCH_DOC_TYPE_1')
    other_details_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(other_details_button_locator))
    other_details_button.click()
    time.sleep(5)

    district_locator = (By.ID, 'P2000_DISTRICT')
    district_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(district_locator))
    district_button.send_keys("Jabalpur")
    time.sleep(5)

    current_financial_year = (By.XPATH, '//*[@id="CurrentFinancialYear1"]')
    current_financial_year_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(current_financial_year))
    current_financial_year_button.click()
    time.sleep(5)

    deed_type = (By.XPATH, '//*[@id="P2000_DEED_TYPE"]/div/div/div[3]/input')
    deed_type_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(deed_type))
    deed_type_input.send_keys("Conveyance")
    deed_type_input.send_keys(Keys.ENTER)
    print("entered conveyance")
    time.sleep(5)
    for attempt in range (1,11):
        print(f"Second CAPTCHA attempt {attempt}/10")
        try:
            captcha_image_locator = (By.XPATH, "/html/body/app-root/div/app-layout/div/div/div/div/app-search-document/div[3]/div[2]/div[2]/div/fieldset/div[4]/div[1]/div/div[3]/div/img")
            captcha_input_field_locator = (By.XPATH, "/html/body/app-root/div/app-layout/div/div/div/div/app-search-document/div[3]/div[2]/div[2]/div/fieldset/div[4]/div[1]/div/div[1]/div/input")

            solved_text = process_and_read_captcha(driver, captcha_image_locator, captcha_input_field_locator)
            time.sleep(2)
            if solved_text:
                print("captcha solved")
                
                # Wait for the loading overlay to disappear to prevent click interception
                print("Waiting for loading overlay to disappear...")
                WebDriverWait(driver, 20).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay"))
                )
                print("Loading overlay is gone.")
                
                search2_locator=(By.XPATH, '/html/body/app-root/div/app-layout/div/div/div/div/app-search-document/div[3]/div[2]/div[2]/div/fieldset/div[4]/div[2]/div/button[1]')
                search2_button= WebDriverWait(driver,10).until(EC.element_to_be_clickable(search2_locator))
                search2_button.click()
                print("search button clicked")
                time.sleep(4)
                property_locator = (By.XPATH, '/html[1]/body[1]/app-root[1]/div[1]/app-layout[1]/div[1]/div[1]/div[1]/div[1]/app-search-document[1]/div[3]/div[2]/div[2]/div[1]/fieldset[2]/div[1]/div[2]/div[1]/div[2]/div[1]/table[1]/tbody[1]/tr[1]/td[9]/span[1]/mat-icon[1]')
                property_button= WebDriverWait(driver, 30).until(EC.element_to_be_clickable(property_locator))
                print("Search successful. Opened property details.")
                time.sleep(2)
                property_button.click()   
                print("opened pdf")
                return True
            else:
                print("WAS NOT ABLE TO SOLVE THE CAPTCHA")
                time.sleep(2)
        except Exception as e:
            print(f"An error occurred during second CAPTCHA attempt {attempt}: {e}")
            try:    
                print("waiting for eror msg")
                error_msg= (By. XPATH , "/html[1]/body[1]/div[3]/div[1]/div[6]/button[1]")
                error_ok= WebDriverWait(driver,10).until(EC.element_to_be_clickable(error_msg))
                error_ok.click()
                print("clicked ok")
                time.sleep(1)
            except Exception as msg_e:
                print(f"was not able to find error msg : {msg_e}")
    print(f"Failed to complete search after 10 attempts.")
    return False
   

if __name__ == "__main__":
     
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.maximize_window()
        website_url = "https://sampada.mpigr.gov.in/#/clogin"
        driver.get(website_url)    
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username"))) 
        time.sleep(2)
        
        english_button_locator = (By.XPATH, "//a[contains(text(), 'English')]")
        english_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(english_button_locator)
        )
        english_button.click()
        time.sleep(5)
        login()
 
        search_button_locator = (By.XPATH, '//*[@id="SearchDocument"]/a')
        search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(search_button_locator))
        search_button.click()
        time.sleep(5)

        other_details()     

        time.sleep(15)

    except Exception as e:
        print(f"An unexpected error occurred during the main script execution: {e}")
        import traceback
        traceback.print_exc()

    
