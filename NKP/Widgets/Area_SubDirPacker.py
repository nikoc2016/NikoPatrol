import os
import time

from PySide2.QtWidgets import QTextEdit, QPushButton, QVBoxLayout, QCheckBox, QHBoxLayout, QLabel, QSizePolicy, \
    QButtonGroup, QRadioButton

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoLib.NKRoboCopy import NKRoboCopy
from NikoKit.NikoQt.NQKernel.NQComponent.NQThread import NQThread
from NikoKit.NikoQt.NQKernel.NQFunctions import clear_layout_margin
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlEdit import NQWidgetUrlEdit
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector

import os.path as p

from NikoKit.NikoStd import NKConst, NKLaunch
from NikoKit.NikoStd.NKPrintableMixin import NKPrintableMixin


class SubDirPackerArea(NKPArea):
    def __init__(self, pack_up_uid, pack_up_dp_name):
        self.lang = NKP.Runtime.Service.NKLang.tran
        self.pack_thread = PackingThread()
        self.pack_thread.start()

        self.root_setting_lay: QVBoxLayout = None
        self.autosave_src_root: NQWidgetUrlSelector = None
        self.autosave_dest_dir: NQWidgetUrlSelector = None

        self.sub_dir_lay: QVBoxLayout = None
        self.autosave_sub_dir_list: NQWidgetUrlEdit = None
        self.copy_radio_group: QButtonGroup = None
        self.autosave_copy_selected: QRadioButton = None
        self.autosave_copy_unselected: QRadioButton = None
        self.autosave_hide_cmd: QCheckBox = None

        self.btn_lay: QHBoxLayout = None
        self.btn_start: QPushButton = None
        self.btn_pause: QPushButton = None
        self.btn_restart: QPushButton = None

        super().__init__(area_id=f"pkup_{pack_up_uid}",
                         area_title=(self.lang("ui_pkup_title") % pack_up_dp_name))

    def construct(self):
        super().construct()
        self.autosave_enable_checkbox.hide()
        self.root_setting_lay = QVBoxLayout()
        clear_layout_margin(self.root_setting_lay)
        self.autosave_src_root = NQWidgetUrlSelector(title=self.lang("ui_pkup_src_root"),
                                                     mode=NQWidgetUrlSelector.MODE_DIR)
        self.autosave_dest_dir = NQWidgetUrlSelector(title=self.lang("ui_pkup_dest_dir"),
                                                     mode=NQWidgetUrlSelector.MODE_DIR)

        self.sub_dir_lay = QVBoxLayout()
        self.autosave_sub_dir_list = NQWidgetUrlEdit(mode=NQWidgetUrlEdit.MODE_DIR_ONLY)
        self.copy_radio_group = QButtonGroup()
        self.autosave_copy_selected = QRadioButton(self.lang("ui_pkup_copy_selected"))
        self.autosave_copy_selected.setChecked(True)
        self.autosave_copy_unselected = QRadioButton(self.lang("ui_pkup_copy_unselected"))
        self.copy_radio_group.addButton(self.autosave_copy_selected)
        self.copy_radio_group.addButton(self.autosave_copy_unselected)

        self.btn_lay = QHBoxLayout()
        self.btn_start = QPushButton(self.lang("ui_pkup_start"))
        self.autosave_hide_cmd = QCheckBox(self.lang("ui_pkup_hide_cmd"))
        self.autosave_hide_cmd.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.btn_pause = QPushButton(self.lang("ui_pkup_pause"))
        self.btn_restart = QPushButton(self.lang("ui_pkup_restart"))

        self.root_setting_lay.addWidget(self.autosave_src_root)
        self.root_setting_lay.addWidget(self.autosave_dest_dir)

        self.sub_dir_lay.addWidget(self.autosave_sub_dir_list)
        self.sub_dir_lay.addWidget(self.autosave_copy_selected)
        self.sub_dir_lay.addWidget(self.autosave_copy_unselected)
        self.sub_dir_lay.addWidget(self.autosave_hide_cmd)
        self.sub_dir_lay.addLayout(self.btn_lay)

        self.btn_lay.addWidget(self.btn_start)
        self.btn_lay.addWidget(self.btn_pause)
        self.btn_lay.addWidget(self.btn_restart)

        root_setting_area = NQWidgetArea(title=self.lang("ui_pkup_root_setting_area"),
                                         central_layout=self.root_setting_lay,
                                         collapsable=False)

        subdir_area = NQWidgetArea(title=self.lang("ui_pkup_subdir_setting_area"),
                                   central_layout=self.sub_dir_lay,
                                   collapsable=False)

        help_image = QLabel()
        help_image.setPixmap(NKP.Runtime.Data.Res.QPixmap("help_pkup.png"))
        self.main_lay.addWidget(help_image)
        self.main_lay.addWidget(root_setting_area)
        self.main_lay.addWidget(subdir_area)

    def connect_signals(self):
        super().connect_signals()
        NKP.Runtime.Signals.second_passed.connect(self.slot_update)
        self.btn_start.clicked.connect(self.slot_start)
        self.btn_pause.clicked.connect(self.slot_pause)
        self.btn_restart.clicked.connect(self.slot_restart)

    def slot_update(self):
        self.pack_thread.basic_logs[0] = (f"[Pause:{self.pack_thread.pause_flag}] "
                                          f"[Analyzed:{self.pack_thread.analyzed_flag}] "
                                          f"[Stop:{self.pack_thread.stop_flag}]", None)
        if self.pack_thread.error_logs:
            all_lines = self.pack_thread.basic_logs + [("Errors:", NKConst.COLOR_STD_ERR)] + self.pack_thread.error_logs
            self.console_out.render_lines(all_lines)
        else:
            self.console_out.render_lines(self.pack_thread.basic_logs)

    def setup_thread(self):
        self.pack_thread.src_root = self.autosave_src_root.get_url()
        self.pack_thread.dest_dir = self.autosave_dest_dir.get_url()
        self.pack_thread.inverse = self.autosave_copy_unselected.isChecked()
        self.pack_thread.hide_cmd = self.autosave_hide_cmd.isChecked()
        self.pack_thread.sub_dirs = self.autosave_sub_dir_list.get_urls()

    def slot_start(self):
        self.setup_thread()
        self.pack_thread.pause_flag = False

    def slot_pause(self):
        self.setup_thread()
        self.pack_thread.pause_flag = True

    def slot_restart(self):
        self.pack_thread.reset_all()
        self.slot_start()


