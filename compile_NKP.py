import os.path as p
from NikoKit.NikoLib import NKFileSystem
from NikoKit.NikoLib.NKFileSystem import get_exe_info
from NikoKit.NikoLib.NKResource import NKResource
from NikoKit.NikoStd import NKLaunch


class Runtime:
    compiled = None
    my_dir = None
    my_file_name = None
    my_file_ext = None


def main():
    Runtime.compiled, Runtime.my_dir, Runtime.my_file_name, Runtime.my_file_ext = get_exe_info(__file__)

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
    NKResource.pack_dir_to_res(res_dir=p.join(Runtime.my_dir, "NKP_Res"),
                               res_lib_path=p.join(Runtime.my_dir, "NKP_Res.py"),
                               ext_list=[".png"])


def pack_resource_custom():
    NKResource.pack_dir_to_res(res_dir=p.join(Runtime.my_dir, "Custom_Res"),
                               res_lib_path=p.join(Runtime.my_dir, "NKP_Custom_Res.py"),
                               ext_list=[".png"])


def clear_compiled():
    NKFileSystem.delete_try(p.join(Runtime.my_dir, "Distribute", "NKPatrol"))


def compile_nkp():
    NKLaunch.run_system(command=["PyInstaller", "-Fa", p.join(Runtime.my_dir, "run_NKP.py"),
                                 "-i", p.join(Runtime.my_dir, "NKP_Res", "NKP.ico"),
                                 "--clean",
                                 "--distpath", p.join(Runtime.my_dir, "Distribute", "NKPatrol")], pause=True)


def compile_nkp_no_console():
    NKLaunch.run_system(command=["PyInstaller", "-Fa", p.join(Runtime.my_dir, "run_NKP.py"),
                                 "-i", p.join(Runtime.my_dir, "NKP_Res", "NKP.ico"),
                                 "--clean",
                                 "--distpath", p.join(Runtime.my_dir, "Distribute", "NKPatrol"),
                                 "-w"], pause=True)


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
