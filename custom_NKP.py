import NKP
from LineProducer import LineProducerLang, LineProducerArea
from NKP import NKP_Runtime, NKP_Res, NKP_Res_Custom
from NKP import NKP_Language
from NKP.Widgets import NKPMainWindow
from NKP.Widgets.Area_SubDirPacker import SubDirPackerArea
from NikoKit.NikoStd import NKConst
from NikoKit.NikoStd.NKVersion import NKVersion


def init_hook():
    NKP.Runtime = NKPMRuntime  # Hook On to Diy
    NKP.MainWin = NKPMMainWindow  # Hook On to Diy
    NKP.name = "LineProducerTools"  # Must Change So AppData Won't Collide
    NKP.skip_main_win_load = False  # Skipping load main win, do it manually in after_hook()
    NKP.enable_tray_manager = False  # Disable This if you want it one-time-run
    NKP.name_short = "NKP"
    NKP.icon_res_name = "LP_LOGO.png"
    NKP.version = NKVersion("1.0.0")
    NKP.version_tag = NKVersion.ALPHA
    NKP.resource_patch = NKP_Res.res
    NKP.resource_patch.update(NKP_Res_Custom.res)
    NKP_Language.ZH_CN_Patch.update(
        {
        }
    )


def after_hook():
    NKP.Runtime.Service.NKLang.chosen_language = NKConst.ZH_CN


class NKPMRuntime(NKP_Runtime.NKPRuntime):
    pass


class NKPMMainWindow(NKPMainWindow):
    def __init__(self):
        NKP.Runtime.Service.NKLang.patch(NKConst.ZH_CN, LineProducerLang.ZH_CN)
        auto_render_areas = [
            LineProducerArea.LineProducerArea(),
            SubDirPackerArea(pack_up_uid="toonz", pack_up_dp_name="Toonz")
        ]
        super().__init__(
            w_title=f"{NKP.name}",
            auto_render_areas=auto_render_areas,
            single_instance=False,
            w_width=1200,
            w_height=700
        )

    def connect_signals(self):
        super().connect_signals()
