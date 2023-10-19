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

		self.cadInterfaceType = APP_CONTEXT

		print(f"----> init finished")

	def show(self):
		self.form.show()

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
