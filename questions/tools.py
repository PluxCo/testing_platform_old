import os
import pickle


class Settings(dict):
    """
    Singleton class for managing application settings.
    """

    def __init__(self):
        super().__init__()

    def __new__(cls):
        """
        Ensure that only one instance of the Settings class is created (Singleton pattern).

        Returns:
            Settings: The instance of the Settings class.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(Settings, cls).__new__(cls)
        return cls.instance

    def setup(self, filename, default_values: dict):
        """
        Set up the settings instance with a filename and default values.

        Args:
            filename (str): The name of the file to store/retrieve settings.
            default_values (dict): Default values for the settings.
        """
        self.file = filename
        self._update_handlers = []

        # Set default values for the settings
        for k, v in default_values.items():
            self.setdefault(k, v)

        # Create the file if it doesn't exist
        if not os.path.exists(filename):
            with open(filename, "wb") as file:
                pickle.dump(dict(), file)

        # Load settings from the file
        with open(filename, "rb") as file:
            self.update(pickle.load(file))

    def update_settings(self):
        """
        Update the settings in the file and trigger update handlers.
        """
        with open(self.file, "wb") as file:
            pickle.dump(self.copy(), file)

        # Trigger update handlers
        for handler in self._update_handlers:
            handler()

    def add_update_handler(self, handler):
        """
        Add a handler function to be called when settings are updated.

        Args:
            handler: The handler function to be added.
        """
        if hasattr(self, "_update_handlers"):
            self._update_handlers.append(handler)
        else:
            self._update_handlers = [handler]
