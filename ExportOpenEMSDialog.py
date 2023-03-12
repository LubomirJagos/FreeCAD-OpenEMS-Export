from PySide import QtGui, QtCore
from PySide.QtCore import Slot
import FreeCAD as App
import FreeCADGui, Part, os
import re
import Draft
import random
import numpy as np
import collections
import math

#import needed local classes
import sys

sys.path.insert(0, os.path.dirname(__file__))

from utilsOpenEMS.SettingsItem.SettingsItem import SettingsItem
from utilsOpenEMS.SettingsItem.PortSettingsItem import PortSettingsItem
from utilsOpenEMS.SettingsItem.ExcitationSettingsItem import ExcitationSettingsItem
from utilsOpenEMS.SettingsItem.LumpedPartSettingsItem import LumpedPartSettingsItem
from utilsOpenEMS.SettingsItem.MaterialSettingsItem import MaterialSettingsItem
from utilsOpenEMS.SettingsItem.SimulationSettingsItem import SimulationSettingsItem
from utilsOpenEMS.SettingsItem.GridSettingsItem import GridSettingsItem
from utilsOpenEMS.SettingsItem.FreeCADSettingsItem import FreeCADSettingsItem

from utilsOpenEMS.ScriptLinesGenerator.OctaveScriptLinesGenerator import OctaveScriptLinesGenerator
from utilsOpenEMS.ScriptLinesGenerator.PythonScriptLinesGenerator import PythonScriptLinesGenerator

from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers
from utilsOpenEMS.GuiHelpers.FreeCADHelpers import FreeCADHelpers
from utilsOpenEMS.GuiHelpers.FreeCADDocObserver import FreeCADDocObserver

from utilsOpenEMS.GuiHelpers.GuiSignals import GuiSignals

from utilsOpenEMS.SaveLoad.IniFile import IniFile

# UI file (use Qt Designer to modify)
from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

path_to_ui = "./ui/dialog.ui"

