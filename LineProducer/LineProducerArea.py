from PySide2.QtWidgets import QVBoxLayout, QPushButton

from LineProducer.LineProducerFuncs import get_shots_from_dir
from NKP.Widgets import NKPArea
from NikoKit.NikoQt.NQKernel.NQFunctions import lay
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetArea import NQWidgetArea
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetCopyLine import NQWidgetCopyLine
from NikoKit.NikoQt.NQKernel.NQGui.NQWidgetUrlSelector import NQWidgetUrlSelector


class LineProducerArea(NKPArea):
    def __init__(self):
        self.autosave_gsfd_dir_select: NQWidgetUrlSelector = None
        self.gsfd_info_copy: NQWidgetCopyLine = None
        self.gsfd_generate_btn: QPushButton = None

        super().__init__(area_id=f"line_producer",
                         area_title="Line Producer")

    def construct(self):
        super().construct()
        self.autosave_enable_checkbox.hide()

        # GetShotsFromDirectory
        self.autosave_gsfd_dir_select = NQWidgetUrlSelector(mode=NQWidgetUrlSelector.MODE_DIR)
        self.gsfd_info_copy = NQWidgetCopyLine()
        self.gsfd_generate_btn = QPushButton("Generate")

        gsfd_area = NQWidgetArea(title="Get Shots from Dir", central_layout=lay([
            self.autosave_gsfd_dir_select,
            self.gsfd_info_copy,
            lay([self.gsfd_generate_btn], vertical=False)
        ], True, False, False))

        self.main_lay.addWidget(gsfd_area)

    def connect_signals(self):
        super().connect_signals()
        self.gsfd_generate_btn.clicked.connect(self.slot_gsfd)

    def slot_gsfd(self):
        self.gsfd_info_copy.set_value(get_shots_from_dir(target_dir=self.autosave_gsfd_dir_select.get_url()))
