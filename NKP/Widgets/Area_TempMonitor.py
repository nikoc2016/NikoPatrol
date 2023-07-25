import time
import os.path as p

from PySide2.QtCore import QObject, Signal, QThread

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoLib import NKFileSystem
from NikoKit.NikoLib.NKOpenHardwareMonitor import NKOpenHM
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoStd import NKLaunch, NKTime


class OhmJsonFetcher(QObject):
    finished = Signal()

    def __init__(self, contact_url="http://localhost:8085/data.json"):
        super().__init__()
        # Private Storage
        self.error = None
        self.result = None
        self.new_url_await = contact_url
        self.now_url_running = ""
        self.contactor = NKOpenHM()

        # Thread Control
        self.pause_flag = True
        self.stop_flag = False

    def set_url(self, contact_url):
        self.new_url_await = contact_url

    def fetch_forever(self):
        while not self.stop_flag:
            if not self.pause_flag:
                if self.new_url_await != self.now_url_running:
                    self.now_url_running = self.new_url_await
                    self.contactor.json_url = self.now_url_running
                try:
                    self.result = self.contactor.get_snapshot()
                    self.error = None
                except Exception as e:
                    self.result = None
                    self.error = str(e)
            time.sleep(1)
        self.finished.emit()


class TemperatureMonitorArea(NKPArea):
    def __init__(self):
        self.autosave_temp_limit_input = NQWidgetInput(prompt=NKP.Runtime.Service.NKLang.tran("ui_tm_shutdown_temp"),
                                                       mode=NQWidgetInput.MODE_INT,
                                                       default_value=105,
                                                       min_value=60,
                                                       max_value=200,
                                                       stretch_in_the_end=True)
        self.autosave_path_to_ohm = NQWidgetUrlSelector(title=NKP.Runtime.Service.NKLang.tran("ui_tm_ohm_exe_path"),
                                                        url=r"C:\Program Files\OpenHardwareMonitor"
                                                            r"\OpenHardwareMonitor.exe",
                                                        mode=NQWidgetUrlSelector.MODE_PATH)
        self.autosave_json_url_of_ohm = NQWidgetInput(prompt=NKP.Runtime.Service.NKLang.tran("ui_tm_ohm_json_url"),
                                                      mode=NQWidgetInput.MODE_TEXT,
                                                      default_value="http://localhost:8085/data.json",
                                                      stretch_in_the_end=True)
        self.autosave_shutdown_count = 0
        self.autosave_shutdown_timestamp = None
        self.update_timeout_sec = 0
        self.current_temperature = 0
        self.ohm_json_fetcher = OhmJsonFetcher()

        self.status = [
            NKP.Runtime.Service.NKLang.tran("ui_tm_ohm_status_off"),
            "",  # Launch Status
            "",  # CPU Status
            "",  # GPU Status
            NKP.Runtime.Service.NKLang.tran("ui_tm_current_shutdown_status")
        ]

        super().__init__(area_id="TemperatureMonitor",
                         area_title=NKP.Runtime.Service.NKLang.tran("ui_tm_title"))

        self.main_lay.addWidget(self.autosave_temp_limit_input)
        self.main_lay.addWidget(self.autosave_path_to_ohm)
        self.main_lay.addWidget(self.autosave_json_url_of_ohm)

        self.console_out.setFixedHeight(80)

        self.start_thread()

    def start_thread(self):
        NKP.Runtime.Threads.TempMonitorOHM = QThread()
        self.ohm_json_fetcher.moveToThread(NKP.Runtime.Threads.TempMonitorOHM)
        NKP.Runtime.Threads.TempMonitorOHM.started.connect(self.ohm_json_fetcher.fetch_forever)
        self.ohm_json_fetcher.finished.connect(self.clear_thread)
        NKP.Runtime.Threads.TempMonitorOHM.start()

    def stop_thread(self):
        self.ohm_json_fetcher.stop_flag = True

    def clear_thread(self):
        NKP.Runtime.Threads.TempMonitorOHM.quit()
        NKP.Runtime.Threads.TempMonitorOHM.deleteLater()
        NKP.Runtime.Threads.TempMonitorOHM = None

    def connect_signals(self):
        super().connect_signals()
        NKP.Runtime.Signals.second_passed.connect(self.slot_update)

    def slot_update(self):
        self.status[4] = self.lang("ui_tm_current_shutdown_status") % (str(self.current_temperature),
                                                                       self.autosave_temp_limit_input.get_value(),
                                                                       self.autosave_shutdown_count,
                                                                       str(self.autosave_shutdown_timestamp))

        proc_running = NKFileSystem.is_proc_running("OpenHardwareMonitor.exe")
        ohm_connected = False
        if proc_running:
            self.status[0] = self.lang("ui_tm_ohm_status_on")
        else:
            self.status[0] = self.lang("ui_tm_ohm_status_off")
            self.ohm_json_fetcher.pause_flag = True

        if self.update_timeout_sec > 0:
            self.update_timeout_sec -= 1
        else:
            if self.autosave_enable_checkbox.isChecked():
                if not proc_running:
                    ohm_exe_path = self.autosave_path_to_ohm.get_url()
                    if ohm_exe_path and p.isfile(ohm_exe_path):
                        self.status[1] = self.lang("ui_tm_ohm_launching")
                        self.update_timeout_sec = 2
                        NKLaunch.run(self.autosave_path_to_ohm.get_url())
                    else:
                        self.status[1] = self.lang("ui_tm_ohm_launching_fail_no_url")
                else:
                    self.ohm_json_fetcher.set_url(self.autosave_json_url_of_ohm.get_value())
                    if self.ohm_json_fetcher.pause_flag:
                        self.status[1] = self.lang("ui_tm_ohm_retrieving_json")
                        self.ohm_json_fetcher.pause_flag = False
                        self.update_timeout_sec = 1
                    else:
                        if self.ohm_json_fetcher.result is None:
                            self.status[1] = self.lang("ui_tm_ohm_retrieving_json_fail") % str(
                                self.ohm_json_fetcher.error)
                            self.ohm_json_fetcher.pause_flag = True
                            self.update_timeout_sec = 3
                        else:
                            self.status[1] = ""
                            ohm_connected = True
                            cpu_line = ""
                            highest_temperature = 0
                            for cpu in self.ohm_json_fetcher.result["cpus"]:
                                cpu_line += self.lang("ui_tm_current_cpu_status") % (cpu["name"],
                                                                                     cpu["temp"],
                                                                                     cpu["load"],
                                                                                     cpu["power"])
                                cpu_temp = float(cpu["temp"].split()[0])
                                if cpu_temp > highest_temperature:
                                    highest_temperature = cpu_temp

                            gpu_line = ""
                            for gpu in self.ohm_json_fetcher.result["gpus"]:
                                gpu_line += self.lang("ui_tm_current_gpu_status") % (gpu["name"],
                                                                                     gpu["temp"],
                                                                                     gpu["load"],
                                                                                     gpu["fans"],
                                                                                     gpu["power"])
                                gpu_temp = float(gpu["temp"].split()[0])
                                if gpu_temp > highest_temperature:
                                    highest_temperature = gpu_temp

                            self.status[2] = cpu_line
                            self.status[3] = gpu_line
                            self.current_temperature = highest_temperature

                            # Actual Shutdown Feature

                            if (self.autosave_enable_checkbox.isChecked()
                                    and highest_temperature > float(self.autosave_temp_limit_input.get_value())):
                                self.autosave_shutdown_count += 1
                                self.autosave_shutdown_timestamp = NKTime.NKDatetime.datetime_to_str(
                                    NKTime.NKDatetime.now()
                                )
                                NKP.Runtime.Signals.auto_save.emit()
                                time.sleep(1)
                                NKLaunch.run("shutdown -s -t 0")

        if not ohm_connected:
            self.status[2] = ""
            self.status[3] = ""

        self.render_status()

    def render_status(self):
        render_text = ""
        for line in self.status:
            if line:
                render_text += line + "\n"
        self.console_out.setText(render_text)
