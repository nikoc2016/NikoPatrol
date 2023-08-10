import time

from PySide2.QtWidgets import QTextEdit, QPushButton, QVBoxLayout, QCheckBox, QHBoxLayout, QLabel

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoQt.NQKernel.NQComponent.NQThread import NQThread
from NikoKit.NikoQt.NQKernel.NQFunctions import clear_layout_margin
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlEdit import NQWidgetUrlEdit
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector


class SubDirPackerArea(NKPArea):
    def __init__(self, pack_up_uid, pack_up_dp_name):
        self.lang = NKP.Runtime.Service.NKLang.tran
        self.pack_thread = PackingThread()
        self.pack_thread.start()

        self.pk_setting_lay: QVBoxLayout = None
        self.autosave_src_root: NQWidgetUrlSelector = None
        self.autosave_dest_dir: NQWidgetUrlSelector = None
        self.autosave_inverse_selection: QCheckBox = None
        self.autosave_use_cut: QCheckBox = None
        self.autosave_root_replacement: QCheckBox = None
        self.autosave_root_replace_to: NQWidgetInput = None

        self.sub_dir_lay: QVBoxLayout = None
        self.autosave_sub_dir_list: NQWidgetUrlEdit = None

        self.btn_start: QPushButton = None
        self.btn_pause: QPushButton = None
        self.btn_restart: QPushButton = None

        super().__init__(area_id=f"pkup_{pack_up_uid}",
                         area_title=(self.lang("ui_pkup_title") % pack_up_dp_name))

    def construct(self):
        super().construct()
        self.autosave_enable_checkbox.hide()
        setting_vs_help_lay = QHBoxLayout()
        clear_layout_margin(setting_vs_help_lay)
        self.pk_setting_lay = QVBoxLayout()
        self.autosave_src_root = NQWidgetUrlSelector(title=self.lang("ui_pkup_src_root"),
                                                     mode=NQWidgetUrlSelector.MODE_DIR)
        self.autosave_dest_dir = NQWidgetUrlSelector(title=self.lang("ui_pkup_dest_dir"),
                                                     mode=NQWidgetUrlSelector.MODE_DIR)
        self.autosave_inverse_selection = QCheckBox(self.lang("ui_pkup_inverse_selection"))
        self.autosave_use_cut = QCheckBox(self.lang("ui_pkup_cut"))
        root_replace_lay = QHBoxLayout()
        clear_layout_margin(root_replace_lay)
        self.autosave_root_replacement = QCheckBox(self.lang("ui_pkup_root_replacement"))
        self.autosave_root_replace_to = NQWidgetInput(prompt="",
                                                      min_width=200,
                                                      stretch_in_the_end=True)

        help_image = QLabel()
        help_image.setPixmap(NKP.Runtime.Data.Res.QPixmap("help_pkup.png"))

        self.sub_dir_lay = QVBoxLayout()
        self.autosave_sub_dir_list = NQWidgetUrlEdit()

        self.btn_start = QPushButton(self.lang("ui_pkup_start"))
        self.btn_pause = QPushButton(self.lang("ui_pkup_pause"))
        self.btn_restart = QPushButton(self.lang("ui_pkup_restart"))

        setting_vs_help_lay.addLayout(self.pk_setting_lay)
        setting_vs_help_lay.addWidget(help_image)

        self.pk_setting_lay.addWidget(self.autosave_src_root)
        self.pk_setting_lay.addWidget(self.autosave_dest_dir)
        self.pk_setting_lay.addWidget(self.autosave_inverse_selection)
        # Disabled because don't know how to safely perform, maybe folder is in use?
        # self.pk_setting_lay.addWidget(self.autosave_use_cut)
        self.pk_setting_lay.addLayout(root_replace_lay)

        root_replace_lay.addWidget(self.autosave_root_replacement)
        root_replace_lay.addWidget(self.autosave_root_replace_to)

        self.sub_dir_lay.addWidget(self.autosave_sub_dir_list)

        pk_setting_area = NQWidgetArea(title=self.lang("ui_pkup_setting_area"),
                                       central_layout=setting_vs_help_lay,
                                       collapsable=False)

        subdir_area = NQWidgetArea(title=self.lang("ui_pkup_subdir_area"),
                                   central_layout=self.sub_dir_lay,
                                   collapsable=False)

        self.main_lay.addWidget(pk_setting_area)
        self.main_lay.addWidget(subdir_area)

        self.button_layout.addWidget(self.btn_start)
        self.button_layout.addWidget(self.btn_pause)
        self.button_layout.addWidget(self.btn_restart)

    def connect_signals(self):
        super().connect_signals()
        NKP.Runtime.Signals.second_passed.connect(self.slot_update)

    def slot_update(self):
        self.console_out.render_lines(self.pack_thread.logs)

    def setup_thread(self):
        self.pack_thread.src_root = self.autosave_src_root.get_url()
        self.pack_thread.dest_dir = self.autosave_dest_dir.get_url()
        self.pack_thread.inverse = self.autosave_inverse_selection.isChecked()
        self.pack_thread.use_cut = self.autosave_use_cut.isChecked()
        if not self.autosave_root_replacement.isChecked():
            self.pack_thread.root_replace_to = ""
        else:
            self.pack_thread.root_replace_to = self.autosave_root_replace_to.get_value()

    def slot_start(self):
        self.setup_thread()
        self.pack_thread.pause_flag = False

    def slot_pause(self):
        self.setup_thread()
        self.pack_thread.pause_flag = True

    def slot_restart(self):
        self.pack_thread.reset_all()
        self.slot_start()


class PackingThread(NQThread):
    def __init__(self):
        super().__init__()
        self.pause_flag = True
        self.src_root = ""
        self.dest_dir = ""
        self.inverse = False
        self.use_cut = False
        self.root_replace_to = ""
        self.logs = [("", None) for _ in range(5)]

        # Workflow Control
        self.analyzed_flag = False
        self.tasks = []
        self.task_idx = 0

    def run(self):
        while not self.stop_flag:
            self.logs[0] = (f"[Pause:{self.pause_flag}] [Analyzed:{self.analyzed_flag}] [Stop:{self.stop_flag}]", None)
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

    def do_a_task(self):
        # get a task by self.task_idx += 1
        # setup logs[2] status of progress, total + percentage
        # setup logs[3] of src_dir copying
        # setup logs[4] of tgt_dir copying
        # if last task, reset pause flag, analyzed, and tasks
        pass

    def reset_all(self):
        self.pause_flag = True
        self.src_root = ""
        self.dest_dir = ""
        self.inverse = False
        self.use_cut = False
        self.root_replace_to = ""
        self.logs = [("", None) for _ in range(5)]

        # Workflow Control
        self.analyzed_flag = False
        self.tasks = []
        self.task_idx = 0
