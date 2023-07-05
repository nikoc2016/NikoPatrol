import NKP
from NKP import NKP_Runtime, NKP_Res, NKP_Res_Custom
from NKP import NKP_Language
from NKP.Widgets import NKPMainWindow
from NKP.Widgets.Area_TempMonitor import TemperatureMonitorArea
from NikoKit.NikoStd.NKVersion import NKVersion


def init_hook():
    NKP.Runtime = NKPMRuntime  # Hook On to Diy
    NKP.MainWin = NKPMMainWindow  # Hook On to Diy
    NKP.name = "NKPatrol-DefaultMod"  # Must Change So AppData Won't Collide
    NKP.name_short = "NKP"
    NKP.icon_res_name = "NKP.png"
    NKP.version = NKVersion("1.0.0")
    NKP.version_tag = NKVersion.ALPHA
    NKP.resource_patch = NKP_Res.res
    NKP.resource_patch.update(NKP_Res_Custom.res)
    NKP_Language.lang_patch.update(
        {}
    )


class NKPMRuntime(NKP_Runtime.NKPRuntime):
    pass


class NKPMMainWindow(NKPMainWindow):
    def __init__(self):
        auto_render_areas = [
            TemperatureMonitorArea()
        ]
        super().__init__(auto_render_areas=auto_render_areas)
