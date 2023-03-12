from PySide.QtCore import Signal, QObject

class GuiSignals(QObject):
    materialsChanged = Signal(str)
