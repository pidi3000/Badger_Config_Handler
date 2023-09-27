# Badger_Config_Handler
A python library for handling code-declared and file-defined settings.

Supports saving to JSON and YAML files.


# Data types

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
Save config to file

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

NOTE: the property [parent_section](#parent_section) is NOT available during this

---

### pre_process()
Pre process values before [save()](#save)

useful for:
- converting unsupported data type to a [native](#native) or [supported](#supported) type
- converting absolute paths to relative (keeps them short in the config file)

---

### post_process()
post process values after [load()](#load)

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
