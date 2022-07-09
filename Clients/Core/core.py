import logging
import json
from multiprocessing.sharedctypes import Value
import os
import importlib.machinery
import importlib.util
import asyncio

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
        self.__results = []

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

        result = {"Plugin": plugin["plugin"], "Type": plugin_type, "Name": plugin["name"]}
        if plugin_type == "python":
            if "config" in plugin.keys():
                result["Config"] = plugin["config"]
                result["Result"] = await self.__run_python_plugin(plugin["plugin"], plugin["config"])
            else:
                result["Result"] = await self.__run_python_plugin(plugin["plugin"])

        self.__results.append(result)

        if "next" in plugin.keys():
            for next_plugin in plugin["next"]:
                self.__run_plugin(next_plugin)

        run_next_if_true = False
        run_next_if_false = False
        for res in result["Result"]:
            if res["status"]:
                run_next_if_true = True
            else:
                run_next_if_false = True

        if run_next_if_true:
            if "next_if_true" in plugin.keys():
                for next_plugin in plugin["next_if_true"]:
                    self.__run_plugin(next_plugin)

        if run_next_if_false:
            if "next_if_false" in plugin.keys():
                for next_plugin in plugin["next_if_false"]:
                    self.__run_plugin(next_plugin)

    async def run(self) -> None:
        coros = []
        for plugin in self.__flow:
            if not plugin:
                break
            coros.append(self.__run_plugin(plugin))
        done, pending = await asyncio.wait(coros)
        for tsk in done:
            try:
                await tsk
            except Exception as e:
                print("Exception raised in one of the tasks:", repr(e))
        logger.info("Exporting all results")
        await self.__export_results(self.__results)
