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
        # get the webdriver from the response
        driver = response.request.meta['driver']
        # initialize webdriver wait for 10 secondds
        wait = WebDriverWait(driver, 10)
        # find the load more button
        load_more_button = driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]")[0]
        # scroll to the load more button
        driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
        # click the load more button
        driver.execute_script("arguments[0].click()", load_more_button)
        # while loop to click all the load more button until its no more in view
        while driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]"):
            try:
                driver.execute_script("arguments[0].scrollIntoView()", driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]")[0])
                driver.execute_script("arguments[0].click()", driver.find_elements(by=By.XPATH, value="//button[text()[contains(.,'Load More')]]")[0])
            except:
                pass
            pass
        
        # wait until picture items are visible
        wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@data-hook='product-list-grid-item']")))
        # get all the items for purchase
        listings = driver.find_elements(by=By.XPATH, value="//li[@data-hook='product-list-grid-item']")[:]
        # initialize items to use the scrapy pipeline
        items = GalleryListingsItem()
        # for loop to iterate over all listings
        for i in range(len(listings)):
            # wait for listings to be in view
            wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@data-hook='product-list-grid-item']")))
            # scroll to particular listing
            driver.execute_script("arguments[0].scrollIntoView();",  driver.find_elements(by=By.XPATH, value="//li[@data-hook='product-list-grid-item']")[i])
            # click on listing
            driver.find_elements(by=By.XPATH, value="//li[@data-hook='product-list-grid-item']")[i].click()
            # wait until listing title is in view
            wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[@data-hook='product-title']")))
            # get the listing title
            title_element_text = driver.find_elements(by=By.XPATH, value="//h1[@data-hook='product-title']")[0].text
            # get the listing description
            description_element_text = driver.find_elements(by=By.XPATH, value="//pre[@data-hook='description']")[0].text
            # make description lower case
            small_case_description_text = str(description_element_text).lower()
            # get price of listing
            price = driver.find_elements(by=By.XPATH, value="//span[@data-hook='formatted-primary-price']")[0].text
            
            try:
                # using regex to find combination that ends with 'cm'
                measure = re.findall(r'(.*)cm', small_case_description_text)[0].split("x")
            except:
                try:
                    # using regex to find dimension if the first one did not get the dimension
                    measure = re.findall('(\d+(\.\d+|)\s?x\s?\d+(\.\d+|)(\s?x\s?\d*(\.?\d+|))?)', small_case_description_text)[0].split("x")
                except:
                    # fallback if both regex fail
                    measure = ['None', 'None']
            # get description by removing the dimension from it
            description = re.split(r'\d', description_element_text)[0]
            # remove pound symbol from price
            formatted_price = price.replace("£", "")
            # get current url
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


            # webdriver goes to previous page
            driver.back()
            # wait until listings is in view
            wait.until(EC.visibility_of_element_located((By.XPATH, "//li[@data-hook='product-list-grid-item']")))
            # a little wait
            time.sleep(3)
            yield items
        
