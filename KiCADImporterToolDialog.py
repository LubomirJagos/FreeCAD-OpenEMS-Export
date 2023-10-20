from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtCore import Slot
import os, sys
import re

#import needed local classes
import sys
import traceback

from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers
from utilsOpenEMS.GuiHelpers.FactoryCadInterface import FactoryCadInterface
from utilsOpenEMS.GuiHelpers.GuiSignals import GuiSignals

APP_CONTEXT = "None"

try:
	from utils3rdParty.fcad_pcb import kicad

	APP_CONTEXT = "FreeCAD"
except:
	pass

print(f"APP_CONTEXT set to {APP_CONTEXT}")

APP_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
path_to_ui = os.path.join(APP_DIR, "ui", "dialog_KiCAD_Importer.ui")

#
# Main GUI panel class
#
class KiCADImporterToolDialog(QtCore.QObject):

	def __init__(self):
		QtCore.QObject.__init__(self)

		self.APP_DIR = APP_DIR
		self.cadInterfaceType = APP_CONTEXT

		#
		# LOCAL OPENEMS OBJECT
		#
		self.cadHelpers = FactoryCadInterface.createHelper(self.APP_DIR)

		#
		# Change current path to script file folder
		#
		os.chdir(APP_DIR)

		# this will create a Qt widget from our ui file
		self.form = self.cadHelpers.loadUI(path_to_ui, self)

		#
		# GUI helpers function like display message box and so
		#
		self.guiHelpers = GuiHelpers(self.form, statusBar = self.form.statusBar, APP_DIR=APP_DIR)
		self.guiSignals = GuiSignals()

		#
		#	BUTTONS HANDLERS
		#
		self.form.buttonOpenFile.clicked.connect(self.buttonOpenFileClicked)
		self.form.buttonImportPcb.clicked.connect(self.buttonImportPcbClicked)

		print(f"----> init finished")

	def show(self):
		self.form.show()
		self.form.raise_()

	def close(self):
		self.form.close()

	def buttonOpenFileClicked(self):
		filename, filter = QtWidgets.QFileDialog.getOpenFileName(parent=self.form, caption='Open KiCAD PCB file', dir=self.APP_DIR)
		self.form.inputFileLineEdit.setText(filename)

	def buttonImportPcbClicked(self):
		filename = self.form.inputFileLineEdit.text()
		copper_thickness = self.form.copperThickness.value()
		board_thickness = self.form.boardThickness.value()
		combo = self.form.importSettingsCombo.isChecked()
		fuseCoppers = self.form.importSettingsFuseCoppers.isChecked()

		pcb = kicad.KicadFcad(filename)
		pcb.make(copper_thickness=copper_thickness, board_thickness=board_thickness, combo=combo, fuseCoppers=fuseCoppers)

####################################################################################################################################################################
# End of PANEL definition
####################################################################################################################################################################
 
if __name__ == "__main__":

	if APP_CONTEXT in ["FreeCAD"]:
		panel = KiCADImporterToolDialog()
		panel.show()
	else:
		print("This app cannot run standalone, just in context of FreeCAD.")

	print("KiCADImporterToolDialog.py finished.")
