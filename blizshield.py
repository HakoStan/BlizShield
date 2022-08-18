import curses
import logging
import asyncio
import os
import json
import time
from Clients import __main__ as clients
from Clients.Framework import utils

EXIT = " EXIT"
RUN = "RUN"
LOAD = "LOAD FLOW"
CREATE_FLOW = "CREATE FLOW"
PRINT_FLOW = "PRINT FLOW"
MENU = [RUN, LOAD, CREATE_FLOW, PRINT_FLOW, EXIT]
DEFAULT_EXPORTER = {
    "type": "elastic",
    "config": {
        "ip": "rabinovit.ch",
        "port": 9200
    }
}

NO_CONDITION = "RUN ANYWAY"
ONLY_IF_STATUS_TRUE = "RUN ONLY IF STATUS IS TRUE"
ONLY_IF_STATUS_FALSE = "RUN ONLY IF STATUS IS FALSE"


class CursesHandler(logging.Handler):
    def __init__(self, screen):
        logging.Handler.__init__(self)
        self.screen = screen

    def emit(self, record):
        try:
            msg = self.format(record)
            screen = self.screen
            fs = "\n%s"
            try:
                screen.addstr(fs % msg)
            except:
                pass
            screen.box()
            screen.refresh()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            raise


class MenuDisplay:
    def __init__(self, menu):
        # set menu parameter as class property
        self.menu = menu

        self.flow_path = None

        # run curses application
        curses.wrapper(self.mainloop)

    def mainloop(self, stdscr):
        # turn off cursor blinking
        curses.curs_set(0)

        # color scheme for selected row
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        # set screen object as class property
        self.stdscr = stdscr

        # Logger
        mh = CursesHandler(self.stdscr)
        rootLogger = logging.getLogger()

        logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] %(name)-12s: %(levelname)-8s %(message)s")
        mh.setFormatter(logFormatter)
        mh.setLevel(logging.DEBUG)

        rootLogger.addHandler(mh)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

        # get screen height and width
        self.screen_height, self.screen_width = self.stdscr.getmaxyx()

        # specify the current selected row
        current_row = 0

        # print the menu
        self.print_menu(self.menu, current_row)

        while 1:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(self.menu) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if self.menu[current_row] == EXIT and self.confirm("Are you sure you want to exit?"):
                    break
                elif self.menu[current_row] == RUN:
                    self.print_run_menu()
                elif self.menu[current_row] == LOAD:
                    self.print_load_menu()
                elif self.menu[current_row] == CREATE_FLOW:
                    name = self.print_create_flow()
                    if name is not None:
                        self.flow_path = f"{name}.json"
                elif self.menu[current_row] == PRINT_FLOW:
                    if self.flow_path is not None:
                        self.print_flow_menu()
            self.print_menu(self.menu, current_row)

    def print_flow_menu(self):
        self.stdscr.clear()
        self.stdscr.refresh()

        with open(f"Clients/Data/{self.flow_path}", "r") as fd:
            full_config = fd.read()

        config = json.loads(full_config)
        r = 0
        for step in config["core"]["flow"]:
            next_str = ""
            if "next" in step.keys():
                next_str = " ==> "
            self.stdscr.addstr(r, 0, f"{step['name']} ({step['plugin']}) {next_str}")
            r += 1
        self.stdscr.addstr(r, 0, "Press Any Key To Go Back To The Menu...")
        self.stdscr.getch()
        self.stdscr.refresh()

    def get_plugin_config_template(self, plugin):
        with open(f"Clients/Plugins/Python/{plugin}/config.json") as f:
            return json.loads(f.read())

    def get_plugin(self, plugin):
        self.stdscr.clear()
        self.stdscr.refresh()
        curses.echo()

        pd = {"plugin": plugin, "type": "python"}

        self.stdscr.addstr(0, 0, "Plugin Name: ")
        name = self.stdscr.getstr().decode('utf8')
        pd["name"] = name

        plugin_config_template = self.get_plugin_config_template(plugin)
        pd["config"] = {}

        idx = 1
        for k, v in plugin_config_template.items():
            self.stdscr.addstr(idx, 0, f"{k} :")
            val = self.stdscr.getstr().decode('utf8')
            pd["config"][k] = val
            idx += 1

        self.stdscr.refresh()
        return pd

    def get_plugins(self):
        lst = []
        for root, dirs, files in os.walk("Clients/Plugins/Python"):
            for name in dirs:
                if "pycache" in name:
                    continue
                lst.append(name)
        return lst

    def get_next_condition(self):
        self.stdscr.clear()
        self.stdscr.refresh()

        next_condition_menu = [NO_CONDITION, ONLY_IF_STATUS_TRUE, ONLY_IF_STATUS_FALSE]
        current_row = 0
        self.print_menu(next_condition_menu, current_row)
        self.stdscr.addstr(0, 0, "Choose next condition!\n")

        while True:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(next_condition_menu) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                return next_condition_menu[current_row]
            self.print_menu(next_condition_menu, current_row)
            self.stdscr.addstr(0, 0, "Choose next condition!\n")
        return None

    def __get_all_names_from_plugin(self, plugin):
        names = [plugin["name"]]
        if "next" in plugin.keys():
            for n_plug in plugin["next"]:
                names.extend(self.__get_all_names_from_plugin(n_plug))
            return names
        if "next_if_true" in plugin.keys():
            for n_plug in plugin["next_if_true"]:
                names.extend(self.__get_all_names_from_plugin(n_plug))
            return names
        if "next_if_false" in plugin.keys():
            for n_plug in plugin["next_if_false"]:
                names.extend(self.__get_all_names_from_plugin(n_plug))
            return names
        return names

    def _get_all_plugins_names(self, flow):
        plugins = []
        for prev_plugin in flow:
            plugins.extend(self.__get_all_names_from_plugin(prev_plugin))
        return plugins

    def add_plugin_after_plugin(self, plugin, flow):
        self.stdscr.clear()
        self.stdscr.refresh()

        prev_plugins_names = self._get_all_plugins_names(flow)
        current_row = 0
        self.print_menu(prev_plugins_names, current_row)
        self.stdscr.addstr(0, 0, "Choose after which plugin you want to run!\n")

        while True:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(prev_plugins_names) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                prev_plugin_name = prev_plugins_names[current_row]
                how_to_run = self.get_next_condition()
                for idx, prev_plugin in enumerate(flow):
                    if prev_plugin["name"] == prev_plugin_name:
                        if how_to_run == NO_CONDITION:
                            if "next" in flow[idx].keys():
                                flow[idx]["next"].append(plugin)
                            else:
                                flow[idx]["next"] = [plugin]
                        elif how_to_run == ONLY_IF_STATUS_TRUE:
                            if "next_if_true" in flow[idx].keys():
                                flow[idx]["next_if_true"].append(plugin)
                            else:
                                flow[idx]["next_if_true"] = [plugin]
                        elif how_to_run == ONLY_IF_STATUS_FALSE:
                            if "next_if_false" in flow[idx].keys():
                                flow[idx]["next_if_false"].append(plugin)
                            else:
                                flow[idx]["next_if_false"] = [plugin]
                return flow
            self.print_menu(prev_plugins_names, current_row)
            self.stdscr.addstr(0, 0, "Choose after which plugin you want to run!\n")
        return flow

    def add_plugin_to_flow(self, plugin, flow):
        self.stdscr.clear()
        self.stdscr.refresh()

        PARALLEL = "PARALLEL"
        SEQUANTIAL = "SEQUANTIAL"

        PLUGIN_ORDER_MENU = [PARALLEL, SEQUANTIAL]
        current_row = 0
        self.print_menu(PLUGIN_ORDER_MENU, current_row)
        self.stdscr.addstr(0, 0, "Choose plugin order!\n")

        while True:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(PLUGIN_ORDER_MENU) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                order_type = PLUGIN_ORDER_MENU[current_row]
                if order_type == PARALLEL:
                    flow.append(plugin)
                    return flow
                elif order_type == SEQUANTIAL:
                    return self.add_plugin_after_plugin(plugin, flow)
                else:
                    raise Exception("Bad order type")
            self.print_menu(PLUGIN_ORDER_MENU, current_row)
            self.stdscr.addstr(0, 0, "Choose plugin order!\n")
        return None

    def print_add_plugin_menu(self, flow):
        self.stdscr.clear()
        self.stdscr.refresh()

        add_plugin_menu = self.get_plugins()
        current_row = 0
        self.print_menu(add_plugin_menu, current_row)
        self.stdscr.addstr(0, 0, "Choose Plugin!\n")

        while True:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(add_plugin_menu) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                plugin_type = add_plugin_menu[current_row]
                plugin = self.get_plugin(plugin_type)
                flow = self.add_plugin_to_flow(plugin, flow)
                return flow
            self.print_menu(add_plugin_menu, current_row)
            self.stdscr.addstr(0, 0, "Choose Plugin!\n")
        return flow

    def print_create_flow(self):
        self.stdscr.clear()
        self.stdscr.refresh()

        flow = []
        CREATE_FLOW_MENU = ["ADD PLUGIN", "SAVE", "CANCEL"]
        current_row = 0
        self.print_menu(CREATE_FLOW_MENU, current_row)
        self.stdscr.addstr(0, 0, "You are now creating a new FLOW!\n")\

        while True:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(CREATE_FLOW_MENU) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                f = CREATE_FLOW_MENU[current_row]
                if f == "CANCEL":
                    if self.confirm("Are you sure you want to cancel?"):
                        break
                elif f == "SAVE":
                    if self.confirm("Are you sure you want to save the flow?"):
                        if len(flow) == 0:
                            break
                        self.stdscr.clear()
                        self.stdscr.refresh()
                        self.stdscr.addstr(0, 0, "Flow Name: ")
                        self.stdscr.refresh()
                        curses.echo()
                        name = self.stdscr.getstr().decode('utf8')
                        self.stdscr.addstr(1, 0, "Saving the flow, please wait...")
                        self.stdscr.refresh()
                        flow_str = json.dumps({"core": {"flow": flow, "exporters": [DEFAULT_EXPORTER]}}, indent=4, sort_keys=False)
                        with open(f"Clients/Data/{name}.json", "w") as fd:
                            fd.write(flow_str)
                        time.sleep(5)
                        return name
                else:
                    flow = self.print_add_plugin_menu(flow)
            self.print_menu(CREATE_FLOW_MENU, current_row)
            self.stdscr.addstr(0, 0, "You are now creating a new FLOW!\n")
        return None

    def print_load_menu(self):
        self.stdscr.clear()
        self.stdscr.refresh()

        files = []
        for file in os.listdir("Clients/Data"):
            if file.endswith(".json"):
                files.append(file)

        if len(files) == 0:
            self.stdscr.addstr("You don't have any flow files!\n")
            self.stdscr.addstr("Create a new one!\n")
            self.stdscr.addstr("\nPress any key to continue.")
            self.stdscr.getch()
            return

        exit_to_main_menu_text = "EXIT TO MAIN MENU"
        files.append(exit_to_main_menu_text)
        current_row = 0
        self.print_menu(files, current_row)
        while 1:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(files) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                f = files[current_row]
                if f == exit_to_main_menu_text:
                    break
                if self.confirm(f"Are you sure you want to select {f} file?"):
                    self.flow_path = files[current_row]
                    break
            self.print_menu(files, current_row)

    def print_run_menu(self):
        self.stdscr.clear()
        self.stdscr.addstr("Loading...\n")
        self.stdscr.refresh()
        time.sleep(2)
        self.stdscr.clear()
        self.stdscr.refresh()

        loop = asyncio.get_event_loop()
        if self.flow_path is None:
            self.stdscr.addstr("You didn't load any flow file\n")
        else:
            config = json.load(open(utils.get_data_file_path(self.flow_path)))
            try:
                loop.run_until_complete(clients.run_core(config))
            except:
                self.stdscr.clear()
                self.stdscr.refresh()
                self.stdscr.addstr("Exception Raised While Running The Flow!")

        time.sleep(3)
        self.stdscr.clear()
        self.stdscr.refresh()
        try:
            self.stdscr.addstr("\nFinished!!!")
            self.stdscr.addstr("\nPress any key to continue.")
        except:
            pass
        self.stdscr.getch()

    def print_menu(self, menu, selected_row_idx):
        self.stdscr.clear()
        for idx, row in enumerate(menu):
            x = self.screen_width // 2 - len(row) // 2
            y = self.screen_height // 2 - len(menu) // 2 + idx
            if idx == selected_row_idx:
                self.color_print(y, x, row, 1)
            else:
                self.stdscr.addstr(y, x, row)

        # Render status bar
        if self.flow_path:
            statusbarstr = f"Flow Selected: {self.flow_path}"
        else:
            statusbarstr = "Flow Was Not Selected Yet!"
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(self.screen_height-1, 0, statusbarstr)
        self.stdscr.addstr(self.screen_height-1, len(statusbarstr), " " * (self.screen_width - len(statusbarstr) - 1))
        self.stdscr.attroff(curses.color_pair(1))

        self.stdscr.refresh()

    def color_print(self, y, x, text, pair_num):
        self.stdscr.attron(curses.color_pair(pair_num))
        self.stdscr.addstr(y, x, text)
        self.stdscr.attroff(curses.color_pair(pair_num))

    def print_confirm(self, selected="Yes"):
        # clear Yes/No line
        curses.setsyx(self.screen_height // 2 + 1, 0)
        self.stdscr.clrtoeol()

        y = self.screen_height // 2 + 1
        options_width = 10

        # print Yes
        option = "Yes"
        x = self.screen_width // 2 - options_width // 2 + len(option)
        if selected == option:
            self.color_print(y, x, option, 1)
        else:
            self.stdscr.addstr(y, x, option)

        # print No
        option = "No"
        x = self.screen_width // 2 + options_width // 2 - len(option)
        if selected == option:
            self.color_print(y, x, option, 1)
        else:
            self.stdscr.addstr(y, x, option)

        self.stdscr.refresh()

    def confirm(self, confirmation_text):
        self.print_center(confirmation_text)

        current_option = "Yes"
        self.print_confirm(current_option)

        while 1:
            key = self.stdscr.getch()

            if key == curses.KEY_RIGHT and current_option == "Yes":
                current_option = "No"
            elif key == curses.KEY_LEFT and current_option == "No":
                current_option = "Yes"
            elif key == curses.KEY_ENTER or key in [10, 13]:
                return True if current_option == "Yes" else False

            self.print_confirm(current_option)

    def print_center(self, text):
        self.stdscr.clear()
        x = self.screen_width // 2 - len(text) // 2
        y = self.screen_height // 2
        self.stdscr.addstr(y, x, text)
        self.stdscr.refresh()


if __name__ == "__main__":
    MenuDisplay(MENU)
