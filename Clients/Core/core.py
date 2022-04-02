import logging
import json
from multiprocessing.sharedctypes import Value
import os
import importlib.machinery
import importlib.util

from ..Framework import utils
from ..Exporters.elastic import ElasticExporter
from ..Exporters.file import FileExporter


logger = logging.getLogger(__name__.split('.')[-1])


ALLOWED_TYPES = ["python"]
ALLOWED_EXPORTERS = ["file", "elastic"]
ALLOWED_CONDITION_TYPE = ["eq", "gt", "ge", "lt", "le"]
# eq - equal, gt - greather than, ge - greather or equal, lt - less than, le - less or equal

class Core:
    def __init__(self,
        flow: list[dict],
        exporters: list) -> None:
        logger.info("Initiating Core")

        self.__exporters = []
        # Initialize Exporters
        for exporter in exporters:
            exporter_type = exporter["type"]
            if exporter_type not in ALLOWED_EXPORTERS:
                raise Exception(f"Exporter {exporter_type} is not allowed!")
            if exporter_type == "elastic":
                self.__exporters.append(ElasticExporter(**exporter["config"]))
            if exporter_type == "file":
                self.__exporters.append(FileExporter(**exporter["config"]))
        self.__flow = flow

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

    async def __export_results(self, results: list) -> None:
        for exporter in self.__exporters:
            exporter.export(results)

    async def __run_plugin(self, plugin: dict) -> dict:
        if "type" not in plugin.keys() or "name" not in plugin.keys() or "plugin" not in plugin.keys():
            raise ValueError("Plugin Descriptor Should Contain 'name', 'type' and 'plugin' fields")
        plugin_type = plugin["type"].lower()
        if plugin_type not in ALLOWED_TYPES:
            raise ValueError(f"Plugin Type {plugin_type} is not allowed")

        result = {"Plugin": plugin["plugin"], "Type": plugin_type}
        if plugin_type == "python":
            if "config" in plugin.keys():
                result["Config"] = plugin["config"]
                result["Result"] = await self.__run_python_plugin(plugin["plugin"], plugin["config"])
            else:
                result["Result"] = await self.__run_python_plugin(plugin["plugin"])
        return result

    async def __get_plugin_by_name_from_flow(self, name: str) -> dict:
        for plugin in self.__flow:
            if plugin['name'] == name:
                return plugin
        raise ValueError(f"No plugin named {name} in the flow")

    async def __get_conditions_result(self, conditions: dict, result: dict) -> bool:
        final_result = False
        condition = conditions
        if "type" not in condition.keys() or "key" not in condition.keys() or "value" not in condition.keys():
            raise ValueError("Key type, key and value is a must in a condition")
        if condition["type"] not in ALLOWED_CONDITION_TYPE:
            raise ValueError(f"Allowed condition types are: {str(ALLOWED_CONDITION_TYPE)}")
        
        if type(result["Result"]) == list:
            for single_result in result["Result"]:
                if condition["type"] == "eq":
                    if single_result[condition["key"]] == condition["value"]:
                        final_result = True
                        break
                if condition["type"] == "gt":
                    if single_result[condition["key"]] > condition["value"]:
                        final_result = True
                        break
                if condition["type"] == "ge":
                    if single_result[condition["key"]] >= condition["value"]:
                        final_result = True
                        break
                if condition["type"] == "lt":
                    if single_result[condition["key"]] < condition["value"]:
                        final_result = True
                        break
                if condition["type"] == "le":
                    if single_result[condition["key"]] <= condition["value"]:
                        final_result = True
                        break
        else:
            raise ValueError("Got result that is not of type list .. This is not supported yet")

        if "or" in condition.keys():
            return final_result or await self.__get_conditions_result(condition["or"], result)
        if "and" in condition.keys():
            return final_result and await self.__get_conditions_result(condition["and"], result)
        return final_result

    async def __get_next_plugin(self, plugin: dict, result: dict) -> dict:
        if "next" not in plugin.keys():
            logger.info(f"Plugin {plugin['name']} got no next. So, its the last plugin to run")
            return None
        next = plugin["next"]
        if type(next) == str:
            return await self.__get_plugin_by_name_from_flow(next)
        elif type(next) != list:
            raise ValueError(f"Wrong next type in the plugin {plugin['name']}")

        for next_plugin in next:
            if "conditions" not in next_plugin.keys():
                raise ValueError("next_plugin value must have conditions key")
            if "true" not in next_plugin.keys() and "false" not in next_plugin.keys():
                raise ValueError(f"Must have true/false results for the condition of next of {plugin['name']}")
            if await self.__get_conditions_result(next_plugin["conditions"], result):
                if "true" in next_plugin.keys():
                    return await self.__get_plugin_by_name_from_flow(next_plugin["true"])
                logger.info(f"Plugin {plugin['name']} was the last one to run")
                return None
            if "false" in next_plugin.keys():
                return await self.__get_plugin_by_name_from_flow(next_plugin["false"])
            logger.info(f"Plugin {plugin['name']} was the last one to run")
            return None

    async def run(self) -> None:
        results = []
        plugin = self.__flow[0]
        while True:
            if not plugin:
                break
            result = await self.__run_plugin(plugin)
            results.append(result)
            plugin = await self.__get_next_plugin(plugin, result)
        logger.info("Exporting all results")
        await self.__export_results(results)
