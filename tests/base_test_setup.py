
import pytest
from pathlib import Path
from typing import Union
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.joinpath("src")))

if True:
    from badger_config_handler import Badger_Config_Base, Badger_Config_Section


class Base_Test():
    TEST_DATA_DIR = Path(__file__).parent.joinpath("data")
    config_file_name: str = "config"
    # TEST_CONFIG_PATH: Path = TEST_DATA_DIR.joinpath(config_file_name)

    @pytest.mark.dependency(name="dependecies_present")
    def test_dependecies_present(self):
        assert self.ensure_dependencies_present()

    def ensure_dependencies_present(self):
        """base test to ensure all dependecies are present

        overwrite in sub class if needed

        Return
        ------
        bool:
            all dependencies present
        tuple[bool, str]:
            optional tuple with str for error messages

        """
        return True

    def get_test_config_path(self):
        return self.TEST_DATA_DIR.joinpath(self.config_file_name)

    def setup_data_dir(self, remove_config_file=True):
        self.TEST_DATA_DIR.mkdir(exist_ok=True)

        if remove_config_file:
            if self.get_test_config_path().exists():
                self.get_test_config_path().unlink()

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
            my_none: str

            my_list: list
            my_dict: dict

            sub_section: Sub_Section

            def setup(self):
                self.my_var = "test"
                self.my_int = 50
                self.my_none = None

                self.my_list = [1, 2]
                self.my_dict = {"first": "derp", "2": 2.5}

                self.sub_section = Sub_Section(section_name="sub")

        if config_file_path is None:
            config_file_path = self.get_test_config_path()

        return base(config_file_path=config_file_path, root_path=self.TEST_DATA_DIR)

    ####################################################################################################

    def get_config_dict(self, conf: Badger_Config_Base):
        data = {}

        for key, value in conf.to_dict(convert_to_native=False).items():

            if isinstance(value, Badger_Config_Section):
                value = self.get_config_dict(value)

            data[key] = value

        return data

    ####################################################################################################

    @pytest.mark.dependency(name="save_config", depends=["dependecies_present"])
    def test_save_config(self, ):
        self.setup_data_dir()
        conf = self.get_test_config()
        conf.save()

    ####################################################################################################
    # test load from file
    ####################################################################################################

    @pytest.mark.dependency(depends=["dependecies_present"])
    def test_load_config(self, ):
        self.setup_data_dir()
        conf = self.get_test_config()
        conf.load()

    ##################################################
    # compare loaded data to original
    ##################################################

    # TODO check
    @pytest.mark.dependency(depends=["dependecies_present"])
    def test_compare_config(self, ):
        self.setup_data_dir()
        conf = self.get_test_config()

        start_conf = self.get_config_dict(conf)
        conf.save()
        conf.load()
        end_conf = self.get_config_dict(conf)

        assert start_conf == end_conf

    ####################################################################################################
    # test sync
    ####################################################################################################

    ##################################################
    # test cases where no config file was found
    ##################################################
    @pytest.mark.dependency(depends=["dependecies_present"])
    def test_sync_no_file_create(self):
        print(self.config_file_name)

        self.setup_data_dir(remove_config_file=True)
        conf = self.get_test_config()

        assert conf.sync() == True

    @pytest.mark.dependency(depends=["dependecies_present"])
    def test_sync_no_file_error(self):
        print(self.config_file_name)

        self.setup_data_dir(remove_config_file=True)
        conf = self.get_test_config()

        with pytest.raises(FileNotFoundError) as e_info:
            conf.sync(auto_craete=False)

    ##################################################
    # test cases where config file exists
    ##################################################
    @pytest.mark.dependency(depends=["dependecies_present", "save_config"])
    def test_sync_file_exist(self):
        self.setup_data_dir(remove_config_file=True)

        # Create a config file
        conf = self.get_test_config()
        conf.save()

        ##############################
        conf = self.get_test_config()

        assert conf.sync() == False

    ####################################################################################################
    # test default None values overwrite
    ####################################################################################################

    @pytest.mark.dependency(depends=["dependecies_present"])
    def test_null_default_handled_right(self):
        self.setup_data_dir()
        conf = self.get_test_config()

        conf.sync()
        start_conf = self.get_config_dict(conf)

        conf.my_none = "test"
        conf.save()

        mid_conf = self.get_config_dict(conf)

        conf = self.get_test_config()
        conf.load()

        end_conf = self.get_config_dict(conf)

        print()
        print("start_conf")
        print(start_conf)

        print()
        print("mid_conf")
        print(mid_conf)

        print()
        print("end_conf")
        print(end_conf)

        assert start_conf != mid_conf
        assert mid_conf == end_conf
        assert start_conf != end_conf

    @pytest.mark.dependency(depends=["dependecies_present"])
    def test_path_support_functions(self):
        self.setup_data_dir(remove_config_file=True)

        class Base(Badger_Config_Base):
            my_path: Path

            def setup(self):
                self.my_path = Path("sub/path")

            def post_process(self):
                self.my_path = self.make_absolute_to_root(
                    relative_path=self.my_path,
                    enforce_in_root=True
                )

            def pre_process(self):
                self.my_path = self.make_relative_to_root(
                    absolute_path=self.my_path
                )

        conf = Base(
            config_file_path=self.get_test_config_path(),
            root_path=self.TEST_DATA_DIR
        )

        conf.sync()
        start_path = conf.my_path

        conf.pre_process()

        mid_path = conf.my_path

        conf.post_process()

        mid_path2 = conf.my_path

        conf.post_process()

        end_path = conf.my_path

        print()
        print("start_conf")
        print(start_path)

        print()
        print("mid_conf")
        print(mid_path)

        print()
        print("mid_path2")
        print(mid_path2)

        print()
        print("end_conf")
        print(end_path)

        assert start_path != mid_path
        assert mid_path != end_path
        assert start_path == end_path
        assert mid_path2 == end_path

    # ? test unsupported data type ?
