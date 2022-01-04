import logging
import json
import os
import importlib.machinery
import importlib.util

from ..Framework import utils
from ..Exporters import elastic


logger = logging.getLogger(__name__.split('.')[-1])


RESULTS_FILE = r"C:\\temp\\Results.json"
ALLOWED_TYPES = ["python"]
ALLOWED_WRITE_MODES = ["file", "elastic"]

class Core:
    def __init__(self,
        plugins_to_run: list[dict],
        write_mode: str) -> None:
        logger.info("Initiating Core")

        if write_mode.lower() not in ALLOWED_WRITE_MODES:
            raise Exception(f"Write Mode {write_mode} is not allowed!")
        self.__write_mode = write_mode
        self.__plugins_to_run = plugins_to_run

    async def __run_python_plugin(self,
        name: str, 
        config: dict = {}):
        plugins_dir = utils.get_plugins_dir("python")
        subfolders = [ f.name.lower() for f in os.scandir(plugins_dir) if f.is_dir() ]
        if name.lower() not in subfolders:
            raise ValueError(f"Plugin {name.lower()} does not exists!")

        loader = importlib.machinery.SourceFileLoader(name, os.path.join(plugins_dir, name, "main.py"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        logger.info(f"Running Module {name} with configuration {config}")
        return mod.run(config)

    async def __write_results(self, results: list) -> None:
        if self.__write_mode.lower() == "file":
            with open(RESULTS_FILE, "w") as f:
                f.write(json.dumps(results))
        elif self.__write_mode.lower() == "elastic":
            elastic.export(results)
    
    async def run(self) -> None:
        results = []
        for plugin in self.__plugins_to_run:
            if "type" not in plugin.keys() or "name" not in plugin.keys():
                raise ValueError("Plugin Descriptor Should Contain 'name' and 'type' fields")
            plugin_type = plugin["type"].lower()
            if plugin_type not in ALLOWED_TYPES:
                raise ValueError(f"Plugin Type {plugin_type} is not allowed")

            result = {"Plugin": plugin["name"], "Type": plugin_type}
            if plugin_type == "python":
                if "config" in plugin.keys():
                    result["Config"] = plugin["config"]
                    result["Result"] = await self.__run_python_plugin(plugin["name"], plugin["config"])
                else:
                    result["Result"] = await self.__run_python_plugin(plugin["name"])
            results.append(result)

        await self.__write_results(results)
