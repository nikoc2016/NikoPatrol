import NKP
from NKP import NKP_Language
from custom_NKP import init_hook, after_hook
from NikoKit.NikoQt.NQLite import NQLite
from NikoKit.NikoStd import NKConst

if __name__ == '__main__':
    # Before QApp Hook
    init_hook()

    # Init Application
    APP = NQLite(name=NKP.name,
                 name_short=NKP.name_short,
                 version=NKP.version,
                 version_tag=NKP.version_tag,
                 entry_py_path=NKP.entry_py_path,
                 config=NKP.config,
                 icon_res_name=NKP.icon_res_name,
                 runtime=NKP.Runtime,
                 appdata_dir=NKP.appdata_dir,
                 log_dir=NKP.log_dir,
                 use_dummy=NKP.use_dummy,
                 quit_on_last_window_closed=NKP.quit_on_last_window_closed,
                 enable_nk_logger=NKP.enable_nk_logger,
                 enable_dark_theme=NKP.enable_dark_theme,
                 enable_resource=NKP.enable_resource,
                 resource_patch=NKP.resource_patch,
                 enable_timer=NKP.enable_timer,
                 enable_window_manager=NKP.enable_window_manager,
                 enable_tray_manager=NKP.enable_tray_manager,
                 enable_appdata_manager=NKP.enable_appdata_manager,
                 enable_data_loader=NKP.enable_data_loader,
                 enable_nk_language=NKP.enable_nk_language)

    # After QApp Hook
    NKP.Runtime.Service.NKLang.patch(NKConst.ZH_CN, NKP_Language.ZH_CN_Patch)
    after_hook()

    if not NKP.skip_main_win_load:
        # Load main window
        NKP.Runtime.Gui.WinMain = NKP.MainWin()
        NKP.Runtime.Gui.WinMain.show()

    APP.serve()
