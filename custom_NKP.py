import NKP
from NKP import NKP_Runtime, NKP_Res, NKP_Res_Custom
from NKP import NKP_Language
from NKP.Widgets import NKPMainWindow
from NKP.Widgets.Area_Butler import ButlerTask, ButlerArea
from NikoKit.NikoStd import NKConst
from NikoKit.NikoStd.NKVersion import NKVersion
from Workers import WorkerA, WorkerB, WorkerC, WorkerD, WorkerE, WorkerF


def init_hook():
    NKP.Runtime = NKPMRuntime  # Hook On to Diy
    NKP.MainWin = NKPMMainWindow  # Hook On to Diy
    NKP.name = "NKPatrol-DemoButler"  # Must Change So AppData Won't Collide
    NKP.skip_main_win_load = False  # Skipping load main win, do it manually in after_hook()
    NKP.enable_tray_manager = True  # Disable This if you want it one-time-run
    NKP.name_short = "NKP"
    NKP.icon_res_name = "NKP.png"
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
        tasks = [
            ButlerTask(task_id="A", worker_cls=WorkerA, run_after_secs=10, run_after_tasks=[]),
            ButlerTask(task_id="B", worker_cls=WorkerB, run_after_secs=100, run_after_tasks=["A"]),
            ButlerTask(task_id="C", worker_cls=WorkerC, run_after_secs=150, run_after_tasks=["B"]),
            ButlerTask(task_id="D", worker_cls=WorkerD, run_after_secs=200, run_after_tasks=["A"]),
            ButlerTask(task_id="E", worker_cls=WorkerE, run_after_secs=250, run_after_tasks=["B"]),
            ButlerTask(task_id="F", worker_cls=WorkerF, run_after_secs=300, run_after_tasks=["E"]),
        ]
        auto_render_areas = [
            ButlerArea("demo_butler", "ButlerDemo", tasks, 6, min_height_px=900)
        ]
        super().__init__(
            w_title=f"{NKP.name}",
            auto_render_areas=auto_render_areas,
            single_instance=True,
            w_width=1920,
            w_height=1080,
        )

    def connect_signals(self):
        super().connect_signals()
