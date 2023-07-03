import NKP
import NKP_Custom_Res
import NKP_Widgets
import NKP_Res
import NKP_Runtime
from NikoKit.NikoStd.NKVersion import NKVersion


def init_hook():
    NKP.Runtime = NKP_Runtime.NKPRuntime  # Hook On to Diy
    NKP.MainWin = NKP_Widgets.NKPMainWindow  # Hook On to Diy
    NKP.name = "NKPatrol"  # Must Change So AppData Won't Collide
    NKP.name_short = "NKP"
    NKP.icon_res_name = "NKP.png"
    NKP.version = NKVersion("1.0.0")
    NKP.version_tag = NKVersion.ALPHA
    NKP.resource_patch = NKP_Res.res
    NKP.resource_patch.update(NKP_Custom_Res.res)
    NKP.lang_patch = {}
