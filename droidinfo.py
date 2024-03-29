# coding=utf-8
import os
import re
import sys
from workflow import Workflow, ICON_INFO, ICON_GROUP, ICON_WARNING

__author__ = 'benny'

MANU_MEIZU = "meizu"
MANU_SAMSUNG = "samsung"
MANU_HUAWEI = "huawei"
MANU_XIAOMI = "xiaomi"
MANU_OPPO = "oppo"

MANU_ALPS = "alps"


def execute(cmd):
    return os.popen(cmd).readlines()


# #格式化打印
def print_key_value_table(list, key, value):
    list.append([key, value])


def get_right_value(value):
    return value.split('=')[1]


def find(collection, target):
    for ele in collection:
        if target in ele:
            return ele.strip()


def getdevices():
    lines = execute('adb devices')
    
    found = False
    ret = []
    err = -1
    if lines:
        err = 0
        for line in lines:
            line = line.strip()
            if found:
                if line:
                    ret.append(line.split('\t')[0])
            elif 'List of devices attached' == line:
                found = True

    return ret,err


def main(wf):
    #os.environ['PATH'] += ':' + android_home
    results = getdevices()
    if results[1] == -1:
        wf.add_item(title='Adb not found, you should set the adb path first.', icon=ICON_WARNING)
    else:
        devices = results[0]
        device_count = len(devices)

        arg_count = len(sys.argv)

        device = ''
        # >1 devices; has chosen
        if device_count > 1 and arg_count > 1 and sys.argv[1]:
            index = 0
            try:
                index = int(sys.argv[1])
                if index >= device_count:
                    index = 0
            except:
                pass

            device = devices[index]

        # 1 device, whatever chosen
        elif device_count == 1:
            device = devices[0]

        if device:
            info = []
            build_prop_str = 'adb -s %s shell cat /system/build.prop' % device
     

            # 获取厂商
            result_manufacturer_str = find(execute(build_prop_str), "ro.product.manufacturer")
            manufacturer = get_right_value(result_manufacturer_str).lower()
            if manufacturer == MANU_ALPS:
                manufacturer = get_right_value(find(execute(build_prop_str), "ro.product.brand="))
                manufacturer = manufacturer.lower()

            # 获取型号
            if MANU_XIAOMI == manufacturer:
                ro_build_product = get_right_value(find(execute(build_prop_str), "ro.build.product="))
                if 'HM' in ro_build_product:
                    model = "HONGMI"
                else:
                    model = "XIAOMI"
            else:
                model = get_right_value(find(execute(build_prop_str), "ro.product.model="))

            print_key_value_table(info, "Model", model)

            print_key_value_table(info, "Manufacturer", manufacturer)

            # 获取安卓版本
            result_android_version = get_right_value(find(execute(build_prop_str), "ro.build.version.release"))
            print_key_value_table(info, "Version", result_android_version)

            # 获取cpu数量
            result_cpu = execute('adb -s %s shell ls /sys/devices/system/cpu/' % device)
            cpu_core_number = 0
            for item in result_cpu:
                if re.match(r"cpu[0-9]", item):
                    cpu_core_number += 1

            print_key_value_table(info, "CPU Core Number", cpu_core_number)

            # 获取cpu最大频率
            result_for_cpu_freq = execute(
                'adb -s %s shell cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq' % device)
            print_key_value_table(info, "CPU Max Freq(HZ)", result_for_cpu_freq[0])

            # 获取内存信息
            result_for_meminfo = execute('adb -s %s shell cat /proc/meminfo' % device)
            mem_total_str = ""
            for meminfo_item in result_for_meminfo:
                if "MemTotal" in meminfo_item:
                    mem_total_str = meminfo_item
                    break

            mem_total = mem_total_str.lower().replace(" ", "").split(":")[1].replace("kb", "").strip()
            print_key_value_table(info, "MemTotal(KB)", mem_total)
            mem_total_mb = float(mem_total) / 1024.0
            print_key_value_table(info, "MemTotal(MB)", mem_total_mb)

            # 获取屏幕密度，有的厂商没法从这个字段取【适配】
            result_density_str = find(execute(build_prop_str), "density")
            if result_density_str:
                density = get_right_value(result_density_str)
                density_scale = int(density) / 160.0
                print_key_value_table(info, "Density(scale)", "%s(%s)" % (density, density_scale))

            # 获取屏幕分辨率
            raw_dumysys_window = execute('adb -s %s shell dumpsys window' % device)
            # result_mFrame = raw_dumysys_window , /r "mFrame"

            resolution = "0", "0"

            if MANU_OPPO == manufacturer:
                resolution = find(raw_dumysys_window, "mUnrestrictedScreen=").replace(" ", "").replace(
                    "mUnrestrictedScreen=(0,0)",
                    "").split("x")
            else:
                resolution = find(raw_dumysys_window, "mRestrictedScreen").replace(" ", "").replace(
                    "mRestrictedScreen=(0,0)",
                    "").split("x")

            print_key_value_table(info, "Resolution", resolution[0] + "x" + resolution[1])

            # 获取imei
            raw_imei = execute('adb -s %s shell dumpsys iphonesubinfo' % device)
            if raw_imei:
                for ele in raw_imei:
                    matcher = re.match(r'.*Device ID\s*=\s*(.*)', ele)
                    if matcher:
                        for imei in matcher.groups():
                            print_key_value_table(info, "IMEI", imei.strip())

            
            # 获取ROM，【适配】
            if MANU_MEIZU == manufacturer:
                rom = get_right_value(find(execute(build_prop_str), "ro.build.display"))
            elif MANU_SAMSUNG == manufacturer:
                rom = get_right_value(find(execute(build_prop_str), "ro.build.description="))
            elif MANU_HUAWEI == manufacturer:
                rom = get_right_value(find(execute(build_prop_str), "emui"))
            elif MANU_XIAOMI == manufacturer:
                rom = get_right_value(find(execute(build_prop_str), "ro.build.description="))
            elif MANU_OPPO == manufacturer:
                opporom = find(execute(build_prop_str), "ro.build.version.opporom=")
                if opporom:
                    rom = get_right_value(find(execute(build_prop_str), "ro.build.version.opporom="))
                else:
                    rom = get_right_value(find(execute(build_prop_str), "ro.build.display.id"))
            else:
                rom = get_right_value(find(execute(build_prop_str), "ro.build.display.id"))

            print_key_value_table(info, "ROM", rom)

            # print info
            #if device_count > 1:
            #    wf.add_item(title='Found %s devices, change args to show others.' % device_count,
            #                subtitle='Pass a value between 0 and %d to see other devices.' % (device_count - 1),
            #                icon=ICON_GROUP)
            for info_ele in info:
                title = unicode("【%s】%s", 'utf-8') % (info_ele[0], info_ele[1])
                wf.add_item(title=title,
                            icon=ICON_INFO, largetext=title, copytext=title)

        elif device_count > 0:
            for i in range(0, device_count):
                title = unicode("【%d】%s", 'utf-8') % (i, devices[i])
                wf.add_item(title=title, valid=False, autocomplete=str(i), largetext=title, copytext=title)
        else:
            wf.add_item(title='No devices.')

    # Send the results to Alfred as XML
    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow()
    sys.exit(wf.run(main))
