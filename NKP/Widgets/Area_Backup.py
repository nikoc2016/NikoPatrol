import os
import re
import time
import os.path as p
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox
from typing import List, Tuple
import datetime

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoLib import NKZip, NKFileSystem
from NikoKit.NikoLib.NKRoboCopy import NKRoboCopy
from NikoKit.NikoQt.NQKernel.NQComponent.NQThread import NQThread
from NikoKit.NikoQt.NQKernel.NQFunctions import color_line as cl, clear_layout_margin
from NikoKit.NikoQt.NQKernel.NQGui.NQWidget7zCompress import NQWidget7zCompress
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetCheckList import NQWidgetCheckList
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoStd import NKConst
from NikoKit.NikoStd import NKTime


class BackUpArea(NKPArea):
    def __init__(self,
                 back_up_uid,
                 back_up_dp_name):
        # Private Storage
        self.elapsed_secs = 0
        self.console_lines = []  # (str_line, str_hex_color)
        self.bk_thread: BackUpThread = None

        # GUI Component
        self.parallel_lay: QHBoxLayout = None
        self.left_lay: QVBoxLayout = None
        self.backup_lay: QVBoxLayout = None
        self.delete_lay: QVBoxLayout = None
        self.delete_mode_lay: QVBoxLayout = None
        self.delete_param_lay: QVBoxLayout = None
        self.compress_lay: QVBoxLayout = None

        self.autosave_src: NQWidgetUrlSelector = None
        self.autosave_dest: NQWidgetUrlSelector = None
        self.autosave_frequency_sec: NQWidgetInput = None
        self.autosave_enable_compress: QCheckBox = None
        self.autosave_hour_limit: NQWidgetInput = None
        self.autosave_day_limit: NQWidgetInput = None
        self.autosave_week_limit: NQWidgetInput = None
        self.autosave_month_limit: NQWidgetInput = None
        self.autosave_year_limit: NQWidgetInput = None
        self.autosave_overall_limit: NQWidgetInput = None
        self.autosave_delete_mode: NQWidgetCheckList = None
        self.autosave_compress_setting: NQWidget7zCompress = None

        # In super, construct and connect_signals will be called
        super().__init__(area_id=f"Bkup_{back_up_uid}",
                         area_title=NKP.Runtime.Service.NKLang.tran("ui_bkup_title") % back_up_dp_name)

    def construct(self):
        super().construct()
        self.parallel_lay = QHBoxLayout()
        self.left_lay = QVBoxLayout()
        clear_layout_margin(self.left_lay)
        self.backup_lay = QVBoxLayout()
        self.delete_lay = QHBoxLayout()
        self.delete_mode_lay = QVBoxLayout()
        self.delete_param_lay = QVBoxLayout()
        self.compress_lay = QVBoxLayout()

        self.autosave_src = NQWidgetUrlSelector(title=self.lang("ui_bkup_src"), mode=NQWidgetUrlSelector.MODE_DIR)
        self.autosave_dest = NQWidgetUrlSelector(title=self.lang("ui_bkup_dest"), mode=NQWidgetUrlSelector.MODE_DIR)
        self.autosave_frequency_sec = NQWidgetInput(prompt=self.lang("ui_bkup_feq"),
                                                    mode=NQWidgetInput.MODE_INT,
                                                    default_value=3600,
                                                    min_value=1,
                                                    max_value=None,
                                                    stretch_in_the_end=True)
        self.autosave_enable_compress = QCheckBox(self.lang("ui_bkup_enable_compress"))
        self.autosave_hour_limit = NQWidgetInput(prompt=self.lang("ui_bkup_hour_limit"),
                                                 mode=NQWidgetInput.MODE_INT,
                                                 default_value=-1,
                                                 stretch_in_the_end=True)
        self.autosave_day_limit = NQWidgetInput(prompt=self.lang("ui_bkup_day_limit"),
                                                mode=NQWidgetInput.MODE_INT,
                                                default_value=-1,
                                                stretch_in_the_end=True)
        self.autosave_week_limit = NQWidgetInput(prompt=self.lang("ui_bkup_week_limit"),
                                                 mode=NQWidgetInput.MODE_INT,
                                                 default_value=-1,
                                                 stretch_in_the_end=True)
        self.autosave_month_limit = NQWidgetInput(prompt=self.lang("ui_bkup_month_limit"),
                                                  mode=NQWidgetInput.MODE_INT,
                                                  default_value=-1,
                                                  stretch_in_the_end=True)
        self.autosave_year_limit = NQWidgetInput(prompt=self.lang("ui_bkup_year_limit"),
                                                 mode=NQWidgetInput.MODE_INT,
                                                 default_value=-1,
                                                 stretch_in_the_end=True)
        self.autosave_overall_limit = NQWidgetInput(prompt=self.lang("ui_bkup_overall_limit"),
                                                    mode=NQWidgetInput.MODE_INT,
                                                    default_value=-1,
                                                    stretch_in_the_end=True)
        self.autosave_delete_mode = NQWidgetCheckList(exclusive=True)
        self.autosave_delete_mode.add_option(option_name="1",
                                             display_text=self.lang("ui_bkup_keep_newest"),
                                             checked=False)
        self.autosave_delete_mode.add_option(option_name="2",
                                             display_text=self.lang("ui_bkup_keep_oldest"),
                                             checked=False)
        self.autosave_delete_mode.add_option(option_name="3",
                                             display_text=self.lang("ui_bkup_keep_average"),
                                             checked=True)
        self.autosave_compress_setting = NQWidget7zCompress(disable_source_url=True,
                                                            disable_out_url=True,
                                                            disable_compress_btn=True,
                                                            disable_delete_src=True)
        self.autosave_compress_setting.user_in_delete_files_after_compression_box.setChecked(True)

        self.main_lay.addLayout(self.parallel_lay)
        backup_area = NQWidgetArea(title=self.lang("ui_bkup_bk_setting"),
                                   central_layout=self.backup_lay,
                                   collapsable=False)

        delete_area = NQWidgetArea(title=self.lang("ui_bkup_delete_setting"),
                                   central_layout=self.delete_lay,
                                   collapsable=False)

        compress_area = NQWidgetArea(title=self.lang("ui_bkup_comp_setting"),
                                     central_layout=self.compress_lay,
                                     collapsable=False)
        self.parallel_lay.addLayout(self.left_lay)
        self.parallel_lay.addWidget(compress_area)

        self.left_lay.addWidget(backup_area)
        self.left_lay.addWidget(delete_area)

        self.backup_lay.addWidget(self.autosave_src)
        self.backup_lay.addWidget(self.autosave_dest)
        self.backup_lay.addWidget(self.autosave_frequency_sec)
        self.backup_lay.addStretch()

        self.delete_lay.addLayout(self.delete_param_lay)
        self.delete_lay.addLayout(self.delete_mode_lay)

        self.delete_param_lay.addWidget(self.autosave_hour_limit)
        self.delete_param_lay.addWidget(self.autosave_day_limit)
        self.delete_param_lay.addWidget(self.autosave_week_limit)
        self.delete_param_lay.addWidget(self.autosave_month_limit)
        self.delete_param_lay.addWidget(self.autosave_year_limit)
        self.delete_param_lay.addWidget(self.autosave_overall_limit)
        self.delete_param_lay.addStretch()

        self.delete_mode_lay.addWidget(self.autosave_delete_mode)
        self.delete_mode_lay.addStretch()

        self.autosave_compress_setting.layout.insertWidget(0, self.autosave_enable_compress)
        self.compress_lay.addWidget(self.autosave_compress_setting)
        self.compress_lay.addStretch()

    def connect_signals(self):
        super().connect_signals()
        NKP.Runtime.Signals.second_passed.connect(self.slot_update)

    def slot_update(self):
        self.console_lines = []

        # Thread Basic Info
        if isinstance(self.bk_thread, NQThread) and self.bk_thread.isRunning():
            self.console_lines.append((self.lang("ui_bkup_thread_started"), NKConst.COLOR_LIME))
            thread_stopped = False
        else:
            self.console_lines.append((self.lang("ui_bkup_thread_stopped"), None))
            thread_stopped = True

        if not self.autosave_enable_checkbox.isChecked():
            self.console_lines.append((self.lang("disabled"), NKConst.COLOR_EASY_RED))
        else:
            backup_trigger = False

            # Next Update Info
            self.elapsed_secs += 1
            if self.elapsed_secs > int(self.autosave_frequency_sec.get_value()):
                self.elapsed_secs = 0
                backup_trigger = True
            self.console_lines.append((self.lang("ui_bkup_next_bkup") % (
                str(self.elapsed_secs),
                str(self.autosave_frequency_sec.get_value()),
            ), None))

            # Start Backup Thread
            if thread_stopped and backup_trigger:
                try:
                    self.bk_thread.deleteLater()
                except:
                    pass
                self.bk_thread = None
                if self.autosave_enable_compress.isChecked():
                    compress_command = self.autosave_compress_setting.generate_7z_command_list()
                else:
                    compress_command = None
                self.bk_thread = BackUpThread(
                    backup_src_dir=self.autosave_src.get_url(),
                    backup_dest_dir=self.autosave_dest.get_url(),
                    compress_command=compress_command,
                    hour_limit=self.autosave_hour_limit.get_value(),
                    day_limit=self.autosave_day_limit.get_value(),
                    week_limit=self.autosave_week_limit.get_value(),
                    month_limit=self.autosave_month_limit.get_value(),
                    year_limit=self.autosave_year_limit.get_value(),
                    overall_limit=self.autosave_overall_limit.get_value(),
                    delete_mode=int(self.autosave_delete_mode.get_checked())
                )
                self.bk_thread.start()

        # Display Thread Console Logs
        try:
            logs = self.bk_thread.console_lines[:]
            self.console_lines.append(("", None))
            self.console_lines.extend(logs)
        except:
            pass

        self.console_out.render_lines(self.console_lines)


