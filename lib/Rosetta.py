import argparse
from cmd2 import Cmd2ArgumentParser

test = Cmd2ArgumentParser()
test.add_argument("id", type=int, help="Идентификатор теста")

stream = Cmd2ArgumentParser()
stream.add_argument("id", type=int, help="Идентификатор потока")

port = Cmd2ArgumentParser()
port_sb = port.add_subparsers(dest="command", required=True)
port_id = port_sb.add_parser("id", help="<int> - Идентификатор порта в системе").add_argument(
    "id", type=int, help="<int> - Идентификатор порта в системе"
)

port_mode_help_txt = """
    init - Инициализирует подключение, преимущественно отправляет трафик
    respond - Преимущественно принимает входящие сообщения, также обрабатывает флаги сегментов tcp 
    both - Работает read/write. Отправляет и принимает сообщения (дуплексный режим)"""
port_mode = port_sb.add_parser("mode", help="Режим работы интерфейса").add_argument(
    "mode", choices=["init", "respond", "both"], help=port_mode_help_txt
)

vlan = Cmd2ArgumentParser()
vlan.add_argument("id", type=int, help="<int> - Идентиификатор vlan ")

frame = Cmd2ArgumentParser()
frame_sb = frame.add_subparsers(dest="command")
frame_size = frame_sb.add_parser("size", help="<int> - Размер фрейма").add_argument(
    "size", type=int, help="<int> - Размер фрейма"
)

frame_mode_help_txt = """
<fix> - Фиксированный размер фрейма
<imix> - Переменная длина фрейма, поддерживается только Cisco профиль 7(64) : 4(512) : 1(1514)
"""
frame_mode = frame_sb.add_parser("mode", help=frame_mode_help_txt).add_argument(
    "mode", choices=["fix", "imix"], help="Профиль размера фрейма"
)


def create_traffic_side_parser(prog_name: str) -> Cmd2ArgumentParser:
    """Создает полноценное дерево команд для настройки стороны трафика (source/destination)."""

    parser = Cmd2ArgumentParser(prog=prog_name)
    sb_1 = parser.add_subparsers(dest="sub_1", required=True)

    # ip
    ip_parser = sb_1.add_parser("ip", help=f"Настройка IP параметров {prog_name}")
    ip_subparsers = ip_parser.add_subparsers(dest="sub_2", required=True)

    address_parser = ip_subparsers.add_parser("address", help="Настройка IP адресов")
    address_subparsers = address_parser.add_subparsers(dest="command", required=True)

    range_parser = address_subparsers.add_parser("range", help=f"Диапазон IP-адресов {prog_name}")
    range_parser.add_argument("start_ip", type=str, help="Начальный IP-адрес (например, 10.0.0.1)")
    range_parser.add_argument("end_ip", type=str, help="Конечный IP-адрес (например, 10.0.0.254)")

    # port
    port_parser = sb_1.add_parser("port", help=f"Настройка портов {prog_name}")
    port_subparsers = port_parser.add_subparsers(dest="command", required=True)

    port_range_parser = port_subparsers.add_parser("range", help=f"Диапазон портов {prog_name}: <start> <end>")
    port_range_parser.add_argument("start_port", type=int, choices=range(0, 65536), help="Начальный порт (0-65535)")
    port_range_parser.add_argument("end_port", type=int, choices=range(0, 65536), help="Конечный порт (0-65535)")

    return parser


source = create_traffic_side_parser("source")
destination = create_traffic_side_parser("destination")
