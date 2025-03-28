import os
import yaml 
import shutil
from datetime import datetime as dt, timedelta as td

# access User Settings
class UserSettings:
    USER_SETTINGS_FILE = 'user_settings.yaml'
    USER_SETTINGS_TEMPLATE_FILE = 'user_settings.template.yaml'

    def __init__(self):       
        self.user_settings_path = self._get_absolute_path(self.USER_SETTINGS_FILE)
        self.user_settings_template_path = self._get_absolute_path(self.USER_SETTINGS_TEMPLATE_FILE)
        
        self._copy_template_if_needed()
                
        with open(self.user_settings_path, 'r') as f:
            self._data = yaml.safe_load(f)

    def __getattr__(self, name):
        return self._data.get(name)
        
    def _get_absolute_path(self, file_name):
        """
        generates absolute file path, assuming file_name is in same dir as __file__
        """
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, file_name)
        
    def _copy_template_if_needed(self):
        """
        copies template file into a copy that user can edit without git tracking
        """
        
        if not os.path.exists(self.user_settings_path):
            try:                
                shutil.copy(self.user_settings_template_path, self.user_settings_path)
                print(f"User settings not found. Template copied and renamed to: {self.user_settings_path}")
            except Exception as e:
                print(f"Error copying template: {e}")
        
        