import traceback

from PySide2 import QtWidgets
from PySide2.QtCore import QCoreApplication, Signal

import NKP
from PySide2.QtWidgets import QVBoxLayout, QCheckBox, QSizePolicy, QScrollArea, QWidget, QHBoxLayout, QPushButton

from NikoKit.NikoLib import NKFileSystem
from NikoKit.NikoLib.NKAppDataManager import NKAppDataMixin
from NikoKit.NikoQt.NQKernel import NQFunctions
from NikoKit.NikoQt.NQKernel.NQComponent.NQMenu import NQMenuOption
from NikoKit.NikoQt.NQKernel.NQFunctions import clear_layout_margin
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetConsoleTextEdit import NQWidgetConsoleTextEdit
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetInput import NQWidgetInput
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector
from NikoKit.NikoQt.NQKernel.NQGui.NQWindow import NQWindow
from NikoKit.NikoQt.NQKernel.NQGui.NQWindowConsole import NQWindowPythonConsole
from NikoKit.NikoStd.NKPrint import eprint


class NKPMainWindow(NKAppDataMixin, NQWindow):

    def extract_auto_save_data(self, nkp_area):
        save_data = {}
        for member_name in nkp_area.__dict__:
            if member_name.startswith("autosave_"):
                member = nkp_area.__dict__[member_name]
                save_key = f"{nkp_area.area_id}.{member_name.replace('autosave_', '')}"
                save_value = ""
                if isinstance(member, QCheckBox):
                    save_value = member.isChecked()
                elif isinstance(member, NQWidgetInput):
                    save_value = member.get_value()
                elif isinstance(member, NQWidgetUrlSelector):
                    save_value = member.get_url()
                elif isinstance(member, (int, float, str, type(None))):
                    save_value = member
                elif isinstance(member, (list, dict)):
                    save_value = NKFileSystem.datastructure_to_base64(member)
                else:
                    eprint(f"AutoSave::Extract::Not Support Type:{type(member)}")
                save_data[save_key] = save_value
        return save_data

    def apply_auto_save_data(self, nkp_area, member_name, member_value):
        member_name = "autosave_" + member_name
        if member_name not in nkp_area.__dict__:
            eprint(f"AutoSave::Apply::Can't locate {nkp_area.area_id}.{member_name}:{member_value}")
        else:
            member = nkp_area.__dict__[member_name]
            if isinstance(member, QCheckBox):
                member.setChecked(member_value)
            elif isinstance(member, NQWidgetInput):
                member.set_value(member_value)
            elif isinstance(member, NQWidgetUrlSelector):
                member.set_url(member_value)
            elif isinstance(member, (int, float, str, type(None))):
                nkp_area.__dict__[member_name] = member_value
            elif isinstance(member, (list, dict)):
                nkp_area.__dict__[member_name] = NKFileSystem.base64_to_datastructure(member_value)
            else:
                eprint(f"AutoSave::Apply::Not Support Type:{type(member)}||"
                       f"{nkp_area.area_id}.{member_name}:{member_value}")

    @classmethod
    def new_appdata(cls):
        return {}

    def extract_appdata(self):
        appdata = {}
        for area in self.auto_render_areas:
            save_data = self.extract_auto_save_data(area)
            appdata.update(save_data)
        return appdata

    def apply_appdata(self, appdata):
        for save_key in appdata:
            if "." in save_key:
                area_id = save_key.split(".")[0]
                member_name = save_key.split(".")[1]
                member_value = appdata[save_key]
                for area in self.auto_render_areas:
                    if area.area_id == area_id:
                        self.apply_auto_save_data(area, member_name, member_value)

    def __init__(self,
                 w_width=700,
                 w_height=400,
                 w_margin_x=None,
                 w_margin_y=None,
                 w_title=NKP.name,
                 auto_render_areas=None,
                 *args,
                 **kwargs):
        super(NKPMainWindow, self).__init__(
            appdata_mgr=NKP.Runtime.Service.AppDataMgr,
            appdata_name=NKP.name,
            w_width=w_width,
            w_height=w_height,
            w_margin_x=w_margin_x,
            w_margin_y=w_margin_y,
            w_title=w_title,
            *args,
            **kwargs
        )

        # GUI Component
        self.root_scroll_lay = QVBoxLayout()
        clear_layout_margin(self.root_scroll_lay)
        self.root_scroll_adapter = QScrollArea()
        self.root_scroll_adapter.setWidgetResizable(True)
        self.main_lay_adapter = QWidget()
        self.main_lay_adapter.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_lay = QVBoxLayout()

        if auto_render_areas:
            self.auto_render_areas = auto_render_areas
        else:
            self.auto_render_areas = []

        self.configure_tray_menu()

        self.load_auto_render_areas()
        self.setLayout(self.root_scroll_lay)
        self.root_scroll_lay.addWidget(self.root_scroll_adapter)
        self.root_scroll_adapter.setWidget(self.main_lay_adapter)
        self.main_lay_adapter.setLayout(self.main_lay)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.load_appdata()

    def connect_signals(self):
        NKP.Runtime.Signals.tray_clicked.connect(self.slot_tray_clicked)
        NKP.Runtime.Signals.auto_save.connect(self.save_appdata)

    def load_auto_render_areas(self):
        # Expiring the old layout
        NQFunctions.clear_layout(self.main_lay)
        self.main_lay.deleteLater()

        # Creating the new layout
        self.main_lay = QVBoxLayout()
        self.main_lay.setSpacing(0)
        self.main_lay.setContentsMargins(2, 2, 2, 2)
        self.main_lay_adapter.setLayout(self.main_lay)
        for area in self.auto_render_areas:
            self.main_lay.addWidget(area)
        self.main_lay.addStretch()

    @staticmethod
    def slot_exit():
        QCoreApplication.instance().quit()

    @staticmethod
    def slot_python_console():
        NQWindowPythonConsole(w_title="Python Console", allow_execute=True, custom_commands={"NKP": NKP}).show()

    def slot_tray_clicked(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            NKP.Runtime.Gui.WinMain.slot_show()

    def configure_tray_menu(self):
        my_menu = [
            NQMenuOption(name="show_gui", display_name=self.lang("show", "window"),
                         slot_callback=self.slot_show),
            NQMenuOption(name="show_python_console", display_name=self.lang("show", " Python", "console"),
                         slot_callback=self.slot_python_console),
            NQMenuOption(name="quit", display_name=self.lang("quit"),
                         slot_callback=self.slot_exit)
        ]
        NKP.Runtime.Gui.TrayIconMgr.tray_menu_generator.set_content_list(my_menu)
        NKP.Runtime.Gui.TrayIconMgr.rebuild()


class NKPArea(NQWidgetArea):
    def __init__(self,
                 area_id="area_one",
                 area_title="area_title"):
        # Private Data
        self.area_id = area_id
        self.area_title = area_title

        # GUI Component
        self.main_lay = QVBoxLayout()  # This is for custom gui components
        self.button_layout = QHBoxLayout()   # This is for custom buttons

        self.central_layout = QVBoxLayout()
        clear_layout_margin(self.main_lay)
        clear_layout_margin(self.central_layout)
        clear_layout_margin(self.button_layout)
        self.autosave_enable_checkbox = QCheckBox(NKP.Runtime.Service.NKLang.tran("enable"))
        self.save_setting_button = QPushButton(NKP.Runtime.Service.NKLang.tran("save_settings"))
        self.console_out = NQWidgetConsoleTextEdit(auto_scroll=True)
        self.console_out.setFixedHeight(150)
        self.central_layout.addWidget(self.autosave_enable_checkbox)
        self.central_layout.addLayout(self.main_lay)
        self.central_layout.addWidget(self.console_out)
        self.central_layout.addLayout(self.button_layout)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_setting_button)
        self.button_layout.addStretch()
        super().__init__(title=self.area_title, central_layout=self.central_layout)

    def connect_signals(self):
        super().connect_signals()
        self.save_setting_button.clicked.connect(NKP.Runtime.Signals.auto_save)
