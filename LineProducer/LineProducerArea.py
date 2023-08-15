import traceback

from PySide2.QtWidgets import QVBoxLayout, QPushButton, QTabWidget, QLineEdit, QTextEdit, QLabel, QRadioButton, \
    QButtonGroup, QComboBox, QHBoxLayout

import NKP
from LineProducer.LineProducerFuncs import get_shots_from_dir, compare_shots
from NKP import NKP_Language
from NKP.Widgets import NKPArea
from NikoKit.NikoQt.NQKernel.NQFunctions import lay, lay_adaptor
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetCheckList import NQWidgetCheckList
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetCopyPasteLine import NQWidgetCopyPasteLine
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoStd import NKConst


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
        self.ap_7z_command: NQWidgetInput = None
        self.ap_7z_prepare_btn: QPushButton = None
        self.ap_7z_run_btn: QPushButton = None

        super().__init__(area_id=f"line_producer",
                         area_title="Line Producer")

    def construct(self):
        self.autosave_enable_checkbox.hide()

        # Tab Host
        self.main_tab = QTabWidget()
        self.lay_1 = QVBoxLayout()
        self.lay_2 = QHBoxLayout()
        self.main_tab.addTab(lay_adaptor(self.lay_1), self.lang("lp_shots_management"))
        self.main_tab.addTab(lay_adaptor(self.lay_2), self.lang("lp_ap"))

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
        self.ap_7z_command = QLineEdit()
        self.ap_7z_prepare_btn = QPushButton(self.lang("lp_ap_7z_prepare"))
        self.ap_7z_run_btn = QPushButton(self.lang("lp_ap_7z_run"))

        control_lay = lay(contents=[
            ap_net_drv_help,
            self.autosave_ap_low_model,
            self.autosave_ap_high_model,
            self.ap_refresh_projects_btn,
            self.ap_refresh_assets_btn,
            self.ap_7z_prepare_btn,
            lay(contents=[ap_7z_command_label, self.ap_7z_command],
                vertical=False, major_item=self.ap_7z_command, lead_stretch=False, end_stretch=False, margin=0),
            self.ap_7z_run_btn
        ], lead_stretch=False, end_stretch=True)
        control_area = NQWidgetArea(title=self.lang("lp_ap_control_panel"), central_layout=control_lay)

        pack_lay = lay(contents=[
            self.autosave_ap_net_drv_url,
            lay(contents=[ap_project_select_label, self.ap_project_select],
                vertical=False, major_item=self.ap_project_select, lead_stretch=False, end_stretch=False, margin=2),
            lay(contents=[
                lay(contents=[ap_char_label, self.ap_char_list], lead_stretch=False, end_stretch=False, margin=2),
                lay(contents=[ap_env_label, self.ap_env_list], lead_stretch=False, end_stretch=False, margin=2),
                lay(contents=[ap_prop_label, self.ap_prop_list], lead_stretch=False, end_stretch=False, margin=2),
            ], vertical=False, lead_stretch=False, end_stretch=False, margin=0)
        ], lead_stretch=False, end_stretch=False)
        pack_area = NQWidgetArea(title=self.lang("lp_ap_pack_panel"), central_layout=pack_lay)

        self.lay_2.addWidget(control_area)
        self.lay_2.addWidget(pack_area)
        self.lay_2.setStretchFactor(pack_area, 1)

        # Setting Layout
        self.lay_1.addWidget(gsfd_area)
        self.lay_1.addWidget(cs_area)
        self.main_lay.addWidget(self.main_tab)

        super().construct()

    def connect_signals(self):
        super().connect_signals()
        self.gsfd_generate_btn.clicked.connect(self.slot_gsfd)
        self.cs_compare_btn.clicked.connect(self.slot_cs)

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
