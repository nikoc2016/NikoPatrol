from datetime import datetime

from PySide2.QtGui import Qt
from PySide2.QtWidgets import QSplitter, QLabel, QPushButton

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoLib import NKLogger
from NikoKit.NikoQt.NQKernel import NQFunctions
from NikoKit.NikoQt.NQKernel.NQComponent.NQThreadManager import NQThreadManager, STATUS_NOT_EXIST, STATUS_QUEUED, \
    STATUS_RUNNING, STATUS_COMPLETED
from NikoKit.NikoQt.NQKernel.NQFunctions import color_line
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetConsoleTextEdit import NQWidgetConsoleTextEdit
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetTaskList import NQWidgetTaskList
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoStd import NKConst, NKTime
from NikoKit.NikoStd.NKPrint import eprint
from NikoKit.NikoStd.NKTime import NKDatetime


# Declare your tasks and trigger mechanism, create a list of tasks and pass in.
class ButlerTask:
    def __init__(self, task_id:str, worker_cls, run_after_secs:int, run_after_tasks:list, run_at_time:str):
        # User Declaration
        self.task_id = task_id                 # [str] unique_id to the task
        self.worker_cls = worker_cls           # [class] worker class NOT instance
        self.run_after_secs = run_after_secs   # [int] task runs again after N seconds, -1 disable.
        self.run_after_tasks = run_after_tasks # [list<str>]  task runs when certain tasks just finished.
        self.run_at_time = run_at_time         # [str] tasks runs daily at hh:mm:ss

        # Butler Private Workspace             # CLIENT DONT TOUCH
        self.task_label: QLabel = None         # For ButlerArea renders progression
        self.task_instance = None              # For ButlerArea feeds in ThreadManager and runs.
        self.task_count_up = 0                 # For ButlerArea +1 until it reaches run_after_secs and reset.



