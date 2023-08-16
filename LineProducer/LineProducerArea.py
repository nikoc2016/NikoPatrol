import os
import os.path as p
import tempfile
import time
import traceback

from PySide2.QtWidgets import QVBoxLayout, QPushButton, QTabWidget, QLineEdit, QTextEdit, QLabel, QRadioButton, \
    QButtonGroup, QComboBox, QHBoxLayout

import NKP
from LineProducer.LineProducerFuncs import get_shots_from_dir, compare_shots, get_latest_maya_file, \
    analyze_low_model_resource
from NKP import NKP_Language
from NKP.Widgets import NKPArea
from NikoKit.NikoLib import NKFileSystem
from NikoKit.NikoMaya.public_functions import get_texture_from_text
from NikoKit.NikoQt.NQKernel.NQComponent.NQThread import NQThread
from NikoKit.NikoQt.NQKernel.NQFunctions import lay, lay_adaptor
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetCheckList import NQWidgetCheckList
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetCopyPasteLine import NQWidgetCopyPasteLine
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoStd import NKConst, NKTime, NKLaunch


class LineProducerArea(NKPArea):
    def __init__(self):
        # Lang Preload
        self.lang = NKP.Runtime.Service.NKLang.tran

        # Tab
        self.main_tab: QTabWidget = None
        self.lay_1: QVBoxLayout = None
        self.lay_2: QVBoxLayout = None

        # GetShotsFromDirectory
        self.autosave_gsfd_dir_select: NQWidgetUrlSelector = None
        self.gsfd_info_copy: NQWidgetCopyPasteLine = None
        self.gsfd_generate_btn: QPushButton = None

        # CompareShots
        self.autosave_cs_base_data: QTextEdit = None
        self.cs_target_data: NQWidgetCopyPasteLine = None
        self.cs_result_label: QLabel = None
        self.cs_result: NQWidgetCopyPasteLine = None
        self.cs_status: QLabel = None
        self.cs_compare_btn: QPushButton = None

        # AssetPacker
        self.ap_analyze_thread: AssetResourceAnalyzeThread = None

        self.autosave_ap_net_drv_url: NQWidgetUrlSelector = None
        self.ap_project_select: QComboBox = None
        self.ap_refresh_projects_btn: QPushButton = None
        self.ap_refresh_assets_btn: QPushButton = None
        self.ap_char_list: NQWidgetCheckList = None
        self.ap_env_list: NQWidgetCheckList = None
        self.ap_prop_list: NQWidgetCheckList = None

        self.ap_high_low_group: QButtonGroup = None
        self.autosave_ap_low_model: QRadioButton = None
        self.autosave_ap_high_model: QRadioButton = None
        self.autosave_ap_7z_out_dir: NQWidgetUrlSelector = None
        self.ap_7z_command: QLineEdit = None
        self.ap_7z_prepare_btn: QPushButton = None
        self.ap_7z_prepare_status: QLabel = None
        self.ap_7z_run_btn: QPushButton = None
        self.ap_7z_run_status: QLabel = None

        super().__init__(area_id=f"line_producer",
                         area_title="Line Producer")

    def construct(self):
        self.autosave_enable_checkbox.hide()

        # Tab Host
        self.main_tab = QTabWidget()
        self.lay_1 = QVBoxLayout()
        self.lay_2 = QHBoxLayout()

        # GetShotsFromDirectory
        self.autosave_gsfd_dir_select = NQWidgetUrlSelector(title=self.lang("lp_shot_dir"),
                                                            mode=NQWidgetUrlSelector.MODE_DIR)
        self.gsfd_info_copy = NQWidgetCopyPasteLine(no_paste=True)
        self.gsfd_info_copy.hide()
        self.gsfd_generate_btn = QPushButton(self.lang("generate"))

        gsfd_area = NQWidgetArea(title=self.lang("lp_get_shots_from_dir"), central_layout=lay(contents=[
            self.autosave_gsfd_dir_select,
            self.gsfd_info_copy,
            lay(contents=[self.gsfd_generate_btn], vertical=False)  # Button Layout
        ], vertical=True, lead_stretch=False, end_stretch=False))

        # CompareShots
        cs_base_data_label = QLabel(self.lang("lp_cs_base_data"))
        self.autosave_cs_base_data = QTextEdit()
        self.autosave_cs_base_data.setLineWrapMode(QTextEdit.NoWrap)
        self.autosave_cs_base_data.setMinimumHeight(120)
        cs_target_data_label = QLabel(self.lang("lp_cs_target_data"))
        self.cs_target_data = NQWidgetCopyPasteLine(prompt="", no_copy=True, read_only=False)
        self.cs_result_label = QLabel(self.lang("lp_cs_result"))
        self.cs_result_label.hide()
        self.cs_result = NQWidgetCopyPasteLine(prompt="", no_paste=True)
        self.cs_result.hide()
        self.cs_status = QLabel("")
        self.cs_status.hide()
        self.cs_compare_btn = QPushButton(self.lang("compare"))

        cs_area = NQWidgetArea(title=self.lang("lp_cs"), central_layout=lay(contents=[
            cs_base_data_label,
            self.autosave_cs_base_data,
            cs_target_data_label,
            self.cs_target_data,
            self.cs_result_label,
            self.cs_result,
            self.cs_status,
            lay(contents=[self.cs_compare_btn], vertical=False)  # Button Layout
        ], vertical=True, lead_stretch=False, end_stretch=False))

        # AssetPacker
        ap_net_drv_help = QTextEdit()
        ap_net_drv_help.setReadOnly(True)
        ap_net_drv_help.setMaximumHeight(90)
        ap_net_drv_help.setPlainText(self.lang("lp_ap_net_drv_help"))
        self.autosave_ap_net_drv_url = NQWidgetUrlSelector(self.lang("lp_ap_net_drv_root_dir"),
                                                           url="X:\\",
                                                           mode=NQWidgetUrlSelector.MODE_DIR)
        ap_project_select_label = QLabel(self.lang("lp_ap_select_project"))
        self.ap_project_select = QComboBox()
        self.ap_refresh_projects_btn = QPushButton(self.lang("lp_ap_refresh_projects"))
        self.ap_refresh_assets_btn = QPushButton(self.lang("lp_ap_refresh_assets"))
        ap_char_label = QLabel(self.lang("lp_ap_select_asset_character"))
        self.ap_char_list = NQWidgetCheckList(exclusive=False)
        ap_env_label = QLabel(self.lang("lp_ap_select_asset_env"))
        self.ap_env_list = NQWidgetCheckList(exclusive=False)
        ap_prop_label = QLabel(self.lang("lp_ap_select_asset_prop"))
        self.ap_prop_list = NQWidgetCheckList(exclusive=False)
        self.ap_high_low_group = QButtonGroup()
        self.autosave_ap_low_model = QRadioButton(self.lang("lp_ap_low_model"))
        self.autosave_ap_low_model.setChecked(True)
        self.autosave_ap_high_model = QRadioButton(self.lang("lp_ap_high_model"))
        self.ap_high_low_group.addButton(self.autosave_ap_low_model)
        self.ap_high_low_group.addButton(self.autosave_ap_high_model)
        ap_7z_command_label = QLabel(self.lang("lp_ap_7z_command"))
        self.autosave_ap_7z_out_dir = NQWidgetUrlSelector(title=self.lang("lp_ap_7z_out_dir"),
                                                          mode=NQWidgetUrlSelector.MODE_DIR)
        self.ap_7z_command = QLineEdit()
        self.ap_7z_command.hide()
        self.ap_7z_prepare_btn = QPushButton(self.lang("lp_ap_7z_prepare"))
        self.ap_7z_prepare_status = QLabel()
        self.ap_7z_prepare_status.hide()
        self.ap_7z_run_btn = QPushButton(self.lang("lp_ap_7z_run"))
        self.ap_7z_run_status = QLabel()
        self.ap_7z_run_status.hide()

        control_lay = lay(contents=[
            ap_net_drv_help,
            self.autosave_ap_low_model,
            self.autosave_ap_high_model,
            self.autosave_ap_7z_out_dir,
            self.ap_7z_prepare_btn,
            self.ap_7z_prepare_status,
            lay(contents=[ap_7z_command_label, self.ap_7z_command],
                vertical=False, major_item=self.ap_7z_command, lead_stretch=False, end_stretch=False, margin=0),
            self.ap_7z_run_btn,
            self.ap_7z_run_status,
        ], lead_stretch=False, end_stretch=True)
        control_area = NQWidgetArea(title=self.lang("lp_ap_control_panel"), central_layout=control_lay)

        pack_lay = lay(contents=[
            self.autosave_ap_net_drv_url,
            lay(contents=[ap_project_select_label, self.ap_project_select],
                vertical=False, major_item=self.ap_project_select, lead_stretch=False, end_stretch=False, margin=2),
            lay(contents=[self.ap_refresh_projects_btn, self.ap_refresh_assets_btn], vertical=False,
                lead_stretch=True, end_stretch=True, margin=2),
            lay(contents=[
                lay(contents=[ap_char_label, self.ap_char_list], lead_stretch=False, end_stretch=False, margin=2),
                lay(contents=[ap_env_label, self.ap_env_list], lead_stretch=False, end_stretch=False, margin=2),
                lay(contents=[ap_prop_label, self.ap_prop_list], lead_stretch=False, end_stretch=False, margin=2),
            ], vertical=False, lead_stretch=False, end_stretch=False, margin=0)
        ], lead_stretch=False, end_stretch=False)
        pack_area = NQWidgetArea(title=self.lang("lp_ap_pack_panel"), central_layout=pack_lay)
        self.slot_ap_refresh_projects()
        self.slot_ap_refresh_assets()

        # Setting Layout
        self.lay_1.addWidget(gsfd_area)
        self.lay_1.addWidget(cs_area)

        self.lay_2.addWidget(control_area)
        self.lay_2.addWidget(pack_area)
        self.lay_2.setStretchFactor(pack_area, 1)

        self.main_lay.addWidget(self.main_tab)
        self.main_tab.addTab(lay_adaptor(self.lay_1), self.lang("lp_shots_management"))
        self.main_tab.addTab(lay_adaptor(self.lay_2), self.lang("lp_ap"))

        super().construct()

    def connect_signals(self):
        super().connect_signals()
        self.gsfd_generate_btn.clicked.connect(self.slot_gsfd)
        self.cs_compare_btn.clicked.connect(self.slot_cs)

        NKP.Runtime.Signals.second_passed.connect(self.slot_ap_update)
        self.ap_refresh_projects_btn.clicked.connect(self.slot_ap_refresh_projects)
        self.ap_refresh_assets_btn.clicked.connect(self.slot_ap_refresh_assets)
        self.autosave_ap_net_drv_url.signal_changed.connect(self.slot_ap_refresh_projects)
        self.ap_project_select.currentIndexChanged.connect(self.slot_ap_refresh_assets)
        self.ap_7z_prepare_btn.clicked.connect(self.slot_ap_7z_prepare_stage1)
        self.ap_7z_run_btn.clicked.connect(self.slot_ap_7z_run)

    # GetShotsFromDirectory
    def slot_gsfd(self):
        self.gsfd_info_copy.show()
        self.gsfd_info_copy.set_value(get_shots_from_dir(target_dir=self.autosave_gsfd_dir_select.get_url()))

    # CompareShots
    def slot_cs(self):
        scenes_raw = self.autosave_cs_base_data.toPlainText()
        if ";" in scenes_raw:
            scenes_raw = scenes_raw.replace(";", "\n")
            self.autosave_cs_base_data.setText(scenes_raw)
        scenes = scenes_raw.split("\n")
        target_scene = self.cs_target_data.get_value()

        if ";" in target_scene:
            self.cs_result_label.hide()
            self.cs_result.hide()
            self.cs_status.show()
            self.cs_status.setText(self.lang("lp_cs_compare_only_one"))
            return

        matched = False
        try:
            for scene in scenes:
                additions, subtractions = compare_shots(scene, target_scene)
                if additions == "Scene unmatched":
                    continue
                else:
                    matched = True
                    self.cs_result_label.show()
                    self.cs_result.show()
                    self.cs_status.show()
                    self.cs_result.set_value(f"More:{','.join(additions)}, Lack:{','.join(subtractions)}")
                    self.cs_status.setText(self.lang("lp_cs_compared"))
        except Exception as e:
            self.console_out.render_text(traceback.format_exc(), color_hex=NKConst.COLOR_STD_ERR)
        if not matched:
            self.cs_result_label.hide()
            self.cs_result.hide()
            self.cs_status.show()
            self.cs_status.setText(self.lang("lp_cs_no_match"))

    def slot_ap_refresh_projects(self):
        projects = os.listdir(p.join(self.autosave_ap_net_drv_url.get_url(), "Projects"))
        self.ap_project_select.clear()
        for project in projects:
            self.ap_project_select.addItem(project)

    def slot_ap_refresh_assets(self):
        net_drv = self.autosave_ap_net_drv_url.get_url()
        project = self.ap_project_select.currentText()
        asset_dir = p.join(net_drv, "Projects", project, "Publish", "Assets")
        scan_dirs = [p.join(asset_dir, "Char"), p.join(asset_dir, "Envir"), p.join(asset_dir, "Prop")]
        names = [[] for _ in range(len(scan_dirs))]
        for idx, scan_dir in enumerate(scan_dirs):
            if p.isdir(scan_dir):
                for sub_folder in os.listdir(scan_dir):
                    if p.isdir(p.join(scan_dir, sub_folder)):
                        names[idx].append(sub_folder)

        self.ap_char_list.remove_all_options()
        for char_name in names[0]:
            self.ap_char_list.add_option(option_name=char_name, display_text=char_name, checked=False)

        self.ap_env_list.remove_all_options()
        for char_name in names[1]:
            self.ap_env_list.add_option(option_name=char_name, display_text=char_name, checked=False)

        self.ap_prop_list.remove_all_options()
        for char_name in names[2]:
            self.ap_prop_list.add_option(option_name=char_name, display_text=char_name, checked=False)

    def get_pack_up_config(self, full_dir=False):
        net_drv = self.autosave_ap_net_drv_url.get_url()
        project = self.ap_project_select.currentText()
        assets = []
        for char in self.ap_char_list.get_checked():
            if full_dir:
                char = p.join(net_drv, "Projects", project, "Publish", "Assets", "Char", char)
            assets.append((char, "char"))
        for env in self.ap_env_list.get_checked():
            if full_dir:
                env = p.join(net_drv, "Projects", project, "Publish", "Assets", "Envir", env)
            assets.append((env, "env"))
        for prop in self.ap_prop_list.get_checked():
            if full_dir:
                prop = p.join(net_drv, "Projects", project, "Publish", "Assets", "Prop", prop)
            assets.append((prop, "prop"))

        return net_drv, project, assets

    def slot_ap_7z_prepare_stage1(self):
        if self.autosave_ap_low_model.isChecked():
            _, _, assets = self.get_pack_up_config(full_dir=True)
            if assets:
                self.clear_analyze_thread()
                self.ap_analyze_thread = AssetResourceAnalyzeThread()
                self.ap_analyze_thread.assets = assets
                self.ap_analyze_thread.finished.connect(self.slot_ap_7z_prepare_stage2)
                self.ap_analyze_thread.start()
        else:
            self.slot_ap_7z_prepare_stage2()

    def slot_ap_7z_prepare_stage2(self):
        pack_list_file_location = p.join(tempfile.gettempdir(), "AssetPackingList")
        NKFileSystem.scout(pack_list_file_location)
        pack_list_file = p.join(pack_list_file_location,
                                NKTime.NKDatetime.datetime_to_str(NKTime.NKDatetime.now()) + ".txt")

        _, project, assets = self.get_pack_up_config(full_dir=True)

        if self.autosave_ap_high_model.isChecked():
            pack_list = [p.join(asset_dir, "*") for asset_dir, asset_type in assets]
        elif self.autosave_ap_low_model.isChecked():
            pack_list = []
            for asset_tuple, resource_list in self.ap_analyze_thread.assets_to_resources.items():
                pack_list.extend(resource_list)
        else:
            self.console_out.render_text("High or Low not selected", NKConst.COLOR_STD_ERR)
            return

        with open(pack_list_file, "w") as f:
            f.write("\n".join(pack_list))

        pack_out_path = p.join(self.autosave_ap_7z_out_dir.get_url(), project + ".7z")

        self.ap_7z_command.setText(f"7zG a {pack_out_path} -i@{pack_list_file} -spf")
        self.ap_7z_command.show()

    def slot_ap_7z_run(self):
        command = self.ap_7z_command.text()
        if command:
            NKLaunch.run(command=command, display_mode=NKLaunch.DISPLAY_MODE_NORMAL)
            self.ap_7z_run_status.setText(self.lang("lp_ap_7z_executed"))
        else:
            self.ap_7z_run_status.setText(self.lang("lp_ap_7z_generate_command_first"))
        self.ap_7z_run_status.show()

    def slot_ap_update(self):
        if self.ap_analyze_thread is not None:
            self.ap_7z_prepare_status.show()
            try:
                if self.ap_analyze_thread.current_idx < len(self.ap_analyze_thread.assets):
                    asset_tuple = self.ap_analyze_thread.assets[self.ap_analyze_thread.current_idx]
                    asset_name = p.basename(asset_tuple[0])
                    asset_type = asset_tuple[1]

                    percentage = int(float(self.ap_analyze_thread.current_idx) /
                                     float(len(self.ap_analyze_thread.assets)) * 100)
                    status = (f"Analyzing {asset_name}({asset_type}) "
                              f"{self.ap_analyze_thread.current_idx + 1}/{len(self.ap_analyze_thread.assets)} "
                              f"{percentage}%")
                else:
                    status = self.lang("lp_ap_7z_analyzed")
            except Exception as e:
                status = str(e)
            self.ap_7z_prepare_status.setText(status)
        else:
            self.ap_7z_prepare_status.hide()

    def clear_analyze_thread(self):
        try:
            self.ap_analyze_thread.stop_flag = True
            self.ap_analyze_thread.deleteLater()
        except:
            pass
        self.ap_analyze_thread = None


class AssetResourceAnalyzeThread(NQThread):
    def __init__(self):
        super().__init__()
        self.assets = []  # (asset_dir, asset_type)
        self.assets_to_resources = {}  # tuple: ["D:\*", "D:\a.abc"]
        self.current_idx = 0

    def run(self):
        while not self.stop_flag:
            if not self.pause_flag:
                if self.current_idx < len(self.assets):
                    asset_tuple = self.assets[self.current_idx]
                    asset_dir, asset_type = asset_tuple
                    self.assets_to_resources[asset_tuple] = analyze_low_model_resource(asset_dir=asset_dir,
                                                                                       asset_type=asset_type)
                    self.current_idx += 1
                else:
                    self.stop_flag = True
            else:
                time.sleep(1)
