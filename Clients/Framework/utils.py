import os
import json
import uuid


def get_plugins_dir(type: str) -> str:
    this_dir, _ = os.path.split(__file__)
    return os.path.join(this_dir, "..", "Plugins", type.capitalize())

def get_data_file_path(name):
    this_dir, _ = os.path.split(__file__)
    return os.path.join(this_dir, "..", "Data", name)


def read_config():
    config_filename = os.environ["CONFIG_FILE"]
    return json.load(open(get_data_file_path((config_filename))))

class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class SingletonID(metaclass=SingletonMeta):
    def __init__(self):
        self.id = str(uuid.uuid4())