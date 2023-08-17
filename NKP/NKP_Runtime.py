from PySide2.QtCore import Signal

from NikoKit.NikoQt.NQApplication.NQRuntime import DefaultSignals, NQRuntime


class NKPSignals(DefaultSignals):
    auto_save = Signal()


class NKPRuntime(NQRuntime):
    class Gui(NQRuntime.Gui):
        WinMain = None

    class Threads(NQRuntime.Threads):
        TempMonitorOHM = None

    Signals = NKPSignals()
    SI_Lock = None
    SI_Quit = False
