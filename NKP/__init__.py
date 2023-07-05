from NKP import NKP_Runtime
from NikoKit.NikoStd.NKVersion import NKVersion

Runtime = NKP_Runtime.NKPRuntime  # Will be Override by NKP_Custom.init_hook
MainWin = None

name = "NKPatrol"
name_short = "NKP"
version = NKVersion("1.0.0")
version_tag = NKVersion.ALPHA
entry_py_path = __file__
config = None
icon_res_name = "NKP.png"
appdata_dir = ""
log_dir = None  # None -> appdata_dir; "" -> No Log; "url" -> custom log
use_dummy = False
quit_on_last_window_closed = False
enable_nk_logger = True
enable_dark_theme = True
enable_resource = True
resource_patch = {}
enable_timer = True
enable_window_manager = True
enable_tray_manager = True
enable_appdata_manager = True
enable_data_loader = True
enable_nk_language = True