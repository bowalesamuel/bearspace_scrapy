import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from gallery_listings.items import GalleryListingsItem
import re


class BearspaceSpider(scrapy.Spider):
    name = 'bearspace'
    allowed_domains = ['bearspace.co.uk']
    start_urls = ['http://www.bearspace.co.uk/']

    def parse(self, response):
        url = 'http://www.bearspace.co.uk/purchase'
        yield SeleniumRequest(url=url, callback=self.parse_result)
        
    def parse_result(self, response):
        driver = response.request.meta['driver']
        wait = WebDriverWait(driver, 10)
        load_more_button = driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]")[0]
        driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
        driver.execute_script("arguments[0].click()", load_more_button)
        
        while driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]"):
            try:
                driver.execute_script("arguments[0].scrollIntoView()", driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]")[0])
                driver.execute_script("arguments[0].click()", driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]")[0])
            except:
                pass
            pass
        
        wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@data-hook='product-list-grid-item']")))
        listings = driver.find_elements(by=By.XPATH, value="//li[@data-hook='product-list-grid-item']")[:]
        items = GalleryListingsItem()
        for i in range(len(listings)):
            wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@data-hook='product-list-grid-item']")))
            driver.execute_script("arguments[0].scrollIntoView();",  driver.find_elements(by=By.XPATH, value="//li[@data-hook='product-list-grid-item']")[i])
            driver.find_elements(by=By.XPATH, value="//li[@data-hook='product-list-grid-item']")[i].click()
            wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[@data-hook='product-title']")))
            title_element_text = driver.find_elements(by=By.XPATH, value="//h1[@data-hook='product-title']")[0].text
            description_element_text = driver.find_elements(by=By.XPATH, value="//pre[@data-hook='description']")[0].text
            small_case_description_text = str(description_element_text).lower()
            price = driver.find_elements(by=By.XPATH, value="//span[@data-hook='formatted-primary-price']")[0].text
            try:
                measure = re.findall(r'(.*)cm', small_case_description_text)[0].split("x")
            except:
                try:
                    measure = re.findall('(\d+(\.\d+|)\s?x\s?\d+(\.\d+|)(\s?x\s?\d*(\.?\d+|))?)', small_case_description_text)[0].split("x")
                except:
                    measure = ['None', 'None']
            description = re.split(r'\d', description_element_text)[0]
            formatted_price = price.replace("£", "")
            items["url"] = driver.current_url
            items["title"] = title_element_text
            if str(measure[0]).lower().endswith("w"):
                items["height_cm"] = str(measure[-1]).lower().replace("h", "")
                items["width_cm"] = str(measure[0]).lower().replace("w", "")
            else:
                items["height_cm"] = measure[0].split("height")[-1].split("cm")[0].split("x")[0]
                items["width_cm"] = measure[-1].split("x")[-1]
            items["media"] = description
            items["price_gbp"] = formatted_price

            driver.back()
            wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@data-hook='product-list-grid-item']")))
            time.sleep(3)
            yield items
        
