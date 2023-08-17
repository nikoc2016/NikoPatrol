from PySide2.QtWidgets import QPushButton

import NKP
from LineProducer import LineProducerArea, LineProducerLang
from NKP import NKP_Runtime, NKP_Res, NKP_Res_Custom
from NKP import NKP_Language
from NKP.Widgets import NKPMainWindow
from NKP.Widgets.Area_AppLauncher import AppLauncherArea
from NKP.Widgets.Area_Backup import BackUpArea
from NKP.Widgets.Area_TempMonitor import TemperatureMonitorArea
from NikoKit.NikoLib import NKZip
from NikoKit.NikoStd import NKConst
from NikoKit.NikoStd.NKVersion import NKVersion

from NKP.Widgets.Area_SubDirPacker import SubDirPackerArea


def init_hook():
    NKP.Runtime = NKPMRuntime  # Hook On to Diy
    NKP.MainWin = NKPMMainWindow  # Hook On to Diy
    NKP.name = "NKPatrol-VServer"  # Must Change So AppData Won't Collide
    NKP.skip_main_win_load = False  # Skipping load main win, do it manually in after_hook()
    NKP.enable_tray_manager = True  # Disable This if you want it one-time-run
    NKP.name_short = "NKP"
    NKP.icon_res_name = "NKP.png"
    NKP.version = NKVersion("1.0.1")
    NKP.version_tag = NKVersion.ALPHA
    NKP.resource_patch = NKP_Res.res
    NKP.resource_patch.update(NKP_Res_Custom.res)
    NKP_Language.ZH_CN_Patch.update(
        {
            "ui_extract_7za": "安装精简版7Z"
        }
    )


def after_hook():
    NKP.Runtime.Service.NKLang.chosen_language = NKConst.ZH_CN


class NKPMRuntime(NKP_Runtime.NKPRuntime):
    pass


class NKPMMainWindow(NKPMainWindow):
    def __init__(self):
        self.install_7za_button = QPushButton(NKP.Runtime.Service.NKLang.tran("ui_extract_7za"))
        NKP.Runtime.Service.NKLang.patch(NKConst.ZH_CN, LineProducerLang.ZH_CN)
        auto_render_areas = [
            LineProducerArea.LineProducerArea(),
            TemperatureMonitorArea(),
            SubDirPackerArea(pack_up_uid="toonz", pack_up_dp_name="Toonz"),
            BackUpArea("gvf_share", "gvf_share"),
            AppLauncherArea("media_browser", "MediaBrowser")
        ]
        super().__init__(
            w_title=f"{NKP.name}",
            auto_render_areas=auto_render_areas,
            single_instance=True,
            w_height=720,
            w_width=1200,
        )
        self.button_lay.insertWidget(self.button_lay.count() - 1, self.install_7za_button)

    def connect_signals(self):
        super().connect_signals()
        self.install_7za_button.clicked.connect(self.slot_install_7za)

    def slot_install_7za(self):
        print("Extracting 7z to temp.")
        NKZip.prepare_7z_binaries()
