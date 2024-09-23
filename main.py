from GeminiAPI import GeminiAPI
from Yaml2Class import Yaml2Class
from WebDriver import WebDriver
from dotenv import load_dotenv

load_dotenv()

URL = 'https://zapier.com/pricing'
SAAS_NAME = 'Zapier'

def main():
    driver = WebDriver()
    html = driver.get(URL)
    gemini = GeminiAPI(html)
    plans_yaml = gemini.get_plans()
    yaml2Class = Yaml2Class(SAAS_NAME)
    plans_names = yaml2Class.parse_plans(plans_yaml)
    features_yaml = gemini.get_features(plans_names)
    usage_limits_yaml = gemini.get_usage_limits(plans_names, features_yaml)
    add_ons_yaml = gemini.get_add_ons()

if __name__ == '__main__':
    main()