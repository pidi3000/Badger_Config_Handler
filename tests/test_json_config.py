

from base_test_setup import Base_Test

TEST_CONFIG_NAME = "config.json"

# test save to file
def test_save_config():
    Base_Test(TEST_CONFIG_NAME).test_save_config()


# test load from file
def test_load_config():
    Base_Test(TEST_CONFIG_NAME).test_load_config()

# compared loaded data to original


def test_compare_config():
    Base_Test(TEST_CONFIG_NAME).test_compare_config()


# test sync

# ? test unsupported data type ?
