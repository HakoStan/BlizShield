import logging
import os
import importlib.machinery
import importlib.util

from ..Framework import utils


logger = logging.getLogger(__name__.split('.')[-1])


ALLOWED_TYPES = ["python"]

class Core:
    def __init__(self,
        plugins_to_run: list[dict],
        write_mode: str) -> None:
        logger.info("Initiating Core")

        self.__write_mode = write_mode
        self.__plugins_to_run = plugins_to_run

    async def __run_python_plugin(self, 
        name: str, 
        config: dict = {}) -> None:
        plugins_dir = utils.get_plugins_dir("python")
        subfolders = [ f.name.lower() for f in os.scandir(plugins_dir) if f.is_dir() ]
        if name.lower() not in subfolders:
            raise ValueError(f"Plugin {name.lower()} does not exists!")

        loader = importlib.machinery.SourceFileLoader(name, os.path.join(plugins_dir, name, "main.py"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        mod.run(config)

    async def run(self) -> None:
        for plugin in self.__plugins_to_run:
            if "type" not in plugin.keys() or "name" not in plugin.keys():
                raise ValueError("Plugin Descriptor Should Contain 'name' and 'type' fields")
            plugin_type = plugin["type"].lower()
            if plugin_type not in ALLOWED_TYPES:
                raise ValueError(f"Plugin Type {plugin_type} is not allowed")
            if plugin_type == "python":
                if "config" in plugin.keys():
                    await self.__run_python_plugin(plugin["name"], plugin["config"])
                else:
                    await self.__run_python_plugin(plugin["name"])
        # TODO :: Add Write To File

