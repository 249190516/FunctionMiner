import uiautomator2 as UI
import os

operatorDevices = 'emulator-5554'

if __name__ == '__main__':
    # init
    script_path = os.path.dirname(os.path.abspath(__file__))
    hierarchy_path = os.path.join(script_path, "hierarchy3.xml")

    device = UI.Device(operatorDevices)
    info = device.app_current()
    page_source = device.dump_hierarchy(compressed=False, pretty=False)
    with open(hierarchy_path, "w", encoding="utf-8") as file:
        file.write(page_source)
