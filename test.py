import lib.dev as devbind


def init_devbind():
    """Инициализация внутренних структур оригинального скрипта"""
    # Загружаем списки модулей (vfio-pci, igb_uio и т.д.)
    devbind.check_modules()

    # Заставляем скрипт просканировать PCI и заполнить глобальный словарь devbind.devices
    # network_devices - это шаблон, по которому скрипт ищет сетевые карты (Class 02)
    devbind.get_device_details(devbind.network_devices)


def get_network_status_table():
    """Собирает данные из словаря DPDK и выводит вашу таблицу"""
    # Обновляем состояние устройств
    init_devbind()

    header = "{:<13} | {:<9} | {:<32} | {:<11} | {:<16}".format(
        "PCI Address", "Kernel If", "Description", "Driver", "Owner"
    )
    separator = "=" * len(header)

    print(separator)
    print(header)
    print(separator)

    # Фильтруем только сетевые устройства (Class начинается с '02')
    net_devices = [d for d in devbind.devices.values() if d.get("Class", "").startswith("02")]
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
        if driver in devbind.dpdk_drivers:
            owner = "Userspace (DPDK)"
        elif driver != "-":
            owner = "Kernel"
        else:
            owner = "None"

        print("{:<13} | {:<9} | {:<32} | {:<11} | {}".format(pci, iface, desc, driver, owner))
    print(separator)


def bind_device(pci_address, driver_name):
    """Привязывает одно устройство к указанному драйверу"""
    # Используем родную функцию DPDK: bind_all(dev_list, driver, force)
    print(f"Выполняем привязку {pci_address} к {driver_name}...")
    devbind.bind_all([pci_address], driver_name, force=False)


def unbind_device(pci_address):
    """Отвязывает устройство от текущего драйвера"""
    # Используем родную функцию DPDK: unbind_all(dev_list, force)
    print(f"Выполняем отвязку {pci_address}...")
    devbind.unbind_all([pci_address], force=False)


if __name__ == "__main__":
    # Пример использования
    get_network_status_table()

    # Раскомментируйте для тестирования биндинга/анбиндинга (требуются права root):
    # unbind_device("0000:03:00.0")
    # bind_device("0000:03:00.0", "vfio-pci")

    # print("\n--- СТАТУС ПОСЛЕ ИЗМЕНЕНИЙ ---")
    # get_network_status_table()
