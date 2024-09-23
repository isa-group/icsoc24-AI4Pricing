import google.generativeai as genai
from google.generativeai import GenerationConfig
from bs4 import BeautifulSoup
from bs4.element import Tag
import os

class GeminiAPI:
    def __init__(self, html):
        self.html = html
        self.selected_table = self._get_selected_table()
        genai.configure(api_key=os.getenv('GOOGLE_AI_STUDIO'))
        self.model = 'gemini-1.5-flash'
        self.config = GenerationConfig(temperature=0.0)
    
    def get_plans(self) -> str:
        prompt = self._get_plans_promt()
        return self._make_request(prompt)
    
    def get_features(self, plans_names:str) -> str:
        prompt = self._get_features_prompt(plans_names)
        return self._make_request(prompt)
    
    def get_usage_limits(self, plans_names:str, features_response:str) -> str:
        features_yaml = self._post_process(features_response)
        prompt = self._get_usage_limits_prompt(plans_names, features_yaml)
        return self._make_request(prompt,)
    
    def get_add_ons(self) -> str:
        prompt = self._get_add_ons_prompt()
        return self._make_request(prompt)
    
    def _get_selected_table(self) -> str:
        soup = BeautifulSoup(self.html, 'lxml')
        tables = soup.find_all('table')
        
        if len(tables) > 0:
            selected_table = tables[0]
            for table in tables:
                if len(table) > len(selected_table):
                    selected_table = table
                    
            if selected_table is not None and selected_table.parent is not None:
                original_table = selected_table

                while selected_table.parent and len([e for e in list(selected_table.parent.children) if isinstance(e, Tag)]) == 1:
                    selected_table = selected_table.parent
                
                if len(selected_table.parent.find_all('table')) > 1:
                    selected_table = selected_table.parent
                else:
                    selected_table = original_table
        else:
            selected_table = self.html
        
        return selected_table
    
    @staticmethod
    def _post_process(response_text:str) -> str:
        response_text = response_text.strip()
        
        if response_text.startswith("\n"):
            response_text = response_text[1:]
        
        if response_text.endswith("\n"):
            response_text = response_text[:len(response_text)-1]
            
        response_text = response_text.strip()
        
        if response_text.startswith("```yaml"):
            response_text = response_text.replace("```yaml", '')
        
        if response_text.endswith("```"):
            response_text = response_text.replace("```", '')
        
        response_text = response_text.strip()
        
        if response_text.startswith("\n"):
            response_text = response_text[1:]
        
        if response_text.endswith("\n"):
            response_text = response_text[:len(response_text.strip())-1]
        
        return response_text.strip()
        
    def _make_request(self, prompt:str) -> str:
        response = genai.GenerativeModel(self.model, generation_config=self.config).generate_content(contents=[prompt])
        
        return self._post_process(response.text)
    
    def _get_plans_promt(self) -> str:
        prompt = f'''
        For the following HTML code, extract the plans. For each plan indicates its description (if any), its price, its price with discount if its possible to pay it annually. If the plan has no description, indicate it. If the plan has no annual discounted price, indicate it. You should also use the same unit and currency for all the plans and all the prices. You must assume that if the plan has no annual discounted price, it is not possible to pay it annually; therefore the monthly price should always be higher than the annual price. 
        For example for two plans the first one called 'Basic' with a description 'This is a basic plan' and a price of 100€ per month, and a discounted price of 960€ per year (80€ per month when paid annually), and the second one called 'Pro' with no description, a price of 200€ per month, and no discounted price, the YAML output would be:
        plan: Basic
        description: This is a basic plan
        monthly_price: 100
        annual_price: 80
        unit: user/month
        currency: EUR
        ---
        plan: Pro
        description: null
        monthly_price: 200
        annual_price: null
        unit: user/month
        currency: EUR
        ---
        The HTML code is:
        {self.html}
        '''
        return prompt
    
    def _get_features_prompt(self, plans_names:str) -> str:
        prompt = f'''
        For the following HTML code, extract the features. For each feature indicates its name, its description (if any), its plans. If the feature has no description, indicate it. Features offered as a limited trial or demo for a specific plan, thus not providing any permanent access, will not be included within the feature set of such plan. E.g. Slack’s 2023 “Free” plan does not include “file history”. 
        For example for two features the first one called 'Record audio notes' with a description 'Record audio notes' and available in the 'Free' and 'Essentials' plans, and the second one called 'Play audio notes' with no description, and available in the 'Free' plan, the YAML output would be:
        feature: Record audio notes
        description: Record audio notes
        plans:
        - Free
        - Essentials
        ---
        feature: Play audio notes
        description: null
        plans:
        - Free
        ---
        Furthermore, take into account that the plans included for every feature should be one of the following: {plans_names}.
        Finally, you must remove the features that are not really a feature of the SaaS, such as the 'Pricing' feature.
        The HTML code is:
        {self.selected_table}
        '''
        return prompt
    
    def _get_usage_limits_prompt(self, plans_names:str, features_response:str) -> str:
        prompt = f'''
        Update the features list modeled in the YAML file with the usage limits and add-ons. For each feature, indicate its usage limits and add-ons. If the feature has no usage limits or add-ons, indicate it. If the feature has usage limits or add-ons, indicate them. For example, for a fictional feature called 'Users' with a description 'The amount of users you can have' and available in the 'Free', 'Essentials', 'Team' and 'Agency' plans, and with an additional information that is shown in a HTML box that states 10 users with Free plan, 100 users with Essentials plan and unlimited users with Team and Agency plans and with a cost of 10€ per new user above the limit for Free and Essentials plan and a cost of 15€ per new user above the limit for Team and Agency plans, the YAML output would be:
        feature: People
        description: The amount of people you can have
        plans:
        - Free: 10 people
        - Essentials: 100 people
        - Team: 10000000000 people
        - Agency: 10000000000 people
        add_on:
        - Free: 10 €/person
        - Essentials: 10 €/person
        - Team: 15 €/person
        - Agency: 15 €/person
        ---
        If the feature extra information is a boolean value (like a checkbox), it should not be included in the 'add_on' field and the feature should not be updated in any way. For example, for a fictional feature called 'File history' with a description 'Access to file history' and available in the 'Free' and 'Essentials' plans, and with an additional information that is shown in a HTML box that states 'Included' with Free plan, the YAML output would be:
        feature: File history
        description: Access to file history
        plans:
        - Free
        - Essentials
        add_on: null
        ---
        If you found a limit that says 'Unlimited', 'No limit' or similar, please change it to use the value 10000000000.
        It is mandatory that you follow the following template for the HTML code:
        feature: {{feature_name}}
        description: {{feature_description}}
        plans:
        - {{plan_name}}
        add_on: {{add_on}}
        where {{feature_name}} is the name of the feature, {{feature_description}} is the description of the feature, {{plan_name}} is the name of the plan where the feature is available, and {{add_on}} is the add_on information of the feature.
        Take into account that {{plan_name}} should be one of the following: {plans_names} and that the {{plan_name}} could be accompanied by a number to establish the limit of use for that plan and JUST ONE word to describe the unit, e.g. 10 users, 10 user, 10 GB, 10 GB/user, etc.
        The {{add_on}} field should be the cost of adding more of that feature, if there is no cost, this field should be null. The format is mandatory to be formed with a number to establish the price and JUST ONE word to describe the currency associated, e.g. 10 €/user, 10 €/GB, 100 €, etc and should be linked to each of the plans that appears in the 'plans' attribute (it will follow a similar structure).
        Please, use the features modeled in the YAML file as the features to update. You must ensure that that update the 'plans' attribute do not add any price or currency information. On the other hand you must ensure that only price and currency information is shown in the 'add_on' attribute. Therefore, don't forget that currency symbols (e.g. $, €, £, ¥, ₣, etc.) shows info that must be in the 'add_on' attribute and cannot appear on the 'plans' attribute. Lastly, both the 'plans' and 'add_on' attributes must follow the pattern {{plan_name}}: {{value}} where {{value}} is a number accompanied by just one word: a currency or a unit depending if we are talking about an 'add_on' or a 'plan' respectively ({{add_on_value}}={{number}} {{currency}}/{{plans_value}}={{number}} {{unit}}).
        The features modeled in the YAML file are:
        {features_response}
        The HTML code where you can find the information to update the attributes of the features of the previous list is:
        {self.selected_table}
        '''
        return prompt
    
    def _get_add_ons_prompt(self) -> str:
        prompt = f'''
        You need to find add_ons that can be subscribed to the plans of the SaaS. Do not search for add-ons inside the feature-plans table. Add-ons are different, they are like extra features that are not included within the plans but that can be subscribed to. For each add_on, indicate the plans for which it is available, the price of the add_on, and the currency of the add_on. If the add_on has no price, indicate it. If the add_on has no currency, indicate it. For example, for a fictional add_on called 'AI Editor' available for the plans 'Team' and 'Agency' with a price of 10€ per month and a description that says 'Enable the AI Editor to leverage your power', the YAML output would be:
        add_on: AI Editor
        description: Enable the AI Editor to leverage your power
        plans:
        - Team
        - Agency
        price: 10
        unit: user/month
        ---
        The add_on structure is:
        add_on: {{add_on_name}}
        description: {{add_on_description}}
        plans:
        - {{plan_name}}
        price: {{price}}
        unit: {{unit}}
        where {{add_on_name}} is the name of the add_on, {{add_on_description}} is the description of the add_on, {{plan_name}} is the name of the plan where the add_on is available, {{price}} is the price of the add_on, and {{unit}} is the unit of the add_on. If there is any information missing, indicate it as null. The {{add_on_name}} is mandatory and cannot be neither null nor repeated.
        In case you do not find any add-on, return a yaml file with 0 add-ons like:
        ```yaml
        null
        ```
        The HTML of the whole page where you should locate the add-ons is:
        {self.html}
        '''
        return prompt