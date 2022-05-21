import curses
import logging
import asyncio
import json
import time
import os
import json
from Clients import __main__ as clients
from Clients.Framework import utils

EXIT = " EXIT"
RUN = "RUN"
LOAD = "LOAD FLOW"
CREATE_FLOW = "CREATE FLOW"
PRINT_FLOW = "PRINT FLOW"
MENU = [RUN, LOAD, CREATE_FLOW, PRINT_FLOW, EXIT]
DEFAULT_EXPORTER = {
    "type": "file",
    "config": {
        "path": "C:\\temp\\results.json"
    }
}


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
                        self.flow_path = name
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

    def get_plugin(self, plugin):
        self.stdscr.clear()
        self.stdscr.refresh()
        curses.echo()

        pd = {"plugin": plugin, "type": "python"}

        self.stdscr.addstr(0, 0, "Plugin Name: ")
        name = self.stdscr.getstr().decode('utf8')
        pd["name"] = name

        if plugin == "PortScanner":
            self.stdscr.addstr(1, 0, "IP: ")
            ip = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(2, 0, "Start Port: ")
            start_port = int(self.stdscr.getstr().decode('utf8'))
            self.stdscr.addstr(3, 0, "End Port: ")
            end_port = int(self.stdscr.getstr().decode('utf8'))
            pd["config"] = {
                "ip": ip,
                "start_port": start_port,
                "end_port": end_port
            }
        elif plugin == "WordpressScanner":
            self.stdscr.addstr(1, 0, "Host: ")
            host = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(2, 0, "API Token: ")
            api_token = self.stdscr.getstr().decode('utf8')
            pd["config"] = {
                "host": host,
                "api_token": api_token
            }
        elif plugin == "SmbScanner":
            self.stdscr.addstr(1, 0, "IP: ")
            ip = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(2, 0, "Username: ")
            username = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(3, 0, "Password: ")
            password = self.stdscr.getstr().decode('utf8')
            pd["config"] = {
                "ip": ip,
                "username": username,
                "password": password
            }
        elif plugin == "FtpScanner":
            self.stdscr.addstr(1, 0, "IP: ")
            ip = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(2, 0, "Username: ")
            username = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(3, 0, "Password: ")
            password = self.stdscr.getstr().decode('utf8')
            pd["config"] = {
                "ip": ip,
                "username": username,
                "password": password
            }
        elif plugin == "HostScanner":
            self.stdscr.addstr(1, 0, "Subnet: ")
            subnet = self.stdscr.getstr().decode('utf8')
            self.stdscr.addstr(2, 0, "Ports (Seperated with comma): ")
            ports_str = self.stdscr.getstr().decode('utf8')
            row_ports = ports_str.split(',')
            ports = []
            for port in row_ports:
                ports.append(int(port.strip()))
            pd["config"] = {
                "subnet": subnet,
                "possible_ports": ports
            }
        self.stdscr.refresh()
        return pd

    def print_create_flow(self):
        self.stdscr.clear()
        self.stdscr.refresh()

        flow = []
        PLUGINS = ["FtpScanner", "HostScanner", "PortScanner", "SmbScanner", "WordpressScanner", "SAVE", "CANCEL"]
        current_row = 0

        self.print_menu(PLUGINS, current_row)
        self.stdscr.addstr(0, 0, "You are now creating a new FLOW!\n")
        while 1:
            key = self.stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(PLUGINS) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                f = PLUGINS[current_row]
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

                        for idx, step in enumerate(flow):
                            if idx == len(flow) - 1:
                                break
                            flow[idx]["next"] = flow[idx + 1]["name"]

                        row = 2
                        for step in flow:
                            next_str = ""
                            if "next" in step.keys():
                                next_str = " ==> "
                            self.stdscr.addstr(row, 0, f"{step['name']} ({step['plugin']}){next_str}")
                            row += 1

                        self.stdscr.refresh()
                        flow_str = json.dumps({"core": {"flow": flow, "exporters": [DEFAULT_EXPORTER]}})
                        with open(f"Clients/Data/{name}.json", "w") as fd:
                            fd.write(flow_str)
                        time.sleep(5)
                        return name
                else:
                    flow.append(self.get_plugin(f))
            self.print_menu(PLUGINS, current_row)
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

        self.stdscr.addstr("\nFinished!!!")
        self.stdscr.addstr("\nPress any key to continue.")
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
