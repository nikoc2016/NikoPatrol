import json

from PySide2.QtWidgets import QTextEdit, QPushButton, QLabel

import NKP
from NKP.Widgets import NKPArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector


class ZipEditorArea(NKPArea):
    def __init__(self):
        self.lang = NKP.Runtime.Service.NKLang.tran

        # GUI Components
        self.autosave_zip_json_path: NQWidgetUrlSelector = None
        self.coordinates_edit: QTextEdit = None
        self.status_label: QLabel = None
        self.btn_load: QPushButton = None
        self.btn_save: QPushButton = None

        super().__init__(area_id="zipline_editor", area_title=self.lang("sotf_zipline_editor"))

    def construct(self):
        super().construct()
        self.autosave_enable_checkbox.hide()
        self.console_out.hide()

        self.autosave_zip_json_path = NQWidgetUrlSelector(title=self.lang("zip_json_path"),
                                                          mode=NQWidgetUrlSelector.MODE_PATH)
        self.coordinates_edit = QTextEdit()
        self.coordinates_edit.setLineWrapMode(QTextEdit.NoWrap)

        self.status_label = QLabel()
        self.btn_load = QPushButton(self.lang("load"))
        self.btn_save = QPushButton(self.lang("save"))

        self.main_lay.addWidget(self.autosave_zip_json_path)
        self.main_lay.addWidget(self.coordinates_edit)
        self.main_lay.addWidget(self.status_label)
        self.button_layout.addWidget(self.btn_load)
        self.button_layout.addWidget(self.btn_save)

    def connect_signals(self):
        super().connect_signals()
        self.btn_load.clicked.connect(self.slot_load)
        self.btn_save.clicked.connect(self.slot_save)

    def slot_load(self):
        lines = []
        try:
            with open(self.autosave_zip_json_path.get_url(), 'r') as json_file:
                save_data = json.load(json_file)
                try:
                    zip_lines = json.loads(save_data["Data"]["ZipLineManager"])["Ziplines"]
                    for zip_line in zip_lines:
                        lines.append(str(zip_line))
                except json.JSONDecodeError as e:
                    self.status_label.setText(f"Decode Error: {e}")
        except FileNotFoundError:
            self.status_label.setText("Json file not found.")
        except json.JSONDecodeError as e:
            self.status_label.setText(f"Decode Error: {e}")
        self.coordinates_edit.setText("\n".join(lines))

    def slot_save(self):
        lines = self.coordinates_edit.toPlainText().split("\n")
        coordinates = [eval(dict_str) for dict_str in lines]
        try:
            # Read Origin
            with open(self.autosave_zip_json_path.get_url(), 'r') as json_file:
                save_data = json.load(json_file)
            zip_mgr = json.loads(save_data["Data"]["ZipLineManager"])

            # Assigning new values
            zip_mgr["Ziplines"] = coordinates
            save_data["Data"]["ZipLineManager"] = json.dumps(zip_mgr, ensure_ascii=False)

            # Write
            with open(self.autosave_zip_json_path.get_url(), 'w') as json_file:
                json.dump(save_data, json_file, ensure_ascii=False)
        except FileNotFoundError:
            self.status_label.setText("Json file not found.")
        except json.JSONDecodeError as e:
            self.status_label.setText(f"Decode Error: {e}")
