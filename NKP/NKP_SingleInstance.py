import errno
import os
import os.path as p
import tempfile

from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QMessageBox

import NKP
from NikoKit.NikoLib import NKFileSystem
from NikoKit.NikoStd.NKVersion import NKVersion


# Temp\NKPLocks\NKP\NKPatrol-DefaultMod\0-0-0-Awake
# Temp\NKPLocks\NKP\NKPatrol-DefaultMod\0-0-0-Close
# Temp\NKPLocks\NKP\NKPatrol-DefaultMod\0-0-0

def si_start_check():
    running_versions = si_get_running_versions()
    for i in running_versions:
        print(i)
    if running_versions:
        latest_version = None  # Set to None means I am the latest
        for running_version in running_versions:
            if running_version >= NKP.version:
                latest_version = running_version
        if latest_version:
            with open(p.join(si_get_lock_dir(), f'{str(latest_version).replace(".", "-")}-Awake'), "w") as f:
                f.write("Awake")
            NKP.Runtime.SI_Quit = True
        else:
            si_close_old_check(running_versions)

    if not NKP.Runtime.SI_Quit:
        NKP.Runtime.SI_Lock = open(p.join(si_get_lock_dir(),
                                          f'{str(NKP.version).replace(".", "-")}'), "w")


def si_interact_check():
    lock_dir = si_get_lock_dir()
    files = os.listdir(lock_dir)
    for file in files:
        v = str(NKP.version).replace(".", "-")
        awake_file = f"{v}-Awake"
        close_file = f"{v}-Close"
        if file == awake_file:
            while True:
                try:
                    os.remove(p.join(lock_dir, awake_file))
                    break
                except:
                    pass
            NKP.Runtime.Gui.WinMain.activateWindow()
            NKP.Runtime.Gui.WinMain.showNormal()
            NKP.Runtime.Gui.WinMain.show()
        if file == close_file:
            while True:
                try:
                    os.remove(p.join(lock_dir, close_file))
                    break
                except:
                    pass
            QCoreApplication.instance().quit()


def si_get_lock_dir():
    lock_dir = p.join(tempfile.gettempdir(), "NKPLocks", NKP.Runtime.App.name)
    NKFileSystem.scout(lock_dir)
    return lock_dir


def si_is_locked(file_path):
    try:
        os.remove(file_path)
        return False
    except OSError as e:
        if e.errno != errno.ENOENT:
            return True


def si_get_running_versions():
    lock_dir = si_get_lock_dir()
    files = os.listdir(lock_dir)
    running_versions = []
    for file in files:
        file_p = p.join(lock_dir, file)
        if p.isfile(file_p) and si_is_locked(file_p):
            v = file.split("-")
            running_versions.append(NKVersion(version_string=f"{v[0]}.{v[1]}.{v[2]}"))
    return running_versions


def si_close_old_check(running_versions):
    close_old_prompt = QMessageBox()
    close_old_prompt.setIcon(QMessageBox.Question)
    close_old_prompt.setWindowTitle(f"{NKP.Runtime.App.name} V{NKP.version} {NKP.version_tag}")
    old_versions = ",".join([str(running_version) for running_version in running_versions])
    close_old_prompt.setText(NKP.Runtime.Service.NKLang.tran("ui_close_old") % old_versions)
    close_old_prompt.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    close_old_prompt.setDefaultButton(QMessageBox.Yes)

    result = close_old_prompt.exec_()
    if result == QMessageBox.Yes:
        for running_version in running_versions:
            with open(p.join(si_get_lock_dir(),
                      f'{str(running_version).replace(".", "-")}-Close'), "w") as f:
                f.write("Close")
