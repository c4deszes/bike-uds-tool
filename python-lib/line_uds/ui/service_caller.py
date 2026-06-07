from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import *

from typing import Any, List, Dict, Tuple, Union
from enum import Enum

from line_protocol.network.nodes import Node
from line_uds.uds_tool import UdsTool, UdsNodeStatusListener, UdsPropertyValue
from line_uds.profile import UdsProfile, UdsProperty, UdsService, UdsServiceParam, UdsBoolTypeDefinition, UdsIntTypeDefinition, UdsEnumTypeDefinition, UdsTypeDefinition, UdsVoidTypeDefinition

from line_uds.ui.input_types import UdsNumericInput, UdsBooleanInput, UdsEnumInput, UdsStructInput

import logging
logger = logging.getLogger(__name__)

class UdsServiceParamInput(QWidget):

    def __init__(self, param: UdsServiceParam):
        super().__init__()
        self.param = param
        if isinstance(self.param.param_type, UdsIntTypeDefinition):
            # TODO: set min/max values based on type definition
            self._input = UdsNumericInput(0,
                                          self.param.param_type.get_minimum(),
                                          self.param.param_type.get_maximum())
        elif isinstance(self.param.param_type, UdsBoolTypeDefinition):
            self._input = UdsBooleanInput(False)
        elif isinstance(self.param.param_type, UdsEnumTypeDefinition):
            self._input = UdsEnumInput(self.param.param_type.values, self.param.param_type.values[0])
        else:
            self._input = UdsStructInput()

        layout = QHBoxLayout()
        layout.addWidget(QLabel(param.param_name, self))
        layout.addWidget(self._input)
        self.setLayout(layout)

    def get_value(self):
        return self._input.get_value()
    
    def lock(self):
        self._input.lock()

    def unlock(self):
        self._input.unlock()

class UdsServiceParamTableView(QWidget):

    def __init__(self, params: List[UdsServiceParam]):
        super().__init__()
        self.param_views: Dict[UdsServiceParam, UdsServiceParamInput] = {}

        layout = QVBoxLayout()

        for i, param in enumerate(params):
            param_input = UdsServiceParamInput(param)
            #param_input.sig_changed.connect(self.on_param_changed)
            self.param_views[param] = param_input

            row_layout = QHBoxLayout()
            row_layout.addWidget(param_input)
            layout.addLayout(row_layout)

        self.setLayout(layout)

    def get_param_values(self) -> Dict[UdsServiceParam, any]:
        values = {}
        for param, view in self.param_views.items():
            values[param] = view.get_value()
        return values

    def lock(self):
        for _, view in self.param_views.items():
            view.lock()

    def unlock(self):
        for _, view in self.param_views.items():
            view.unlock()
    
class UdsServiceResultView(QWidget):
    
    def __init__(self, return_type: UdsTypeDefinition):
        super().__init__()
        self.return_type = return_type
        
        self.return_value = QTextEdit()
        self.return_value.setReadOnly(True)

        self.return_code = QLineEdit()
        self.return_code.setDisabled(True)

        layout = QVBoxLayout()
        status_box = QHBoxLayout()
        status_box.addWidget(QLabel("Status:"))
        status_box.addWidget(self.return_code)
        layout.addLayout(status_box)

        if not isinstance(return_type, UdsVoidTypeDefinition):
            layout.addWidget(self.return_value)
        self.setLayout(layout)

    def update_result(self, status_code: int, result: Any = None):
        self.return_code.setText(str(status_code))
        if result is not None and not isinstance(self.return_type, UdsVoidTypeDefinition):
            self.return_value.clear()
            self.return_value.setText(result)

class UdsServiceView(QWidget):

    sigOut_call = pyqtSignal(UdsService, dict)
    sigIn_finish = pyqtSignal(int, object)
    
    def __init__(self, service: UdsService):
        super().__init__()
        self.service = service
        label = QLabel(f"Service {self.service.service_id}: {self.service.name}", self)

        self.param_table = UdsServiceParamTableView(self.service.params)
        self.result_view = UdsServiceResultView(self.service.return_type)

        # Params
        param_view = QVBoxLayout()
        param_group = QGroupBox("Parameters")
        param_view.addWidget(self.param_table)
        param_group.setLayout(param_view)

        results_view = QVBoxLayout()
        results_group = QGroupBox("Results")
        results_group.setLayout(results_view)
        results_view.addWidget(self.result_view)

        self.call_button = QPushButton("Call Service")
        self.call_button.clicked.connect(self.do_call_service)

        main_layout = QVBoxLayout()
        main_layout.addWidget(label)
        if len(self.service.params) > 0:
            main_layout.addWidget(param_group)
        main_layout.addWidget(results_group)
        main_layout.addWidget(self.call_button)
        self.setLayout(main_layout)

        self.sigIn_finish.connect(self.finish_call)

    def lock(self):
        self.param_table.lock()
        self.call_button.setDisabled(True)

    def unlock(self):
        self.param_table.unlock()
        self.call_button.setDisabled(False)

    def do_call_service(self):
        self.lock()

        param_values = self.param_table.get_param_values()
        self.sigOut_call.emit(self.service, param_values)

    def finish_call(self, status_code: int = None, result: Any = None):
        self.unlock()
        self.result_view.update_result(status_code, result)

class UdsServiceInterface(QWidget, UdsNodeStatusListener):

    def __init__(self, node: Node, profile: UdsProfile, tool: UdsTool = None):
        super().__init__()
        self.node = node
        self.profile = profile
        self.tool = tool
        self.tool.add_listener(self)

        self.service_views: Dict[UdsService, UdsServiceView] = {}
        
        tabs = QTabWidget(self)
        
        for group in profile.get_service_groups():
            group_services = [service for service in profile.services if service.group == group]
            group_widget = QWidget()
            group_layout = QVBoxLayout()
            for service in group_services:
                service_view = UdsServiceView(service)
                service_view.sigOut_call.connect(self.call_service)
                self.service_views[service] = service_view
                group_layout.addWidget(service_view)
            group_layout.addStretch()
            group_widget.setLayout(group_layout)
            tabs.addTab(group_widget, group)

        main_layout = QHBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def call_service(self, service: UdsService, params: Dict[UdsServiceParam, Any]):
        self.tool.call_service(self.node.address, service.service_id, {param.param_name: value for param, value in params.items()})

    def on_service_finish(self, node: Node, service: UdsService, result):
        service_view = self.service_views[service]
        service_view.sigIn_finish.emit(0, result.value)

    def on_service_failure(self, node: Node, service: UdsService, exception: Exception):
        service_view = self.service_views[service]
        service_view.sigIn_finish.emit(-1, "N/A")
