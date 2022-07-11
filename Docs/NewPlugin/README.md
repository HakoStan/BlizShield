# How to create a new plugin
1. locate the root directory of the project and navigate to ```Client\Plugins\```
   1. Currently we only support python plugins (although this can be expanded easily)
   ```Clients\Plugins\Python```
2. Add a directory for the new plugin. For the sake of the example we'll call it `NewPlugin`
3. Every python plugin must have 3 files in its directory
   1. `config.json` - a file explaning the configuration for the plugin in JSON format. Example:
   ```json
    {
        "subnet": "",
        "possible_ports": ""
    }
   ```
   By this config, Blizshield knows that the plugin should receive 2 arguments - subnet and possible_ports.
   2. `__init__.py` - Empty file, must be there for the python convention
   3. `main.py` - the main logic python file, implementing your plugin. blizshield will load this file and expect for one function of this format:
   ```python
   def run(config: dict) -> list[dict]
   ```
   The method should be called run, get a config dict and return a list of results as a list of dictionaries.
   4. Suggestion - add a "status" key to the each result dict.
4. After adding this files, implement the logic of your plugin and you are good to go.