#
# Main GUI panel class
#
class ExportOpenEMSDialog(QtCore.QObject):

	def finished(self):
		self.observer.endObservation()
		self.observer = None
		print("Observer terminated.")

	def eventFilter(self, object, event):
		if event.type() == QtCore.QEvent.Close:
			self.finished()
		return super(ExportOpenEMSDialog, self).eventFilter(object, event)
		
	def __init__(self):		
		QtCore.QObject.__init__(self)

		#
		#	Direcotry for generated .m file for openEMS
		#		- by default set to None, that means simulation file should be generated into current directory
		#
		self.simulationOutputDir = None

		#
		# LOCAL OPENEMS OBJECT
		#
		self.freeCADHelpers = FreeCADHelpers()

		#
		# Change current path to script file folder
		#
		abspath = os.path.abspath(__file__)
		dname = os.path.dirname(abspath)
		os.chdir(dname)

		# this will create a Qt widget from our ui file
		self.form = FreeCADGui.PySideUic.loadUi(path_to_ui, self)
		# self.form.finished.connect(self.finished) # QDialog event
		self.form.installEventFilter(self)
		
		# add a statusBar widget (comment to revert to QMessageBox if there are any problems)
		self.statusBar = QtGui.QStatusBar()
		self.statusBar.setStyleSheet("QStatusBar{border-top: 1px outset grey;}")
		self.form.dialogVertLayout.addWidget(self.statusBar)

		#
		# instantiate script generators using this dialog form
		#
		self.octaveScriptGenerator = OctaveScriptLinesGenerator(self.form, statusBar = self.statusBar)
		self.pythonScriptGenerator = PythonScriptLinesGenerator(self.form, statusBar = self.statusBar)
		self.scriptGenerator = self.octaveScriptGenerator													#variable which store current script generator

		#
		#	Connect function to change script generator
		#
		self.form.radioButton_octaveType.clicked.connect(self.radioButtonOutputScriptsTypeClicked)
		self.form.radioButton_pythonType.clicked.connect(self.radioButtonOutputScriptsTypeClicked)

		#
		# GUI helpers function like display message box and so
		#
		self.guiHelpers = GuiHelpers(self.form, statusBar = self.statusBar)
		self.guiSignals = GuiSignals()

		#
		# INI file object to used for save/load operation
		#
		self.simulationSettingsFile = IniFile(self.form, statusBar = self.statusBar, guiSignals = self.guiSignals)

		#
		# TOP LEVEL ITEMS / Category Items (excitation, grid, materials, ...)
		#
		self.guiHelpers.initRightColumnTopLevelItems()

		#select first item
		topItem = self.form.objectAssignmentRightTreeWidget.itemAt(0,0)
		self.form.objectAssignmentRightTreeWidget.setCurrentItem(topItem)

		self.form.moveLeftButton.clicked.connect(self.onMoveLeft)
		self.form.moveRightButton.clicked.connect(self.onMoveRight)
		
		#########################################################################################################
		#	Left Column - FreeCAD objects list
		#########################################################################################################

		self.initLeftColumnTopLevelItems()	
		self.form.objectAssignmentLeftTreeWidget.itemDoubleClicked.connect(self.objectAssignmentLeftTreeWidgetItemDoubleClicked)	
		
		#########################################################################################################
		#	RIGHT COLUMN - Simulation Object Assignment
		#########################################################################################################
		
		self.form.objectAssignmentRightTreeWidget.itemSelectionChanged.connect(self.objectAssignmentRightTreeWidgetItemSelectionChanged)
		
		self.form.objectAssignmentRightTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  
		self.form.objectAssignmentRightTreeWidget.customContextMenuRequested.connect(self.objectAssignmentRightTreeWidgetContextClicked)
		self.form.objectAssignmentRightTreeWidget.itemDoubleClicked.connect(self.objectAssignmentRightTreeWidgetItemDoubleClicked)

		#########################################################################################################
		#########################################################################################################
		#########################################################################################################

		#
		# SETTINGS FOR BUTTONS CLICK, functions assignments
		#
		self.form.gridSettingsAddButton.clicked.connect(self.gridSettingsAddButtonClicked)
		self.form.gridSettingsRemoveButton.clicked.connect(self.gridSettingsRemoveButtonClicked)
		self.form.gridSettingsUpdateButton.clicked.connect(self.gridSettingsUpdateButtonClicked)

		self.form.materialSettingsAddButton.clicked.connect(self.materialSettingsAddButtonClicked)
		self.form.materialSettingsRemoveButton.clicked.connect(self.materialSettingsRemoveButtonClicked)
		self.form.materialSettingsUpdateButton.clicked.connect(self.materialSettingsUpdateButtonClicked)
		self.guiSignals.materialsChanged.connect(self.materialsChanged)

		self.form.excitationSettingsAddButton.clicked.connect(self.excitationSettingsAddButtonClicked)
		self.form.excitationSettingsRemoveButton.clicked.connect(self.excitationSettingsRemoveButtonClicked)
		self.form.excitationSettingsUpdateButton.clicked.connect(self.excitationSettingsUpdateButtonClicked)

		self.form.portSettingsAddButton.clicked.connect(self.portSettingsAddButtonClicked)
		self.form.portSettingsRemoveButton.clicked.connect(self.portSettingsRemoveButtonClicked)
		self.form.portSettingsUpdateButton.clicked.connect(self.portSettingsUpdateButtonClicked)

		self.form.lumpedPartSettingsAddButton.clicked.connect(self.lumpedPartSettingsAddButtonClicked)
		self.form.lumpedPartSettingsRemoveButton.clicked.connect(self.lumpedPartSettingsRemoveButtonClicked)
		self.form.lumpedPartSettingsUpdateButton.clicked.connect(self.lumpedPartSettingsUpdateButtonClicked)

		#
		# Handle function for grid radio buttons click
		#
		self.form.userDefinedRadioButton.clicked.connect(self.userDefinedRadioButtonClicked)
		self.form.fixedCountRadioButton.clicked.connect(self.fixedCountRadioButtonClicked)
		self.form.fixedDistanceRadioButton.clicked.connect(self.fixedDistanceRadioButtonClicked)

		# Handle function for MATERIAL RADIO BUTTONS
		self.form.materialUserDefinedRadioButton.toggled.connect(self.materialUserDeinedRadioButtonToggled)	
		self.form.materialConductingSheetRadioButton.toggled.connect(self.materialConductingSheetRadioButtonToggled)

		#
		# Clicked on "Generate OpenEMS Script"
		#		
		self.form.generateOpenEMSScriptButton.clicked.connect(self.generateOpenEMSScriptButtonClicked)

		#
		# Clicked on BUTTONS FOR OBJECT PRIORITIES
		#		
		self.form.moveupPriorityButton.clicked.connect(self.moveupPriorityButtonClicked)
		self.form.movedownPriorityButton.clicked.connect(self.movedownPriorityButtonClicked)

		#
		# Clicked on BUTTONS FOR MESH PRIORITIES
		#		
		self.form.moveupMeshPriorityButton.clicked.connect(self.moveupPriorityMeshButtonClicked)
		self.form.movedownMeshPriorityButton.clicked.connect(self.movedownPriorityMeshButtonClicked)

		#
		#	Octave/Matlab script generating buttons handlers
		#
		self.form.eraseAuxGridButton.clicked.connect(self.eraseAuxGridButtonClicked)														# Clicked on "Erase aux Grid"
		self.form.abortSimulationButton.clicked.connect(lambda: self.abortSimulationButtonClicked(self.simulationOutputDir))													# Clicked on "Write ABORT Simulation File"
		self.form.drawS11Button.clicked.connect(lambda: self.scriptGenerator.drawS11ButtonClicked(self.simulationOutputDir))			# Clicked on "Write Draw S11 Script"
		self.form.drawS21Button.clicked.connect(lambda: self.scriptGenerator.drawS21ButtonClicked(self.simulationOutputDir))			# Clicked on "Write Draw S21 Script"
		self.form.writeNf2ffButton.clicked.connect(lambda: self.scriptGenerator.writeNf2ffButtonClicked(self.simulationOutputDir))	# Clicked on "Write NF2FF"

		#
		# GRID
		#	- button "Display gridlines...."
		#	- button "Create userdef..."
		#	- select rectangular or cylindrical grid
		#		
		self.form.createUserdefGridLinesFromCurrentButton.clicked.connect(self.createUserdefGridLinesFromCurrentButtonClicked)
		self.form.displayXYGridLinesInModelButton.clicked.connect(self.displayXYGridLinesInModelButtonClicked)
		self.form.gridRectangularRadio.toggled.connect(self.gridCoordsTypeChoosed)
		self.form.gridCylindricalRadio.toggled.connect(self.gridCoordsTypeChoosed)

		#
		# Material, Grid, Excitation, ... item changed handler functions.
		#		
		self.form.materialSettingsTreeView.currentItemChanged.connect(self.materialTreeWidgetItemChanged)	
		self.form.excitationSettingsTreeView.currentItemChanged.connect(self.excitationTreeWidgetItemChanged)	
		self.form.gridSettingsTreeView.currentItemChanged.connect(self.gridTreeWidgetItemChanged)	
		self.form.portSettingsTreeView.currentItemChanged.connect(self.portTreeWidgetItemChanged)	
		self.form.lumpedPartTreeView.currentItemChanged.connect(self.lumpedPartTreeWidgetItemChanged)	

		#PORT tab settings events handlers
		self.form.lumpedPortRadioButton.toggled.connect(self.portSettingsTypeChoosed)
		self.form.microstripPortRadioButton.toggled.connect(self.portSettingsTypeChoosed)
		self.form.circularWaveguidePortRadioButton.toggled.connect(self.portSettingsTypeChoosed)
		self.form.rectangularWaveguidePortRadioButton.toggled.connect(self.portSettingsTypeChoosed)
		self.form.etDumpPortRadioButton.toggled.connect(self.portSettingsTypeChoosed)
		self.form.htDumpPortRadioButton.toggled.connect(self.portSettingsTypeChoosed)
		self.form.nf2ffBoxPortRadioButton.toggled.connect(self.portSettingsTypeChoosed)

		#SIMULATION Boundary Conditions change event mapping
		self.form.BCxmin.currentIndexChanged.connect(self.BCxminCurrentIndexChanged)
		self.form.BCxmax.currentIndexChanged.connect(self.BCxmaxCurrentIndexChanged)
		self.form.BCymin.currentIndexChanged.connect(self.BCyminCurrentIndexChanged)
		self.form.BCymax.currentIndexChanged.connect(self.BCymaxCurrentIndexChanged)
		self.form.BCzmin.currentIndexChanged.connect(self.BCzminCurrentIndexChanged)
		self.form.BCzmax.currentIndexChanged.connect(self.BCzmaxCurrentIndexChanged)

		####################################################################################################
		# GUI SAVE/LOAD from file
		####################################################################################################
		self.form.saveToFileSettingsButton.clicked.connect(self.saveToFileSettingsButtonClicked)
		self.form.loadFromFileSettingsButton.clicked.connect(self.loadFromFileSettingsButtonClicked)

		#
		# FILTER LEFT COLUMN ITEMS
		#
		self.form.objectAssignmentFilterLeft.returnPressed.connect(self.applyObjectAssignmentFilter)

		# MinDecrement changed 
		self.form.simParamsMinDecrement.valueChanged.connect(self.simParamsMinDecrementValueChanged)
		
		### Other Initialization
		
		# initialize dB preview label with converted value
		self.simParamsMinDecrementValueChanged(self.form.simParamsMinDecrement.value()) 
	
		# create observer instance
		self.observer = FreeCADDocObserver()
		self.observer.objectCreated += self.freecadObjectCreated
		self.observer.objectChanged += self.freecadObjectChanged
		self.observer.objectDeleted += self.freecadBeforeObjectDeleted
		self.observer.startObservation()	

		#
		#	add default PEC material
		#
		self.materialAddPEC()
	
	def freecadObjectCreated(self, obj):
		print("freecadObjectCreated :{} ('{}')".format(obj.FullName, obj.Label))
		# A new object has been created. Only the list of available objects needs to be updated.
		filterStr = self.form.objectAssignmentFilterLeft.text()
		self.initLeftColumnTopLevelItems(filterStr)
		
	
	def freecadObjectChanged(self, obj, prop):
		print("freecadObjectChanged :{} ('{}') property changed: {}".format(obj.FullName, obj.Label, prop))
		if prop == 'Label':
			# The label (displayed name) of an object has changed.
			# (TODO) Update all mentions in the ObjectAssigments panel.
			filterStr = self.form.objectAssignmentFilterLeft.text()
			self.initLeftColumnTopLevelItems(filterStr)
		
		
	def freecadBeforeObjectDeleted(self,obj):
		# event is generated before object is being removed, so observing instances have to 
		# (TODO) un-list the object without drawing upon the FreeCAD objects list, and
		# (TODO) propagate changes to prevent corruption. 
		#    Simple approach: delete dependent entries.
		#    Advanced: remember and gray out deleted objects to allow settings to be restored when
		#    the user brings the object back with Redo.
		print("freecadObjectDeleted :{} ('{}')".format(obj.FullName, obj.Label))
		
		
	def simParamsMinDecrementValueChanged(self, newValue):
		if newValue == 0:
			s = '( -inf dB )'
		else:
			s = '( ' + str(np.round(10 * np.log10(newValue), decimals=2)) + ' dB )' 
		self.form.simParamsMinDecrementdBLabel.setText(s)

	def BCxminCurrentIndexChanged(self, index):
		self.form.PMLxmincells.setEnabled(self.form.BCxmin.currentText() == "PML")

	def BCxmaxCurrentIndexChanged(self, index):
		self.form.PMLxmaxcells.setEnabled(self.form.BCxmax.currentText() == "PML")

	def BCyminCurrentIndexChanged(self, index):
		self.form.PMLymincells.setEnabled(self.form.BCymin.currentText() == "PML")

	def BCymaxCurrentIndexChanged(self, index):
		self.form.PMLymaxcells.setEnabled(self.form.BCymax.currentText() == "PML")

	def BCzminCurrentIndexChanged(self, index):
		self.form.PMLzmincells.setEnabled(self.form.BCzmin.currentText() == "PML")

	def BCzmaxCurrentIndexChanged(self, index):
		self.form.PMLzmaxcells.setEnabled(self.form.BCzmax.currentText() == "PML")

	def eraseAuxGridButtonClicked(self):
		print("--> Start removing auxiliary gridlines from 3D view.")
		auxGridLines = App.ActiveDocument.Objects
		for gridLine in auxGridLines:
			print("--> Removing " + gridLine.Label + " from 3D view.")
			if "auxGridLine" in gridLine.Label:
				App.ActiveDocument.removeObject(gridLine.Name)
		print("--> End removing auxiliary gridlines from 3D view.")

	def createUserdefGridLinesFromCurrentButtonClicked(self):
		"""
		print("--> Start creating user defined grid from 3D model.")
		allObjects = App.ActiveDocument.Objects
		gridLineListX = []
		gridLineListY = []
		gridLineListZ = []
		for gridLine in allObjects:
			if "auxGridLine" in gridLine.Label:
				gridLineDirection = abs(gridLine.End - gridLine.Start)
				if (gridLineDirection[0] > 0):
					gridLineListX.append(gridLine)
		

		print("Discovered " + str(len(gridLineList)) + " gridlines in model.")
		print("--> End creating user defined grid from 3D model.")
		"""
		self.guiHelpers.displayMessage("createUserdefGridLinesFromCurrentButtonClicked")

	def displayXYGridLinesInModelButtonClicked(self):        
		print('displayXYGridLinesInModelButtonClicked: start draw whole XY grid for each object')

		gridCategory = self.form.objectAssignmentRightTreeWidget.findItems("Grid", QtCore.Qt.MatchFixedString)[0]
		for gridItemIndex in range(gridCategory.childCount()):
			for objIndex in range(gridCategory.child(gridItemIndex).childCount()):
				currItem = gridCategory.child(gridItemIndex).child(objIndex)
				print(currItem.text(0))
				self.objectDrawGrid(currItem)

	#
	#	Update NF2FF list at POSTPROCESSING TAB
	#
	def updateNF2FFList(self):
		#
		#	If Postprocessing tab is actived then fill combobox with nf2ff possible objects
		#
		self.form.portNf2ffObjectList.clear()
		for k in range(0, self.form.objectAssignmentRightTreeWidget.topLevelItemCount()):
			if (self.form.objectAssignmentRightTreeWidget.topLevelItem(k).text(0) == "Port"):
				for l in range(0, self.form.objectAssignmentRightTreeWidget.topLevelItem(k).childCount()):
					if (self.form.objectAssignmentRightTreeWidget.topLevelItem(k).child(l).data(0, QtCore.Qt.UserRole).type == "nf2ff box"):
						self.form.portNf2ffObjectList.addItem(self.form.objectAssignmentRightTreeWidget.topLevelItem(k).child(l).text(0))

	def updateObjectAssignmentRightTreeWidgetItemData(self, groupName, itemName, data):
		updatedItems = self.form.objectAssignmentRightTreeWidget.findItems(
			itemName, 
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)

		#there can be more items in right column which has same name, like air under MAterials and Grid, so always is needed to compare if parent
		#is same as parent from update function when this was called to update new settings
		for item in updatedItems:
			if item.parent().text(0) == groupName:
				item.setData(0, QtCore.Qt.UserRole, data)


	def objectAssignmentRightTreeWidgetItemSelectionChanged(self):
		currItemLabel = self.form.objectAssignmentRightTreeWidget.currentItem().text(0)
		print(currItemLabel)
		if (currItemLabel):
			FreeCADGui.Selection.clearSelection()
			self.freeCADHelpers.selectObjectByLabel(currItemLabel)

			
	def objectAssignmentRightTreeWidgetContextClicked(self, event):
		self.objAssignCtxMenu = QtGui.QMenu(self.form.objectAssignmentRightTreeWidget)
		action_expand   = self.objAssignCtxMenu.addAction("Expand all")
		actioN_collapse = self.objAssignCtxMenu.addAction("Collapse all")
		menu_action = self.objAssignCtxMenu.exec_(self.form.objectAssignmentRightTreeWidget.mapToGlobal(event))
		if menu_action is not None:
			if menu_action == action_expand:
				self.form.objectAssignmentRightTreeWidget.expandAll()
			if menu_action == actioN_collapse:
				self.form.objectAssignmentRightTreeWidget.collapseAll()
				
	#
	#	Handler for DOUBLE CLICK on grid item in FreeCAD objects list
	#
	def objectAssignmentLeftTreeWidgetItemDoubleClicked(self):
		self.onMoveRight()

	#
	#	Handler for DOUBLE CLICK on grid item in object assignment list
	#
	def objectAssignmentRightTreeWidgetItemDoubleClicked(self):
		currItem = self.form.objectAssignmentRightTreeWidget.currentItem()
		self.objectDrawGrid(currItem)

	#
	#	Draw auxiliary grid in FreeCAD 3D view
	#
	def objectDrawGrid(self, currItem):
		#
		#	Drawing auxiliary object grid for meshing.
		#
		#		example how to draw line for grid: self.freeCADHelpers.drawDraftLine("gridXY", [-78.0, -138.0, 0.0], [5.0, -101.0, 0.0])

		currSetting = currItem.data(0, QtCore.Qt.UserRole)
		genScript = ""

		#	must be selected FreeCAD object which is child of grid item which gridlines will be draw
		gridObj =  App.ActiveDocument.getObjectsByLabel(currItem.text(0))
		if ("FreeCADSettingItem" in currSetting.type):
			if ("GridSettingsItem" in currItem.parent().data(0, QtCore.Qt.UserRole).__class__.__name__):
				currSetting = currItem.parent().data(0, QtCore.Qt.UserRole)
			else:
				self.guiHelpers.displayMessage('Cannot draw grid for non-grid item object.')
				return
		else:
			self.guiHelpers.displayMessage('Cannot draw grid for object group.')
			return

		bbCoords = gridObj[0].Shape.BoundBox
	
		print("Start drawing aux grid for: " + currSetting.name)
		print("Enabled coords: " + str(currSetting.xenabled) + " " + str(currSetting.yenabled) + " " + str(currSetting.zenabled))

		#getting model boundaries to draw gridlines properly
		modelMinX, modelMinY, modelMinZ, modelMaxX, modelMaxY, modelMaxZ = self.freeCADHelpers.getModelBoundaryBox(self.form.objectAssignmentRightTreeWidget)

		#don't know why I put here this axis list code snippet probably to include case if there are some auxiliary axis but now seems useless
		#THERE IS QUESTION IN WHICH PLANE GRID SHOULD BE DRAWN IF in XY, XZ or YZ
		currGridAxis = self.form.auxGridAxis.currentText().lower()
		print("Aux grid axis: " + currGridAxis)

		refUnit = currSetting.getSettingsUnitAsNumber()
		#refUnit = 1
		print("Current object grid units set as number to: refUnit: " + str(refUnit))

		"""
		axisList = collections.deque(['x', 'y', 'z'])
		while axisList[0] != currGridAxis:
			axisList.rotate()
		"""

		if (currSetting.coordsType == 'cylindrical' and currGridAxis == "z"):

			if (currSetting.getType() == 'Fixed Distance'):
				#need to be done for this case
				pass

			elif (currSetting.getType() == 'Fixed Count'):

	            #collecting Z coordinates where grid will be drawn, gird will be drawn in XY plane
				zAuxGridCoordList = []
				if (currSetting.zenabled):
					if int(currSetting.getXYZ(refUnit)['z']) != 0:

						if int(currSetting.getXYZ(refUnit)['z']) == 1:
							zlines = np.array([(bbCoords.ZMin + bbCoords.ZMax)/2])
						else:
							zlines = np.linspace(bbCoords.ZMin, bbCoords.ZMax, int(currSetting.getXYZ(refUnit)['z']))
							
						#collecting Z coordinates where grid layers will be drawn
						for zGridLine in zlines:
							zAuxGridCoordList.append(zGridLine)

				print("zlines")
				print(zAuxGridCoordList)
				if len(zAuxGridCoordList) == 0:
					zAuxGridCoordList.append(bbCoords.ZMax)
	
				for zAuxGridCoord in zAuxGridCoordList:
					
					bbPointsVectors = [App.Vector(bbCoords.YMin, bbCoords.XMin, 0), App.Vector(bbCoords.YMin, bbCoords.XMax, 0), App.Vector(bbCoords.YMax, bbCoords.XMin, 0), App.Vector(bbCoords.YMax, bbCoords.XMax, 0)]
					angle1 = math.atan2(bbCoords.YMin, bbCoords.XMin) + 2*math.pi % (2*math.pi)
					angle2 = math.atan2(bbCoords.YMin, bbCoords.XMax) + 2*math.pi % (2*math.pi)
					angle3 = math.atan2(bbCoords.YMax, bbCoords.XMin) + 2*math.pi % (2*math.pi)
					angle4 = math.atan2(bbCoords.YMax, bbCoords.XMax) + 2*math.pi % (2*math.pi)
					
					minAngle = min([angle1, angle2, angle3, angle4])
					maxAngle = max([angle1, angle2, angle3, angle4])						
					radius = max([math.sqrt(modelMinX**2 + modelMinY**2), math.sqrt(modelMaxX**2 + modelMaxY**2)])

					print("Calculate ylines for cylindrical coords.")
					print("minAngle: " + str(minAngle))
					print("maxAngle: " + str(maxAngle))
					print("radius: " + str(radius))						

					#DRAW X LINES auxiliary grid in 3D view
					if (currSetting.xenabled):						
						a = np.array([angle1, angle2, angle3, angle4])
						indicesMin = a.argmin()
						indicesMax = a.argmax()
						closestLineToCenter = bbPointsVectors[indicesMin] - bbPointsVectors[indicesMax]

						#minRadius = closestLineToCenter.distanceToPoint(App.Vector(0,0,0))
						minRadius = abs((bbPointsVectors[indicesMax].x - bbPointsVectors[indicesMin].x)*bbPointsVectors[indicesMin].y - (bbPointsVectors[indicesMax].y - bbPointsVectors[indicesMin].y)*bbPointsVectors[indicesMin].x)/closestLineToCenter.Length
						maxRadius = max([math.sqrt(bbCoords.XMin**2 + bbCoords.YMin**2), math.sqrt(bbCoords.XMax**2 + bbCoords.YMax**2)])

						if float(currSetting.getXYZ(refUnit)['x']) == 1:
							xlines = np.array([(minRadius + maxRadius)/2])
						else:
							xlines = np.linspace(minRadius, maxRadius, int(currSetting.getXYZ(refUnit)['x']))
							
						for xGridLine in xlines:
							self.freeCADHelpers.drawDraftCircle("auxGridLine", App.Vector(0,0,zAuxGridCoord), xGridLine)
		
					#DRAW Y LINES auxiliary grid in 3D view
					if (currSetting.yenabled):												
						if float(currSetting.getXYZ(refUnit)['y']) == 1:
							ylines = np.array([(minAngle, maxAngle)/2])
						else:
							ylines = np.linspace(minAngle, maxAngle, int(currSetting.getXYZ(refUnit)['y']))
							
						print(ylines)

						for yGridLine in ylines:
							self.freeCADHelpers.drawDraftLine("auxGridLine", [0, 0, zAuxGridCoord], [math.cos(yGridLine)*radius, math.sin(yGridLine)*radius, zAuxGridCoord])

		elif (currSetting.coordsType == 'rectangular' and currGridAxis == "z"):

			#######################################################################################################################################################################
		  	# Z grid axis
			#######################################################################################################################################################################

			print("Drawing GRID in Z axis.")

			if (currSetting.getType() == 'Fixed Distance'):
	
				#here adding Z coordinates for which grid will be drawn so grid will be drawn in XY plane, so here are collected just Z coords for which it will be drawn
				zAuxGridCoordList = []
				if (currSetting.zenabled):
					if float(currSetting.getXYZ(refUnit)['z']) != 0:
						zlines = np.arange(bbCoords.ZMin, bbCoords.ZMax, currSetting.getXYZ(refUnit)['z'])    #split Z interval and generate Z layers
						for zGridLine in zlines:
							zAuxGridCoordList.append(zGridLine)
				if len(zAuxGridCoordList) == 0:
					zAuxGridCoordList.append(bbCoords.ZMax)
	
				for zAuxGridCoord in zAuxGridCoordList:
					#DRAW X LINES auxiliary grid in 3D view
					if (currSetting.xenabled):
						if float(currSetting.getXYZ(refUnit)['x']) !=  0:
							xlines = np.arange(bbCoords.XMin, bbCoords.XMax, currSetting.getXYZ(refUnit)['x'])
							for xGridLine in xlines:
								#self.freeCADHelpers.drawDraftLine("auxGridLine", [xGridLine, bbCoords.YMin, zAuxGridCoord], [xGridLine, bbCoords.YMax, zAuxGridCoord])
								self.freeCADHelpers.drawDraftLine("auxGridLine", [xGridLine, modelMinY, zAuxGridCoord], [xGridLine, modelMaxY, zAuxGridCoord])
		
					#DRAW Y LINES auxiliary grid in 3D view
					if (currSetting.yenabled):
						if float(currSetting.getXYZ(refUnit)['y']) != 0:
							ylines = np.arange(bbCoords.YMin, bbCoords.YMax, currSetting.getXYZ(refUnit)['y'])
							for yGridLine in ylines:
								#self.freeCADHelpers.drawDraftLine("auxGridLine", [bbCoords.XMin, yGridLine, zAuxGridCoord], [bbCoords.XMax, yGridLine, zAuxGridCoord])
								self.freeCADHelpers.drawDraftLine("auxGridLine", [modelMinX, yGridLine, zAuxGridCoord], [modelMaxX, yGridLine, zAuxGridCoord])
	
			elif (currSetting.getType() == 'Fixed Count'):
	
	            #collecting Z coordinates where grid will be drawn, grid will be drawn in XY plane
				zAuxGridCoordList = []
				if (currSetting.zenabled):
					if float(currSetting.getXYZ(refUnit)['z']) != 0:
						if float(currSetting.getXYZ(refUnit)['z']) == 1:
							zlines = np.arange(bbCoords.ZMin, bbCoords.ZMax, int(currSetting.getXYZ(refUnit)['z']))
						else:
							zlines = np.array([(bbCoords.ZMin + bbCoords.ZMax)/2])
							
						#collecting Z coordinates where grid layers will be drawn
						for zGridLine in zlines:
							zAuxGridCoordList.append(zGridLine)
				if len(zAuxGridCoordList) == 0:
					zAuxGridCoordList.append(bbCoords.ZMax)
	
				for zAuxGridCoord in zAuxGridCoordList:
					#DRAW X LINES auxiliary grid in 3D view
					if (currSetting.xenabled):
						if float(currSetting.getXYZ(refUnit)['x']) == 1:
							xlines = np.array([(bbCoords.XMin + bbCoords.XMax)/2])
						else:
							xlines = np.linspace(bbCoords.XMin, bbCoords.XMax, int(currSetting.getXYZ(refUnit)['x']))
							
						for xGridLine in xlines:
							#self.freeCADHelpers.drawDraftLine("auxGridLine", [xGridLine, bbCoords.YMin, zAuxGridCoord], [xGridLine, bbCoords.YMax, zAuxGridCoord])
							self.freeCADHelpers.drawDraftLine("auxGridLine", [xGridLine, modelMinY, zAuxGridCoord], [xGridLine, modelMaxY, zAuxGridCoord])
		
					#DRAW Y LINES auxiliary grid in 3D view
					if (currSetting.yenabled):
						if float(currSetting.getXYZ(refUnit)['y']) == 1:
							ylines = np.array([(bbCoords.YMin + bbCoords.YMax)/2])
						else:
							ylines = np.linspace(bbCoords.YMin, bbCoords.YMax, int(currSetting.getXYZ(refUnit)['y']))

						for yGridLine in ylines:
							#self.freeCADHelpers.drawDraftLine("auxGridLine", [bbCoords.XMin, yGridLine, zAuxGridCoord], [bbCoords.XMax, yGridLine, zAuxGridCoord])
							self.freeCADHelpers.drawDraftLine("auxGridLine", [modelMinX, yGridLine, zAuxGridCoord], [modelMaxX, yGridLine, zAuxGridCoord])
	
			elif (currSetting.getType() == 'User Defined'):
				#UNIT FOR MESH										
				genScript += "meshUnit = " + currSetting.getUnitAsScriptLine() + "; % all length in mm\n"
				genScript += "mesh = " + currSetting.getXYZ(refUnit) + ";\n"

		elif (currSetting.coordsType == 'rectangular' and currGridAxis == "x"):

			#######################################################################################################################################################################
		  	# X grid axis - STILL EXPERIMENTAL require REPAIR
			#######################################################################################################################################################################

			print("Drawing GRID in X axis.")
			
			if (currSetting.getType() == 'Fixed Distance'):
	
				#here adding Z coordinates for which grid will be drawn so grid will be drawn in XY plane, so here are collected just Z coords for which it will be drawn
				xAuxGridCoordList = []
				if (currSetting.xenabled):
					if float(currSetting.getXYZ(refUnit)['x']) != 0:
						xlines = np.arange(bbCoords.XMin, bbCoords.XMax, currSetting.getXYZ(refUnit)['x'])    #split Z interval and generate Z layers
						for xGridLine in xlines:
							xAuxGridCoordList.append(xGridLine)
				if len(xAuxGridCoordList) == 0:
					xAuxGridCoordList.append(bbCoords.XMax)
	
				for xAuxGridCoord in xAuxGridCoordList:
					#DRAW Z LINES auxiliary grid in 3D view
					if (currSetting.zenabled):
						if float(currSetting.getXYZ(refUnit)['z']) !=  0:
							zlines = np.arange(bbCoords.ZMin, bbCoords.ZMax, currSetting.getXYZ(refUnit)['z'])
							for zGridLine in zlines:
								self.freeCADHelpers.drawDraftLine("auxGridLine", [xAuxGridCoord, modelMinY, zGridLine], [xAuxGridCoord, modelMaxY, zGridLine])
		
					#DRAW Y LINES auxiliary grid in 3D view
					if (currSetting.yenabled):
						if float(currSetting.getXYZ(refUnit)['y']) != 0:
							ylines = np.arange(bbCoords.YMin, bbCoords.YMax, currSetting.getXYZ(refUnit)['y'])
							for yGridLine in ylines:
								self.freeCADHelpers.drawDraftLine("auxGridLine", [xAuxGridCoord, yGridLine, modelMinZ], [xAuxGridCoord, yGridLine, modelMaxZ])
	
			elif (currSetting.getType() == 'Fixed Count'):
	
	            #collecting Z coordinates where grid will be drawn, grid will be drawn in XY plane
				xAuxGridCoordList = []
				if (currSetting.xenabled):
					if float(currSetting.getXYZ(refUnit)['x']) != 0:
						if float(currSetting.getXYZ(refUnit)['x']) == 1:
							xlines = np.array([(bbCoords.XMin + bbCoords.XMax)/2])
						else:
							xlines = np.arange(bbCoords.XMin, bbCoords.XMax, int(currSetting.getXYZ(refUnit)['x']))   #collecting Z coordinates where grid layers will be drawn
							
						for xGridLine in xlines:
							xAuxGridCoordList.append(xGridLine)

				if len(xAuxGridCoordList) == 0:
					xAuxGridCoordList.append(bbCoords.XMax)
	
				for xAuxGridCoord in xAuxGridCoordList:
					#DRAW X LINES auxiliary grid in 3D view
					if (currSetting.zenabled):
						if float(currSetting.getXYZ(refUnit)['z']) == 1:
							zlines = np.array([(bbCoords.ZMin + bbCoords.ZMax)/2])
						else:
							zlines = np.linspace(bbCoords.ZMin, bbCoords.ZMax, int(currSetting.getXYZ(refUnit)['z']))
						
						for zGridLine in zlines:
							self.freeCADHelpers.drawDraftLine("auxGridLine", [xAuxGridCoord, modelMinY, zGridLine], [xAuxGridCoord, modelMaxY, zGridLine])
		
					#DRAW Y LINES auxiliary grid in 3D view
					if (currSetting.yenabled):
						if float(currSetting.getXYZ(refUnit)['y']) == 1:
							ylines = np.array([(bbCoords.YMin + bbCoords.YMax)/2])
						else:
							ylines = np.linspace(bbCoords.YMin, bbCoords.YMax, int(currSetting.getXYZ(refUnit)['y']))
						
						for yGridLine in ylines:
								self.freeCADHelpers.drawDraftLine("auxGridLine", [xAuxGridCoord, yGridLine, modelMinZ], [xAuxGridCoord, yGridLine, modelMaxZ])
	
			elif (currSetting.getType() == 'User Defined'):
				#UNIT FOR MESH										
				genScript += "meshUnit = " + currSetting.getUnitAsScriptLine() + "; % all length in mm\n"
				genScript += "mesh = " + currSetting.getXYZ(refUnit) + ";\n"
				
		elif (currSetting.coordsType == 'rectangular' and currGridAxis == "y"):

			#######################################################################################################################################################################
		  	# Y grid axis - NOT IMPLEMENTED
			#######################################################################################################################################################################

			print("Drawing GRID in Y axis.")

			if (currSetting.getType() == 'Fixed Distance'):
	
				#here adding Z coordinates for which grid will be drawn so grid will be drawn in XY plane, so here are collected just Z coords for which it will be drawn
				yAuxGridCoordList = []
				if (currSetting.yenabled):
					if float(currSetting.getXYZ(refUnit)['y']) != 0:
						ylines = np.arange(bbCoords.YMin, bbCoords.YMax, currSetting.getXYZ(refUnit)['y'])    #split Y interval and generate Z layers
						for yGridLine in ylines:
							yAuxGridCoordList.append(yGridLine)
				if len(yAuxGridCoordList) == 0:
					yAuxGridCoordList.append(bbCoords.YMax)
	
				for yAuxGridCoord in yAuxGridCoordList:
					#DRAW Z LINES auxiliary grid in 3D view
					if (currSetting.zenabled):
						if float(currSetting.getXYZ(refUnit)['z']) !=  0:
							zlines = np.arange(bbCoords.ZMin, bbCoords.ZMax, currSetting.getXYZ(refUnit)['z'])
							for zGridLine in zlines:
								self.freeCADHelpers.drawDraftLine("auxGridLine", [modelMinX, yAuxGridCoord, zGridLine], [modelMaxX, yAuxGridCoord, zGridLine])
		
					#DRAW X LINES auxiliary grid in 3D view
					if (currSetting.xenabled):
						if float(currSetting.getXYZ(refUnit)['x']) != 0:
							xlines = np.arange(bbCoords.XMin, bbCoords.XMax, currSetting.getXYZ(refUnit)['x'])
							for xGridLine in xlines:
								self.freeCADHelpers.drawDraftLine("auxGridLine", [xGridLine, yAuxGridCoord, modelMinZ], [xGridLine, yAuxGridCoord, modelMaxZ])
	
			elif (currSetting.getType() == 'Fixed Count'):
	
	            #collecting Z coordinates where grid will be drawn, grid will be drawn in XY plane
				yAuxGridCoordList = []
				if (currSetting.yenabled):
					if float(currSetting.getXYZ(refUnit)['y']) != 0:
						if float(currSetting.getXYZ(refUnit)['y']) == 1:
							ylines = np.array([(bbCoords.YMin + bbCoords.YMax)/2])
						else:
							ylines = np.arange(bbCoords.YMin, bbCoords.YMax, int(currSetting.getXYZ(refUnit)['y']))   #collecting Y coordinates where grid layers will be drawn

						for yGridLine in ylines:
							yAuxGridCoordList.append(yGridLine)

				if len(yAuxGridCoordList) == 0:
					yAuxGridCoordList.append(bbCoords.YMax)
	
				for yAuxGridCoord in yAuxGridCoordList:
					#DRAW Z LINES auxiliary grid in 3D view
					if (currSetting.zenabled):
						if float(currSetting.getXYZ(refUnit)['z']) == 1:
							zlines = np.array([(bbCoords.ZMin + bbCoords.ZMax)/2])
						else:
							zlines = np.linspace(bbCoords.ZMin, bbCoords.ZMax, int(currSetting.getXYZ(refUnit)['z']))

						for zGridLine in zlines:
							self.freeCADHelpers.drawDraftLine("auxGridLine", [modelMinX, yAuxGridCoord, zGridLine], [modelMaxX, yAuxGridCoord, zGridLine])
		
					#DRAW X LINES auxiliary grid in 3D view
					if (currSetting.xenabled):
						if float(currSetting.getXYZ(refUnit)['x']) == 1:
							xlines = np.array([(bbCoords.XMin + bbCoords.XMax)/2])
						else:
							xlines = np.linspace(bbCoords.XMin, bbCoords.XMax, int(currSetting.getXYZ(refUnit)['x']))

						for xGridLine in xlines:
							self.freeCADHelpers.drawDraftLine("auxGridLine", [xGridLine, yAuxGridCoord, modelMinZ], [xGridLine, yAuxGridCoord, modelMaxZ])
	
			elif (currSetting.getType() == 'User Defined'):
				#UNIT FOR MESH										
				genScript += "meshUnit = " + currSetting.getUnitAsScriptLine() + "; % all length in mm\n"
				genScript += "mesh = " + currSetting.getXYZ(refUnit) + ";\n"

		#update whole document
		App.ActiveDocument.recompute()
		print("---> Aux grid drawing finished. \n" + genScript)

	#######################################################################################################################################################################
  	# END GRID DRAWING
	#######################################################################################################################################################################
	
	def initLeftColumnTopLevelItems(self, filterStr = ""):
		self.form.objectAssignmentLeftTreeWidget.clear()

		items = self.freeCADHelpers.getOpenEMSObjects(filterStr)
		treeItems = []
		for i in items:
			print("openEMS object to export:" + i.Label)

			# ADDING ITEMS with UserData object which storethem in intelligent way
			#
			topItem = QtGui.QTreeWidgetItem([i.Label])
			itemData = FreeCADSettingsItem(name = i.Label, freeCadId = i.Name)
			topItem.setData(0, QtCore.Qt.UserRole, itemData)
			if (i.Name.find("Sketch") > -1):
				topItem.setIcon(0, QtGui.QIcon("./img/wire.svg")) 
			elif (i.Name.find("Discretized_Edge") > -1): 
				topItem.setIcon(0, QtGui.QIcon("./img/curve.svg"))
			else:
				topItem.setIcon(0, QtGui.QIcon("./img/object.svg")) 
			treeItems.append(topItem)

		
		self.form.objectAssignmentLeftTreeWidget.insertTopLevelItems(0, treeItems)

	#
	#	ABORT simulation button handler
	#		write empty file ABORT into tmp/ folder what should abort simulation in next iteration
	#
	def abortSimulationButtonClicked(self, outputDir=None):
		programdir = os.path.dirname(App.ActiveDocument.FileName)

		if not outputDir is None:
			absoluteOutputDir = os.path.join(outputDir, "tmp")
		else:
			absoluteOutputDir = os.path.join(programdir, "tmp")

		outFile = os.path.join(absoluteOutputDir, "ABORT")
		print("------------->" + outFile)

		if os.path.exists(absoluteOutputDir):
			f = open(outFile, "w+", encoding='utf-8')
			f.write("THIS CAN BE JUST EMPTY FILE. ABORT simulation.")
			f.close()
			print(f"ABORT file written into {absoluteOutputDir}")
			self.guiHelpers.displayMessage(f"ABORT file written into {absoluteOutputDir}", forceModal=False)
		else:
			print(f"Simulation tmp/ folder not found at expected path: {absoluteOutputDir}")
			self.guiHelpers.displayMessage(f"Simulation tmp/ folder not found at expected path: {absoluteOutputDir}", forceModal=False)

	def materialUserDeinedRadioButtonToggled(self):
		if (self.form.materialUserDefinedRadioButton.isChecked()):
			self.form.materialEpsilonNumberInput.setEnabled(True)
			self.form.materialMueNumberInput.setEnabled(True)
			self.form.materialKappaNumberInput.setEnabled(True)
			self.form.materialSigmaNumberInput.setEnabled(True)
		else:
			self.form.materialEpsilonNumberInput.setEnabled(False)
			self.form.materialMueNumberInput.setEnabled(False)
			self.form.materialKappaNumberInput.setEnabled(False)
			self.form.materialSigmaNumberInput.setEnabled(False)

	def materialConductingSheetRadioButtonToggled(self):
		if (self.form.materialConductingSheetRadioButton.isChecked()):
			self.form.materialConductingSheetThickness.setEnabled(True)
			self.form.materialConductingSheetUnits.setEnabled(True)
			self.form.materialConductingSheetConductivity.setEnabled(True)
		else:
			self.form.materialConductingSheetThickness.setEnabled(False)
			self.form.materialConductingSheetUnits.setEnabled(False)
			self.form.materialConductingSheetConductivity.setEnabled(False)

	def applyObjectAssignmentFilter(self):
		print("Filter left column")
		filterStr = self.form.objectAssignmentFilterLeft.text()
		self.initLeftColumnTopLevelItems(filterStr)

	#
	#	Get COORDINATION TYPE
	#		this function traverse priority tree view and return coordination type of the most high item
	#
	#	returns string coords type
	#
	def getModelCoordsType(self):
		for k in range(self.form.objectAssignmentPriorityTreeView.topLevelItemCount()):
			priorityObjNameSplitted = self.form.objectAssignmentPriorityTreeView.topLevelItem(k).text(0).split(',')
			if (priorityObjNameSplitted[0].strip() == "Grid"):
				gridCategoryItem = self.form.objectAssignmentRightTreeWidget.findItems("Grid", QtCore.Qt.MatchFixedString)
				gridObj = [gridCategoryItem[0].child(x) for x in range(gridCategoryItem[0].childCount()) if gridCategoryItem[0].child(x).text(0) == priorityObjNameSplitted[1].strip()]
				return gridObj[0].data(0, QtCore.Qt.UserRole).coordsType
		return ""

	def getSimParamsUnitsStr(self):
		units = self.form.simParamsUnitsNumberInput.currentText()
		if (units == 'Hz'):
			units2 = ''
			pass
		elif(units == "kHz"):
			units2 = 'e3'
			pass
		elif(units == "MHz"):
			units2 = 'e6'
			pass
		elif(units == "GHz"):
			units2 = 'e9'
			pass
		return units2

	def getSimParamsFcStr(self):
		units = self.getSimParamsUnitsStr()
		return str(self.form.simParamFcNumberInput.value()) + units

	def getSimParamsF0Str(self):
		units = self.getSimParamsUnitsStr()
		return str(self.form.simParamF0NumberInput.value()) + units

	def show(self):
		self.form.show()

	#
	#	Button << to assign object from FreeCAD to OpenEMS solver structure
	#
	def onMoveLeft(self):
		print("Button << clicked.")
		rightItem = self.form.objectAssignmentRightTreeWidget.selectedItems()[0]

		#
		#	REMOVE FROM PRIORITY OBJECT ASSIGNMENT tree view
		#
		prioritySettingsItemName = rightItem.parent().parent().text(0) + ", " + rightItem.parent().text(0) + ", " + rightItem.text(0)

		#going through items in priority object list and searching for name, when matched it's removed from list
		itemsCount = self.form.objectAssignmentPriorityTreeView.topLevelItemCount()
		for k in range(itemsCount):
			priorityItem = self.form.objectAssignmentPriorityTreeView.topLevelItem(k)
			if prioritySettingsItemName in priorityItem.text(0):
				self.form.objectAssignmentPriorityTreeView.takeTopLevelItem(k)
				print("Removing item " + prioritySettingsItemName + " from priority object list.")
				break	#this will break loop SO JUST ONE ITEM FROM PRIORITY LIST IS DELETED

		#
		#	REMOVE FROM PRIORITY MESH ASSIGNMENT tree view
		#

		#going through items in priority mesh list and searching for name, when matched it's removed from list
		itemsCount = self.form.meshPriorityTreeView.topLevelItemCount()
		for k in range(itemsCount):
			priorityItem = self.form.meshPriorityTreeView.topLevelItem(k)
			if prioritySettingsItemName in priorityItem.text(0):
				self.form.meshPriorityTreeView.takeTopLevelItem(k)
				print("Removing item " + prioritySettingsItemName + " from priority mesh list.")
				break	#this will break loop SO JUST ONE ITEM FROM PRIORITY LIST IS DELETED

		#
		#	REMOVE ITEM FROM OpenEMS Simulation assignments tree view
		#
		rightItem.parent().removeChild(rightItem)

		return

	#
	#	Button >> to remove object assignment
	#
	def onMoveRight(self):
		print("Button >> clicked.")

		# here are created 2 clones of item in left column to be putted into right column into some category
		# as material, port or something and there is also priority list where another clone is inserted
		leftItem = self.form.objectAssignmentLeftTreeWidget.selectedItems()[0].clone()
		leftItem2 = self.form.objectAssignmentLeftTreeWidget.selectedItems()[0].clone()

		rightItem = self.form.objectAssignmentRightTreeWidget.selectedItems()[0]

		#check if item is type of SettingsItem based on its class name and if yes then add subitems into it
		print("Adding item into right column, type: " + str(type(rightItem.data(0, QtCore.Qt.UserRole))))
		reResult = re.search("([A-Za-z]*)SettingsItem'", str(type(rightItem.data(0, QtCore.Qt.UserRole))))
		if (reResult):
			if (reResult.group(1).lower() == 'excitation'):
				self.guiHelpers.displayMessage("Excitation doesn't accept any objects.")
				return
			if (reResult.group(1).lower() == 'freecad'):
				self.guiHelpers.displayMessage("FreeCAD object cannot have child item.")
				return
			else:
				print("Item " + leftItem.text(0) + " added into " + rightItem.text(0))
	
			#
			# ADD ITEM INTO RIGHT LIST, first clone is inserted
			#
			rightItem.addChild(leftItem)
			rightItem.setExpanded(True)

			#
			# ADD ITEM INTO PRIORITY LIST, must be 2nd copy that's reason why there is used leftItem2 to have different clone of left item
			#
			addItemToPriorityList = True

			newAddedItemName = rightItem.parent().text(0) + ", " + rightItem.text(0) + ", " + leftItem2.text(0)
			leftItem2.setData(0, QtCore.Qt.UserRole, rightItem.data(0, QtCore.Qt.UserRole))
	
			#
			#	Check if item is already in priority list, must be in same category as material, port or so to be not added due it will be duplicate
			#	There are 2 priority lists:
			#		1. objects priority for 3D objects - materials, ports
			#		2. mesh priority objects
			#
			isGridObjectToBeAdded = reResult.group(1).lower() == 'grid'

			if (isGridObjectToBeAdded):
				priorityListItems = self.form.meshPriorityTreeView.findItems(newAddedItemName, QtCore.Qt.MatchFixedString)
				addItemToPriorityList = len(priorityListItems) == 0	#check for DUPLICATES
			else:
				priorityListItems = self.form.objectAssignmentPriorityTreeView.findItems(newAddedItemName, QtCore.Qt.MatchFixedString)
				addItemToPriorityList = len(priorityListItems) == 0	#check for DUPLICATES
			
			if addItemToPriorityList:
				#	Item is gonna be added into list:
				#		1. copy icon of object category in right list to know what is added (PORT, MATERIAL, Excitation, ...)
				#		2. add item into priority list with according icon and category				
				leftItem2.setText(0, newAddedItemName)

				if (isGridObjectToBeAdded):
					self.form.meshPriorityTreeView.insertTopLevelItem(0, leftItem2)						
				else:
					self.form.objectAssignmentPriorityTreeView.insertTopLevelItem(0, leftItem2)

				#
				# If grid settings is not set to be top priority lines, therefore it's disabled (because then it's not take into account when generate mesh lines and it's overlapping something)
				#
				self.guiHelpers.updateMeshPriorityDisableItems()
				
				leftItem2.setIcon(0, rightItem.parent().icon(0)) #set same icon as parent have means same as category
				print("Object " + leftItem2.text(0)+ " added into priority list")
			else:
				#
				#	NO ITEM WOULD BE ADDED BECAUSE ALREADY IS IN LIST
				#
				print("Object " + leftItem2.text(0)+ " in category " + rightItem.parent().text(0) + " already in priority list")


		else:
				self.guiHelpers.displayMessage("Item must be added into some settings inside category.")


	#
	#	PRIORITY OBJECT LIST move item UP
	#
	def moveupPriorityButtonClicked(self):
		currItemIndex = self.form.objectAssignmentPriorityTreeView.indexOfTopLevelItem(self.form.objectAssignmentPriorityTreeView.currentItem())
		if currItemIndex > 0:
			takenItem = self.form.objectAssignmentPriorityTreeView.takeTopLevelItem(currItemIndex)
			self.form.objectAssignmentPriorityTreeView.insertTopLevelItem(currItemIndex-1, takenItem)
			self.form.objectAssignmentPriorityTreeView.setCurrentItem(takenItem)

	#
	#	PRIORITY OBJECT LIST move item DOWN
	#
	def movedownPriorityButtonClicked(self):
		currItemIndex = self.form.objectAssignmentPriorityTreeView.indexOfTopLevelItem(self.form.objectAssignmentPriorityTreeView.currentItem())
		countAllItems = self.form.objectAssignmentPriorityTreeView.topLevelItemCount()
		if currItemIndex < countAllItems-1:
			takenItem = self.form.objectAssignmentPriorityTreeView.takeTopLevelItem(currItemIndex)
			self.form.objectAssignmentPriorityTreeView.insertTopLevelItem(currItemIndex+1, takenItem)
			self.form.objectAssignmentPriorityTreeView.setCurrentItem(takenItem)

	#
	#	PRIORITY MESH LIST move item UP
	#
	def moveupPriorityMeshButtonClicked(self):
		currItemIndex = self.form.meshPriorityTreeView.indexOfTopLevelItem(self.form.meshPriorityTreeView.currentItem())
		if currItemIndex > 0:
			takenItem = self.form.meshPriorityTreeView.takeTopLevelItem(currItemIndex)
			self.form.meshPriorityTreeView.insertTopLevelItem(currItemIndex-1, takenItem)
			self.form.meshPriorityTreeView.setCurrentItem(takenItem)

	#
	#	PRIORITY MESH LIST move item DOWN
	#
	def movedownPriorityMeshButtonClicked(self):
		currItemIndex = self.form.meshPriorityTreeView.indexOfTopLevelItem(self.form.meshPriorityTreeView.currentItem())
		countAllItems = self.form.meshPriorityTreeView.topLevelItemCount()
		if currItemIndex < countAllItems-1:
			takenItem = self.form.meshPriorityTreeView.takeTopLevelItem(currItemIndex)
			self.form.meshPriorityTreeView.insertTopLevelItem(currItemIndex+1, takenItem)
			self.form.meshPriorityTreeView.setCurrentItem(takenItem)

	def checkTreeWidgetForDuplicityName(self,refTreeWidget, itemName):
		isDuplicityName = False
		iterator = QtGui.QTreeWidgetItemIterator(refTreeWidget, QtGui.QTreeWidgetItemIterator.All)
		while iterator.value():
			item = iterator.value()
			if item.text(0) == itemName:
				isDuplicityName = True
				self.guiHelpers.displayMessage("Please change name, item with this name already exists.", True)
			iterator +=1
		return isDuplicityName

	#
	#	Save button clicked
	#
	def saveToFileSettingsButtonClicked(self):
		outputFile = self.simulationSettingsFile.writeToFile()

		if outputFile is None:
			return

		programname = os.path.basename(outputFile)
		programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
		self.simulationOutputDir = f"{os.path.dirname(outputFile)}/{programbase}_openEMS_simulation"
		print(f"-----> saveToFileSettingsButtonClicked, setting simulationOutputDir: {self.simulationOutputDir}")

	def loadFromFileSettingsButtonClicked(self):
		outputFile = self.simulationSettingsFile.readFromFile()

		if outputFile is None:
			return

		programname = os.path.basename(outputFile)
		programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
		self.simulationOutputDir = f"{os.path.dirname(outputFile)}/{programbase}_openEMS_simulation"
		print(f"-----> loadFromFileSettingsButtonClicked, setting simulationOutputDir: {self.simulationOutputDir}")

		#
		#	Add default PEC material during load
		#
		self.materialAddPEC()

	#
	#	Change current scripts type generator based on radiobutton from UI
	#		if no type by accident is choosed, octave script generator is used
	#
	def radioButtonOutputScriptsTypeClicked(self):
		if self.form.radioButton_octaveType.isChecked():
			self.scriptGenerator = self.octaveScriptGenerator
			self.guiHelpers.displayMessage("Output type changed to octave", forceModal=False)
		elif self.form.radioButton_pythonType.isChecked():
			self.scriptGenerator = self.pythonScriptGenerator
			self.guiHelpers.displayMessage("Output type changed to python", forceModal=False)
		else:
			self.scriptGenerator = self.octaveScriptGenerator
			self.guiHelpers.displayMessage("Some error - output type changed to default octave", forceModal=False)

	#
	#	After click on generate openEMS script file button there is check if settings are saved, if not user is asked if he want's to save settings if not
	#	all simulation connected files will be generated inside local directory next to freecad file.
	#
	def generateOpenEMSScriptButtonClicked(self):
		if (self.simulationOutputDir is None or self.simulationOutputDir == ""):
			saveSettingsFlag = self.guiHelpers.displayYesNoMessage("Simulation settings aren't saved till now, do you want to save them? It's recommended to save sttings, otherwise simulaation files will be generated in same folder as FreeCAD file.")
			if saveSettingsFlag:
				self.saveToFileSettingsButtonClicked()

		#write result .m file into subfolder named after .ini file next to simulation settings .ini file
		print(f"----> start saving file into {self.simulationOutputDir}")

		self.scriptGenerator.generateOpenEMSScript(self.simulationOutputDir)

	# GRID SETTINGS
	#   _____ _____  _____ _____     _____ ______ _______ _______ _____ _   _  _____  _____ 
	#  / ____|  __ \|_   _|  __ \   / ____|  ____|__   __|__   __|_   _| \ | |/ ____|/ ____|
	# | |  __| |__) | | | | |  | | | (___ | |__     | |     | |    | | |  \| | |  __| (___  
	# | | |_ |  _  /  | | | |  | |  \___ \|  __|    | |     | |    | | | . ` | | |_ |\___ \ 
	# | |__| | | \ \ _| |_| |__| |  ____) | |____   | |     | |   _| |_| |\  | |__| |____) |
	#  \_____|_|  \_\_____|_____/  |_____/|______|  |_|     |_|  |_____|_| \_|\_____|_____/ 
	#
	def fixedCountRadioButtonClicked(self):
		self.form.userDefinedGridLinesTextInput.setEnabled(False)
		self.form.gridTopPriorityLinesCheckbox.setEnabled(True)

	def fixedDistanceRadioButtonClicked(self):
		self.form.userDefinedGridLinesTextInput.setEnabled(False)
		self.form.gridTopPriorityLinesCheckbox.setEnabled(True)

	def userDefinedRadioButtonClicked(self):
		self.form.userDefinedGridLinesTextInput.setEnabled(True)

		self.form.gridTopPriorityLinesCheckbox.setCheckState(QtCore.Qt.Unchecked)
		self.form.gridTopPriorityLinesCheckbox.setEnabled(False)
		
	def getCurrentSimulationGridType(self):
		isCoordTypeRectangular = True

		#none grid items defined
		if self.form.gridSettingsTreeView.invisibleRootItem().childCount() == 0:
			return None

		#there are grid items defined, so going through them and find their coordination type, they should be all the same coord type
		currentSimulationGridType = 'rectangular'
		topGridItem = self.form.gridSettingsTreeView.invisibleRootItem()
		definedGridItemsCount = topGridItem.childCount()
		for k in range(0, definedGridItemsCount):
			if topGridItem.child(k).data(0, QtCore.Qt.UserRole).coordsType != currentSimulationGridType:
				currentSimulationGridType = 'cylindrical'

		return currentSimulationGridType

	def getGridItemFromGui(self):
		name = self.form.gridSettingsNameInput.text()

		gridX = 0
		gridY = 0
		gridZ = 0

		gridItem = GridSettingsItem()
		gridItem.name = name

		xenabled = self.form.gridXEnable.isChecked()
		yenabled = self.form.gridYEnable.isChecked()
		zenabled = self.form.gridZEnable.isChecked()
		gridItem.xenabled = xenabled
		gridItem.yenabled = yenabled
		gridItem.zenabled = zenabled

		if (self.form.gridRectangularRadio.isChecked()):
			gridItem.coordsType = "rectangular"
		if (self.form.gridCylindricalRadio.isChecked()):
			gridItem.coordsType = "cylindrical"

		if (self.form.fixedCountRadioButton.isChecked()):
			gridItem.type = "Fixed Count"
			gridX = self.form.fixedCountXNumberInput.value()
			gridY = self.form.fixedCountYNumberInput.value()
			gridZ = self.form.fixedCountZNumberInput.value()

			gridItem.fixedCount = {}
			gridItem.fixedCount['x'] = gridX
			gridItem.fixedCount['y'] = gridY
			gridItem.fixedCount['z'] = gridZ

			print("---> Saved GridSetting ")
			print(str(gridX) + " " + str(gridY) + " " + str(gridZ))

		if (self.form.fixedDistanceRadioButton.isChecked()):
			gridItem.type = "Fixed Distance"
			gridX = self.form.fixedDistanceXNumberInput.value()
			gridY = self.form.fixedDistanceYNumberInput.value()
			gridZ = self.form.fixedDistanceZNumberInput.value()

			gridItem.fixedDistance = {}
			gridItem.fixedDistance['x'] = gridX
			gridItem.fixedDistance['y'] = gridY
			gridItem.fixedDistance['z'] = gridZ

		if (self.form.userDefinedRadioButton.isChecked()):
			gridItem.type = "User Defined"
			gridItem.userDefined['data'] = self.form.userDefinedGridLinesTextInput.toPlainText()

		gridItem.units = self.form.gridUnitsInput.currentText()
		gridItem.units2 = self.form.gridUnitsInput_2.currentText()
		gridItem.generateLinesInside = self.form.gridGenerateLinesInsideCheckbox.isChecked()
		gridItem.topPriorityLines = self.form.gridTopPriorityLinesCheckbox.isChecked()

		return gridItem
		

	def gridSettingsAddButtonClicked(self):		
		settingsInst = self.getGridItemFromGui()

		#check if all items have same type of coordinate system
		currentSimulationGridType = self.getCurrentSimulationGridType()
		if currentSimulationGridType != None and settingsInst.coordsType != currentSimulationGridType:
			self.guiHelpers.displayMessage("All current defined grids are " + currentSimulationGridType + " you have to remove them or change type of current grid item.")
			return

		#check for duplicity in names if there is some warning message displayed
		#if everything is OK, item is added into tree
		isDuplicityName = self.checkTreeWidgetForDuplicityName(self.form.gridSettingsTreeView, settingsInst.name)
		if (not isDuplicityName):

			#disable/enable grid plane drawing if rectangular, for cylindrical just axis z
			if settingsInst.coordsType == "rectangular":
				self.form.auxGridAxis.setEnabled(True)				
			else:
				#set grid drawing plane to 'z' and disable chosing plane to draw grid
				index = self.form.auxGridAxis.findText('z', QtCore.Qt.MatchFixedString)
				if index >= 0:
					 self.form.auxGridAxis.setCurrentIndex(index)
				self.form.auxGridAxis.setEnabled(False)				

			#add item into gui tree views
			self.guiHelpers.addSettingsItemGui(settingsInst)
			self.guiHelpers.updateMeshPriorityDisableItems()	#update grid priority table at object assignment panel

	def gridSettingsRemoveButtonClicked(self):
		#selectedItem = self.form.gridSettingsTreeView.selectedItems()[0].data(0, QtCore.Qt.UserRole)
		#self.guiHelpers.displayMessage(selectedItem.serializeToString())

		selectedItem = self.form.gridSettingsTreeView.selectedItems()[0]
		print("Selected port name: " + selectedItem.text(0))

		gridGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
			selectedItem.text(0),
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)
		gridGroupItem = None
		for item in gridGroupWidgetItems:
			if (item.parent().text(0) == "Grid"):
				gridGroupItem = item
		print("Currently removing port item: " + gridGroupItem.text(0))

		#	Remove from Priority List
		priorityName = gridGroupItem.parent().text(0) + ", " + gridGroupItem.text(0);
		self.guiHelpers.removePriorityName(priorityName)

		#	Remove from Assigned Object
		self.form.gridSettingsTreeView.invisibleRootItem().removeChild(selectedItem)
		gridGroupItem.parent().removeChild(gridGroupItem)

		self.guiHelpers.updateMeshPriorityDisableItems()	#update grid priority table at object assignment panel

	def gridSettingsUpdateButtonClicked(self):
		### capture UI settings	
		settingsInst = self.getGridItemFromGui() 

		### replace old with new settingsInst
		selectedItems = self.form.gridSettingsTreeView.selectedItems()
		if len(selectedItems) != 1:
			return
		selectedItems[0].setData(0, QtCore.Qt.UserRole, settingsInst)

		### update other UI elements to propagate changes
		# replace oudated copy of settingsInst 
		self.updateObjectAssignmentRightTreeWidgetItemData("Grid", selectedItems[0].text(0), settingsInst)		
		# update grid priority table at object assignment panel
		self.guiHelpers.updateMeshPriorityDisableItems()
		

	def gridCoordsTypeChoosed(self):
		"""	
		if (self.form.gridRectangularRadio.isChecked()):
			self.form.gridUnitsInput.clear()
			self.form.gridUnitsInput.addItem("mm")
			self.form.gridUnitsInput.addItem("m")
			self.form.gridUnitsInput.addItem("cm")
			self.form.gridUnitsInput.addItem("nm")
			self.form.gridUnitsInput.addItem("pm")
			self.form.gridXEnable.setText("X")
			self.form.gridYEnable.setText("Y")
		
		if (self.form.gridCylindricalRadio.isChecked()):
			self.form.gridUnitsInput.clear()
			self.form.gridUnitsInput.addItem("rad")
			self.form.gridUnitsInput.addItem("deg")
			self.form.gridXEnable.setText("r")
			self.form.gridYEnable.setText("phi")
		"""

		if (self.form.gridRectangularRadio.isChecked()):
			self.form.gridXEnable.setText("X")
			self.form.gridYEnable.setText("Y")
			self.form.gridUnitsInput_2.setEnabled(False)
		
		if (self.form.gridCylindricalRadio.isChecked()):
			self.form.gridXEnable.setText("r")
			self.form.gridYEnable.setText("phi")
			self.form.gridUnitsInput_2.setEnabled(True)
		
	#
	# MATERIAL SETTINGS
	#  __  __       _______ ______ _____  _____          _         _____ ______ _______ _______ _____ _   _  _____  _____ 
	# |  \/  |   /\|__   __|  ____|  __ \|_   _|   /\   | |       / ____|  ____|__   __|__   __|_   _| \ | |/ ____|/ ____|
	# | \  / |  /  \  | |  | |__  | |__) | | |    /  \  | |      | (___ | |__     | |     | |    | | |  \| | |  __| (___  
	# | |\/| | / /\ \ | |  |  __| |  _  /  | |   / /\ \ | |       \___ \|  __|    | |     | |    | | | . ` | | |_ |\___ \ 
	# | |  | |/ ____ \| |  | |____| | \ \ _| |_ / ____ \| |____   ____) | |____   | |     | |   _| |_| |\  | |__| |____) |
	# |_|  |_/_/    \_\_|  |______|_|  \_\_____/_/    \_\______| |_____/|______|  |_|     |_|  |_____|_| \_|\_____|_____/ 
	#      

	def getMaterialItemFromGui(self):
		name = self.form.materialSettingsNameInput.text()
		epsilon = self.form.materialEpsilonNumberInput.value()
		mue = self.form.materialMueNumberInput.value()
		kappa = self.form.materialKappaNumberInput.value()
		sigma = self.form.materialSigmaNumberInput.value()

		# LuboJ, added at March 2023 so this is here to prevent errors
		try:
			conductingSheetThicknessValue = self.form.materialConductingSheetThickness.value()
			conductingSheetThicknessUnits = self.form.materialConductingSheetUnits.currentText()
			conductingSheetConductivity = self.form.materialConductingSheetConductivity.value()
		except:
			conductingSheetThicknessValue = 40.0
			conductingSheetThicknessUnits = "um"

		materialItem = MaterialSettingsItem()
		materialItem.name = name
		materialItem.constants = {}	# !!! <--- THIS MUST BE HERE, OTHERWISE ALL CONSTANTS IN ALL MATERIAL ITEMS HAVE SAME VALUE LIKE REFERENCING SAME OBJECT

		materialItem.constants['epsilon'] = epsilon
		materialItem.constants['mue'] = mue
		materialItem.constants['kappa'] = kappa
		materialItem.constants['sigma'] = sigma	

		materialItem.constants['conductingSheetThicknessValue'] = conductingSheetThicknessValue
		materialItem.constants['conductingSheetThicknessUnits'] = conductingSheetThicknessUnits
		materialItem.constants['conductingSheetConductivity'] = conductingSheetConductivity

		if (self.form.materialMetalRadioButton.isChecked() == 1):
			materialItem.type = "metal"
		elif (self.form.materialUserDefinedRadioButton.isChecked() == 1):
			materialItem.type = "userdefined"
		elif (self.form.materialConductingSheetRadioButton.isChecked() == 1):
			materialItem.type = "conducting sheet"

		return materialItem
		
	
	def materialSettingsAddButtonClicked(self):
		materialItem = self.getMaterialItemFromGui()

		# display message box with current material settings to be added
		#self.guiHelpers.displayMessage(materialItem.serializeToString())

		#check for duplicity in names if there is some warning message displayed
		isDuplicityName = self.checkTreeWidgetForDuplicityName(self.form.materialSettingsTreeView, materialItem.name)
		isPEC = (materialItem.name.upper() == "PEC")

		if (isPEC and materialItem.type != "metal"):
			self.guiHelpers.displayMessage("Material with name PEC must be just metal, cannot be something else.")
			return

		if (isDuplicityName):
			return

		self.guiHelpers.addSettingsItemGui(materialItem)
		self.guiSignals.materialsChanged.emit("add")
			

	def materialSettingsRemoveButtonClicked(self):
		selectedItem = self.form.materialSettingsTreeView.selectedItems()[0]
		materialSettings = selectedItem.data(0, QtCore.Qt.UserRole)
		print("Selected material name: " + selectedItem.text(0))

		#
		#	PEC material with type metal cannot be removed
		#		but if it has different params by random than it can be removed.
		#
		if (materialSettings.name.upper() == "PEC" and materialSettings.type == "metal"):
			self.guiHelpers.displayMessage("Maaterial PEC which is metal cannot be removed.")
			return

		materialGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
			selectedItem.text(0), 
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)

		# material name MUST BE UNIQUE, this will go through all defined material in Object assignment right column
		# and return particular material group item in tree view object
		materialGroupItem = None
		for item in materialGroupWidgetItems:
			if (item.parent().text(0) == "Material"):
				materialGroupItem = item
		print("Currently removing material item: " + materialGroupItem.text(0))

		#
		# 1. There are microstrip ports with material definition which must be removed first
		#
		portGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
			"Port",
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
		)[0]
		microstripPortsWithMaterialToDelete = []	#there can be more microstrip ports with same material assignment but different parameters
		for k in range(portGroupWidgetItems.childCount()):
			item = portGroupWidgetItems.child(k)
			if (item.data(0, QtCore.Qt.UserRole).type == "microstrip" and item.data(0, QtCore.Qt.UserRole).mslMaterial == selectedItem.text(0)):
				microstripPortsWithMaterialToDelete.append(item)
		for portToRemove in microstripPortsWithMaterialToDelete:
			message = f"This port is removed because material '{materialGroupItem.text(0)}' is removed: {portToRemove.text(0)}"
			print("\t" + message)
			self.guiHelpers.displayMessage(message)
			self.portSettingsRemoveButtonClicked(portToRemove.text(0))

		#
		# 2. Remove from Priority list (Object and Grid priority list)
		#
		priorityName = materialGroupItem.parent().text(0) + ", " + materialGroupItem.text(0);
		self.guiHelpers.removePriorityName(priorityName)

		#
		# 3. Remove from Materials list
		#
		self.form.materialSettingsTreeView.invisibleRootItem().removeChild(selectedItem)
		materialGroupItem.parent().removeChild(materialGroupItem)

		self.guiSignals.materialsChanged.emit("remove")

	def materialSettingsUpdateButtonClicked(self):
		### capture UI settings
		settingsInst = self.getMaterialItemFromGui()

		if (settingsInst.name.upper() == "PEC" and settingsInst.type != "metal"):
			self.guiHelpers.displayMessage("Material PEC can be defined just as metal nothing else. This update will not perform.")
			return

		### replace old with new settingsInst
		selectedItems = self.form.materialSettingsTreeView.selectedItems()
		if len(selectedItems) != 1:
			return
		selectedItems[0].setData(0, QtCore.Qt.UserRole, settingsInst)
		
		### update other UI elements to propagate changes
		# replace oudated copy of settingsInst 
		self.updateObjectAssignmentRightTreeWidgetItemData("Material", selectedItems[0].text(0), settingsInst)
		self.guiHelpers.displayMessage(f"Material {settingsInst.name} was updated", forceModal=False)

		self.guiSignals.materialsChanged.emit("update")

	@Slot(str)
	def materialsChanged(self, operation):
		"""
		Triggers when there is change at material tab and updates related settings in gui accordingly:
			- add new material
			- remove material
			- update material
		:param operation: "add" | "remove" | "update"
		:return: None
		"""
		#print(f"@Slot materialsChanged: {operation}")

		if (operation in ["add", "remove", "update"]):
			self.portUpdateMicrostripPortMaterialComboBox()  # update microstrip port material combobox

	def materialAddPEC(self):
		"""
		Add PEC material as metal, this is done by default due PEC must be reserved word for perfect electric conductor (metal) to not confused most simulations
		in microwave design it's fully established name, if it will be defined as something else it will be confusing.
		:return: None
		"""
		# iterates over materials due if there is PEC defined as metal
		objectAssignemntRightPortParent = self.form.objectAssignmentRightTreeWidget.findItems(
			"Material",
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)[0]

		# here metal and conducting sheet are added into microstrip possible material combobox
		for k in range(objectAssignemntRightPortParent.childCount()):
			materialData = objectAssignemntRightPortParent.child(k).data(0, QtCore.Qt.UserRole)
			if (materialData.name == "PEC" and materialData.type == "metal"):
				return
			elif (materialData.name == "PEC" and materialData.type != "metal"):
				self.guiHelpers.displayMessage("There is material defined as PEC but it's not metal, check if it's as it should be, this is not normal settings as PEC is expected to be metal.")
				return

		self.form.materialSettingsNameInput.setText("PEC")
		self.form.materialMetalRadioButton.toggle()
		self.form.materialSettingsAddButton.clicked.emit()

	# EXCITATION SETTINGS
	#  ________   _______ _____ _______    _______ _____ ____  _   _    _____ ______ _______ _______ _____ _   _  _____  _____ 
	# |  ____\ \ / / ____|_   _|__   __|/\|__   __|_   _/ __ \| \ | |  / ____|  ____|__   __|__   __|_   _| \ | |/ ____|/ ____|
	# | |__   \ V / |      | |    | |  /  \  | |    | || |  | |  \| | | (___ | |__     | |     | |    | | |  \| | |  __| (___  
	# |  __|   > <| |      | |    | | / /\ \ | |    | || |  | | . ` |  \___ \|  __|    | |     | |    | | | . ` | | |_ |\___ \ 
	# | |____ / . \ |____ _| |_   | |/ ____ \| |   _| || |__| | |\  |  ____) | |____   | |     | |   _| |_| |\  | |__| |____) |
	# |______/_/ \_\_____|_____|  |_/_/    \_\_|  |_____\____/|_| \_| |_____/|______|  |_|     |_|  |_____|_| \_|\_____|_____/ 
	#                                                                                                                          

	def getExcitationItemFromGui(self):
		name = self.form.excitationSettingsNameInput.text()

		excitationItem = ExcitationSettingsItem()
		excitationItem.name = name
		excitationItem.units = self.form.excitationUnitsNumberInput.currentText()

		if (self.form.sinusodialExcitationRadioButton.isChecked()):
			excitationItem.type = 'sinusodial'
			excitationItem.sinusodial = {}
			excitationItem.sinusodial['f0'] = self.form.sinusodialExcitationF0NumberInput.value()
		if (self.form.gaussianExcitationRadioButton.isChecked()):
			excitationItem.type = 'gaussian'
			excitationItem.gaussian = {}
			excitationItem.gaussian['fc'] = self.form.gaussianExcitationFcNumberInput.value()
			excitationItem.gaussian['f0'] = self.form.gaussianExcitationF0NumberInput.value()
		if (self.form.customExcitationRadioButton.isChecked()):
			excitationItem.type = 'custom'
			excitationItem.custom = {}
			excitationItem.custom['functionStr'] = self.form.customExcitationTextInput.text()
			excitationItem.custom['f0'] = self.form.customExcitationF0NumberInput.value()
		return excitationItem


	def excitationSettingsAddButtonClicked(self):
		settingsInst = self.getExcitationItemFromGui()

		#check for duplicity in names if there is some warning message displayed
		isDuplicityName = self.checkTreeWidgetForDuplicityName(self.form.excitationSettingsTreeView, settingsInst.name)
		isMoreThanOne = self.form.excitationSettingsTreeView.topLevelItemCount() > 0

		if (isDuplicityName):
			return
		if (isMoreThanOne):
			self.guiHelpers.displayMessage("There could be just one excitation!")
			return
		
		self.guiHelpers.addSettingsItemGui(settingsInst)
		

	def excitationSettingsRemoveButtonClicked(self):
		selectedItem = self.form.excitationSettingsTreeView.selectedItems()[0]
		print("Selected port name: " + selectedItem.text(0))

		excitationGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
			selectedItem.text(0),
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)
		excitationGroupItem = None
		for item in excitationGroupWidgetItems:
			if (item.parent().text(0) == "Excitation"):
				excitationGroupItem = item
		print("Currently removing port item: " + excitationGroupItem.text(0))

		self.form.excitationSettingsTreeView.invisibleRootItem().removeChild(selectedItem)
		excitationGroupItem.parent().removeChild(excitationGroupItem)

	def excitationSettingsUpdateButtonClicked(self):
		### capture UI settings
		settingsInst = self.getExcitationItemFromGui()
	
		### replace old with new settingsInst
		selectedItems = self.form.excitationSettingsTreeView.selectedItems()
		if len(selectedItems) != 1:
			self.guiHelpers.displayMessage("Excitation ERROR during update.", forceModal=False)
			return
		selectedItems[0].setData(0, QtCore.Qt.UserRole, settingsInst)
		
		### update other UI elements to propagate changes
		# replace oudated copy of settingsInst 
		self.updateObjectAssignmentRightTreeWidgetItemData("Excitation", selectedItems[0].text(0), settingsInst)
		self.guiHelpers.displayMessage("Excitation updated.", forceModal=False)

	# PORT SETTINGS
	#  _____   ____  _____ _______    _____ ______ _______ _______ _____ _   _  _____  _____ 
	# |  __ \ / __ \|  __ \__   __|  / ____|  ____|__   __|__   __|_   _| \ | |/ ____|/ ____|
	# | |__) | |  | | |__) | | |    | (___ | |__     | |     | |    | | |  \| | |  __| (___  
	# |  ___/| |  | |  _  /  | |     \___ \|  __|    | |     | |    | | | . ` | | |_ |\___ \ 
	# | |    | |__| | | \ \  | |     ____) | |____   | |     | |   _| |_| |\  | |__| |____) |
	# |_|     \____/|_|  \_\ |_|    |_____/|______|  |_|     |_|  |_____|_| \_|\_____|_____/ 
	#    

	def getPortItemFromGui(self):
		name = self.form.portSettingsNameInput.text()

		portItem = PortSettingsItem()
		portItem.name = name

		portItem.R = self.form.portResistanceInput.value()
		portItem.RUnits = self.form.portResistanceUnitsInput.currentText()
		portItem.isActive = self.form.portActive.isChecked()
		portItem.direction = self.form.portDirectionInput.currentText()

		if (self.form.lumpedPortRadioButton.isChecked()):
			portItem.type = "lumped"
		if (self.form.microstripPortRadioButton.isChecked()):
			portItem.type = "microstrip"
			portItem.mslMaterial = self.form.microstripPortMaterialComboBox.currentText()
			portItem.mslPropagation = self.form.microstripPortPropagationDirectionComboBox.currentText()
			portItem.mslFeedShiftValue = self.form.microstripPortFeedpointShiftValue.value()
			portItem.mslFeedShiftUnits = self.form.microstripPortFeedpointShiftUnits.currentText()
			portItem.mslMeasPlaneShiftValue = self.form.microstripPortMeasureShiftValue.value()
			portItem.mslMeasPlaneShiftUnits = self.form.microstripPortMeasureShiftUnits.currentText()

		if (self.form.circularWaveguidePortRadioButton.isChecked()):
			portItem.type = "circular waveguide"
			portItem.modeName = self.form.portWaveguideModeName.currentText()
			portItem.polarizationAngle = self.form.portWaveguidePolarizationAngle.currentText()
			portItem.excitationAmplitude = self.form.portWaveguideExcitationAmplitude.value()

		if (self.form.rectangularWaveguidePortRadioButton.isChecked()):
			portItem.type = "rectangular waveguide"
		if (self.form.etDumpPortRadioButton.isChecked()):
			portItem.type = "et dump"
		if (self.form.htDumpPortRadioButton.isChecked()):
			portItem.type = "ht dump"
		if (self.form.nf2ffBoxPortRadioButton.isChecked()):
			portItem.type = "nf2ff box"
			
		return portItem

	def portSettingsAddButtonClicked(self):
		settingsInst = self.getPortItemFromGui()

		#check for duplicity in names if there is some warning message displayed
		isDuplicityName = self.checkTreeWidgetForDuplicityName(self.form.portSettingsTreeView, settingsInst.name)

		if (not isDuplicityName):
			self.guiHelpers.addSettingsItemGui(settingsInst)
			if (settingsInst.type == "nf2ff box"):
				self.updateNF2FFList()

	def portSettingsRemoveButtonClicked(self, name = None):
		#if there is no name it's called from UI, if there is name it's called as function this is done to have one function removing port properly for both cases
		if (name == None):
			selectedItem = self.form.portSettingsTreeView.selectedItems()[0]
			print("Selected port name: " + selectedItem.text(0))
		else:
			selectedItem = self.form.portSettingsTreeView.findItems(name, QtCore.Qt.MatchExactly)[0]
			print("Called by name to remove port: " + selectedItem.text(0))

		portGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
			selectedItem.text(0),
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)
		portGroupItem = None
		for item in portGroupWidgetItems:
			if (item.parent().text(0) == "Port"):
				portGroupItem = item
		print("Currently removing port item: " + portGroupItem.text(0))

		# Removing from Priority List
		priorityName = portGroupItem.parent().text(0) + ", " + portGroupItem.text(0);
		self.guiHelpers.removePriorityName(priorityName)

		# Removing from Object Assugnment Tree
		self.form.portSettingsTreeView.invisibleRootItem().removeChild(selectedItem)
		portGroupItem.parent().removeChild(portGroupItem)

		# If NF2FF box removed then update NF2FF list on POSTPROCESSING TAB
		if (portGroupItem.data(0, QtCore.Qt.UserRole).type == "nf2ff box"):
			self.updateNF2FFList()

	def portSettingsUpdateButtonClicked(self):
		### capture UI settings
		settingsInst = self.getPortItemFromGui()
	
		### replace old with new settingsInst
		selectedItems = self.form.portSettingsTreeView.selectedItems()
		if len(selectedItems) != 1:
			return
		selectedItems[0].setData(0, QtCore.Qt.UserRole, settingsInst)
		
		### update other UI elements to propagate changes
		# replace oudated copy of settingsInst 
		self.updateObjectAssignmentRightTreeWidgetItemData("Port", selectedItems[0].text(0), settingsInst)	

	def portSettingsTypeChoosed(self):
		#first disable all additional settings for ports
		self.form.microstripPortSettingsGroup.setEnabled(False)
		self.form.waveguideSettingsGroup.setEnabled(False)

		#enable current choosed radiobox settings for port
		if (self.form.circularWaveguidePortRadioButton.isChecked()):
			self.form.waveguideSettingsGroup.setEnabled(True)
		elif (self.form.microstripPortRadioButton.isChecked()):
			self.form.microstripPortSettingsGroup.setEnabled(True)

	def portUpdateMicrostripPortMaterialComboBox(self):
		"""
		Update items in combobox for microstrip port, this add just metal and conducting sheets material types. It clears all items and fill them agains with actual values.
		"""
		self.form.microstripPortMaterialComboBox.clear()

		# iterates over materials due if there are metal or conducting sheet they are added into microstrip possible materials combobox
		objectAssignemntRightPortParent = self.form.objectAssignmentRightTreeWidget.findItems(
			"Material",
			QtCore.Qt.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive
			)[0]

		# here metal and conducting sheet are added into microstrip possible material combobox
		for k in range(objectAssignemntRightPortParent.childCount()):
			materialData = objectAssignemntRightPortParent.child(k).data(0, QtCore.Qt.UserRole)
			if (materialData.type in ["metal", "conducting sheet"]):
				self.form.microstripPortMaterialComboBox.addItem(materialData.name)


	#  _     _    _ __  __ _____  ______ _____    _____        _____ _______            _   _   _
	# | |   | |  | |  \/  |  __ \|  ____|  __ \  |  __ \ /\   |  __ \__   __|          | | | | (_)                
	# | |   | |  | | \  / | |__) | |__  | |  | | | |__) /  \  | |__) | | |     ___  ___| |_| |_ _ _ __   __ _ ___ 
	# | |   | |  | | |\/| |  ___/|  __| | |  | | |  ___/ /\ \ |  _  /  | |    / __|/ _ \ __| __| | '_ \ / _` / __|
	# | |___| |__| | |  | | |    | |____| |__| | | |  / ____ \| | \ \  | |    \__ \  __/ |_| |_| | | | | (_| \__ \
	# |______\____/|_|  |_|_|    |______|_____/  |_| /_/    \_\_|  \_\ |_|    |___/\___|\__|\__|_|_| |_|\__, |___/
	#                                                                                                    __/ |    
	#                                                                                                   |___/    
	#
	
	def getLumpedPartItemFromGui(self):
		name = self.form.lumpedPartSettingsNameInput.text()

		lumpedPartItem = LumpedPartSettingsItem()
		lumpedPartItem.name = name

		if (self.form.lumpedPartLEnable.isChecked()):
			lumpedPartItem.params['L'] = self.form.lumpedPartLInput.value()
			lumpedPartItem.params['LUnits'] = self.form.lumpedPartLUnits.currentText()
			lumpedPartItem.params['LEnabled'] = 1
		if (self.form.lumpedPartREnable.isChecked()):
			lumpedPartItem.params['R'] = self.form.lumpedPartRInput.value()
			lumpedPartItem.params['RUnits'] = self.form.lumpedPartRUnits.currentText()
			lumpedPartItem.params['REnabled'] = 1
		if (self.form.lumpedPartCEnable.isChecked()):
			lumpedPartItem.params['C'] = self.form.lumpedPartCInput.value()
			lumpedPartItem.params['CUnits'] = self.form.lumpedPartCUnits.currentText()
			lumpedPartItem.params['CEnabled'] = 1

		return lumpedPartItem
		
	
	def lumpedPartSettingsAddButtonClicked(self):
		# capture UI settings
		settingsInst = self.getLumpedPartItemFromGui()		

		#check for duplicity in names if there is some warning message displayed
		isDuplicityName = self.checkTreeWidgetForDuplicityName(self.form.lumpedPartTreeView, settingsInst.name)
		if (not isDuplicityName):
			self.guiHelpers.addSettingsItemGui(settingsInst)
			

	def lumpedPartSettingsRemoveButtonClicked(self):
		selectedItem = self.form.lumpedPartTreeView.selectedItems()[0]
		print("Selected lumpedpart name: " + selectedItem.text(0))

		lumpedPartGroupWidgetItems = self.form.objectAssignmentRightTreeWidget.findItems(
			selectedItem.text(0),
			QtCore.Qt.MatchExactly|QtCore.Qt.MatchFlag.MatchRecursive
			)
		lumpedPartGroupItem = None
		for item in lumpedPartGroupWidgetItems:
			if (item.parent().text(0) == "LumpedPart"):
				lumpedPartGroupItem = item
		print("Currently removing lumped part item: " + lumpedPartGroupItem.text(0))

		###
		#	Removing from Priority List
		###
		priorityName = lumpedPartGroupItem.parent().text(0) + ", " + lumpedPartGroupItem.text(0);
		self.guiHelpers.removePriorityName(priorityName)

		self.form.lumpedPartTreeView.invisibleRootItem().removeChild(selectedItem)
		lumpedPartGroupItem.parent().removeChild(lumpedPartGroupItem)
		

	def lumpedPartSettingsUpdateButtonClicked(self):
		### capture UI settings
		settingsInst = self.getLumpedPartItemFromGui()		
	
		### replace old with new settingsInst
		selectedItems = self.form.portSettingsTreeView.selectedItems()
		if len(selectedItems) != 1:
			return
		selectedItems[0].setData(0, QtCore.Qt.UserRole, settingsInst)
		
		### update other UI elements to propagate changes
		# replace oudated copy of settingsInst 
		self.updateObjectAssignmentRightTreeWidgetItemData("LumpedPart", selectedItems[0].text(0), settingsInst)	



	#   _____________   ____________  ___    __       _____ _______________________   _____________
	#  / ____/ ____/ | / / ____/ __ \/   |  / /      / ___// ____/_  __/_  __/  _/ | / / ____/ ___/
	# / / __/ __/ /  |/ / __/ / /_/ / /| | / /       \__ \/ __/   / /   / /  / //  |/ / / __ \__ \ 
	#/ /_/ / /___/ /|  / /___/ _, _/ ___ |/ /___    ___/ / /___  / /   / / _/ // /|  / /_/ /___/ / 
	#\____/_____/_/ |_/_____/_/ |_/_/  |_/_____/   /____/_____/ /_/   /_/ /___/_/ |_/\____//____/  
	#
	def materialTreeWidgetItemChanged(self, current, previous):
		print("Material item changed.")

		#if last item was erased from port list do nothing
		if not self.form.materialSettingsTreeView.currentItem():
			return

		currSetting = self.form.materialSettingsTreeView.currentItem().data(0, QtCore.Qt.UserRole)
		self.form.materialSettingsNameInput.setText(currSetting.name)

		#ATTENTIONS there is ocnversion to float() used BELOW
		if (currSetting.type == 'metal'):
			self.form.materialMetalRadioButton.click()
		elif (currSetting.type == 'userdefined'):
			self.form.materialUserDefinedRadioButton.click()
		elif (currSetting.type == 'conducting sheet'):
			self.form.materialConductingSheetRadioButton.click()

		self.form.materialEpsilonNumberInput.setValue(float(currSetting.constants['epsilon']))
		self.form.materialMueNumberInput.setValue(float(currSetting.constants['mue']))
		self.form.materialKappaNumberInput.setValue(float(currSetting.constants['kappa']))
		self.form.materialSigmaNumberInput.setValue(float(currSetting.constants['sigma']))

		# set microstrip related values in material tab (thickness and units)
		# if not found looks for 'um'
		#	else set first item in combobox what is 'm'
		try:
			self.form.materialConductingSheetThickness.setValue(float(currSetting.constants['conductingSheetThicknessValue']))
			index = self.form.materialConductingSheetUnits.findText(currSetting.constants['conductingSheetThicknessUnits'], QtCore.Qt.MatchFixedString)
			if index >= 0:
				self.form.materialConductingSheetUnits.setCurrentIndex(index)
			else:
				index = self.form.materialConductingSheetUnits.findText("um", QtCore.Qt.MatchFixedString)
				if index >= 0:
					self.form.materialConductingSheetUnits.setCurrentIndex(index)
				else:
					self.form.materialConductingSheetUnits.setCurrentIndex(0)

			self.form.materialConductingSheetConductivity.setValue(float(currSetting.constants['conductingSheetConductivity']))
		except Exception as e:
			print(f"materialTreeWidgetItemChanged() ERROR: {e}")

		return

	def gridTreeWidgetItemChanged(self, current, previous):
		print("Grid item changed.")

		#if last item was erased from port list do nothing
		if not self.form.gridSettingsTreeView.currentItem():
			return

		#set values to zero to not left previous settings to confuse user
		self.form.fixedDistanceXNumberInput.setValue(0)
		self.form.fixedDistanceYNumberInput.setValue(0)
		self.form.fixedDistanceZNumberInput.setValue(0)
		self.form.fixedCountXNumberInput.setValue(0)
		self.form.fixedCountYNumberInput.setValue(0)
		self.form.fixedCountZNumberInput.setValue(0)
		self.form.userDefinedGridLinesTextInput.setPlainText("")
		self.form.gridXEnable.setChecked(False)
		self.form.gridYEnable.setChecked(False)
		self.form.gridZEnable.setChecked(False)
		self.form.gridGenerateLinesInsideCheckbox.setChecked(False)
		self.form.gridTopPriorityLinesCheckbox.setChecked(False)

		#set values in grid settings by actual selected item
		currSetting = self.form.gridSettingsTreeView.currentItem().data(0, QtCore.Qt.UserRole)
		self.form.gridSettingsNameInput.setText(currSetting.name)

		index = self.form.gridUnitsInput.findText(currSetting.units, QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.gridUnitsInput.setCurrentIndex(index)

		if (currSetting.coordsType == "rectangular"):
			self.form.gridRectangularRadio.click()
		if (currSetting.coordsType == "cylindrical"):
			self.form.gridCylindricalRadio.click()

		if (currSetting.type == "Fixed Distance"):
			self.form.fixedDistanceRadioButton.click()
			self.form.fixedDistanceXNumberInput.setValue(currSetting.fixedDistance['x'])
			self.form.fixedDistanceYNumberInput.setValue(currSetting.fixedDistance['y'])
			self.form.fixedDistanceZNumberInput.setValue(currSetting.fixedDistance['z'])
		elif (currSetting.type == "Fixed Count"):
			self.form.fixedCountRadioButton.click()
			self.form.fixedCountXNumberInput.setValue(currSetting.fixedCount['x'])
			self.form.fixedCountYNumberInput.setValue(currSetting.fixedCount['y'])
			self.form.fixedCountZNumberInput.setValue(currSetting.fixedCount['z'])
			pass
		elif (currSetting.type == "User Defined"):
			self.form.userDefinedRadioButton.click()
			self.form.userDefinedGridLinesTextInput.setPlainText(currSetting.userDefined['data'])
			pass
		else:
			pass
			
		self.form.gridXEnable.setChecked(currSetting.xenabled)
		self.form.gridYEnable.setChecked(currSetting.yenabled)
		self.form.gridZEnable.setChecked(currSetting.zenabled)

		self.form.gridGenerateLinesInsideCheckbox.setChecked(currSetting.generateLinesInside)
		self.form.gridTopPriorityLinesCheckbox.setChecked(currSetting.topPriorityLines)

		return

	def excitationTreeWidgetItemChanged(self, current, previous):
		print("Excitation item changed.")

		#if last item was erased from port list do nothing
		if not self.form.excitationSettingsTreeView.currentItem():
			return

		currSetting = self.form.excitationSettingsTreeView.currentItem().data(0, QtCore.Qt.UserRole)
		self.form.excitationSettingsNameInput.setText(currSetting.name)
		if (currSetting.type == "sinusodial"):
			self.form.sinusodialExcitationRadioButton.click()
			self.form.sinusodialExcitationF0NumberInput.setValue(currSetting.sinusodial['f0'])
		elif (currSetting.type == "gaussian"):
			self.form.gaussianExcitationRadioButton.click()
			self.form.gaussianExcitationF0NumberInput.setValue(currSetting.gaussian['f0'])
			self.form.gaussianExcitationFcNumberInput.setValue(currSetting.gaussian['fc'])
			pass
		elif (currSetting.type == "custom"):
			self.form.customExcitationRadioButton.click()
			self.form.customExcitationTextInput.setText(currSetting.custom['functionStr'])
			self.form.customExcitationF0NumberInput.setValue(currSetting.custom['f0'])
			
			index = self.form.excitationUnitsNumberInput.findText(currSetting.units, QtCore.Qt.MatchFixedString)
			if index >= 0:
				self.form.excitationUnitsNumberInput.setCurrentIndex(index)
			pass
		else:
			return #no gui update
			
		index = self.form.excitationUnitsNumberInput.findText(currSetting.units, QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.excitationUnitsNumberInput.setCurrentIndex(index)

		return

	def portTreeWidgetItemChanged(self, current, previous):
		print("Port item changed.")

		#if last item was erased from port list do nothing
		if not self.form.portSettingsTreeView.currentItem():
			return

		currSetting = self.form.portSettingsTreeView.currentItem().data(0, QtCore.Qt.UserRole)
		self.form.portSettingsNameInput.setText(currSetting.name)
		self.form.portResistanceInput.setValue(float(currSetting.R))

		#set active port field direction
		index = self.form.portDirectionInput.findText(currSetting.direction, QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.portDirectionInput.setCurrentIndex(index)		

		index = self.form.portResistanceUnitsInput.findText(currSetting.RUnits, QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.portResistanceUnitsInput.setCurrentIndex(index)

		self.form.portResistanceInput.setEnabled(True)
		self.form.portResistanceUnitsInput.setEnabled(True)

		if (currSetting.type.lower() == "lumped"):
			self.form.lumpedPortRadioButton.click()

		elif (currSetting.type.lower() == "microstrip"):
			self.form.microstripPortRadioButton.click()

			try:
				self.form.microstripPortFeedpointShiftValue.setValue(currSetting.mslFeedShiftValue)
				self.form.microstripPortMeasureShiftValue.setValue(currSetting.mslMeasPlaneShiftValue)

				#set combobox propagation direction
				index = self.form.microstripPortPropagationDirectionComboBox.findText(currSetting.mslPropagation, QtCore.Qt.MatchFixedString)
				if index >= 0:
					self.form.microstripPortPropagationDirectionComboBox.setCurrentIndex(index)

				#set combobox feed shift units
				index = self.form.microstripPortFeedpointShiftUnits.findText(currSetting.mslFeedShiftUnits, QtCore.Qt.MatchFixedString)
				if index >= 0:
					self.form.microstripPortFeedpointShiftUnits.setCurrentIndex(index)

				#set combobox measure plane shift units
				index = self.form.microstripPortMeasureShiftUnits.findText(currSetting.mslMeasPlaneShiftUnits, QtCore.Qt.MatchFixedString)
				if index >= 0:
					self.form.microstripPortMeasureShiftUnits.setCurrentIndex(index)
			except Exception as e:
				self.guiHelpers.displayMessage(f"ERROR update microstrip current settings: {e}", forceModal=False)

		elif (currSetting.type.lower() == "circular waveguide"):
			self.form.circularWaveguidePortRadioButton.click()

			#set mode, e.g. TE11, TM21, ...
			index = self.form.portWaveguideModeName.findText(currSetting.modeName, QtCore.Qt.MatchFixedString)
			if index >= 0:
				self.form.portWaveguideModeName.setCurrentIndex(index)

			#set polarization angle
			index = self.form.portWaveguidePolarizationAngle.findText(currSetting.polarizationAngle, QtCore.Qt.MatchFixedString)
			if index >= 0:
				self.form.portWaveguidePolarizationAngle.setCurrentIndex(index)

			self.form.portWaveguideExcitationAmplitude.setValue(float(currSetting.excitationAmplitude))

		elif (currSetting.type.lower() == "rectangular waveguide"):
			self.form.rectangularWaveguidePortRadioButton.click()
		elif (currSetting.type.lower() == "et dump"):
			self.form.portResistanceInput.setEnabled(False)
			self.form.portResistanceUnitsInput.setEnabled(False)
			self.form.etDumpPortRadioButton.click()
		elif (currSetting.type.lower() == "ht dump"):
			self.form.portResistanceInput.setEnabled(False)
			self.form.portResistanceUnitsInput.setEnabled(False)
			self.form.htDumpPortRadioButton.click()
		elif (currSetting.type.lower() == "nf2ff box"):
			self.form.portResistanceInput.setEnabled(False)
			self.form.portResistanceUnitsInput.setEnabled(False)
			self.form.nf2ffBoxPortRadioButton.click()
		else:
			pass #no gui update

		self.form.portActive.setChecked(currSetting.isActive)	#convert value from INI file to bool

		return

	def simulationTreeWidgetItemChanged(self, current, previous):
		print("Simulation params changed.")
		return

	def lumpedPartTreeWidgetItemChanged(self, current, previous):
		print("Lumped part item changed.")

		#if last item was erased from port list do nothing
		if not self.form.lumpedPartTreeView.currentItem():
			return

		currSetting = self.form.lumpedPartTreeView.currentItem().data(0, QtCore.Qt.UserRole)
		self.form.lumpedPartSettingsNameInput.setText(currSetting.name)

		self.form.lumpedPartLEnable.setChecked(False)
		self.form.lumpedPartREnable.setChecked(False)
		self.form.lumpedPartCEnable.setChecked(False)
		if (currSetting.params['LEnabled']):
			self.form.lumpedPartLEnable.setChecked(True)
		if (currSetting.params['REnabled']):
			self.form.lumpedPartREnable.setChecked(True)
		if (currSetting.params['CEnabled']):
			self.form.lumpedPartCEnable.setChecked(True)

		self.form.lumpedPartLInput.setValue(currSetting.params['L'])
		self.form.lumpedPartRInput.setValue(currSetting.params['R'])
		self.form.lumpedPartCInput.setValue(currSetting.params['C'])

		index = self.form.lumpedPartLUnits.findText(currSetting.params['LUnits'], QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.lumpedPartLUnits.setCurrentIndex(index)
		index = self.form.lumpedPartRUnits.findText(currSetting.params['RUnits'], QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.lumpedPartRUnits.setCurrentIndex(index)
		index = self.form.lumpedPartCUnits.findText(currSetting.params['CUnits'], QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.form.lumpedPartCUnits.setCurrentIndex(index)

		return

####################################################################################################################################################################
# End of PANEL definition
####################################################################################################################################################################
 
if __name__ == "__main__":
	panel = ExportOpenEMSDialog()
	panel.show()
