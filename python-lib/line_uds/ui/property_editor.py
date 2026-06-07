from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIntValidator

from typing import Any, List, Dict, Tuple, Union
from enum import Enum

from line_protocol.network.nodes import Node
from line_uds.uds_tool import UdsNodeStatus, UdsTool, UdsNodeStatusListener, UdsPropertyValue
from line_uds.profile import UdsProfile, UdsProperty, UdsService, UdsServiceParam, UdsBoolTypeDefinition, UdsIntTypeDefinition, UdsEnumTypeDefinition, UdsTypeDefinition, UdsVoidTypeDefinition

from line_uds.ui.input_types import UdsNumericInput, UdsBooleanInput, UdsEnumInput, UdsStructInput

import logging
logger = logging.getLogger(__name__)

class UdsPropertyInputStatus(Enum):
    """Represents the status of property inputs"""

    SYNC = 1
    CHANGED = 2
    UNKNOWN = 3
    ERROR = 4

class UdsPropertyInputStatusIndicator(QLabel):

    def __init__(self):
        super().__init__()
        self.setFixedSize(10, 10)
        self.set_status(UdsPropertyInputStatus.UNKNOWN)

    def set_status(self, status: UdsPropertyInputStatus):
        color = {
            UdsPropertyInputStatus.SYNC: "green",
            UdsPropertyInputStatus.CHANGED: "orange",
            UdsPropertyInputStatus.UNKNOWN: "gray",
            UdsPropertyInputStatus.ERROR: "red"
        }.get(status, "red")
        self.setStyleSheet(f"QLabel {{ background-color: {color}; }}")

class UdsPropertyInput(QWidget):

    sigOut_changed = pyqtSignal(UdsProperty, object)

    def __init__(self, property: UdsProperty, value: Any = None):
        super().__init__()
        self._prop = property
        initial_value = value if value is not None else self._prop.default_value

        if isinstance(self._prop.typedef, UdsIntTypeDefinition):
            self._input = UdsNumericInput(initial_value, self._prop.min, self._prop.max)
            self._input.sigOut_changed.connect(lambda val: self.on_value_changed(self._prop, val))
        elif isinstance(self._prop.typedef, UdsBoolTypeDefinition):
            self._input = UdsBooleanInput(initial_value)
            self._input.sigOut_changed.connect(lambda val: self.on_value_changed(self._prop, val))
        elif isinstance(self._prop.typedef, UdsEnumTypeDefinition):
            self._input = UdsEnumInput(self._prop.typedef.values, initial_value)
            self._input.sigOut_changed.connect(lambda val: self.on_value_changed(self._prop, val))
        else:
            self._input = UdsStructInput()

        layout = QHBoxLayout()
        layout.addWidget(QLabel(self._prop.prop_name, self))
        layout.addWidget(self._input)
        self.setLayout(layout)

    def get_value(self):
        return self._input.get_value()
    
    def set_value(self, value):
        self._input.set_value(value)

    def on_value_changed(self, prop: UdsProperty, value: Any):
        self.sigOut_changed.emit(self._prop, value)

class UdsPropertyTableView(QWidget):

    def __init__(self, properties: List[UdsProperty]):
        super().__init__()
        self.property_views: Dict[UdsProperty, UdsPropertyInput] = {}

        layout = QVBoxLayout()

        for i, prop in enumerate(properties):
            prop_input = UdsPropertyInput(prop)
            #prop_input.sig_changed.connect(self.on_property_changed)
            self.property_views[prop] = prop_input

            row_layout = QHBoxLayout()
            row_layout.addWidget(prop_input)
            layout.addLayout(row_layout)

        self.setLayout(layout)

    def get_property_values(self) -> Dict[UdsProperty, Any]:
        values = {}
        for prop, view in self.property_views.items():
            values[prop] = view.get_value()
        return values

    def update_properties(self, properties: Dict[UdsProperty, Any]):
        for prop, value in properties.items():
            if prop in self.property_views:
                view = self.property_views[prop]
                view.set_value(value)

class UdsPropertyEditor(QWidget, UdsNodeStatusListener):
    def __init__(self, node: Node, profile: UdsProfile, tool: UdsTool = None):
        super().__init__()
        self.node = node
        self.profile = profile
        self.tool = tool
        self.tool.add_listener(self)

        self.tables: Dict[str, UdsPropertyTableView] = {}

        tabs = QTabWidget(self)

        for group in profile.get_property_groups():
            table_view = UdsPropertyTableView(profile.get_properties_by_group(group))
            self.tables[group] = table_view
            scroll_layout = QVBoxLayout()
            scroll_layout.addWidget(table_view)
            scroll_layout.addStretch()
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(QWidget())
            scroll_area.widget().setLayout(scroll_layout)
            tabs.addTab(scroll_area, group)

        grid_layout = QGridLayout()

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send)
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load)

        grid_layout.addWidget(send_button, 0, 0)
        grid_layout.addWidget(load_button, 0, 1)

        progress = QProgressBar()
        grid_layout.addWidget(progress, 1, 0, 1, 2)

        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        main_layout.addLayout(grid_layout)
        self.setLayout(main_layout)

    def send(self):
        for group, table_view in self.tables.items():
            for prop, value in table_view.get_property_values().items():
                self.tool.set_property(self.node.address, prop.prop_id, value)

    def load(self):
        for group, table_view in self.tables.items():
            for prop in table_view.property_views.keys():
                self.tool.get_property(self.node.address, prop.prop_id)

    def on_property_change(self, node, prop: UdsProperty, data: UdsPropertyValue):
        for group, table_view in self.tables.items():
            table_view.update_properties({prop: data.value})
