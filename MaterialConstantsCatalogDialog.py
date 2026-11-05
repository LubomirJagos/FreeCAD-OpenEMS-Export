from PySide import QtGui, QtCore, QtWidgets
from PySide.QtCore import Slot
from PySide.QtCore import QSortFilterProxyModel, Qt
import os
import csv

#import needed local classes
import sys
import glob

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
path_to_ui = os.path.join(APP_DIR, "ui", "dialog_MaterialConstantsCatalog.ui")

#
# Main GUI panel class
#
class MaterialConstantsCatalogDialog(QtCore.QObject):

	def __init__(self, parentForm=None):
		QtCore.QObject.__init__(self)

		self.APP_DIR = APP_DIR
		self.cadInterfaceType = APP_CONTEXT
		self.parentForm = parentForm

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

		#
		#	Settings for table view
		#
		self.model = QtGui.QStandardItemModel()
		self.model.setHorizontalHeaderLabels([
			"Material", "Permittivity (εr)",
			"Permeability (μr)", "Conductivity (σ)",
			"Loss Tangent (tanδ)"
		])

		# Proxy for filtering
		self.proxy = QtCore.QSortFilterProxyModel()
		self.proxy.setSourceModel(self.model)
		self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self.proxy.setFilterKeyColumn(0)  # filter by material name

		# View
		self.form.table.setModel(self.proxy)
		self.form.table.setSortingEnabled(True)
		self.form.table.setSelectionBehavior(QtGui.QTableView.SelectRows)
		self.form.table.horizontalHeader().setStretchLastSection(True)
		self.form.table.setEditTriggers(QtGui.QAbstractItemView.EditTrigger.NoEditTriggers)

		# Connect search
		self.form.search_bar.textChanged.connect(
			self.proxy.setFilterFixedString
		)

		self.form.table.doubleClicked.connect(self.onRowDoubleClicked)

		# Find first CSV in catalog folder
		print("Listing material catalog available csv files:")

		# catalog_path = os.path.join(os.path.dirname(__file__), "materialConstantsCatalog")
		catalog_path = os.path.join(APP_DIR, "materialConstantsCatalog")
		csv_files = glob.glob(os.path.join(catalog_path, "*.csv"))

		print(csv_files)

		if not csv_files:
			raise FileNotFoundError(f"No CSV files found in {catalog_path}")

		csv_path = csv_files[0]  # take first file found
		self.form.inputFileLineEdit.setText(csv_path)

		# ... rest of your init ...
		self.load_csv(csv_path)

		print(f"----> init finished")

	def show(self):
		self.form.show()
		self.form.search_bar.setText("")	#clear search bar
		self.form.raise_()

	def close(self):
		self.form.close()

	def buttonOpenFileClicked(self):
		filename, filter = QtWidgets.QFileDialog.getOpenFileName(parent=self.form, caption='Open material constants file', dir=self.APP_DIR)
		self.form.inputFileLineEdit.setText(filename)
		self.load_csv(filename)

	def load_csv(self, path):
		self.model.removeRows(0, self.model.rowCount())
		with open(path, newline='') as f:
			reader = csv.DictReader(f, delimiter=';')
			for row in reader:
				self.model.appendRow([
					QtGui.QStandardItem(row["material"]),
					QtGui.QStandardItem(row["permittivity"]),
					QtGui.QStandardItem(row["permeability"]),
					QtGui.QStandardItem(row["conductivity"]),
					QtGui.QStandardItem(row["loss_tangent"]),
				])


	def onRowDoubleClicked(self, index):
		# Get row from proxy model (accounts for sorting/filtering)
		row = index.row()

		# Read values from each column
		material_name = self.proxy.index(row, 0).data()
		permittivity = self.proxy.index(row, 1).data()
		permeability = self.proxy.index(row, 2).data()
		conductivity = self.proxy.index(row, 3).data()
		loss_tangent = self.proxy.index(row, 4).data()

		# Set values to parent form spin widgets
		if self.parentForm is not None:
			self.parentForm.materialUserDefinedRadioButton.click()
			self.parentForm.materialSettingsNameInput.setText(str(material_name))
			self.parentForm.materialEpsilonNumberInput.setValue(float(permittivity))
			self.parentForm.materialMueNumberInput.setValue(float(permeability))
			self.parentForm.materialSigmaNumberInput.setValue(float(conductivity))
			self.parentForm.materialTanDeltaNumberInput.setValue(float(loss_tangent))

			# Close catalog dialog after selection
			self.close()

####################################################################################################################################################################
# End of PANEL definition
####################################################################################################################################################################
 
if __name__ == "__main__":

	if APP_CONTEXT in ["FreeCAD"]:
		panel = MaterialConstantsCatalogDialog()
		panel.show()
	else:
		print("This app cannot run standalone, just in context of FreeCAD.")

	print("MaterialConstantsCatalogDialog.py finished.")
