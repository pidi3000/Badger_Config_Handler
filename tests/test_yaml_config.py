
import importlib
import pytest

from base_test_setup import Base_Test

TEST_CONFIG_NAME = "config.yaml"


@pytest.mark.dependency()
def test_yaml_lib_installed():
    library_name = "yaml"

    try:
        importlib.import_module(library_name)
        library_installed = True
    except ImportError:
        library_installed = False

    assert library_installed, f"The '{library_name}' library is not installed."


# test save to file
@pytest.mark.dependency(depends=["test_yaml_lib_installed"])
def test_save_config():
    Base_Test(TEST_CONFIG_NAME).test_save_config()


# test load from file
@pytest.mark.dependency(depends=["test_yaml_lib_installed"])
def test_load_config():
    Base_Test(TEST_CONFIG_NAME).test_load_config()


# compared loaded data to original
@pytest.mark.dependency(depends=["test_yaml_lib_installed"])
def test_compare_config():
    Base_Test(TEST_CONFIG_NAME).test_compare_config()


def test_null_default_handled_right():
    Base_Test(TEST_CONFIG_NAME).test_null_default_handled_right()

# test sync

# ? test unsupported data type ?


if __name__ == "__main__":
    test_null_default_handled_right()
