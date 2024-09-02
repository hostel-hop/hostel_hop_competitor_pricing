from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import json
import re
import time

class ScriptAnalyzer:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.setup_driver()

    def setup_driver(self): 
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)

    def analyze_scripts(self):
        self.driver.get(self.url)
        time.sleep(5) 
        scripts = self.driver.find_elements(By.TAG_NAME, 'script')
        for i, script_element in enumerate(scripts):
            script_content = script_element.get_attribute('innerHTML')
            print(f"Script {i} content: {script_content[:500]}") 
            
            if script_content:
                try:
                    self.driver.execute_script(script_content)
                    time.sleep(2)  
                    html_after_script = self.driver.page_source
                    print(f"HTML after script {i}: {html_after_script[:500]}")  
                except Exception as e:
                    print(f"Error executing script {i}: {e}")

    def extract_price_info(self):
        price_elements = self.driver.find_elements(By.CSS_SELECTOR, '.price')  
        prices = [price.text for price in price_elements]
        print("Extracted prices:", prices)

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def run_analysis(self):
        try:
            self.analyze_scripts()
            self.extract_price_info()
        finally:
            self.close_driver()

#=======================================================
                    
def read_urls(file_path):
    with open(file_path, 'r') as file:
        urls = file.read().splitlines()
    return urls

if __name__ == "__main__":
    count = 1
    urls = read_urls('matched_urls.txt')
    for i, url in enumerate(urls):
        if i >= count:
            analyzer = ScriptAnalyzer(url)
            analyzer.run_analysis()
            break
