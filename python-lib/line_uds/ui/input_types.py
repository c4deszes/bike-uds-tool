from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIntValidator

from typing import Any, List, Dict, Tuple, Union
from enum import Enum

class InputWidget():

    def set_value(self, value: Any):
        raise NotImplementedError()

    def get_value(self) -> Any:
        raise NotImplementedError()
    
    def lock(self):
        raise NotImplementedError()
    
    def unlock(self):
        raise NotImplementedError()

class UdsNumericInput(QWidget, InputWidget):

    sigOut_changed = pyqtSignal(int)

    def __init__(self, value: int = 0, min_value: int = None, max_value: int = None):
        super().__init__()
        self._input = QLineEdit(self)
        self._input.setText(str(value))
        self._input.editingFinished.connect(self.on_editing_finished)

        if min_value is not None and max_value is not None:
            validator = QIntValidator()
            validator.setRange(min_value, max_value)
            self._input.setValidator(validator)

        layout = QHBoxLayout()
        layout.addWidget(self._input)
        self.setLayout(layout)

    def set_value(self, value):
        self._input.setText(str(value))

    def get_value(self):
        return int(self._input.text())
    
    def lock(self):
        self._input.setDisabled(True)

    def unlock(self):
        self._input.setDisabled(False)

    def on_editing_finished(self):
        try:
            value = int(self._input.text())
            self.sigOut_changed.emit(value)
        except ValueError:
            pass

class UdsBooleanInput(QWidget, InputWidget):
    
    sigOut_changed = pyqtSignal(bool)

    def __init__(self, value: bool = False):
        super().__init__()
        self._checkbox = QCheckBox(self)
        self._checkbox.setChecked(value)
        self._checkbox.stateChanged.connect(self.on_state_changed)

        layout = QHBoxLayout()
        layout.addWidget(self._checkbox)
        self.setLayout(layout)

    def set_value(self, value: bool):
        self._checkbox.setChecked(value)

    def get_value(self) -> bool:
        return self._checkbox.isChecked()

    def lock(self):
        self._checkbox.setDisabled(True)

    def unlock(self):
        self._checkbox.setDisabled(False)

    def on_state_changed(self, state: bool):
        self.sigOut_changed.emit(state)

class UdsEnumInput(QWidget, InputWidget):
    
    sigOut_changed = pyqtSignal(str)

    def __init__(self, options: List[str], value: str = None):
        super().__init__()
        self._combobox = QComboBox(self)
        for option in options:
            self._combobox.addItem(option)
        if value is not None:
            self._combobox.setCurrentIndex(self._combobox.findText(value))
        self._combobox.currentIndexChanged.connect(self.on_index_changed)

        layout = QHBoxLayout()
        layout.addWidget(self._combobox)
        self.setLayout(layout)

    def set_value(self, value: str):
        self._combobox.setCurrentIndex(self._combobox.findText(value))

    def get_value(self) -> str:
        return self._combobox.currentText()

    def lock(self):
        self._combobox.setDisabled(True)

    def unlock(self):
        self._combobox.setDisabled(False)

    def on_index_changed(self, index):
        value = self._combobox.itemText(index)
        self.sigOut_changed.emit(value)

class UdsStructInput(QWidget):
    # For simplicity, we will just display a placeholder for struct inputs
    def __init__(self):
        super().__init__()
        label = QLabel("Struct input not implemented", self)
        layout = QHBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)
