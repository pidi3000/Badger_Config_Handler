
from __future__ import annotations
from abc import ABC
from typing import Union

########################################
# Supported data type
########################################
from pathlib import Path
from datetime import datetime

########################################


DEBUG_init = False
DEBUG_from_dict = False
DEBUG_to_dict = False

DEBUG__native_to_var = False
DEBUG_save = False
DEBUG_load = False
DEBUG__load_from_file = False
DEBUG__call_on_sections = False

DEBUG_root_path = False

BADGER_NONE = object()

# ? Not adding support for comments for now
# use ruamel.yaml lib for comments
# https://pypi.org/project/ruamel.yaml/
# https://yaml.readthedocs.io/en/latest/overview.html
# https://stackoverflow.com/questions/7255885/save-dump-a-yaml-file-with-comments-in-pyyaml
# // TODO handle settings commented out
# // TODO keep them in the file as comments and don't re-add them with default value

# ! EXPERIMENTAL collections (dict, list, tuple, set) support
# * stil recommended to use subsection for dicts, or only native type vars (maybe add checks for that)
# * lists seem fine, still need more testing
# ! tuple's DO NOT work, could get it working not really worth it though
# ! set's DO NO work in JSON
# * set's work in yaml, but it adds '!!set' to the yaml


class _Config_data_handler(ABC):
    ##################################################
    # Instance Deserialization
    ##################################################
    def from_dict(
        self,
        data: dict[str, Union[str, int, float, bool]],
        safe_load: bool = True,
        danger_convert: bool = False
    ) -> Badger_Config_Section:
        """Reconstruct from dict

        Overrides the this objects values with the ones set in `data`

        used to deserialize section from config file

        Parameters
        ----------
        data : dict[str, Union[str, int, float, bool]]
            the dict representation of this section (as generated from `to_dict()`)
            Certain constraints apply, see Data constraints section below

        safe_load : bool, optional
            # ! UNTESTED ! \n
            by default True\n
            True -> Only variables that already exist in the class are set (uses `hasattr(self, var_name)`)\n
            False -> New variables can be set from config file 

        danger_convert: bool, optional
            # ! UNTESTED ! \n
            by default False
            For details see docs of `_native_to_var()`

        Returns
        -------
        Badger_Config_Section
            returns this instance (after loading values), makes in line actions easier


        Data constraints
        ----------------
        keys : str
            must be the name of a variable staticly defined in the class !not the instance!, for undefined keys see safe_load\n

        values : Union[str, int, float, bool]
            must be of native type.\n
            Values can be converted to other supported datatypes (see calss doc),\n
            The converted to type is defined by the type hint of the variable in the class (identefied with variable name/key)

            for unsupported types see `danger_convert` parameter
        """

        if DEBUG_from_dict:
            print("DEBUG from dict", "-"*50)
            print("-"*20)
            print(self)
            print("-"*20)
            print(data)
            print()

        for s_name, s_value in data.items():
            # print(f"Key: {s_name}, value: {s_value}")
            # a TODO check dict keys as well (make it optional)

            # if not safe_load or hasattr(self, s_name):
            if hasattr(self, s_name):
                if DEBUG_from_dict:
                    print()
                    print("+"*50)
                    print(f"Key: {s_name} \tvalue: {s_value}")

                    print()
                    print("Annotations start")
                    print("all: ", self.__annotations__)

                target_type = self.__annotations__.get(
                    s_name, BADGER_NONE)

                print()

                if target_type is BADGER_NONE:
                    raise TypeError(
                        f"No type hinting set for setting: {s_name}")

                if s_value is not None:
                    # create instance and then get the type
                    # is needed in cases where lists or dicts have content annotated
                    # like this: my_var: list[int]
                    # turn annotation into class
                    target_type = type(target_type())

                else:
                    target_type = None

                if DEBUG_from_dict:
                    # print("post: var:", add_padding(target_type, 20),
                    #     "type:", type(target_type))

                    print("target type: ", target_type)
                    print()

                s_value = self._native_to_var(
                    var_native=s_value,
                    target_type=target_type,
                    # class_var_target=class_var,
                    var_name=s_name,
                    danger_convert=danger_convert
                )

                self.__setattr__(s_name, s_value)

        if DEBUG_from_dict:
            print("DEBUG END from dict", "-"*50)
            print("-"*20)
        return self

    ##################################################
    # Instance Serialization
    ##################################################
    def _get_vars(self, object, input_dict: dict = None, convert_to_native: bool = False, danger_convert: bool = False) -> dict:
        """Convert object's vars to dict

        builds a dict containg all "public vars" of `object`\n
        object can have a list variable named "_exclude_vars_" that contains names off vars
        to exclude from the return dict.\n

        Vars  are considered "public" when:
            - don't start with "_" or "__"
            - is not 'callable'
            - var name is not in "_exclude_vars_" list

        Parameters
        ----------
        object : object
            bassicly any object

        input_dict : dict, optional
            The dict to add to or override values in, by default empty `dict`

        convert_to_native : bool, optional
            by default False
            True -> variable values are converted to a native type if needed

        danger_convert : bool, optional
            # ! UNTESTED ! \n
            by default False
            For details see docs of `_var_to_native()`

        Returns
        -------
        dict
            dict containing all "public vars" of `object`

        Examples
        --------

        With the following class:
        ```
        class Temp():
            _exclude_vars_ = "id" # or ["id"]
            _private_var = "private"
            id = 3
            name = "temp"
            datetime = datetime("01.01.2000") # simplified for demonstration
        ```
        running `Temp.to_dict()` results in the dict:
        ```
        {
            "name": "temp",
            datetime: datetime("01.01.2000") # remains as datetime object
        }
        ```
        """
        var_dict = input_dict if isinstance(input_dict, dict) else {}

        # Get exclude vars
        #########################
        exclude_vars = getattr(object, "_exclude_vars_", None)

        if isinstance(exclude_vars, str):
            exclude_vars = list((exclude_vars,))
        elif exclude_vars is None:
            exclude_vars = list()

        # // TODO uncomment
        exclude_vars.append("root_path")
        exclude_vars.append("section_name")
        exclude_vars.append("parent_section")

        # Extract vars
        #########################
        object_vars: dict = vars(object)
        for var_name, var_value in object_vars.items():
            # check if var is excluded
            if exclude_vars is None or var_name not in exclude_vars:
                is_public = not var_name.startswith(("__", "_"))
                is_funciton = callable(var_value)
                is_class_function = isinstance(var_value, classmethod)

                if is_public and not is_funciton and not is_class_function:
                    if convert_to_native:
                        var_dict[var_name] = self._var_to_native(
                            var_value, danger_convert=danger_convert)
                    else:
                        var_dict[var_name] = var_value

        return var_dict

    def _get_class_vars(self):
        return self._get_vars(self.__class__)

    def _get_instance_vars(self):
        return self._get_vars(self)

    # def to_dict(self, include_class_defaults: bool = True, convert_to_native: bool = True) -> dict:
    def to_dict(self, convert_to_native: bool = True) -> dict:
        """Turn this section into a dict with native datatypes only

        Inlcudes the class defults and instance overrides / additions

        for more details about what is included in the dict,\n
        see `_get_vars()`

        Dict is build like this
        ```
        dict = self._get_vars(self.__class__, None, convert_to_native=True)
        dict = self._get_vars(self, dict, convert_to_native=True)
        ```

        Parameters
        ----------
        convert_to_native: bool, optinal
            by default True,\n
            True -> convert all values to native type

        Returns
        -------
        dict
            dictionary containg all variables
        """

        var_dict = {}
        if True:  # include_class_defaults:
            var_dict = self._get_vars(
                self.__class__, input_dict=var_dict, convert_to_native=convert_to_native)

        var_dict = self._get_vars(
            self, input_dict=var_dict, convert_to_native=convert_to_native)

        if DEBUG_to_dict:
            print("DEBUG to dict:")
            print(var_dict)
            print()

        return var_dict

    ##################################################
    # native type conversion
    # convert data to/from config native type (str, int, etc.)
    ##################################################
    def _is_native_type(self, var=BADGER_NONE, type: type[any] = BADGER_NONE) -> bool:
        """Check if var or type ar of native type

        Parameters
        ----------
        var : any, optional
            any variable value, by default None
        type : type[any], optional
            any data type, by default None

        Returns
        -------
        bool
            True -> when is  of native type

        Raises
        ------
        ValueError
            Either `var` of `type` must be set
        """
        native_types = (str, int, float, bool)  # and None

        if var is not BADGER_NONE:
            # if var is None:
            #     return True
            # print(f"DEBUG NATIVE: var: {var}")
            return isinstance(var, native_types)
            # return isinstance(var, native_types) if var is not None else True
        if type is not BADGER_NONE:
            # return issubclass(var, native_types) # ! TEST check dis works
            for n_type in native_types:
                if type is n_type:
                    return True
            return False

        raise ValueError("Either 'var' or 'type' parameter must be set")

    def _var_to_native(
        self,
        var: Union[str, int, float, bool, None, datetime, Path, Badger_Config_Section],
        danger_convert: bool = False
    ) -> Union[str, int, float, bool, None]:
        """Convert var to a native type

        Parameters
        ----------
        var : Union[str, int, float, bool, None, datetime, Path, Badger_Config_Section]
            var of supported type (see class doc for supported vars)
        danger_convert : bool, optional
            True -> try to stringify unsupported vars using `str(var)`

        Returns
        -------
        Union[str, int, float, bool, None]
            value of var in a native type

        Raises
        ------
        TypeError
            var is of unsupported type and danger_convert is `False`
        """
        if var is None or self._is_native_type(var=var):
            return var

        if isinstance(var, Badger_Config_Section):
            return var.to_dict()

        if isinstance(var, datetime):
            # 'hours', 'minutes', 'seconds', 'milliseconds' and 'microseconds'
            # return var.isoformat(timespec="microseconds")
            return var.isoformat()

        if isinstance(var, Path) or danger_convert:
            return str(var)

        # ! EXPERIMENTAL dict support
        if isinstance(var, (dict, list)):
            return self._collection_to_native(collection=var, danger_convert=danger_convert)

        raise TypeError(f"Unsupported var type: '{type(var)}'")

    def _collection_to_native(self,
                              collection: Union[dict, list, tuple, set],
                              danger_convert: bool = False):

        if isinstance(collection, list):
            new_collection = list()
            for item in collection:
                new_collection.append(
                    self._var_to_native(
                        var=item,
                        danger_convert=danger_convert
                    )
                )
            return new_collection
        elif isinstance(collection, dict):
            new_collection = dict()
            for key, item in collection.items():
                new_collection[key] = self._var_to_native(var=item,
                                                          danger_convert=danger_convert
                                                          )

            return new_collection
        elif isinstance(collection, tuple):
            modified_items = tuple(self._var_to_native(
                var=item, danger_convert=danger_convert) for item in collection)

            return modified_items
        elif isinstance(collection, set):
            modified_items = set(self._var_to_native(
                var=item, danger_convert=danger_convert) for item in collection)
            return modified_items

        raise TypeError("Unsupported collection type")

    def _native_to_var(
        self,
        var_native: Union[str, int, float, bool, None],
        target_type: Union[str, int, float, bool, None, Path, Badger_Config_Section],
        # class_var_target: Union[str, int, float, bool, datetime, Path, Badger_Config_Section],
        var_name: str = None,
        danger_convert: bool = False,
    ) -> any:
        """convert native to target type

        Parameters
        ----------
        var_native : Union[str, int, float, bool, None]
            the var value of native type

        target_type : Union[str, int, float, bool, None, datetime, Path, Badger_Config_Section]
            supported type to convert `var` to

        var_name : str, optional
            Name of the var in the instance , by default None

        danger_convert : bool, optional
            by default False\n
            True -> try to creat instance of unsupported `target_type` using constructor\n
                like this `target_type(var_native)`

        Returns
        -------
        any
            instancce of target_type with the value of `var_native`

        Raises
        ------
        TypeError
            can't craete Badger_Config_Section instance from `var_native`
        ValueError
            `var_native` can't be converted to `target_type`
        TypeError
            `danger_convert` is `False` and `target_type` is unsupported 
        """

        # target_type = type(class_var_target)
        if DEBUG__native_to_var:
            print(f"\nvar_name: {var_name}\n"
                  f"var_native: {var_native} - {type(var_native)}"
                  f"\ntarget_type: {target_type}\n"
                  )

        # if not isinstance(var_native, (str, int, float, bool)):
        #     raise TypeError("var_native must be a str, int, float or bool")

        # value is None
        if target_type is None or target_type is type(None):
            return None

        # already has the right type
        if isinstance(var_native, target_type):
            return var_native

        # Is a config section
        if issubclass(target_type, Badger_Config_Section):
            if DEBUG__native_to_var:
                print("-"*50)
                print("DEBUG _native_to_var: native type", type(var_native))
            if not isinstance(var_native, dict):  # TODO make this a bit more elegent
                raise TypeError(
                    f"var_native must be of type 'dict' to create {Badger_Config_Section.__name__} instance")

            #! Must create a instance of target_type() not Badger_Config_Section().
            #! when craeting from Badger_Config_Section the hasattr(self, s_name) check fails (see from_dict())
            #! because the Badger_Config_Section class has no USER variables

            # class_var_target: Badger_Config_Section
            # class_var_target._set_section_name(section_name=var_name)
            # return class_var_target.from_dict(var_native)
            return target_type(section_name=var_name).from_dict(var_native)

        if issubclass(target_type, datetime):
            return datetime.fromisoformat(var_native)

        if self._is_native_type(type=target_type) or issubclass(target_type, Path) or danger_convert:
            try:
                return target_type(var_native)
            except ValueError:
                raise ValueError(
                    f"Can't convert setting '{var_name}' with value '{var_native}' to type '{target_type}'")

        print(f"Native type {type(var_native)}")
        raise TypeError(f"Unsupported target type: '{target_type}'")


