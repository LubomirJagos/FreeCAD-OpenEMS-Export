from PySide import QtGui, QtCore, QtWidgets
from PySide.QtCore import Slot
from PySide.QtCore import QSortFilterProxyModel, Qt
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
		self.guiHelpers = GuiHelpers(self.parentForm, statusBar = self.form.statusBar, APP_DIR=APP_DIR)
		self.guiSignals = GuiSignals()

		#
		#	BUTTONS HANDLERS
		#
		self.form.buttonOpenFile.clicked.connect(self.buttonOpenFileClicked)
		self.form.buttonImportPcb.clicked.connect(self.buttonImportPcbClicked)

		self.form.buttonImportPartModels.clicked.connect(self.buttonImportPartModelsClicked)
		self.form.buttonCreateLumpedElementsCategories.clicked.connect(self.buttonCreateLumpedElementsCategoriesClicked)
		self.form.buttonDetectLumpedParts.clicked.connect(self.buttonDetectLumpedPartsClicked)
		self.form.partPositionSetButton.clicked.connect(self.partPositionSetButtonClicked)
		self.form.buttonAssignLumpedElementsCategories.clicked.connect(self.buttonAssignLumpedElementsCategoriesClicked)

		#
		#	Settings for table view
		#
		self.model = QtGui.QStandardItemModel()
		self.model.setHorizontalHeaderLabels(["part name", "part value"])

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

		print(f"----> init finished")

	def show(self):
		self.form.show()
		self.form.raise_()

	def close(self):
		self.form.close()

	def buttonOpenFileClicked(self):
		# 1. Get the current text from the line edit
		current_path = self.form.inputFileLineEdit.text().strip()

		# 2. Determine the starting directory
		if current_path and os.path.exists(current_path):
			# If a valid file path exists, extract its directory
			start_dir = os.path.dirname(current_path)
		else:
			# Fallback to your application default directory
			start_dir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())

		filename, filter = QtWidgets.QFileDialog.getOpenFileName(parent=self.form, caption='Open KiCAD PCB file', dir=start_dir)
		self.form.inputFileLineEdit.setText(filename)

	def buttonImportPcbClicked(self):
		filename = self.form.inputFileLineEdit.text()
		combo = self.form.importSettingsCombo.isChecked()
		fuseCoppers = self.form.importSettingsFuseCoppers.isChecked()

		pcb = kicad.KicadFcad(filename)
		pcb.make(combo=combo, fuseCoppers=fuseCoppers, load_parts=False)	#LuboJ: load parts should be enabled later as they will be loaded using my modified fcad_pcb rather than kicad stepup module

	def load_kicad_board(self, pcb_file, insertIntoCurrentDocument=True):
		try:
			import FreeCAD
			import FreeCADGui
		except:
			self.guiHelpers.displayMessage("<font color='#FF0000'><b>Error during import FreeCAD module, check if this addon is running from FreeCAD.</b></font>")
			return

		# 1. Add the StepUp module directory to sys.path
		user_mod_dir = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "kicadStepUpMod")
		if user_mod_dir not in sys.path:
			sys.path.append(user_mod_dir)

		# 2. Import the backend tool module instead of using the GUI command
		try:
			import kicadStepUptools as ksu
		except:
			self.guiHelpers.displayMessage("<font color='#FF0000'><b>Error during import KiCADStepUp module, check if it is installed.</b></font>")
			return

		# 4. Call the function directly with your path argument
		if os.path.exists(pcb_file):
			# This executes the exact same sequence as clicking the button,
			# but skips the popup file chooser dialog.
			ksu.onLoadBoard(pcb_file, insert=insertIntoCurrentDocument)

			FreeCAD.ActiveDocument.recompute()
			print("Board loaded silently!")
		else:
			print(f"Error: File not found at {pcb_file}")

	def buttonImportPartModelsClicked(self):
		target_pcb = self.form.inputFileLineEdit.text()
		self.load_kicad_board(target_pcb)

	def buttonCreateLumpedElementsCategoriesClicked(self):
		print("--> buttonCreateLumpedElementsCategoriesClicked(...)")

		partValuesList = []
		column_index = 1  # 0 is Col 1, 1 is Col 2

		# Loop through every row
		for row in range(self.model.rowCount()):
			index = self.model.index(row, column_index)

			# Check if the cell is not empty/None
			if index is not None:
				partValuesList.append(self.model.data(index, Qt.DisplayRole))
			else:
				partValuesList.append("")  # Or None, depending on your needs

		filteredGeoObjectList = []
		for geoObj in self.cadHelpers.getObjects():
			if re.match("[RLC]{1}[0-9]+", geoObj.Label):
				print(f"----> {geoObj.Label}")
				filteredGeoObjectList.append(geoObj)

		for partValue in partValuesList:
			lumpedElementCategories = self.guiHelpers.getAllLumpedElementCategories()
			print("--> all lumped elements categories")
			print(lumpedElementCategories)
			if not partValue in lumpedElementCategories:
				self.parentForm.lumpedPartREnable.setChecked(False)
				self.parentForm.lumpedPartLEnable.setChecked(False)
				self.parentForm.lumpedPartCEnable.setChecked(False)

				self.parentForm.lumpedPartSettingsNameInput.setText(partValue)

				print(f"----> analyze part value {partValue}")
				match = re.match(r"^([0-9]+\.?[0-9]+)?([a-zA-Z]*)$", str(partValue))
				num_part, unit_part = match.groups()

				if partValue.endswith("Ohm"):
					self.parentForm.lumpedPartREnable.setChecked(True)
					self.parentForm.lumpedPartRInput.setValue(float(num_part))
					self.guiHelpers.setComboboxItem(self.parentForm.lumpedPartRUnits, unit_part)

				if partValue.endswith("H"):
					self.parentForm.lumpedPartLEnable.setChecked(True)
					self.parentForm.lumpedPartLInput.setValue(float(num_part))
					self.guiHelpers.setComboboxItem(self.parentForm.lumpedPartLUnits, unit_part)

				if partValue.endswith("F"):
					self.parentForm.lumpedPartCEnable.setChecked(True)
					self.parentForm.lumpedPartCInput.setValue(float(num_part))
					self.guiHelpers.setComboboxItem(self.parentForm.lumpedPartCUnits, unit_part)

				self.parentForm.lumpedPartSettingsAddButton.click()

	def buttonDetectLumpedPartsClicked(self):
		try:
			import FreeCAD
		except:
			self.guiHelpers.displayMessage("<font color='#FF0000'><b>Error during import FreeCAD module, check if this addon is running from FreeCAD.</b></font>")
			return

		try:
			user_mod_dir = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "kicadStepUpMod", "fcad_parser")
			if user_mod_dir not in sys.path:
				sys.path.append(user_mod_dir)

			from kicad_pcb import KicadPCB
		except:
			self.guiHelpers.displayMessage("<font color='#FF0000'><b>Error during import KiCADStepUp module, check if it is installed.</b></font>")
			return

		target_pcb = self.form.inputFileLineEdit.text()
		pcbObj = KicadPCB.load(target_pcb)

		lumpedElementList = {}
		for footprint in pcbObj.footprint:
			partName = footprint.property[0][1].strip('"')
			partValue = footprint.property[1][1].strip('"')
			print(f"--> {partName}:{partValue}")

			partUnits = ""
			if re.match("R[0-9]+", partName):
				partUnits = "Ohm"
				lumpedElementList[partName] = partValue + partUnits
			if re.match("L[0-9]+", partName):
				partUnits = "H"
				lumpedElementList[partName] = partValue + partUnits
			if re.match("C[0-9]+", partName):
				partUnits = "F"
				lumpedElementList[partName] = partValue + partUnits

		self.model.removeRows(0, self.model.rowCount())
		for name, value in lumpedElementList.items():
			self.model.appendRow([QtGui.QStandardItem(name), QtGui.QStandardItem(value)])

		print(lumpedElementList)

	def partPositionSetButtonClicked(self):
		# 1. Get the selection model and the data model
		selection_model = self.form.table.selectionModel()
		model = self.form.table.model()

		# 2. Get all selected cell indexes
		selected_indexes = selection_model.selectedIndexes()

		# 3. Extract unique row numbers (to avoid duplicating if multiple cells in the same row are selected)
		selected_rows = sorted(list(set(idx.row() for idx in selected_indexes)))

		# 4. Loop through the selected rows and grab Column 0 and Column 1
		selectedImportedLumpedParts = []
		for row in selected_rows:
			# Get index for Column 0 and Column 1
			col0_index = model.index(row, 0)
			col1_index = model.index(row, 1)

			# Extract the actual text/data
			partName = model.data(col0_index, Qt.DisplayRole)
			partValue = model.data(col1_index, Qt.DisplayRole)

			selectedImportedLumpedParts.append(partName)

		print("----> selected kicad parts:")
		print(selectedImportedLumpedParts)

		for obj in self.cadHelpers.getObjects():
			for partName in selectedImportedLumpedParts:
				if obj.Label == partName or obj.Label.startswith(partName+"_"):
					if self.form.partPositionAxis.currentText() == "x":
						obj.Placement.Base.x = self.form.partPosition.value()
					if self.form.partPositionAxis.currentText() == "y":
						obj.Placement.Base.y = self.form.partPosition.value()
					if self.form.partPositionAxis.currentText() == "z":
						obj.Placement.Base.z = self.form.partPosition.value()

	def buttonAssignLumpedElementsCategoriesClicked(self):
		# 1. Get the selection model and the data model
		selection_model = self.form.table.selectionModel()
		model = self.form.table.model()

		# 2. Get all selected cell indexes
		selected_indexes = selection_model.selectedIndexes()

		# 3. Extract unique row numbers (to avoid duplicating if multiple cells in the same row are selected)
		selected_rows = sorted(list(set(idx.row() for idx in selected_indexes)))

		# 4. Loop through the selected rows and grab Column 0 and Column 1
		selectedImportedLumpedParts = {}
		for row in selected_rows:
			# Get index for Column 0 and Column 1
			col0_index = model.index(row, 0)
			col1_index = model.index(row, 1)

			# Extract the actual text/data
			partName = model.data(col0_index, Qt.DisplayRole)
			partValue = model.data(col1_index, Qt.DisplayRole)

			if not partValue in selectedImportedLumpedParts.keys():
				selectedImportedLumpedParts[partValue] = []
			selectedImportedLumpedParts[partValue].append(partName)
		print("----> selected kicad parts:")
		print(selectedImportedLumpedParts)
		self.parentForm.objectAssignmentFilterLeft.setText("")
		self.parentForm.objectAssignmentFilterLeft.returnPressed.emit()

		for k in range(self.parentForm.objectAssignmentRightTreeWidget.topLevelItemCount()):
			categoryItem = self.parentForm.objectAssignmentRightTreeWidget.topLevelItem(k)
			categoryName = categoryItem.text(0)
			print(f"--> looking for lumped part category: {categoryName}")
			if categoryName == "LumpedPart":
				print("--> expanding lumped part category")
				categoryItem.setExpanded(True)

				for j in range(categoryItem.childCount()):
					groupItem = categoryItem.child(j)
					groupName = groupItem.text(0)

					if groupName in selectedImportedLumpedParts.keys():
						print(f"--> assign lumped part: {groupName}")
						for partName in selectedImportedLumpedParts[groupName]:
							for n in range(self.parentForm.objectAssignmentLeftTreeWidget.topLevelItemCount()):
								objectItem = self.parentForm.objectAssignmentLeftTreeWidget.topLevelItem(n)
								objectName = objectItem.text(0)
								if objectName.startswith(partName+"_") or objectName == partName:
									print(f"--> assign lumped part: {objectName} to {groupName}")
									self.parentForm.objectAssignmentLeftTreeWidget.setCurrentItem(objectItem)
									self.parentForm.objectAssignmentRightTreeWidget.setCurrentItem(groupItem)
									self.parentForm.moveRightButton.click()

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
