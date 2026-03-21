from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIntValidator

from typing import Any, List, Dict, Tuple, Union
from enum import Enum

from line_protocol.network.nodes import Node
from line_uds.uds_tool import UdsNodeStatus, UdsTool, UdsNodeStatusListener, UdsPropertyValue
from line_uds.profile import UdsProfile, UdsProperty, UdsService, UdsServiceParam, UdsBoolTypeDefinition, UdsIntTypeDefinition, UdsEnumTypeDefinition, UdsTypeDefinition, UdsVoidTypeDefinition

from line_uds.ui.property_editor import UdsPropertyEditor
from line_uds.ui.service_caller import UdsServiceInterface

class UdsNodeEditor(QWidget):

    def __init__(self, node: Node, profile: UdsProfile, tool: UdsTool = None):
        super().__init__()
        self.node = node
        self.profile = profile
        self.tool = tool

        main_layout = QHBoxLayout()
        self.property_editor = UdsPropertyEditor(node, profile, tool)
        self.service_panel = UdsServiceInterface(node, profile, tool)
        main_layout.addWidget(self.property_editor)
        main_layout.addWidget(self.service_panel)
        self.setLayout(main_layout)

class UdsNodesEditor(QWidget):

    def __init__(self, nodes: Dict[Node, UdsProfile], tool: UdsTool = None):
        super().__init__()
        self.tool = tool
        self.node_editors = {}
        tabs = QTabWidget(self)
        for node, profile in nodes.items():
            editor = UdsNodeEditor(node, profile, tool)
            self.node_editors[node] = editor
            tabs.addTab(editor, node.name)
        main_layout = QHBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
