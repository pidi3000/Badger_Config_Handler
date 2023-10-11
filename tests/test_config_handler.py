

import importlib
from base_test_setup import Base_Test


class Test_Json(Base_Test):
    config_file_name: str = "config.json"
    
class Test_Yaml(Base_Test):
    config_file_name: str = "config.yaml"
    
    
    def ensure_dependencies_present(self):
        library_name = "yaml"

        try:
            importlib.import_module(library_name)
            library_installed = True
        except ImportError:
            library_installed = False

        return library_installed, f"The '{library_name}' library is not installed."
