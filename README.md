# Badger_Config_Handler
A python library for handling code-declared and file-defined settings.

Supports saving to JSON and YAML files.

# Installation

Install from [PyPi](https://pypi.org/project/badger-config-handler/)

```
pip install badger-config-handler
```

# Rules and limitations

1. settings are declared in the class and defined in [setup()](#setup-1)
2. settings **MUST** be declared with a type hint.  example: `my_var: int`
3. settings can only be of [allowed data type](#allowed-data-types)
4. settings not declared in code are ignored in the config file (and are removed on the next save, same for commented out settings)
5. settings can be `None` if they are set to null in the config, regardles of the type hint
6. settings without a default value set in [setup()](#setup-1) are not saved to the config file, but they can still be set from the config file
7. The [root_path](#root_path) and [parent_section](#parent_section) propertys are NOT available in [setup()](#setup-1)



# Example config

``` Python
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
    
    sub_section: Sub_Section # NOT Badger_Config_Section

    def setup(self):
        self.my_var = "test"
        self.my_int = 50
        self.my_none = None
        
        self.sub_section = Sub_Section(section_name="sub")

config = My_Base(
    config_file_path="path/to/config.json",
    root_path="path/to/project/root"
)

config.save()
config.load()
config.sync()
```


# Allowed data types

## native
the file handlers have native support for these types and are used as is,
no conversion is done on these values
- string
- int
- float
- bool
- None / null

---
## supported
### Badger_Config_Section
converted using 
- serialize: `{VAR}.to_dict()` 
- de-serialize: `Badger_Config_Section.from_dict({VAR})`

### datetime.datetime
converted using 
- serialize: `{VAR}.isoformat()` 
- de-serialize: `datetime.fromisoformat({VAR})`

### pathlib.Path
converted using 
- serialize: `str({VAR})` 
- de-serialize: `pathlib.Path({VAR})`

---
## Collections

NOTE:

It is recommended to use a [Config Section](#config-section) instead of Collections.

If collections are used items should be of [native](#native) type only,
if they are not of [native](#native) type they are serialized but can NOT be de-serialize.

Code using these values must handle these cases.

### dict

### list


---
---
---
# Config Base

---
## Property's

---

### _config_file_path
> path to the config file

---


### ALLOWED_FILE_TYPES
> all allowed file extensions

---
---
## Function's

---

### setup()
see [Config_Section.setup()](#setup-1)

---

### save()
Saves config to file

steps:

1. [pre_process()](#pre_process)
2. save to file
3. [post_process()](#post_process)

---

### load()
Load config from file

---

### sync()
Sync config with file

runs: `load()` - `save()` - `load()`

this adds new config fields to the file or removes old ones


---
---
---

# Config Section
---
## Property's

---

### section_name
> name of the current section

---

### root_path
> by default the project root path or overridden by the parent section

---

### parent_section
> reference to the parent section (if it exists)

---
---
## Function's

---

### setup()
Replacement for `__init__()`

should be used to set default values

NOTE: the propertys [root_path](#root_path) and [parent_section](#parent_section) are NOT available during this

---

### pre_process()
Pre process values before [save()](#save)

Warning: the function should be written in a way that running it multiple times in a row doesn't cause problems

useful for:
- converting unsupported data type to a [native](#native) or [supported](#supported) type
- converting absolute paths to relative (keeps them short in the config file)

---

### post_process()
post process values after [load()](#load)

Warning: the function should be written in a way that running it multiple times in a row doesn't cause problems

useful for:
- creating unsupported data type from [native](#native) or [supported](#supported) type
- converting relative paths to absolute (keeps them short in the config file)

---

### to_dict(bool)
converts all values to a dictionary 

**Parameters:**

| param             | type | required | default |
|-------------------|------|----------|---------|
| convert_to_native | bool |          | True    |

---

### from_dict()
Reconstruct Config Section from dictionary

**Parameters:**

 | param          | type                           | description                                                                                                                        | required | default |
|----------------|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------|----------|---------|
| data           | dict\[str, [native](#native)\] | the dict representation of this section (as generated from [to_dict(True)](#to_dictbool) )                                         | x        |         |
| safe_load      | bool                           | ! UNTESTED ! <br> True -> Only variables that already exist in the class are set (uses `hasattr`) <br> False -> New variables can be set from config file |          | True    |
| danger_convert | bool                           | ! UNTESTED ! <br> For details see docs of `_native_to_var()`                                                                        |          | False   |


---
