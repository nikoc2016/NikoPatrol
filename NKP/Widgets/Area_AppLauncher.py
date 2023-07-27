import html
import subprocess
import time
import traceback
import os
import os.path as p

import psutil
import select
from PySide2.QtWidgets import QComboBox, QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoQt.NQKernel.NQComponent.NQThread import NQThread
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetConsoleTextEdit import NQWidgetConsoleTextEdit
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoQt.NQKernel.NQFunctions import color_line as cl, clear_layout_margin
from NikoKit.NikoStd import NKConst, NKLaunch
from NikoKit.NikoStd.NKPrint import eprint


class AppLauncherArea(NKPArea):
    def __init__(self,
                 launch_uid,
                 launch_dp_name):
        self.console_lines = []  # (str_line, str_hex_color)
        self.run_thread: AppLaunchThread = None

        # Log Cache
        self.restart_counter = 0

        # GUI Components
        self.autosave_launch_target: NQWidgetUrlSelector = None
        self.autosave_launch_params: NQWidgetInput = None
        self.autosave_cwd: NQWidgetUrlSelector = None
        self.autosave_env: NQWidgetInput = None
        self.autosave_launch_mode: QComboBox = None
        self.autosave_restart_timeout_sec: NQWidgetInput = None
        self.autosave_run_pipe: QCheckBox = None
        self.autosave_autorun: QCheckBox = None
        self.status_console: NQWidgetConsoleTextEdit = None
        self.run_btn: QPushButton = None
        self.stop_btn: QPushButton = None
        self.restart_btn: QPushButton = None

        # Thread Hosting
        self.run_thread = AppLaunchThread()
        self.run_thread.start()

        super().__init__(area_id=f"launch_{launch_uid}",
                         area_title=NKP.Runtime.Service.NKLang.tran("ui_launch_title") % launch_dp_name)

    def construct(self):  # Auto Call by parent init
        super().construct()
        self.autosave_enable_checkbox.hide()
        self.autosave_launch_target = NQWidgetUrlSelector(title=self.lang("ui_launch_target"),
                                                          mode=NQWidgetUrlSelector.MODE_PATH)
        self.autosave_launch_params = NQWidgetInput(prompt=self.lang("ui_launch_params"),
                                                    mode=NQWidgetInput.MODE_TEXT,
                                                    stretch_in_the_end=True)
        self.autosave_cwd = NQWidgetUrlSelector(title=self.lang("ui_launch_cwd"),
                                                mode=NQWidgetUrlSelector.MODE_DIR)
        self.autosave_env = NQWidgetInput(prompt=self.lang("ui_launch_env"),
                                          mode=NQWidgetInput.MODE_TEXT,
                                          stretch_in_the_end=True)
        self.autosave_launch_mode = QComboBox()
        self.autosave_launch_mode.addItems(
            ["SW_HIDE 0",
             "SW_SHOWNORMAL 1",
             "SW_NORMAL 1",
             "SW_SHOWMINIMIZED 2",
             "SW_SHOWMAXIMIZED 3",
             "SW_MAXIMIZE 3",
             "SW_SHOWNOACTIVATE 4",
             "SW_SHOW 5",
             "SW_MINIMIZE 6",
             "SW_SHOWMINNOACTIVE 7",
             "SW_SHOWNA 8",
             "SW_RESTORE 9",
             "SW_SHOWDEFAULT 10",
             "SW_FORCEMINIMIZE 11",
             "SW_MAX 11"]
        )
        self.autosave_launch_mode.setCurrentText("SW_NORMAL 1")
        self.autosave_restart_timeout_sec = NQWidgetInput(
            prompt=self.lang("ui_launch_restart_interval"),
            mode=NQWidgetInput.MODE_INT,
            default_value="-1",
            stretch_in_the_end=True
        )
        self.autosave_run_pipe = QCheckBox(self.lang("ui_launch_pipe"))
        self.autosave_autorun = QCheckBox(self.lang("ui_launch_autorun"))
        self.status_console = NQWidgetConsoleTextEdit(auto_scroll=True)
        self.run_btn = QPushButton(self.lang("run"))
        self.stop_btn = QPushButton(self.lang("stop"))
        self.restart_btn = QPushButton(self.lang("restart"))

        parallel_lay = QHBoxLayout()
        clear_layout_margin(parallel_lay)
        launch_setting_lay = QVBoxLayout()
        launch_setting_area = NQWidgetArea(title=self.lang("ui_launch_settings"),
                                           collapsable=False,
                                           central_layout=launch_setting_lay)
        thread_status_area = NQWidgetArea(title=self.lang("ui_launch_thread_status"),
                                          collapsable=False,
                                          central_widget=self.status_console)
        clear_layout_margin(launch_setting_lay)
        launch_button_lay = QHBoxLayout()

        launch_setting_lay.addWidget(self.autosave_launch_target)
        launch_setting_lay.addWidget(self.autosave_launch_params)
        launch_setting_lay.addWidget(self.autosave_cwd)
        launch_setting_lay.addWidget(self.autosave_env)
        launch_setting_lay.addWidget(self.autosave_launch_mode)
        launch_setting_lay.addWidget(self.autosave_restart_timeout_sec)
        launch_setting_lay.addWidget(self.autosave_run_pipe)
        launch_setting_lay.addWidget(self.autosave_autorun)
        launch_setting_lay.addLayout(launch_button_lay)

        clear_layout_margin(launch_button_lay, 4)
        launch_button_lay.addWidget(self.run_btn)
        launch_button_lay.addWidget(self.stop_btn)
        launch_button_lay.addWidget(self.restart_btn)

        parallel_lay.addWidget(launch_setting_area)
        parallel_lay.addWidget(thread_status_area)

        self.main_lay.addLayout(parallel_lay)

    def connect_signals(self):  # Auto Call by parent init
        super().connect_signals()
        self.autosave_autorun.stateChanged.connect(self.slot_autorun_changed)
        self.run_btn.clicked.connect(self.slot_run)
        self.stop_btn.clicked.connect(self.slot_stop)
        self.restart_btn.clicked.connect(self.slot_restart)
        NKP.Runtime.Signals.second_passed.connect(self.slot_update)

    def slot_update(self):
        restart_timeout = int(self.autosave_restart_timeout_sec.get_value())
        if restart_timeout > 0:
            self.restart_counter += 1
            if self.restart_counter >= restart_timeout:
                self.restart_counter = 0
                self.slot_restart()

        self.render_console()

    def render_console(self):
        # Display Thread Console Logs
        try:
            console_lines = self.run_thread.console_lines[:]
            pipe_lines = self.run_thread.pipe_lines[:]
            restart_timeout = self.autosave_restart_timeout_sec.get_value()

            if int(restart_timeout) > 0:
                console_lines.append((f"Restart: {self.restart_counter}s/{restart_timeout}s", NKConst.COLOR_GOLD))

            self.status_console.render_lines(console_lines)
            self.console_out.render_lines(pipe_lines)
        except:
            self.status_console.setHtml(cl(self.lang("ui_launch_thread_stopped"),
                                           color_hex=NKConst.COLOR_RED,
                                           change_line=False))

    def slot_autorun_changed(self):
        if self.autosave_autorun.isChecked():
            self.slot_run()

    def slot_run(self):
        self.setup_thread_with_params()
        self.run_thread.run_flag = True

    def slot_stop(self):
        self.run_thread.run_flag = False

    def slot_restart(self):
        self.setup_thread_with_params()
        self.run_thread.restart_flag = True

    def setup_thread_with_params(self):
        self.run_thread.command = f"{self.autosave_launch_target.get_url()} {self.autosave_launch_params.get_value()}"
        cwd = self.autosave_cwd.get_url()
        if not cwd:
            cwd = p.dirname(self.run_thread.command)
            if not cwd:
                cwd = None
        self.run_thread.cwd = cwd
        self.run_thread.display_mode = int(self.autosave_launch_mode.currentText().split(" ")[1])
        self.run_thread.custom_env = None if not self.autosave_env.get_value() else self.autosave_env.get_value()
        self.run_thread.use_pipe = self.autosave_run_pipe.isChecked()


