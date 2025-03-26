import os
import yaml 
from datetime import datetime as dt, timedelta as td

# access User Settings
class UserSettings:
    USER_SETTINGS_FILE = 'user_settings.yaml'

    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        user_settings_path = os.path.join(script_dir, self.USER_SETTINGS_FILE)
        
        with open(user_settings_path, 'r') as f:
            self._data = yaml.safe_load(f)
            
        self._set_analysis_start_date()
            
    def _set_analysis_start_date(self):
        self.ANALYSIS_START_DATE = min(
            [dt.strptime(grant["grant_date"], "%Y-%m-%d").date() for grant in self.grants]
        ) - td(days=7)

    def __getattr__(self, name):
        return self._data.get(name)