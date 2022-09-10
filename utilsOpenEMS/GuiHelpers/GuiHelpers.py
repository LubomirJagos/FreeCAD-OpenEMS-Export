from PySide import QtGui, QtCore

class GuiHelpers:
    def __init__(self, form, statusBar = None):
        self.form = form
        self.statusBar = statusBar

    def displayMessage(self, msgText, forceModal=True):
        if (not forceModal) and (self.statusBar is not None):
            self.statusBar.showMessage(msgText, 5000)
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(msgText)
            msgBox.exec()