class BackUpThread(NQThread):
    def __init__(self,
                 backup_src_dir,
                 backup_dest_dir,
                 compress_command,
                 hour_limit,
                 day_limit,
                 week_limit,
                 month_limit,
                 year_limit,
                 overall_limit,
                 delete_mode
                 ):
        # Config
        self.backup_src_dir = backup_src_dir
        self.backup_dest_dir = backup_dest_dir
        self.compress_command = compress_command
        self.hour_limit = hour_limit
        self.day_limit = day_limit
        self.week_limit = week_limit
        self.month_limit = month_limit
        self.year_limit = year_limit
        self.overall_limit = overall_limit
        self.delete_mode = delete_mode

        # GUI Console
        self.console_lines = []  # Item: (str_line, str_hex_color)

        super().__init__()

    def run(self):
        start_time = NKTime.NKDatetime.datetime_to_str(NKTime.NKDatetime.now())
        self.pr(f"Started Time: {start_time}")

        # directory validation
        if not p.isdir(self.backup_src_dir) or not p.isdir(self.backup_dest_dir):
            self.pr(f"Invalid src_dir or dest_dir: {self.backup_src_dir} | {self.backup_dest_dir}", NKConst.COLOR_RED)
        else:
            # Copy
            bk_dest_folder = p.join(self.backup_dest_dir,
                                    f"{p.basename(self.backup_src_dir)}_{start_time}")
            self.pr(f"Robo copying {self.backup_src_dir}->{bk_dest_folder}...")
            error = NKRoboCopy.mirror_dir_to_dir(source_dir=self.backup_src_dir,
                                                 target_dir=bk_dest_folder,
                                                 silent_mode=True)
            if error:
                self.pr(f"Robo copy error: {error}", NKConst.COLOR_RED)
            else:
                self.pr(f"Robo copy successfully.", NKConst.COLOR_LIME)

                # Compress
                if not self.compress_command:
                    self.pr(f"Compression Disabled, skipped.")
                else:
                    for idx in range(len(self.compress_command)):
                        if self.compress_command[idx] == NQWidget7zCompress.COMP_SRC:
                            self.compress_command[idx] = bk_dest_folder
                        if self.compress_command[idx] == NQWidget7zCompress.COMP_7Z_URL:
                            self.compress_command[idx] = bk_dest_folder + ".7z"

                    self.pr("7z " + " ".join(self.compress_command))
                    result = NKZip.free_7z_command(self.compress_command)
                    while not result.is_finished():
                        time.sleep(1)
                    if result.info()["return_code"] != 0:
                        for error_line in result.info()["std_err"]:
                            self.pr(error_line, NKConst.COLOR_RED)
                    else:
                        self.pr(f"Compress successfully.", NKConst.COLOR_LIME)

            # Deletion
            files = os.listdir(self.backup_dest_dir)
            pattern = r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'
            backup_items = []
            for file in files:
                match = re.search(pattern, file)
                if match:
                    datetime_string = match.group()
                    backup_items.append((NKTime.NKDatetime.str_to_datetime(datetime_string),
                                         p.join(self.backup_dest_dir, file)))
                else:
                    self.pr(f"Invalid Backup: {file}", NKConst.COLOR_RED)

            to_delete = self.prune_backups(backups=backup_items,
                                           hour_limit=int(self.hour_limit),
                                           day_limit=int(self.day_limit),
                                           week_limit=int(self.week_limit),
                                           month_limit=int(self.month_limit),
                                           year_limit=int(self.year_limit),
                                           overall_limit=int(self.overall_limit),
                                           deletion_mode=int(self.delete_mode))

            for backup_url in to_delete:
                self.pr(f"Deleting {backup_url}", NKConst.COLOR_EASY_BLUE)
                if p.isdir(backup_url):
                    NKFileSystem.boom_dir(backup_url, remove_root=True)
                try:
                    os.remove(backup_url)
                except:
                    pass

        self.pr(f"End Time: {str(NKTime.NKDatetime.now())}")

    def pr(self, line, text_color=None):
        self.console_lines.append((line, text_color))

    @staticmethod
    def prune_backups(backups: List[Tuple[datetime.datetime, str]],
                      hour_limit: int,
                      day_limit: int,
                      week_limit: int,
                      month_limit: int,
                      year_limit: int,
                      overall_limit: int,
                      deletion_mode: int) -> List[str]:

        # Classification of backups into respective time intervals
        backups_classified_by_intervals = [[] for _ in range(6)]
        intervals_in_seconds = [3600, 24 * 3600, 7 * 24 * 3600, 30 * 24 * 3600, 365 * 24 * 3600]
        for backup in backups:
            elapsed_time = (datetime.datetime.now() - backup[0]).total_seconds()
            for i, interval in enumerate(intervals_in_seconds):
                if elapsed_time < interval:
                    backups_classified_by_intervals[i].append(backup)
                    break
            else:
                backups_classified_by_intervals[-1].append(backup)

        # Prepare a list to collect backups that need to be deleted
        backups_to_be_deleted = []
        # Define limits for different time intervals
        limits = [hour_limit, day_limit, week_limit, month_limit, year_limit, overall_limit]

        # Process each time interval
        for backups_in_interval, limit in zip(backups_classified_by_intervals, limits):
            if limit == 0:  # If limit is 0, delete all backups in the interval
                backups_to_be_deleted.extend(backups_in_interval)
            elif 0 < limit < len(backups_in_interval):  # If the number of backups exceeds the limit
                if deletion_mode == 1:  # Delete Oldest
                    backups_to_be_deleted.extend(
                        sorted(backups_in_interval, key=lambda b: b[0])[:len(backups_in_interval) - limit])
                elif deletion_mode == 2:  # Delete Newest
                    backups_to_be_deleted.extend(sorted(backups_in_interval, key=lambda b: b[0], reverse=True)[
                                                 :len(backups_in_interval) - limit])
                elif deletion_mode == 3:  # Delete Non-significant
                    earliest_timestamp, latest_timestamp = min(backup[0] for backup in backups_in_interval), max(
                        backup[0] for backup in backups_in_interval)
                    total_time_duration = latest_timestamp - earliest_timestamp
                    ideal_interval = total_time_duration / limit
                    ideal_timestamps = [earliest_timestamp + i * ideal_interval for i in range(limit)]

                    backups_mapped_to_ideal_timestamps = []
                    for ideal_timestamp in ideal_timestamps:
                        closest_backup = min(backups_in_interval, key=lambda backup: abs(backup[0] - ideal_timestamp))
                        backups_mapped_to_ideal_timestamps.append(closest_backup)
                        backups_in_interval.remove(closest_backup)

                    backups_to_be_deleted.extend(
                        backups_in_interval)  # The remaining backups in the interval are to be deleted

        return [backup[1] for backup in backups_to_be_deleted]
