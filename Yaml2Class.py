import re, yaml

class Yaml2Class:
    def __init__(self, saas_name: str):
        self.saas_name = saas_name
    
    @staticmethod
    def _fix_yaml_syntax(yaml_content: str) -> str:
        fixed_lines = []
        
        for line in yaml_content.splitlines():
            # Check for colons in values that are not quoted and contain spaces
            if ':' in line and not re.match(r'^\s*#', line):  # Skip commented lines
                key_value = line.split(':', 1)
                key = key_value[0].strip()
                value = key_value[1].strip()
                
                # Add quotes around values with colons or spaces that aren't quoted
                if ' ' in value or ':' in value:
                    if not (value.startswith('"') and value.endswith('"')) and '"' not in value:
                        value = f'"{value}"'
                    elif not (value.startswith("'") and value.endswith("'")) and "'" not in value:
                        value = f"'{value}'"
                    else:
                        value = value.replace(':', '-')
                
                line = f"{key}: {value}"
            
            if line.strip() == '':
                continue
            
            fixed_lines.append(line)
        
        if fixed_lines[-1] == '---':
            fixed_lines.pop()
        
        return '\n'.join(fixed_lines)
    
    def parse_plans(self, yaml_data: str) -> str:
        yaml_data = self._fix_yaml_syntax(yaml_data)


        plans_response = yaml.load_all(yaml_data, Loader=yaml.CFullLoader)
        
        plans_names_list = [plan['plan'] for plan in plans_response if plan and 'plan' in plan and plan['plan'] is not None]
        plans_names = "', '".join(plans_names_list)
        plans_names = f"'{plans_names}'"
        
        return plans_names