class CopyTask(NKPrintableMixin):
    def __init__(self,
                 src_dir: str,
                 dest_dir: str,
                 exc_dirs: list[str]):
        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.exc_dirs = exc_dirs
        super().__init__()


class PackingThread(NQThread):
    def __init__(self):
        super().__init__()
        self.pause_flag = True
        self.src_root = ""
        self.dest_dir = ""
        self.sub_dirs = []
        self.inverse = False
        self.hide_cmd = False
        self.basic_logs = [("", None) for _ in range(6)]
        self.error_logs = []

        # Workflow Control
        self.analyzed_flag = False
        self.tasks: list[CopyTask] = []
        self.task_idx: int = 0

    def run(self):
        while not self.stop_flag:
            if not self.pause_flag:
                if not self.analyzed_flag:
                    self.analyze_tasks()
                else:
                    self.do_a_task()
            else:
                time.sleep(1)

    def analyze_tasks(self):
        # reset all 3 workflow control
        # task should be source dir to target dir
        # setup logs[1] status of analyzing or done
        self.tasks = []
        self.task_idx = 0
        self.basic_logs[1] = ("Task Analyzing", NKConst.COLOR_BLUE)
        success = True

        try:
            self.src_root = p.normpath(self.src_root)
            self.dest_dir = p.normpath(self.dest_dir)
            self.sub_dirs = [p.normpath(sub_dir) for sub_dir in self.sub_dirs]

            # Normal Mode: Collect each tasks base on sub dir.
            if not self.inverse:
                for sub_dir in self.sub_dirs:
                    if not sub_dir.startswith(self.src_root):
                        self.error_logs.append((f"Subdir wrong root: {sub_dir}", NKConst.COLOR_STD_ERR))
                        continue
                    elif not p.isdir(sub_dir):
                        self.error_logs.append((f"Subdir not exists: {sub_dir}", NKConst.COLOR_STD_ERR))
                        continue
                    else:
                        rebuild_root = sub_dir.replace(os.sep.join(self.src_root.split(os.sep)[:-1]), "")
                        while rebuild_root[0] == os.sep:
                            rebuild_root = rebuild_root[1:]
                        self.tasks.append(CopyTask(sub_dir, p.join(self.dest_dir, rebuild_root), []))

            # Inverse Mode: Establish one task with exception sub dirs.
            else:
                exc_dirs = []
                for exc_dir in self.sub_dirs:
                    if not exc_dir.startswith(self.src_root):
                        self.error_logs.append((f"Exclude subdir wrong root: {exc_dir}", NKConst.COLOR_STD_ERR))
                        continue
                    elif not p.isdir(exc_dir):
                        self.error_logs.append((f"Exclude subdir not exists: {exc_dir}", NKConst.COLOR_STD_ERR))
                        continue
                    else:
                        exc_dirs.append(exc_dir)
                self.tasks.append(CopyTask(self.src_root, p.join(self.dest_dir, p.basename(self.src_root)), exc_dirs))

        except Exception as e:
            self.error_logs.append((str(e), NKConst.COLOR_STD_ERR))
            success = False

        if success:
            self.basic_logs[1] = ("Task Analyzed.", NKConst.COLOR_LIME)
            self.analyzed_flag = True
        else:
            self.basic_logs[1] = ("Analyze Failure", NKConst.COLOR_STD_ERR)
            self.analyzed_flag = False
            self.pause_flag = True

    def do_a_task(self):
        # get a task by self.task_idx += 1
        # setup logs[2] status of progress, total + percentage
        # setup logs[3] of src_dir copying
        # setup logs[4] of tgt_dir copying
        # setup logs[5] of exception child dirs
        # if last task, reset pause flag, analyzed, and tasks
        # Deal with hide_cmd

        if self.task_idx < len(self.tasks):
            task = self.tasks[self.task_idx]
            progress_percentage = int(float(self.task_idx + 1) / float(len(self.tasks)) * 100.0)
            self.basic_logs[2] = (f"Copying ({self.task_idx + 1}/{len(self.tasks)}) {progress_percentage}%",
                                  NKConst.COLOR_LIME)
            self.basic_logs[3] = (f"Source: {task.src_dir}", None)
            self.basic_logs[4] = (f"Destination: {task.dest_dir}", None)
            self.basic_logs[5] = (f"Exception Sub dirs: {task.exc_dirs}", None)
            if self.hide_cmd:
                display_mode = NKLaunch.DISPLAY_MODE_HIDE
            else:
                display_mode = NKLaunch.DISPLAY_MODE_NORMAL

            command = ["robocopy", task.src_dir, task.dest_dir, "/E"]
            if task.exc_dirs:
                command.append("/XD")
                for exc_dir in task.exc_dirs:
                    command.append(exc_dir)

            copy_proc = NKLaunch.run(command=command, display_mode=display_mode)
            copy_proc.wait()

            self.task_idx += 1
        else:
            self.basic_logs[2] = (f"Done ({self.task_idx}/{len(self.tasks)}) 100%",
                                  NKConst.COLOR_LIME)
            self.pause_flag = True

    def reset_all(self):
        self.pause_flag = True
        self.src_root = ""
        self.dest_dir = ""
        self.sub_dirs = []
        self.inverse = False
        self.hide_cmd = False
        self.basic_logs = [("", None) for _ in range(6)]
        self.error_logs = []

        # Workflow Control
        self.analyzed_flag = False
        self.tasks = []
        self.task_idx = 0
