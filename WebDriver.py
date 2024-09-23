from selenium import webdriver
from time import sleep

class WebDriver:
    def __init__(self):
        driver_options = webdriver.ChromeOptions()
        driver_options.headless = False
        self.driver = webdriver.Chrome(options=driver_options)
    
    def get(self, url:str) -> str:
        self.driver.implicitly_wait(2)
        self.driver.get(url)
        #page_content = self.driver.page_source
        sleep(5)
        html = self.driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
        self.driver.quit()
        return html