class AppLaunchThread(NQThread):
    def __init__(self):
        self.console_lines = [("", None) for i in range(10)]
        self.pipe_lines = []
        self.command = ""
        self.cwd = ""
        self.display_mode = 1
        self.custom_env = None
        self.use_pipe = False
        self.proc = None

        # Flags
        self.run_flag = False  # Will run proc if set to True, will kill proc otherwise
        self.restart_flag = False  # Will re-run the proc once detected to True, and set it to False when restarted.

        super().__init__()

    def run(self):
        while not self.stop_flag:
            self.console_lines[0] = (f"stop_flag:{self.stop_flag}", None)
            self.console_lines[1] = (f"pause_flag:{self.pause_flag}", None)
            self.console_lines[2] = (f"run_flag:{self.run_flag}", None)
            self.console_lines[3] = (f"restart_flag:{self.restart_flag}", None)

            if not self.pause_flag:
                try:
                    status_code = self.proc.poll()
                    if status_code is None:
                        status_code = "Proc:Running."
                    elif status_code == 0:
                        status_code = "Proc:Ends."
                    else:
                        status_code = f"Proc:Error ({status_code})"
                    self.console_lines[4] = (status_code, None)
                except:
                    self.console_lines[4] = (f"Proc:({str(self.proc)})", None)

                if self.run_flag and self.proc is None:
                    self.console_lines[5] = (f"command={self.command}", None)
                    self.console_lines[6] = (f"cwd={self.cwd}", None)
                    self.console_lines[7] = (f"dp={self.display_mode}", None)
                    self.console_lines[8] = (f"env={self.custom_env}", None)
                    self.pipe_lines = []
                    try:
                        # Convert string ENV to dict
                        if isinstance(self.custom_env, str):
                            self.custom_env = eval(self.custom_env)
                        if self.use_pipe:
                            self.proc = NKLaunch.run_pipe(self.command, self.cwd, self.custom_env)
                        else:
                            self.proc = NKLaunch.run(self.command, self.cwd, self.display_mode, self.custom_env)
                    except Exception as e:
                        self.run_flag = False
                        self.pipe_lines.append((traceback.format_exc(), NKConst.COLOR_STD_ERR))
                if not self.run_flag and self.proc is not None:
                    self.kill_proc()
                if self.restart_flag:
                    self.restart_flag = False
                    self.kill_proc()
                    self.run_flag = True
                    self.console_lines[4] = ("Proc Restarting", NKConst.COLOR_LIME)

                # Run-Pipe Handling
                if isinstance(self.proc, subprocess.Popen) and self.use_pipe:
                    try:
                        std_out, std_err = self.proc.communicate(timeout=1)
                        self.pipe_lines = []
                        self.pipe_lines.append((std_out.decode(NKConst.SYS_CHARSET), None))
                        self.pipe_lines.append((std_err.decode(NKConst.SYS_CHARSET), NKConst.COLOR_STD_ERR))
                    except subprocess.TimeoutExpired as e:
                        pass
                    except Exception as e:
                        self.pipe_lines = []
                        self.pipe_lines.append((traceback.format_exc(), NKConst.COLOR_STD_ERR))
            time.sleep(1)

    def kill_proc(self):
        if isinstance(self.proc, subprocess.Popen):
            pid = self.proc.pid
            self.console_lines[4] = ("Killing Proc", NKConst.COLOR_RED)
            try:
                self.proc.terminate()
                self.proc.kill()
            except:
                pass

            if psutil.pid_exists(pid):
                NKLaunch.run(["taskkill", "/pid", str(pid), "/f"])
                time.sleep(1)

        self.proc = None
        self.console_lines[5] = (f"", None)
        self.console_lines[6] = (f"", None)
        self.console_lines[7] = (f"", None)
        self.console_lines[8] = (f"", None)