class Badger_Config_Section(_Config_data_handler):
    """ Abstract class of a config section

    Create a child class inhereting this to configure a new section in the config file

    native types:       str, int, float, bool, None
    supported types:    datetime.datetime, pathlib.Path, Badger_Config_Section
    supported collections: dict, list
    """

    root_path: Path
    """Absolute Project/Section root path"""

    section_name: str = "DEFAULT"

    _sections: list[Badger_Config_Section]
    parent_section: Badger_Config_Section

    def __init__(self, root_path: Union[Path, str] = None, section_name: str = None) -> None:
        """ !! DO NOT OVERWRITE !!

        overwriting init will break shit, use the `setup()` function instead

        Parameters
        ----------
        root_path : Union[Path, str], optional
            root path of this section, by default root_path of parent section

        section_name : str, optional
            Name of this section, by default name of the var asinged to in th parent section\n
            base example:\n
            ` my_section = Badger_Config_Section()` -> section_name = "my_section"\n
            override example:\n
            ` my_section = Badger_Config_Section(section_name="otehr_section")` -> section_name = "otehr_section"
        """
        # section_name not empty string
        if section_name is not None and section_name.strip():
            self.section_name = section_name
        else:
            self.section_name = "DEFAULT"
            pass

        if DEBUG_init:
            print()
            print("-"*30)
            print(f"setup Badger_Config_Section")
            print("-"*30)
            print(self)
            print(f"self.section_name = {self.section_name}")
            print(f"section_name = {section_name}")
            print()
        self._set_root_path(root_path=root_path)
        if DEBUG_init:
            print("-"*30)
            print()

        try:
            self.setup()
        except NotImplementedError as e:
            pass

    def setup(self):
        """Prepare instance and set config propertys to default values 

        use this instead of overwriting `__init__()`

        Gets called after `__init__`
        """
        raise NotImplementedError("Subclass has not overriden function")

    def __repr__(self) -> str:
        return f"<Badger_Config_Section: {self.section_name} -- {self.__class__.__name__}>"

    def _make_absolute_path(self, path: Union[Path, str]) -> Path:
        """Turn into absolute Path

        Parameters
        ----------
        path : Union[Path, str]
            the (relative) path

        Returns
        -------
        Path
            absolute path using `Path(path).resolve`

        Raises
        ------
        TypeError
            if `path` is not of type `str` or `pathlib.Path`
        """
        # if isinstance(path, Path):
        #     return path.resolve()

        if isinstance(path, (str, Path)):
            return Path(path).resolve()

        raise TypeError(
            "Only instances of 'str' and 'pathlib.Path' are supported")

    def _check_name_set_and_not_default(self, var_name: str) -> bool:
        """Check class var has non default value

        Parameters
        ----------
        var_name : str
            Name of the class var

        Returns
        -------
        bool
            `True` when value set and not default
        """

        # is set
        if hasattr(self, var_name):
            if getattr(self, var_name) != getattr(self.__class__, var_name):
                return True  # Is not class default
        return False

    def _set_section_name(self, section_name: str, force_override: bool = False):
        """Set the section name with conditions

        The new section name will only be set if it wasn't set previously.\n
        In other words if `section_name` is not set or has the class default value

        Parameters
        ----------
        section_name : str
            desired section name
        force_override : bool, optional
            `True` wil ingore check conditionds and override value, by default `False`
        """

        print(f"section_name set = {hasattr(self, 'section_name')}")

        if section_name is None:
            print(f"section_name is None = {section_name}")
            return

        # if hasattr(self, "section_name") and not force_override:
        # if hasattr(self, "section_name"):
        if self._check_name_set_and_not_default('section_name'):
            print(
                f"section_name already set: {self.section_name}, {self.__class__.section_name}")
            if not force_override:
                return
            print(f"section_name force_override")

        self.section_name = section_name

        print(f"section_name = {self.section_name}")
        print(f"section_name set = {hasattr(self, 'section_name')}")

    def _set_root_path(self, root_path: Union[Path, str], force_override: bool = False):
        """Set the root_path with conditions

        The new root_path will only be set if it has no value.

        if `root_path.is_dir()` is true `root_path.parent` is used

        Parameters
        ----------
        root_path : str
            new root_path
        force_override : bool, optional
            `True` wil ingore check conditionds and override value, by default `False`
        """
        if DEBUG_root_path:
            print(f"root_path set = {hasattr(self, 'root_path')}")

        if root_path is None:
            if DEBUG_root_path:
                print(f"root_path is None= {root_path}")
            return

        # if hasattr(self, "root_path") and not force_override:
        if hasattr(self, "root_path"):
            if DEBUG_root_path:
                print(f"root_path already set")
            if not force_override:
                return
            if DEBUG_root_path:
                print(f"root_path force_override")

        # self.root_path = self._make_absolute_path(root_path)
        self.root_path = Path(root_path)

        _was_file = self.root_path.is_dir()

        if not self.root_path.is_dir():
            self.root_path = self.root_path.parent

        if DEBUG_root_path:
            print(f"root_path = {self.root_path}")
            print(f"root_path was dir: {_was_file}")
            print(f"root_path is dir: {self.root_path.is_dir()}")
            print(f"root_path set = {hasattr(self, 'root_path')}")

    ##################################################
    # Section Handling
    ##################################################
    def _update_sections_all(self, parent_section: Badger_Config_Section = None, root_path: Union[Path, str] = None):
        """Update all child sections

        Updates this instances `roo_path` and `parent_section`,
        then updates all child sections.

        This is used to propagate `root_path` and `parent_section`

        WARNING this might not work on dynamicly defined sub sections


        Parameters
        ----------
        parent_section : Badger_Config_Section, optional
            reference to the parent section instance, by default None
        root_path : Union[Path, str], optional
            new root_path, by default None
        """

        self._update_section(
            parent_section=parent_section,
            root_path=root_path
        )

        self._call_on_sections(
            self._update_sections_all.__name__,
            parent_section=self,
            root_path=self.root_path
            # root_path="path"
        )

    def _update_section(self, parent_section: Badger_Config_Section = None, root_path: Union[Path, str] = None):
        """Update this section

        set's the parent section, root path and collects all child sections

        Parameters
        ----------
        parent_section : Badger_Config_Section, optional
            reference to the parent section instance, by default None
        root_path : Union[Path, str], optional
            new root_path, by default None
        """

        self.parent_section = parent_section
        self._set_root_path(root_path=root_path)

        # print(f"DEBUG UPDATE SECTIONS: {self}")
        sections = []
        # TODO  check if this can work with dynamicly added sub sections
        class_vars = self._get_instance_vars()

        # print("\n")
        # print("#"*30)
        # print(self)
        # print("#"*30)
        # print("\n")
        for key, value in class_vars.items():
            # print()
            # print(f"DEBUG SECTIONS: \nvar name: {key}\nvar value: {value}")
            if isinstance(value, Badger_Config_Section) and key != "parent_section":
                # print("\tSection: ", key, value)
                sections.append(value)

        self._sections = sections

    def _call_on_sections(self, func_name: str, *args, **kwargs):
        """Call a function on all child sections

        `*args` and `**kwargs` are directly handed to the function

        Parameters
        ----------
        func_name : str
            Name of a class function
        """
        if isinstance(self._sections, list):
            for section in self._sections:
                if DEBUG__call_on_sections:
                    print(
                        f"\n\nDEBUG CALL ON ALL SECTIONS: \n"
                        f"section: {section}, \n"
                        f"function: {func_name}\n"
                        f"args: {args}\n"
                        f"kwargs: {kwargs}"
                    )
                try:
                    func = getattr(section, func_name)
                    func(*args, **kwargs)
                except NotImplementedError:
                    print(
                        f"NotImplementedError: \nFunction -> {func_name}\nsection->{section}\n")
                    pass

    ##################################################
    # Data pre/post processing
    ##################################################
    def _pre_process_all(self):
        """Pre-process all child sections
        """
        try:
            self.pre_process()
        except NotImplementedError:
            pass

        self._call_on_sections(self._pre_process_all.__name__)

    def pre_process(self):
        """pre Process data if needed

        Gets called before `safe()` to pre process config values.\n
        usefull to make paths relative in the config file but absolute in code.\n
        Can also be used to de-/serialize a custom data type/ class.
        """

        raise NotImplementedError("Subclass has not overriden function")

    def _post_process_all(self):
        """Post-process all child sections
        """
        try:
            self.post_process()
        except NotImplementedError:
            pass

        self._call_on_sections(self._post_process_all.__name__)

    def post_process(self):
        """Post Process data if needed

        Gets called after `load()` to post process config values.\n
        For example make relative paths absolute.
        usefull to make paths relative in the config file but absolute in code.\n
        Can also be used to de-/serialize a custom data type/ class.
        """
        raise NotImplementedError("Subclass has not overriden function")


