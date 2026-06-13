import cmd2
import lib.Rosetta as Rosetta
import lib.Cartouche as Cartouche
from pprint import pprint


class Cli(cmd2.Cmd):
    def __init__(self):
        super().__init__()
        self.context: list = []
        self.hostname: str = "device"

        # Конфигурации
        self.current_test_id: int = None
        self.current_stream_id: int = None

        self.running_configuration: dict = {"tests": {}}
        self.candidate_configuration: dict = {"tests": {}}

        self.context_update()

    def context_update(self):
        if self.context:
            self.prompt = self.hostname + f"({'-'.join(self.context)})# "
        else:
            self.prompt = self.hostname + "# "

    def get_current_stream(self):
        test_key = f"test {self.current_test_id}"
        stream_key = f"stream {self.current_stream_id}"
        return self.candidate_configuration["tests"][test_key]["streams"][stream_key]

    def format_config(self, config_dict: dict, indent_level: int = 0) -> str:
        lines = []
        spaces = "  " * indent_level

        for key, value in config_dict.items():
            if isinstance(value, dict):
                if not value:
                    lines.append(f"{spaces}{key}")
                elif key == "port":
                    for port_key, port_value in value.items():
                        lines.append(f"{spaces}port {port_key}: {port_value}")
                else:
                    lines.append(f"{spaces}{key}")
                    lines.append(self.format_config(value, indent_level + 1))
            else:
                lines.append(f"{spaces}{key}: {value}")

        return "\n".join(lines)

    @cmd2.with_argparser(Rosetta.show)
    def do_show(self, arg):
        match arg.command:
            case "candiidate":
                if arg.config:
                    if not self.candidate_configuration.get("tests"):
                        print("Конфигурация пуста")
                        return

                    if "stream" in self.context and self.current_test_id and self.current_stream_id:
                        test_key = f"test {self.current_test_id}"
                        stream_key = f"stream {self.current_stream_id}"
                        try:
                            target_data = {test_key: {"streams": {stream_key: self.get_current_stream()}}}
                            print(self.format_config(target_data))
                        except KeyError:
                            print(self.format_config(self.candidate_configuration))
                    elif "test" in self.context and self.current_test_id:
                        test_key = f"test {self.current_test_id}"
                        try:
                            target_data = {test_key: self.candidate_configuration["tests"][test_key]}
                            print(self.format_config(target_data))
                        except KeyError:
                            print(self.format_config(self.candidate_configuration))
                    else:
                        print(self.format_config(self.candidate_configuration))

            case "running":
                if arg.config:
                    pass

            case "datapath":
                match arg.datapath:
                    case "hardware":
                        """Собирает данные из словаря DPDK и выводит вашу таблицу"""

                        # Обновляем состояние устройств
                        Cartouche.check_modules()
                        Cartouche.get_device_details(Cartouche.network_devices)

                        header = "{:<13} | {:<9} | {:<32} | {:<11} | {:<16}".format(
                            "PCI Address", "Kernel If", "Description", "Driver", "Owner"
                        )
                        separator = "=" * len(header)

                        print(separator)
                        print(header)
                        print(separator)

                        # Фильтруем только сетевые устройства (Class начинается с '02')
                        net_devices = [d for d in Cartouche.devices.values() if d.get("Class", "").startswith("02")]
                        # Сортируем по PCI-слоту
                        net_devices.sort(key=lambda x: x["Slot"])

                        for d in net_devices:
                            pci = d.get("Slot", "-")

                            # В DPDK интерфейсов может быть несколько (разделены запятыми)
                            iface = d.get("Interface", "")
                            if not iface or iface == "<none>":
                                iface = "-"

                            desc = d.get("Device_str", "<Unknown Device>")
                            if len(desc) > 32:
                                desc = desc[:29] + "..."

                            driver = d.get("Driver_str", "")
                            if not driver or driver == "<none>":
                                driver = "-"

                            # Определяем владельца на основе списков самого DPDK
                            if driver in Cartouche.dpdk_drivers:
                                owner = "Userspace (DPDK)"
                            elif driver != "-":
                                owner = "Kernel"
                            else:
                                owner = "None"

                            print("{:<13} | {:<9} | {:<32} | {:<11} | {}".format(pci, iface, desc, driver, owner))
                        print(separator)

    def do_exit(self, arg):
        if self.context:
            self.context.pop()
            self.context_update()
        else:
            print("Logout")
            return True

    def do_end(self, arg):
        if self.context:
            self.context.clear()
            self.context_update()
        else:
            print("Logout")
            return True

    def do_config(self, arg):
        if "config" not in self.context:
            self.context.append("config")
            self.context_update()
        else:
            print("Вы уже находитесь в режиме конфигурации")

    @cmd2.with_argparser(Rosetta.test)
    def do_test(self, arg):
        if "config" in self.context:
            test_id = arg.id
            self.current_test_id = test_id
            self.context.append("test")
            self.context_update()

            test_key = "test " + str(test_id)
            tests_dict = self.candidate_configuration["tests"]

            if test_key not in tests_dict:
                tests_dict[test_key] = {"streams": {}}

            pprint(self.candidate_configuration)
        else:
            print("Вы не находитесь в режиме конфигурации")

    @cmd2.with_argparser(Rosetta.stream)
    def do_stream(self, arg):
        if "test" in self.context:
            stream_id = arg.id
            self.current_stream_id = stream_id
            self.context.append("stream")
            self.context_update()

            test_key = f"test {self.current_test_id}"
            stream_key = f"stream {stream_id}"
            streams_dict = self.candidate_configuration["tests"][test_key]["streams"]

            if stream_key not in streams_dict:
                streams_dict[stream_key] = {}

            pprint(self.candidate_configuration)

        else:
            print("Вы не находитесь в режиме конфигурации")

    @cmd2.with_argparser(Rosetta.port)
    def do_port(self, arg):
        if "stream" in self.context:
            stream_dict = self.get_current_stream()

            if "port" not in stream_dict:
                stream_dict["port"] = {}

            match arg.command:
                case "id":
                    stream_dict["port"]["id"] = arg.id
                case "mode":
                    stream_dict["port"]["mode"] = arg.mode

            pprint(self.candidate_configuration)

        else:
            print("Вы не находитесь в режиме конфигурации")

    @cmd2.with_argparser(Rosetta.vlan)
    def do_vlan(self, arg):
        if "stream" in self.context:
            stream_dict = self.get_current_stream()
            stream_dict["vlan"] = arg.id
            pprint(self.candidate_configuration)
        else:
            print("Вы не находитесь в режиме конфигурации")

    @cmd2.with_argparser(Rosetta.frame)
    def do_frame(self, arg):
        if "stream" in self.context:
            stream_dict = self.get_current_stream()

            match arg.command:
                case "size":
                    key = "frame size"
                    if stream_dict.get("frame mode") == "imix":
                        print("Переведи в режим frame mode в режим fix")
                    else:
                        stream_dict[key] = arg.size

                case "mode":
                    key = "frame mode"
                    if "frame size" in stream_dict and arg.mode == "imix":
                        del stream_dict["frame size"]
                    stream_dict[key] = arg.mode

            pprint(self.candidate_configuration)

        else:
            print("Вы не находитесь в режиме конфигурации")

    @cmd2.with_argparser(Rosetta.source)
    def do_source(self, arg):
        if "stream" in self.context:
            stream_dict = self.get_current_stream()

            # Обработка IP range
            if arg.sub_1 == "ip" and arg.sub_2 == "address" and arg.command == "range":
                stream_dict["source ip start"] = arg.start_ip
                stream_dict["source ip end"] = arg.end_ip

            # Обработка Port range
            elif arg.sub_1 == "port" and arg.command == "range":
                if arg.start_port > arg.end_port:
                    print("Ошибка: Начальный порт не может быть больше конечного")
                    return
                stream_dict["source port start"] = arg.start_port
                stream_dict["source port end"] = arg.end_port

            pprint(self.candidate_configuration)
        else:
            print("Вы не находитесь в режиме конфигурации stream")

    @cmd2.with_argparser(Rosetta.destination)
    def do_destination(self, arg):
        if "stream" in self.context:
            stream_dict = self.get_current_stream()

            # Обработка IP range для destination
            if arg.sub_1 == "ip" and arg.sub_2 == "address" and arg.command == "range":
                stream_dict["destination ip start"] = arg.start_ip
                stream_dict["destination ip end"] = arg.end_ip

            # Обработка Port range для destination
            elif arg.sub_1 == "port" and arg.command == "range":
                if arg.start_port > arg.end_port:
                    print("Ошибка: Начальный порт не может быть больше конечного")
                    return
                stream_dict["destination port start"] = arg.start_port
                stream_dict["destination port end"] = arg.end_port

            pprint(self.candidate_configuration)
        else:
            print("Вы не находитесь в режиме конфигурации stream")


if __name__ == "__main__":
    cli = Cli()
    cli.cmdloop()