class ButlerArea(NKPArea):
    def __init__(self,
                 butler_uid,
                 butler_dp_name,
                 tasks,
                 threads_count=1, # 1 means execute tasks sequential
                 min_height_px=-1):
        # Data
        self.threads_count = threads_count
        self.qthread_manager: NQThreadManager = None
        self.tasks = {task.task_id: task for task in tasks}  # {task_id: task_object}
        self.history_html_lines = []
        self.current_log_channel = ""  # NQTM_{task_id}
        self.min_height_px = min_height_px
        self.paused = False             # Don't check this, use is_paused()
        self.autosave_log_dir_str = ""  # DANGER, Update() will sync this NKLogger and Widget(init only)
        self.log_dir_first_assign = False  # When logdir is being loaded from AppData, it needs 1-time sync to widget.

        # GUI Components
        self.task_list: NQWidgetTaskList = None
        self.task_exec_history: NQWidgetConsoleTextEdit = None
        self.task_exec_logs: NQWidgetConsoleTextEdit = None
        self.task_exec_logs_area: NQWidgetArea = None
        self.thread_status: NQWidgetConsoleTextEdit = None

        self.btn_run_selected_task: QPushButton = None
        self.btn_run_all_task: QPushButton = None
        self.btn_pause_all_task: QPushButton = None
        self.btn_resume_all_task: QPushButton = None
        self.btn_clear_all_threads: QPushButton = None
        self.log_dir_url_selector: NQWidgetUrlSelector = None
        self.btn_apply_log_dir: QPushButton = None

        self.init_qthread_manager()
        super().__init__(area_id=f"butler_{butler_uid}",
                         area_title=NKP.Runtime.Service.NKLang.tran("ui_butler_title") % butler_dp_name)

    def construct(self):
        super().construct()

        self.console_out.hide()
        self.task_list = NQWidgetTaskList()
        self.task_exec_history = NQWidgetConsoleTextEdit()
        self.task_exec_logs = NQWidgetConsoleTextEdit()
        self.thread_status = NQWidgetConsoleTextEdit()

        self.btn_run_selected_task = QPushButton(self.lang("ui_butler_btn_run_selected_task"))
        self.btn_run_all_task = QPushButton(self.lang("ui_butler_btn_run_all_task"))
        self.btn_pause_all_task = QPushButton(self.lang("ui_butler_btn_pause_all_task"))
        self.btn_resume_all_task = QPushButton(self.lang("ui_butler_btn_resume_all_task"))
        self.btn_clear_all_threads = QPushButton(self.lang("ui_butler_btn_clear_all_threads"))
        self.log_dir_url_selector = NQWidgetUrlSelector(title=self.lang("ui_butler_log_dir"), mode=NQWidgetUrlSelector.MODE_DIR)
        self.btn_apply_log_dir = QPushButton(self.lang("ui_butler_btn_apply_log_dir"))

        task_list_area = NQWidgetArea(title=self.lang("ui_butler_tasklist_area"),
                                      collapsable=False,
                                      central_widget=self.task_list)

        task_exec_history_area = NQWidgetArea(title=self.lang("ui_butler_task_exec_history_area"),
                                              collapsable=False,
                                              central_widget=self.task_exec_history)

        self.task_exec_logs_area = NQWidgetArea(title=self.lang("ui_butler_task_exec_logs_area") % "None",
                                                collapsable=False,
                                                central_widget=self.task_exec_logs)

        thread_status_area = NQWidgetArea(title=self.lang("ui_butler_thread_status_area"),
                                          collapsable=False,
                                          central_widget=self.thread_status)

        left_right_splitter = QSplitter(Qt.Horizontal)
        top_down_splitter = QSplitter(Qt.Vertical)
        left_right_splitter.addWidget(task_list_area)
        left_right_splitter.addWidget(top_down_splitter)
        left_right_splitter.addWidget(thread_status_area)
        top_down_splitter.addWidget(task_exec_history_area)
        top_down_splitter.addWidget(self.task_exec_logs_area)
        left_right_splitter.setSizes([200, 700, 150])
        top_down_splitter.setSizes([300, 700])

        self.main_lay.addWidget(left_right_splitter)
        self.button_layout.addWidget(self.btn_run_selected_task)
        self.button_layout.addWidget(self.btn_run_all_task)
        self.button_layout.addWidget(self.btn_pause_all_task)
        self.button_layout.addWidget(self.btn_resume_all_task)
        self.button_layout.addWidget(self.btn_clear_all_threads)
        self.button_layout.addWidget(self.log_dir_url_selector)
        self.button_layout.addWidget(self.btn_apply_log_dir)

        if self.min_height_px > -1:
            self.task_list.setMinimumHeight(self.min_height_px)

    def connect_signals(self):
        super().connect_signals()
        self.task_list.task_clicked.connect(self.slot_task_clicked)
        NKP.Runtime.Signals.second_passed.connect(self.update)
        self.btn_run_selected_task.clicked.connect(self.slot_run_selected_task)
        self.btn_run_all_task.clicked.connect(self.slot_run_all_tasks)
        self.btn_pause_all_task.clicked.connect(self.slot_pause_all)
        self.btn_resume_all_task.clicked.connect(self.slot_resume_all)
        self.btn_clear_all_threads.clicked.connect(self.slot_clear_all_threads)
        self.btn_apply_log_dir.clicked.connect(self.slot_apply_log_dir)

    def init_qthread_manager(self):
        self.qthread_manager = NQThreadManager(threads_count=self.threads_count)
        self.qthread_manager.signal_task_error.connect(self.slot_error_handler)
        self.qthread_manager.signal_task_finished.connect(self.slot_finish_handler)

    def update(self):
        # Render UI
        self.update_task_list()
        self.update_task_exec_history()
        self.update_thread_status()
        self.update_task_logs()

        # Sync Log Dir -> NKLogger
        NKP.Runtime.Service.NKLogger.log_dir = self.autosave_log_dir_str
        # Sync Log Dir -> GUI Widget
        if self.autosave_log_dir_str and not self.log_dir_url_selector.get_url() and not self.log_dir_first_assign:
            self.log_dir_first_assign = True
            self.log_dir_url_selector.set_url(self.autosave_log_dir_str)

        # Update All Seconds
        for task_id, task_object in self.tasks.items():
            worker_status = self.qthread_manager.get_worker_status(task_object.task_instance)

            # Not currently executing
            if worker_status == STATUS_COMPLETED or worker_status == STATUS_NOT_EXIST:
                task_object.task_instance = None
                # Enabled time loop
                if task_object.run_after_secs > -1 and not self.is_paused():
                    task_object.task_count_up += 1
                    if task_object.task_count_up >= task_object.run_after_secs:
                        # Time triggers run
                        self.slot_run_task(task_object)
                # Daily Timed Schedule
                if datetime.now().strftime("%H:%M:%S") == task_object.run_at_time:
                    self.slot_run_task(task_object)

    def update_task_list(self):
        for task_id, task_object in self.tasks.items():
            # Create Widget First Time
            if not task_object.task_label:
                task_object.task_label = QLabel()
                task_object.task_label.butler_task_id = task_id  # WARNING: Injecting Private ID
                task_object.task_label.setTextFormat(Qt.RichText)
                self.task_list.add_task(task_object.task_label)

            # Get Exec Status
            thread_status = self.qthread_manager.get_worker_status(task_object.task_instance)
            if thread_status == STATUS_NOT_EXIST:
                exec_status = color_line(line=self.lang("[", "STATUS_REST", "]"),
                                         color_hex=NKConst.COLOR_EASY_BLUE,
                                         change_line=False)
            else:
                exec_status = color_line(line=self.lang("[", thread_status, "]"),
                                         color_hex=NKConst.COLOR_LIME,
                                         change_line=False)

            # Get Task Name
            task_name = self.lang(task_id)

            # Get Task Count Down
            task_next_eta = ""
            if task_object.run_after_secs > -1 and thread_status == STATUS_NOT_EXIST:
                secs_remain = task_object.run_after_secs - task_object.task_count_up
                days, hours, minutes, seconds = NKTime.NKDatetime.secs_to_dhms(secs_remain)
                task_next_eta = self.lang("ui_butler_countdown")
                if days:
                    task_next_eta += str(days) + self.lang("day")
                task_next_eta += f"{hours}:{minutes}:{seconds}"
                task_next_eta = color_line(line=task_next_eta, color_hex=NKConst.COLOR_GOLD, change_line=False)

            # Get Parent Tasks
            task_parents = ""
            if task_object.run_after_tasks:
                task_parents = self.lang("ui_butler_follow_task") + ",".join(task_object.run_after_tasks)
                task_parents = color_line(line=task_parents, color_hex=NKConst.COLOR_GREY, change_line=False)

            # Get Task Daily Timed
            task_timed = ""
            if task_object.run_at_time:
                task_timed = f"{self.lang('ui_butler_timed')}{task_object.run_at_time}"
                task_timed = color_line(line=task_timed, color_hex=NKConst.COLOR_LIME, change_line=False)

            # Update QLabel
            task_object.task_label.setText(f"{exec_status} {task_name} {task_timed} {task_next_eta} {task_parents}")

    def update_task_exec_history(self):
        records = self.history_html_lines[-50:]
        self.task_exec_history.setHtml("<br>".join(records))

    def update_thread_status(self):
        threading_status = []
        threading_status.append(f"{str(id(self.qthread_manager))[-4:]}-{str(self.qthread_manager.__class__.__name__)}")
        for idx, worker in enumerate(self.qthread_manager.get_threads_status()):
            threading_status.append(f"T{idx}>{worker}")
        threading_status.append("Queue:")
        for priority, worker in self.qthread_manager.workers_queue:
            threading_status.append(f"(P{priority}){worker}")
        self.thread_status.setHtml("<br>".join(threading_status))

    def update_task_logs(self):
        if not self.current_log_channel and self.task_list.task_widgets:
            self.task_list.select_task_by_index(0)
        self.task_exec_logs_area.set_title(self.lang("ui_butler_task_exec_logs_area") % self.current_log_channel)

        logs = []
        if self.current_log_channel in NKP.Runtime.Service.NKLogger.logs.keys():
            logs = NKP.Runtime.Service.NKLogger.logs[self.current_log_channel][-100:]

        log_str = ""

        for log in logs:
            log_raw_str = NQFunctions.html_escape(log.log_context)

            if log.log_type == NKLogger.STD_OUT:
                try:
                    dt = NKDatetime.str_to_datetime(log.log_context[:-1])
                    log_str += NQFunctions.color_line(line=log_raw_str,
                                                      color_hex=NKConst.COLOR_GOLD,
                                                      change_line=False)
                except:
                    log_str += NQFunctions.color_line(line=log_raw_str,
                                                      color_hex=NKConst.COLOR_STD_OUT,
                                                      change_line=False)
            elif log.log_type == NKLogger.STD_ERR:
                log_str += NQFunctions.color_line(line=log_raw_str,
                                                  color_hex=NKConst.COLOR_STD_ERR,
                                                  change_line=False)
            elif log.log_type == NKLogger.STD_WARNING:
                log_str += NQFunctions.color_line(line=log_raw_str,
                                                  color_hex=NKConst.COLOR_STD_WARNING,
                                                  change_line=False)
            else:
                log_str += NQFunctions.color_line(line=log_raw_str,
                                                  color_hex=NKConst.COLOR_GREY,
                                                  change_line=False)
        self.task_exec_logs.setHtml(log_str)

    def slot_run_task(self, task_object):
        task_object.task_count_up = 0
        worker_status = self.qthread_manager.get_worker_status(task_object.task_instance)
        if worker_status == STATUS_COMPLETED or worker_status == STATUS_NOT_EXIST:
            task_object.task_instance = task_object.worker_cls()
            task_object.task_instance.butler_task_id = task_object.task_id  # WARNING: Injecting Private ID
            self.qthread_manager.run(task_object.task_instance)
            return True
        else:
            message = f"Area_Butler::Can't run {task_object.task_id} when it is {worker_status}."
            self.history_html_lines.append(color_line(message, NKConst.COLOR_STD_ERR, change_line=False))
        return False

    def slot_run_selected_task(self):
        task = self.tasks[self.task_list.get_selected_task().butler_task_id]
        self.slot_run_task(task)

    def slot_run_all_tasks(self):
        for _, task in self.tasks.items():
            self.slot_run_task(task)

    def slot_pause_all(self):
        # Here in GUI it stops seconds counts, but finish worker's child tasks will still send to QThreadManager.
        # In QThreadManager they accept new tasks, but won't arrange to QThread unless pause dismissed.
        # QThreadManager is responsible for set pause_flags in all workers. No guarantee it pauses in worker.
        # Hence, if worker won't pause, its finish signal will be process in pause mode. Child will be sent to QTM.
        self.paused = True
        self.qthread_manager.pause()

    def slot_resume_all(self):
        self.paused = False
        self.qthread_manager.resume()

    def is_paused(self):
        return self.paused or not self.autosave_enable_checkbox.isChecked()

    def slot_clear_all_threads(self):
        self.slot_pause_all()
        self.qthread_manager.shutdown(wait_sec=3)
        for _, task_object in self.tasks.items():
            task_object.task_instance = None
        self.init_qthread_manager()
        self.slot_resume_all()

    def slot_apply_log_dir(self):
        log_dir = self.log_dir_url_selector.get_url()
        self.autosave_log_dir_str = log_dir  # Update() will push the dir to NKLogger.

    def slot_task_clicked(self, widget_index, task_label):
        self.current_log_channel = "NQTM_" + task_label.butler_task_id
        self.update_task_logs()

    def slot_error_handler(self, worker, error_message):
        time_str = NKTime.NKDatetime.datetime_to_str(NKTime.NKDatetime.now())
        html_line = color_line(color_hex=NKConst.COLOR_STD_ERR,
                          line=f"[{self.lang('error')}] {time_str} {self.lang(worker.butler_task_id)}{worker} -> {error_message}",
                          change_line=False)
        self.history_html_lines.append(html_line)

    def slot_finish_handler(self, worker):
        time_str = NKTime.NKDatetime.datetime_to_str(NKTime.NKDatetime.now())
        self.history_html_lines.append(f"[{self.lang('finish')}] {time_str} {self.lang(worker.butler_task_id)}{worker}")

        # Run Afters Tasks Trigger
        for task_id, task_object in self.tasks.items():
            for after_task_id in task_object.run_after_tasks:
                if worker.butler_task_id == after_task_id:
                    worker_status = self.qthread_manager.get_worker_status(task_object.task_instance)
                    if worker_status == STATUS_COMPLETED or worker_status == STATUS_NOT_EXIST:
                        self.slot_run_task(task_object)