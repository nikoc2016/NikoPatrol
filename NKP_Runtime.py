from NikoKit.NikoQt.NQApplication import NQRuntime


class NKPRuntime(NQRuntime):
    class Gui(NQRuntime.Gui):
        WinMain = None
