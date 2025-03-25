import os
import yaml 

# access User Settings
class UserSettings:
    USER_SETTINGS_FILE = 'user_settings.yaml'

    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        user_settings_path = os.path.join(script_dir, self.USER_SETTINGS_FILE)
        
        with open(user_settings_path, 'r') as f:
            self._data = yaml.safe_load(f)

    def __getattr__(self, name):
        return self._data.get(name)