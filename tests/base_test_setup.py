
from pathlib import Path
import sys
from typing import Union

sys.path.insert(0, str(Path(__file__).parent.parent.joinpath("src")))

if True:
    from badger_config_handler import Badger_Config_Base, Badger_Config_Section


class Base_Test():
    TEST_DATA_DIR = Path(__file__).parent.joinpath("data")
    TEST_CONFIG_PATH: Path
    # print(TEST_DATA_DIR)
    
    def __init__(self, config_file_name: str) -> None:
        """

        Parameters
        ----------
        config_file_name : str
            `config.json` or `config.yaml`
        """
        self.TEST_CONFIG_PATH = self.TEST_DATA_DIR.joinpath(config_file_name)


    def setup_data_dir(self, remove_config_file=True):
        self.TEST_DATA_DIR.mkdir(exist_ok=True)

        if remove_config_file:
            if self.TEST_CONFIG_PATH.exists():
                self.TEST_CONFIG_PATH.unlink()


    def get_test_config(self, config_file_path: Union[Path, str] = None) -> Badger_Config_Base:
        class Sub_Section(Badger_Config_Section):
            section_var: str
            section_int: int

            def setup(self):
                self.section_var = "section"
                self.section_int = 20

        class base(Badger_Config_Base):
            my_var: str
            my_int: int

            def setup(self):
                self.my_var = "test"
                self.my_int = 50

            sub_section = Sub_Section(section_name="sub")
            
        
        if config_file_path is None:
            config_file_path = self.TEST_CONFIG_PATH

        return base(config_file_path=config_file_path, root_path=self.TEST_DATA_DIR)

    ####################################################################################################


    def get_config_dict(self, conf: Badger_Config_Base):
        data = {}
        
        for key, value in conf.to_dict(convert_to_native=False).items():
            
            if isinstance(value,Badger_Config_Section):
                value = self.get_config_dict(value)
                
            data[key] = value
                
        return data
    ####################################################################################################


    # test save to file
    def test_save_config(self, ):
        self.setup_data_dir()
        conf = self.get_test_config()
        conf.save()


    # test load from file
    def test_load_config(self, ):
        self.setup_data_dir()
        conf = self.get_test_config()
        conf.load()

    # compared loaded data to original


    def test_compare_config(self, ):
        self.setup_data_dir()
        conf = self.get_test_config()

        start_conf = self.get_config_dict(conf)
        conf.save()
        conf.load()
        end_conf = self.get_config_dict(conf)

        assert start_conf == end_conf


    # test sync

    # ? test unsupported data type ?