class Badger_Config_Base(Badger_Config_Section):
    """Config Base class that handles file read/write 

    Config handler for Code declared and file defined settings
    """

    ALLOWED_FILE_TYPES = [
        "yaml",
        "yml",
        "json",
    ]
    """Supported file extensions/types"""

    _config_file_path: Path
    """Absolute config file path"""
    _config_file_type: str = None

    def __init__(self, config_file_path: Union[Path, str], root_path: Union[Path, str] = __file__, section_name: str = None) -> None:
        """ !! DO NOT OVERWRITE !!

        overwriting init will break shit, use the `setup()` function instead

        Parameters
        ----------
        config_file_path : Union[Path, str]
            path to the config file, is created if not exists (including folders)

        root_path : Union[Path, str], optional
            Project root path, by default parent directory of this file (`__file__`)

        section_name : str, optional
            Section Name of values not in a sub section, by default "DEFAULT"
        """
        root_path = self._make_absolute_path(root_path)
        super().__init__(root_path=root_path, section_name=section_name)

        self._config_file_path = self._make_absolute_path(config_file_path)

        self._set_file_type()

    def _set_file_type(self):
        """Set file type var for future checks

        Raises
        ------
        TypeError
            Config file type unsupported
        """
        suffix = self._config_file_path.suffix
        try:
            suffix = suffix.removeprefix(".").lower()
        except AttributeError as e:
            prefix = "."
            if suffix.startswith(prefix):
                suffix = suffix[len(prefix):]

        if suffix in self.ALLOWED_FILE_TYPES:
            self._config_file_type = suffix
            # print("Config file type:", self._config_file_type)
            return

        raise TypeError(
            f"Unsupported file type: '{suffix}', only these are suppported: {self.ALLOWED_FILE_TYPES}")

    def _create_dir(self):
        try:
            # print(self._config_file_path.parent)
            self._config_file_path.parent.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
            # print("Folder is already there")

    ##################################################
    # File saving
    ##################################################

    def save(self):
        """Save config to file

        Pre process's all sub sections and write the values to file
        """
        if DEBUG_save:
            print("-"*50)
            print("DEBUG START SAVE")
            print("-"*50)

        self._update_sections_all()
        self._pre_process_all()

        data = self.to_dict()
        self._save_to_file(data=data)

        self._post_process_all()

        if DEBUG_save:
            print("-"*50)
            print("DEBUG END SAVE")
            print("-"*50)

    def _save_to_file(self, data: dict):
        self._create_dir()

        with open(self._config_file_path, "w") as f:
            if self._config_file_type in ["yaml", "yml"]:
                import yaml  # https://github.com/yaml/pyyaml
                yaml.safe_dump(data, f, indent=4)

            elif self._config_file_type in ["json"]:
                import json
                json.dump(data, f, indent=4)

            else:
                raise TypeError(
                    f"Unsupported file type: '{self._config_file_type}', only these are suppported: {self.ALLOWED_FILE_TYPES}")

    ##################################################
    # File loading
    ##################################################
    def load(self, safe_load: bool = True):
        """Save config to file

        Pre process's all sub sections and write the values to file
        """
        """Load settings from file

        Overrides the default values with the one set in file, \n
        then post process's all sub sections

        Parameters
        ----------
        safe_load
            # ! UNTESTED ! \n
            True -> Only variables that already exist in the class are set (uses `hasattr`)\n
            False -> New variables can be set from config file
        """
        if DEBUG_load:
            print("-"*50)
            print("DEBUG START LOAD")
            print("-"*50)

        data = self._load_from_file()
        self.from_dict(data=data, safe_load=safe_load)

        # try:
        if DEBUG_load:
            print("-"*50)
            print("DEBUG START post_process_all")
            print("-"*50)

        self._update_sections_all()
        self._post_process_all()

        if DEBUG_load:
            print("-"*50)
            print("DEBUG END post_process_all")
            print("-"*50)
        # except NotImplementedError:
        #     pass

        if DEBUG_load:
            print("-"*50)
            print("DEBUG END LOAD")
            print("-"*50)

    def _load_from_file(self, attempt_count=0):
        """Load raw data from config file
        """
        if DEBUG__load_from_file:
            print("-"*50)
            print("DEBUG START LOAD FROM FILE")
            print("-"*50)

        if not self._config_file_path.exists():
            self.save()

        with open(self._config_file_path, "r") as f:
            if self._config_file_type in ["yaml", "yml"]:
                import yaml  # https://github.com/yaml/pyyaml
                data = yaml.safe_load(f)

            elif self._config_file_type in ["json"]:
                try:
                    import json
                    data = json.load(f)
                except json.decoder.JSONDecodeError as e:
                    data = None

            else:
                raise TypeError(
                    f"Unsupported file type: '{self._config_file_type}', only these are suppported: {self.ALLOWED_FILE_TYPES}")

        # print_data(data)
        max_attempts = 2
        if data is None:
            if attempt_count < max_attempts:
                self.save()  # ! FIX could accidently overwrite real data
                data = self._load_from_file(attempt_count=attempt_count+1)
            else:
                raise FileNotFoundError(
                    f"Unable to read from file, might be empty. Path: {str(self._config_file_path)}")

        if DEBUG__load_from_file:
            print("-"*50)
            print("DEBUG END LOAD FROM FILE")
            print("-"*50)

        return data

    def sync(self, safe_load: bool = True):
        """Add new variables to existing config file

        Same as running `load()` then `safe()` then `load()`\n

        Parameters
        ----------
        safe_load : bool, optional
            see `load()` for more details, by default True
        """
        self.load(safe_load=safe_load)
        self.save()
        self.load(safe_load=safe_load)
