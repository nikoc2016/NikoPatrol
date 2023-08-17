import os
import os.path as p
import shutil
import time

import psutil

import custom_NKP
from NikoKit.NikoLib import NKFileSystem
from NikoKit.NikoLib.NKFileSystem import get_exe_info
from NikoKit.NikoLib.NKResource import NKResource
from NikoKit.NikoLib.NKRoboCopy import NKRoboCopy
from NikoKit.NikoStd import NKLaunch, NKConst
from NikoKit.NikoStd.NKPrint import eprint
from custom_NKP import init_hook


class Runtime:
    compiled = None
    my_dir = None
    my_file_name = None
    my_file_ext = None


def main():
    Runtime.compiled, Runtime.my_dir, Runtime.my_file_name, Runtime.my_file_ext = get_exe_info(__file__)
    init_hook()

    features = [
        ("Pip Install Req", pip_install_req),
        ("Pack NKP NKP_Res", pack_resource_nkp),
        ("Pack Custom NKP_Res", pack_resource_custom),
        ("(Unnecessary) Clear Compiled", clear_compiled),
        ("Clean Icon Cache", clear_icon_cache),
        ("Compile NKP", compile_nkp),
        ("Compile NKP-No-Console", compile_nkp_no_console),
    ]

    while True:
        print("0. Exit")
        for idx, feature in enumerate(features):
            print(f"{idx + 1}. {feature[0]}")
        choice = int(input("Number:"))
        if choice == 0:
            return
        else:
            features[choice - 1][1]()


def pip_install_req():
    NKLaunch.run_system(["pip3", "install", "-r", p.join(Runtime.my_dir, "requirements.txt")], pause=True)


def pack_resource_nkp():
    NKResource.pack_dir_to_res(res_dir=p.join(Runtime.my_dir, "Res/NKP_Res"),
                               res_lib_path=p.join(Runtime.my_dir, "NKP/NKP_Res.py"),
                               ext_list=[".png"])


def pack_resource_custom():
    NKResource.pack_dir_to_res(res_dir=p.join(Runtime.my_dir, "Res/Custom_Res"),
                               res_lib_path=p.join(Runtime.my_dir, "NKP/NKP_Res_Custom.py"),
                               ext_list=[".png"])


def clear_compiled():
    NKFileSystem.delete_try(p.join(Runtime.my_dir, "build"))
    NKFileSystem.delete_try(p.join(Runtime.my_dir, "Distribute"))
    NKFileSystem.delete_try(p.join(Runtime.my_dir, "__pycache__"))
    NKFileSystem.delete_try(p.join(Runtime.my_dir, "run_NKP.spec"))


def compile_nkp_no_console():
    compile_nkp(no_console=True)


def compile_nkp(no_console=False):
    copy_niko_kit()
    command = ["PyInstaller", "-Fa", p.join(Runtime.my_dir, "run_NKP.py"),
               "-i", p.join(Runtime.my_dir, "Res/Custom_Res", "LP_LOGO.ico"),
               "--clean",
               "--distpath", p.join(Runtime.my_dir, "Distribute", "NKPatrol")]
    if no_console:
        command.append("-w")
    print(f"PyInstalling -> {' '.join(command)}")
    NKLaunch.run(command=command,
                 cwd=Runtime.my_dir,
                 display_mode=NKLaunch.DISPLAY_MODE_NORMAL).wait()
    remove_niko_kit()
    shutil.move(p.join(Runtime.my_dir, "Distribute", "NKPatrol", "run_NKP.exe"),
                p.join(Runtime.my_dir,
                       f"{custom_NKP.NKP.name}_{custom_NKP.NKP.version}_{custom_NKP.NKP.version_tag}.exe"))
    clear_compiled()


def copy_niko_kit():
    print("Copying NikoKit...")
    NKRoboCopy.copy_dir_to_dir(source_dir=p.join(p.dirname(Runtime.my_dir), "NikoKit"),
                               target_dir=p.join(Runtime.my_dir, "NikoKit"),
                               except_dirs=[p.join(p.dirname(Runtime.my_dir), "NikoKit", ".git"),
                                            p.join(p.dirname(Runtime.my_dir), "NikoKit", ".idea"),
                                            p.join(p.dirname(Runtime.my_dir), "NikoKit", "__pycache__")])


def remove_niko_kit():
    print("Deleting NikoKit...")
    NKFileSystem.delete_try(p.join(Runtime.my_dir, "NikoKit"))


def clear_icon_cache():
    commands = ['taskkill /f /im explorer.exe',
                'attrib -h -s -r "%userprofile%AppDataLocalIconCache.db"',
                'del /f "%userprofile%AppDataLocalIconCache.db"',
                'attrib /s /d -h -s -r "%userprofile%AppDataLocalMicrosoftWindowsExplorer*"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_32.db"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_96.db"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_102.db"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_256.db"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_1024.db"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_idx.db"',
                'del /f "%userprofile%AppDataLocalMicrosoftWindowsExplorer	humbcache_sr.db"',
                'echo y|reg delete "HKEY_CLASSES_ROOTLocal SettingsSoftwareMicrosoftWindowsCurrentVersionTrayNotify" /v IconStreams',
                'echo y|reg delete "HKEY_CLASSES_ROOTLocal SettingsSoftwareMicrosoftWindowsCurrentVersionTrayNotify" /v PastIconsStream',
                'start explorer']
    NKLaunch.run_system_sequential(commands)


if __name__ == "__main__":
    main()
