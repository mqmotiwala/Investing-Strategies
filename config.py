import yaml 

# access User Settings
class UserSettings:
    USER_SETTINGS_FILE = 'user_settings.yaml'

    def __init__(self):
        with open(self.USER_SETTINGS_FILE, 'r') as f:
            self._data = yaml.safe_load(f)

    def __getattr__(self, name):
        return self._data.get(name)