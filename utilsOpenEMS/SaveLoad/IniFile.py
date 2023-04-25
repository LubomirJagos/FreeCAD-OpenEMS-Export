import os
import re
import json

from PySide import QtGui, QtCore
import FreeCAD as App

from utilsOpenEMS.GuiHelpers.GuiSignals import GuiSignals

from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers
from utilsOpenEMS.GuiHelpers.FreeCADHelpers import FreeCADHelpers

from utilsOpenEMS.SettingsItem.SettingsItem import SettingsItem
from utilsOpenEMS.SettingsItem.PortSettingsItem import PortSettingsItem
from utilsOpenEMS.SettingsItem.ProbeSettingsItem import ProbeSettingsItem
from utilsOpenEMS.SettingsItem.ExcitationSettingsItem import ExcitationSettingsItem
from utilsOpenEMS.SettingsItem.LumpedPartSettingsItem import LumpedPartSettingsItem
from utilsOpenEMS.SettingsItem.MaterialSettingsItem import MaterialSettingsItem
from utilsOpenEMS.SettingsItem.SimulationSettingsItem import SimulationSettingsItem
from utilsOpenEMS.SettingsItem.GridSettingsItem import GridSettingsItem
from utilsOpenEMS.SettingsItem.FreeCADSettingsItem import FreeCADSettingsItem

from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

class IniFile:

    def __init__(self, form, statusBar = None, guiSignals = None):
        self.form = form
        self.statusBar = statusBar
        self.freeCADHelpers = FreeCADHelpers()
        self.guiHelpers = GuiHelpers(self.form, statusBar = self.statusBar)
        self.guiSignals = guiSignals

    def writeToFile(self):
        freeCadFileDir = os.path.dirname(App.ActiveDocument.FileName)
        filename, filter = QtGui.QFileDialog.getSaveFileName(parent=self.form, caption='Write simulation settings file', dir=freeCadFileDir, filter='*.ini')
        if filename != '':
            self.write(filename)
            return filename

        return None

    def readFromFile(self):
        freeCadFileDir = os.path.dirname(App.ActiveDocument.FileName)
        filename, filter = QtGui.QFileDialog.getOpenFileName(parent=self.form, caption='Open simulation settings file', dir=freeCadFileDir, filter='*.ini')
        if filename != '':
            self.read(filename)
            return filename

        return None

    #   _____    __      ________    _____ ______ _______ _______ _____ _   _  _____  _____
    #  / ____|  /\ \    / /  ____|  / ____|  ____|__   __|__   __|_   _| \ | |/ ____|/ ____|
    # | (___   /  \ \  / /| |__    | (___ | |__     | |     | |    | | |  \| | |  __| (___
    #  \___ \ / /\ \ \/ / |  __|    \___ \|  __|    | |     | |    | | | . ` | | |_ |\___ \
    #  ____) / ____ \  /  | |____   ____) | |____   | |     | |   _| |_| |\  | |__| |____) |
    # |_____/_/    \_\/   |______| |_____/|______|  |_|     |_|  |_____|_| \_|\_____|_____/
    #
    def write(self, filename=None):

        if filename is None or filename == False:
            programname = os.path.basename(App.ActiveDocument.FileName)
            programdir = os.path.dirname(App.ActiveDocument.FileName)
            programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
            outFile = programdir + '/' + programbase + "_settings.ini"
        else:
            outFile = filename

        print("Saving settings to file: " + outFile)
        if self.statusBar is not None:
            self.statusBar.showMessage("Saving settings to file...", 5000)
            QtGui.QApplication.processEvents()

        if (os.path.exists(outFile)):
            os.remove(outFile)  # Remove outFile in case an old version exists.

        settings = QtCore.QSettings(outFile, QtCore.QSettings.IniFormat)

        # SAVE MATERIAL SETTINGS

        materialList = self.freeCADHelpers.getAllTreeWidgetItems(self.form.materialSettingsTreeView)
        for k in range(len(materialList)):
            print("Save new MATERIAL constants into file: ")
            print(materialList[k].constants)

            settings.beginGroup("MATERIAL-" + materialList[k].getName())
            settings.setValue("type", materialList[k].type)

            if (materialList[k].type == "userdefined"):
                settings.setValue("material_epsilon", materialList[k].constants['epsilon'])
                settings.setValue("material_mue", materialList[k].constants['mue'])
                settings.setValue("material_kappa", materialList[k].constants['kappa'])
                settings.setValue("material_sigma", materialList[k].constants['sigma'])
            elif (materialList[k].type == "conducting sheet"):
                try:
                    settings.setValue("conductingSheetThicknessValue", materialList[k].constants['conductingSheetThicknessValue'])
                    settings.setValue("conductingSheetThicknessUnits", materialList[k].constants['conductingSheetThicknessUnits'])
                    settings.setValue("conductingSheetConductivity", materialList[k].constants['conductingSheetConductivity'])
                except Exception as e:
                    settings.setValue("conductingSheetThicknessValue", 40.00)
                    settings.setValue("conductingSheetThicknessUnits", "um")
                    settings.setValue("conductingSheetConductivity", 50e6)
                    print(f"IniFile.py > write(), ERROR, set default values for conductingSheetThicknessValue, conductingSheetThicknessUnits\n{e}")

            settings.endGroup()

        # SAVE GRID SETTINGS

        gridList = self.freeCADHelpers.getAllTreeWidgetItems(self.form.gridSettingsTreeView)
        for k in range(len(gridList)):
            print("Save new GRID constants into file: " + gridList[k].getName())

            settings.beginGroup("GRID-" + gridList[k].getName())
            settings.setValue("coordsType", gridList[k].coordsType)
            settings.setValue("type", gridList[k].type)
            settings.setValue("generateLinesInside", gridList[k].generateLinesInside)
            settings.setValue("topPriorityLines", gridList[k].topPriorityLines)
            settings.setValue("units", gridList[k].units)

            if (gridList[k].type == "Fixed Distance"):
                settings.setValue("xenabled", gridList[k].xenabled)
                settings.setValue("yenabled", gridList[k].yenabled)
                settings.setValue("zenabled", gridList[k].zenabled)
                settings.setValue("fixedDistance", json.dumps(gridList[k].fixedDistance))
            elif (gridList[k].type == "Fixed Count"):
                settings.setValue("xenabled", gridList[k].xenabled)
                settings.setValue("yenabled", gridList[k].yenabled)
                settings.setValue("zenabled", gridList[k].zenabled)
                settings.setValue("fixedCount", json.dumps(gridList[k].fixedCount))
            elif (gridList[k].type == "Smooth Mesh"):
                settings.setValue("xenabled", gridList[k].xenabled)
                settings.setValue("yenabled", gridList[k].yenabled)
                settings.setValue("zenabled", gridList[k].zenabled)
                settings.setValue("smoothMesh", json.dumps(gridList[k].smoothMesh))
            elif (gridList[k].type == "User Defined"):
                settings.setValue("userDefined", json.dumps(gridList[k].userDefined))

            settings.endGroup()

        # SAVE EXCITATION

        excitationList = self.freeCADHelpers.getAllTreeWidgetItems(self.form.excitationSettingsTreeView)
        for k in range(len(excitationList)):
            print("Save new EXCITATION constants into file: " + excitationList[k].getName())

            settings.beginGroup("EXCITATION-" + excitationList[k].getName())
            settings.setValue("type", excitationList[k].type)
            settings.setValue("sinusodial", json.dumps(excitationList[k].sinusodial))
            settings.setValue("gaussian", json.dumps(excitationList[k].gaussian))
            settings.setValue("custom", json.dumps(excitationList[k].custom))
            settings.setValue("units", excitationList[k].units)
            settings.endGroup()

        #
        # SAVE PORT SETTINGS
        #
        portList = self.freeCADHelpers.getAllTreeWidgetItems(self.form.portSettingsTreeView)
        for k in range(len(portList)):
            print("Save new PORT constants into file: " + portList[k].getName())

            settings.beginGroup("PORT-" + portList[k].getName())
            settings.setValue("type", portList[k].type)
            settings.setValue("excitationAmplitude", portList[k].excitationAmplitude)

            if (portList[k].type == "lumped"):
                try:
                    settings.setValue("R", portList[k].R)
                    settings.setValue("RUnits", portList[k].RUnits)
                    settings.setValue("isActive", portList[k].isActive)
                    settings.setValue("infiniteResistance", portList[k].infiniteResistance)
                    settings.setValue("direction", portList[k].direction)
                except Exception as e:
                    print(f"{__file__} > write() lumped ERROR: {e}")

            elif (portList[k].type == "circular waveguide"):
                settings.setValue("isActive", portList[k].isActive)
                settings.setValue("direction", portList[k].direction)
                settings.setValue("modeName", portList[k].modeName)
                settings.setValue("polarizationAngle", portList[k].polarizationAngle)
                settings.setValue("waveguideDirection", portList[k].waveguideCircDir)

            elif (portList[k].type == "rectangular waveguide"):
                settings.setValue("isActive", portList[k].isActive)
                settings.setValue("direction", portList[k].direction)
                settings.setValue("modeName", portList[k].modeName)
                settings.setValue("waveguideDirection", portList[k].waveguideRectDir)

            elif (portList[k].type == "microstrip"):
                try:
                    settings.setValue("R", portList[k].R)
                    settings.setValue("RUnits", portList[k].RUnits)
                    settings.setValue("isActive", portList[k].isActive)
                    settings.setValue("direction", portList[k].direction)

                    settings.setValue("material", portList[k].mslMaterial)
                    settings.setValue("feedShiftValue", portList[k].mslFeedShiftValue)
                    settings.setValue("feedShiftUnits", portList[k].mslFeedShiftUnits)
                    settings.setValue("measPlaneShiftValue", portList[k].mslMeasPlaneShiftValue)
                    settings.setValue("measPlaneShiftUnits", portList[k].mslMeasPlaneShiftUnits)
                    settings.setValue("propagation", portList[k].mslPropagation)
                    settings.setValue("infiniteResistance", portList[k].infiniteResistance)
                except Exception as e:
                    print(f"{__file__} > write() microstrip material ERROR: {e}")

            elif (portList[k].type == "coaxial"):
                try:
                    settings.setValue("R", portList[k].R)
                    settings.setValue("RUnits", portList[k].RUnits)
                    settings.setValue("isActive", portList[k].isActive)
                    settings.setValue("direction", portList[k].direction)

                    settings.setValue("coaxialInnerRadiusValue", portList[k].coaxialInnerRadiusValue)
                    settings.setValue("coaxialInnerRadiusUnits", portList[k].coaxialInnerRadiusUnits)
                    settings.setValue("coaxialShellThicknessValue", portList[k].coaxialShellThicknessValue)
                    settings.setValue("coaxialShellThicknessUnits", portList[k].coaxialShellThicknessUnits)
                    settings.setValue("feedpointShiftValue", portList[k].coaxialFeedpointShiftValue)
                    settings.setValue("feedpointShiftUnits", portList[k].coaxialFeedpointShiftUnits)
                    settings.setValue("measPlaneShiftValue", portList[k].coaxialMeasPlaneShiftValue)
                    settings.setValue("measPlaneShiftUnits", portList[k].coaxialMeasPlaneShiftUnits)

                    settings.setValue("material", portList[k].coaxialMaterial)
                    settings.setValue("conductorMaterial", portList[k].coaxialConductorMaterial)
                    settings.setValue("infiniteResistance", portList[k].infiniteResistance)
                except Exception as e:
                    print(f"{__file__} > write() coaxial material ERROR: {e}")

            elif (portList[k].type == "coplanar"):
                try:
                    settings.setValue("R", portList[k].R)
                    settings.setValue("RUnits", portList[k].RUnits)
                    settings.setValue("isActive", portList[k].isActive)
                    settings.setValue("direction", portList[k].direction)

                    settings.setValue('material', portList[k].coplanarMaterial)
                    settings.setValue('propagation', portList[k].coplanarPropagation)
                    settings.setValue('coplanarGapValue', portList[k].coplanarGapValue)
                    settings.setValue('coplanarGapUnits', portList[k].coplanarGapUnits)
                    settings.setValue('feedpointShiftValue', portList[k].coplanarFeedpointShiftValue)
                    settings.setValue('feedpointShiftUnits', portList[k].coplanarFeedpointShiftUnits)
                    settings.setValue('measPlaneShiftValue', portList[k].coplanarMeasPlaneShiftValue)
                    settings.setValue('measPlaneShiftUnits', portList[k].coplanarMeasPlaneShiftUnits)
                    settings.setValue("infiniteResistance", portList[k].infiniteResistance)
                except Exception as e:
                    print(f"{__file__} > write() coplanar ERROR: {e}")

            elif (portList[k].type == "stripline"):
                try:
                    settings.setValue("R", portList[k].R)
                    settings.setValue("RUnits", portList[k].RUnits)
                    settings.setValue("isActive", portList[k].isActive)
                    settings.setValue("direction", portList[k].direction)

                    settings.setValue('propagation', portList[k].striplinePropagation)
                    settings.setValue('feedpointShiftValue', portList[k].striplineFeedpointShiftValue)
                    settings.setValue('feedpointShiftUnits', portList[k].striplineFeedpointShiftUnits)
                    settings.setValue('measPlaneShiftValue', portList[k].striplineMeasPlaneShiftValue)
                    settings.setValue('measPlaneShiftUnits', portList[k].striplineMeasPlaneShiftUnits)
                    settings.setValue("infiniteResistance", portList[k].infiniteResistance)
                except Exception as e:
                    print(f"{__file__} > write() coplanar ERROR: {e}")

            elif (portList[k].type == "curve"):
                try:
                    settings.setValue("R", portList[k].R)
                    settings.setValue("RUnits", portList[k].RUnits)
                    settings.setValue("isActive", portList[k].isActive)
                    settings.setValue("infiniteResistance", portList[k].infiniteResistance)
                except Exception as e:
                    print(f"{__file__} > write() curve ERROR: {e}")

            settings.endGroup()

        #
        # SAVE PROBES SETTINGS
        #
        probeList = self.freeCADHelpers.getAllTreeWidgetItems(self.form.probeSettingsTreeView)
        for k in range(len(probeList)):
            print("Save new PROBE constants into file: " + probeList[k].getName())

            settings.beginGroup("PROBE-" + probeList[k].getName())
            settings.setValue("type", probeList[k].type)

            if (probeList[k].type == "probe"):
                try:
                    settings.setValue("direction", probeList[k].direction)
                    settings.setValue("probeType", probeList[k].probeType)
                    settings.setValue("probeDomain", probeList[k].probeDomain)
                    settings.setValue("probeFrequencyList", probeList[k].probeFrequencyList)
                except Exception as e:
                    print(f"{__file__} > write() probe ERROR: {e}")

            elif (probeList[k].type == "dumpbox"):
                try:
                    settings.setValue("dumpboxType", probeList[k].dumpboxType)
                    settings.setValue("dumpboxDomain", probeList[k].dumpboxDomain)
                    settings.setValue("dumpboxFileType", probeList[k].dumpboxFileType)
                    settings.setValue("dumpboxFrequencyList", probeList[k].dumpboxFrequencyList)
                except Exception as e:
                    print(f"{__file__} > write() dumpbox ERROR: {e}")

            settings.endGroup()

        #
        # SAVE SIMULATION PARAMS
        #
        simulationSettings = SimulationSettingsItem("Hardwired Name 1")

        simulationSettings.params['max_timestamps'] = self.form.simParamsMaxTimesteps.value()
        simulationSettings.params['min_decrement'] = self.form.simParamsMinDecrement.value()

        simulationSettings.params['generateJustPreview'] = self.form.generateJustPreviewCheckbox.isChecked()
        simulationSettings.params['generateDebugPEC'] = self.form.generateDebugPECCheckbox.isChecked()
        simulationSettings.params['mFileExecCommand'] = self.form.octaveExecCommandList.currentText()
        simulationSettings.params['base_length_unit_m'] = self.form.simParamsDeltaUnitList.currentText()

        simulationSettings.params['BCxmin'] = self.form.BCxmin.currentText()
        simulationSettings.params['BCxmax'] = self.form.BCxmax.currentText()
        simulationSettings.params['BCymin'] = self.form.BCymin.currentText()
        simulationSettings.params['BCymax'] = self.form.BCymax.currentText()
        simulationSettings.params['BCzmin'] = self.form.BCzmin.currentText()
        simulationSettings.params['BCzmax'] = self.form.BCzmax.currentText()
        simulationSettings.params['PMLxmincells'] = self.form.PMLxmincells.value()
        simulationSettings.params['PMLxmaxcells'] = self.form.PMLxmaxcells.value()
        simulationSettings.params['PMLymincells'] = self.form.PMLymincells.value()
        simulationSettings.params['PMLymaxcells'] = self.form.PMLymaxcells.value()
        simulationSettings.params['PMLzmincells'] = self.form.PMLzmincells.value()
        simulationSettings.params['PMLzmaxcells'] = self.form.PMLzmaxcells.value()
        simulationSettings.params['min_gridspacing_enable'] = self.form.genParamMinGridSpacingEnable.isChecked()
        simulationSettings.params['min_gridspacing_x'] = self.form.genParamMinGridSpacingX.value()
        simulationSettings.params['min_gridspacing_y'] = self.form.genParamMinGridSpacingY.value()
        simulationSettings.params['min_gridspacing_z'] = self.form.genParamMinGridSpacingZ.value()

        simulationSettings.params['outputScriptType'] = 'octave'
        if self.form.radioButton_pythonType.isChecked():
            simulationSettings.params['outputScriptType'] = 'python'

        # write parameters frp, above into JSON
        settings.beginGroup("SIMULATION-" + simulationSettings.name)
        settings.setValue("name", simulationSettings.name)
        settings.setValue("params", json.dumps(simulationSettings.params))
        settings.endGroup()

        # SAVE OBJECT ASSIGNMENTS

        topItemsCount = self.form.objectAssignmentRightTreeWidget.topLevelItemCount()
        objCounter = 0
        for k in range(topItemsCount):
            topItem = self.form.objectAssignmentRightTreeWidget.topLevelItem(k)
            topItemName = topItem.text(0)
            print("---> topItem: " + topItem.text(0))
            for m in range(topItem.childCount()):
                childItem = topItem.child(m)
                childItemName = childItem.text(0)
                print("Save new OBJECT ASSIGNMENTS for category -> settings profile: ")
                print("\t" + topItemName + " --> " + childItemName)
                for n in range(childItem.childCount()):
                    objItem = childItem.child(n)
                    objItemName = objItem.text(0)

                    # get unique FreeCAD internal item ID saved in FreeCADSettingsItem
                    objItemId = objItem.data(0, QtCore.Qt.UserRole).getFreeCadId()

                    settings.beginGroup("_OBJECT" + str(objCounter) + "-" + objItemName)
                    settings.setValue("type", "FreeCadObj")
                    settings.setValue("parent", childItemName)
                    settings.setValue("category", topItemName)
                    settings.setValue("freeCadId", objItemId)
                    settings.endGroup()

                    objCounter += 1

        # SAVE LUMPED PART SETTINGS

        lumpedPartList = self.freeCADHelpers.getAllTreeWidgetItems(self.form.lumpedPartTreeView)
        print("Lumped part list contains " + str(len(lumpedPartList)) + " items.")
        for k in range(len(lumpedPartList)):
            print("Saving new LUMPED PART " + lumpedPartList[k].getName())

            settings.beginGroup("LUMPEDPART-" + lumpedPartList[k].getName())
            settings.setValue("params", json.dumps(lumpedPartList[k].params))
            settings.endGroup()

        # SAVE PRIORITY OBJECT LIST SETTINGS

        settings.beginGroup("PRIORITYLIST-OBJECTS")
        priorityObjList = self.form.objectAssignmentPriorityTreeView

        print("Priority list contains " + str(priorityObjList.topLevelItemCount()) + " items.")
        for k in range(priorityObjList.topLevelItemCount()):
            priorityObjName = priorityObjList.topLevelItem(k).text(0)
            print("Saving new PRIORITY for " + priorityObjName)
            settings.setValue(priorityObjName, str(k*10))           #multiply priority by 10 to left there some numbers between
        settings.endGroup()

        # SAVE MESH PRIORITY

        settings.beginGroup("PRIORITYLIST-MESH")
        priorityMeshObjList = self.form.meshPriorityTreeView

        print("Priority list contains " + str(priorityMeshObjList.topLevelItemCount()) + " items.")
        for k in range(priorityMeshObjList.topLevelItemCount()):
            priorityMeshObjName = priorityMeshObjList.topLevelItem(k).text(0)
            print("Saving new MESH PRIORITY for " + priorityMeshObjName)
            settings.setValue(priorityMeshObjName, str(k*10))          #multiply priority by 10 to left there some numbers between
        settings.endGroup()

        # SAVE POSTPROCESSING OPTIONS

        settings.beginGroup("POSTPROCESSING-DefaultName")
        settings.setValue("nf2ffObject", self.form.portNf2ffObjectList.currentText())
        settings.setValue("nf2ffFreqCount", self.form.portNf2ffFreqCount.value())
        settings.setValue("nf2ffThetaStart", self.form.portNf2ffThetaStart.value())
        settings.setValue("nf2ffThetaStop", self.form.portNf2ffThetaStop.value())
        settings.setValue("nf2ffThetaStep", self.form.portNf2ffThetaStep.value())
        settings.setValue("nf2ffPhiStart", self.form.portNf2ffPhiStart.value())
        settings.setValue("nf2ffPhiStop", self.form.portNf2ffPhiStop.value())
        settings.setValue("nf2ffPhiStep", self.form.portNf2ffPhiStep.value())
        settings.endGroup()

        # sys.exit()  # prevents second call
        print("Current settings saved to file: " + outFile)
        self.guiHelpers.displayMessage("Settings saved to file: " + outFile, forceModal=False)
        return


    #  _      ____          _____     _____ ______ _______ _______ _____ _   _  _____  _____
    # | |    / __ \   /\   |  __ \   / ____|  ____|__   __|__   __|_   _| \ | |/ ____|/ ____|
    # | |   | |  | | /  \  | |  | | | (___ | |__     | |     | |    | | |  \| | |  __| (___
    # | |   | |  | |/ /\ \ | |  | |  \___ \|  __|    | |     | |    | | | . ` | | |_ |\___ \
    # | |___| |__| / ____ \| |__| |  ____) | |____   | |     | |   _| |_| |\  | |__| |____) |
    # |______\____/_/    \_\_____/  |_____/|______|  |_|     |_|  |_____|_| \_|\_____|_____/
    #
    def read(self, filename=None):
        print("Load current values from file.")
        if self.statusBar is not None:
            self.statusBar.showMessage("Loading current values from file...", 5000)
            QtGui.QApplication.processEvents()

        # FIRST DELETE ALL GUI TREE WIDGET ITEMS
        self.guiHelpers.deleteAllSettings()

        if filename is None or filename == False:
            #
            # DEBUG: now read hardwired file name with __file__ + "_settings.ini"
            #
            print("setting default filename...")
            programname = os.path.basename(App.ActiveDocument.FileName)
            programdir = os.path.dirname(App.ActiveDocument.FileName)
            programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
            outFile = programdir + '/' + programbase + "_settings.ini"
        else:
            outFile = filename

        print("Loading data from file: " + outFile)
        settings = QtCore.QSettings(outFile, QtCore.QSettings.IniFormat)

        #
        # LOADING ITEMS FROM SETTINGS FILE
        #
        failedLoadedFreeCadObjects = []

        print("Settings file groups:", end="")
        print(settings.childGroups())
        for settingsGroup in settings.childGroups():

            # extract category name from ini name
            itemNameReg = re.search("-(.*)", settingsGroup)
            itemName = itemNameReg.group(1)

            if (re.compile("EXCITATION").search(settingsGroup)):
                print("Excitation item settings found.")
                settings.beginGroup(settingsGroup)
                categorySettings = ExcitationSettingsItem()
                categorySettings.name = itemName
                categorySettings.type = settings.value('type')
                categorySettings.sinusodial = json.loads(settings.value('sinusodial'))
                categorySettings.gaussian = json.loads(settings.value('gaussian'))
                categorySettings.custom = json.loads(settings.value('custom'))
                categorySettings.units = settings.value('units')
                settings.endGroup()

            elif (re.compile("GRID").search(settingsGroup)):
                print("GRID item settings found.")
                settings.beginGroup(settingsGroup)
                categorySettings = GridSettingsItem()
                categorySettings.name = itemName
                categorySettings.coordsType = settings.value('coordsType')
                categorySettings.units = settings.value('units')
                categorySettings.generateLinesInside = _bool(settings.value('generateLinesInside'))
                categorySettings.topPriorityLines = _bool(settings.value('topPriorityLines'))

                categorySettings.type = settings.value('type')
                if (categorySettings.type == "Fixed Distance"):
                    categorySettings.xenabled = _bool(settings.value('xenabled'))
                    categorySettings.yenabled = _bool(settings.value('yenabled'))
                    categorySettings.zenabled = _bool(settings.value('zenabled'))
                    categorySettings.fixedDistance = json.loads(settings.value('fixedDistance'))
                elif (categorySettings.type == "Fixed Count"):
                    categorySettings.xenabled = _bool(settings.value('xenabled'))
                    categorySettings.yenabled = _bool(settings.value('yenabled'))
                    categorySettings.zenabled = _bool(settings.value('zenabled'))
                    categorySettings.fixedCount = json.loads(settings.value('fixedCount'))
                elif (categorySettings.type == "User Defined"):
                    categorySettings.userDefined = json.loads(settings.value('userDefined'))
                elif (categorySettings.type == "Smooth Mesh"):
                    try:
                        categorySettings.xenabled = _bool(settings.value('xenabled'))
                        categorySettings.yenabled = _bool(settings.value('yenabled'))
                        categorySettings.zenabled = _bool(settings.value('zenabled'))
                        categorySettings.smoothMesh = json.loads(settings.value('smoothMesh'))
                    except Exception as e:
                        print(f"Error during load reading smooth mesh: {e}")
                else:
                    print(f"Grid reading {categorySettings.type} cannot find aditional infor needed for settings, default values left set.")

                settings.endGroup()

            elif (re.compile("PORT").search(settingsGroup)):
                print("PORT item settings found.")
                settings.beginGroup(settingsGroup)
                categorySettings = PortSettingsItem()
                categorySettings.name = itemName
                categorySettings.type = settings.value('type')
                try:
                    categorySettings.excitationAmplitude = float(settings.value('excitationAmplitude'))
                    categorySettings.infiniteResistance = _bool(settings.value('infiniteResistance'))
                except Exception as e:
                    print(f"There was error during reading excitation or infiniteResistance port settings: {e}")

                if (categorySettings.type == "lumped"):
                    categorySettings.R = settings.value('R')
                    categorySettings.RUnits = settings.value('RUnits')
                    categorySettings.isActive = _bool(settings.value('isActive'))
                    categorySettings.direction = settings.value('direction')

                elif (categorySettings.type == "circular waveguide"):
                    categorySettings.isActive = _bool(settings.value('isActive'))
                    categorySettings.direction = settings.value('direction')
                    categorySettings.modeName = settings.value('modeName')
                    categorySettings.polarizationAngle = settings.value('polarizationAngle')
                    categorySettings.waveguideCircDir = settings.value('waveguideDirection')

                elif (categorySettings.type == "rectangular waveguide"):
                    categorySettings.isActive = _bool(settings.value('isActive'))
                    categorySettings.direction = settings.value('direction')
                    categorySettings.modeName = settings.value('modeName')
                    categorySettings.waveguideRectDir = settings.value('waveguideDirection')

                elif (categorySettings.type == "microstrip"):
                    #this is in try block to have backward compatibility
                    try:
                        categorySettings.R = settings.value('R')
                        categorySettings.RUnits = settings.value('RUnits')
                        categorySettings.isActive = _bool(settings.value('isActive'))
                        categorySettings.direction = settings.value('direction')
                        categorySettings.mslMaterial = settings.value('material')
                        categorySettings.mslFeedShiftValue = float(settings.value('feedShiftValue'))
                        categorySettings.mslFeedShiftUnits = settings.value('feedShiftUnits')
                        categorySettings.mslMeasPlaneShiftValue = float(settings.value('measPlaneShiftValue'))
                        categorySettings.mslMeasPlaneShiftUnits = settings.value('measPlaneShiftUnits')
                        categorySettings.mslPropagation = settings.value('propagation')
                    except Exception as e:
                        print(f"There was error during reading microstrip port settings: {e}")

                elif (categorySettings.type == "coaxial"):
                    try:
                        categorySettings.R = settings.value('R')
                        categorySettings.RUnits = settings.value('RUnits')
                        categorySettings.isActive = _bool(settings.value('isActive'))
                        categorySettings.direction = settings.value('direction')
                        categorySettings.coaxialInnerRadiusValue = float(settings.value('coaxialInnerRadiusValue'))
                        categorySettings.coaxialInnerRadiusUnits = settings.value('coaxialInnerRadiusUnits')
                        categorySettings.coaxialShellThicknessValue = float(settings.value('coaxialShellThicknessValue'))
                        categorySettings.coaxialShellThicknessUnits = settings.value('coaxialShellThicknessUnits')
                        categorySettings.coaxialFeedpointShiftValue = float(settings.value('feedpointShiftValue'))
                        categorySettings.coaxialFeedpointShiftUnits = settings.value('feedpointShiftUnits')
                        categorySettings.coaxialMeasPlaneShiftValue = float(settings.value('measPlaneShiftValue'))
                        categorySettings.coaxialMeasPlaneShiftUnits = settings.value('measPlaneShiftUnits')

                        #now this is at the end of try block to ensure all properites are read, due conductor material was added so old files doesn't have it
                        categorySettings.coaxialMaterial = settings.value('material')
                        categorySettings.coaxialConductorMaterial = settings.value('conductorMaterial')
                    except Exception as e:
                        print(f"There was error during reading coaxial port settings: {e}")

                elif (categorySettings.type == "coplanar"):
                    try:
                        categorySettings.R = settings.value('R')
                        categorySettings.RUnits = settings.value('RUnits')
                        categorySettings.isActive = _bool(settings.value('isActive'))
                        categorySettings.direction = settings.value('direction')
                        categorySettings.coplanarMaterial = settings.value('material')
                        categorySettings.coplanarPropagation = settings.value('propagation')
                        categorySettings.coplanarGapValue = float(settings.value('coplanarGapValue'))
                        categorySettings.coplanarGapUnits = settings.value('coplanarGapUnits')
                        categorySettings.coplanarFeedpointShiftValue = float(settings.value('feedpointShiftValue'))
                        categorySettings.coplanarFeedpointShiftUnits = settings.value('feedpointShiftUnits')
                        categorySettings.coplanarMeasPlaneShiftValue = float(settings.value('measPlaneShiftValue'))
                        categorySettings.coplanarMeasPlaneShiftUnits = settings.value('measPlaneShiftUnits')
                    except Exception as e:
                        print(f"There was error during reading coplanar port settings: {e}")

                elif (categorySettings.type == "stripline"):
                    try:
                        categorySettings.R = settings.value('R')
                        categorySettings.RUnits = settings.value('RUnits')
                        categorySettings.isActive = _bool(settings.value('isActive'))
                        categorySettings.direction = settings.value('direction')
                        categorySettings.striplinePropagation = settings.value('propagation')
                        categorySettings.striplineFeedpointShiftValue = float(settings.value('feedpointShiftValue'))
                        categorySettings.striplineFeedpointShiftUnits = settings.value('feedpointShiftUnits')
                        categorySettings.striplineMeasPlaneShiftValue = float(settings.value('measPlaneShiftValue'))
                        categorySettings.striplineMeasPlaneShiftUnits = settings.value('measPlaneShiftUnits')
                    except Exception as e:
                        print(f"There was error during reading coplanar port settings: {e}")

                elif (categorySettings.type == "curve"):
                    try:
                        categorySettings.R = settings.value('R')
                        categorySettings.RUnits = settings.value('RUnits')
                        categorySettings.isActive = _bool(settings.value('isActive'))
                    except Exception as e:
                        print(f"There was error during reading curve port settings: {e}")

                settings.endGroup()

            elif (re.compile("PROBE").search(settingsGroup)):
                print("PROBE item settings found.")
                settings.beginGroup(settingsGroup)
                categorySettings = ProbeSettingsItem()
                categorySettings.name = itemName
                categorySettings.type = settings.value('type')

                if (categorySettings.type == "probe"):
                    try:
                        categorySettings.probeType = settings.value('probeType')
                        categorySettings.direction = settings.value('direction')
                        categorySettings.probeDomain = settings.value('probeDomain')

                        categorySettings.probeFrequencyList = settings.value('probeFrequencyList')
                        if len(categorySettings.probeFrequencyList) > 0 and len(categorySettings.probeFrequencyList[0]) == 1:
                            categorySettings.probeFrequencyList = ["".join(categorySettings.probeFrequencyList)]

                    except Exception as e:
                        print(f"There was error during reading probe probe settings: {e}")

                elif (categorySettings.type == "dumpbox"):
                    try:
                        categorySettings.dumpboxType = settings.value('dumpboxType')
                        categorySettings.dumpboxDomain = settings.value('dumpboxDomain')
                        categorySettings.dumpboxFileType = settings.value('dumpboxFileType')

                        categorySettings.dumpboxFrequencyList = settings.value('dumpboxFrequencyList')
                        if len(categorySettings.dumpboxFrequencyList) > 0 and len(categorySettings.dumpboxFrequencyList[0]) == 1:
                            categorySettings.dumpboxFrequencyList = ["".join(categorySettings.dumpboxFrequencyList)]

                    except Exception as e:
                        print(f"There was error during reading dumpbox probe settings: {e}")

                settings.endGroup()

            elif (re.compile("MATERIAL").search(settingsGroup)):
                print("Material item settings found.")
                settings.beginGroup(settingsGroup)
                categorySettings = MaterialSettingsItem()
                categorySettings.name = itemName
                categorySettings.type = settings.value('type')
                categorySettings.constants = {}
                categorySettings.constants['epsilon'] = settings.value('material_epsilon')
                categorySettings.constants['mue'] = settings.value('material_mue')
                categorySettings.constants['kappa'] = settings.value('material_kappa')
                categorySettings.constants['sigma'] = settings.value('material_sigma')

                try:
                    categorySettings.constants['conductingSheetThicknessValue'] = settings.value('conductingSheetThicknessValue')
                    categorySettings.constants['conductingSheetThicknessUnits'] = settings.value('conductingSheetThicknessUnits')
                    categorySettings.constants['conductingSheetConductivity'] = settings.value('conductingSheetConductivity')
                except:
                    print(f"There was error during loading conductive sheet material params for '{itemName}'")
                    pass

                settings.endGroup()

            elif (re.compile("SIMULATION").search(settingsGroup)):
                print("Simulation params item settings found.")
                settings.beginGroup(settingsGroup)
                simulationSettings = SimulationSettingsItem()
                simulationSettings.name = itemName
                simulationSettings.type = settings.value('type')
                simulationSettings.params = json.loads(settings.value('params'))
                print('SIMULATION PARAMS:')
                print(simulationSettings.params)
                settings.endGroup()

                self.form.simParamsMaxTimesteps.setValue(simulationSettings.params['max_timestamps'])
                self.form.simParamsMinDecrement.setValue(simulationSettings.params['min_decrement'])
                self.form.generateJustPreviewCheckbox.setCheckState(QtCore.Qt.Checked if simulationSettings.params.get('generateJustPreview',False) else QtCore.Qt.Unchecked)
                self.form.generateDebugPECCheckbox.setCheckState(
                    QtCore.Qt.Checked if simulationSettings.params.get('generateDebugPEC', False) else QtCore.Qt.Unchecked)
                self.form.octaveExecCommandList.setCurrentText(
                    simulationSettings.params.get("mFileExecCommand", self.form.octaveExecCommandList.itemData(0)))
                self.form.simParamsDeltaUnitList.setCurrentText(
                    simulationSettings.params.get("base_length_unit_m", self.form.simParamsDeltaUnitList.itemData(0)))

                self.guiHelpers.setSimlationParamBC(self.form.BCxmin, simulationSettings.params['BCxmin'])
                self.guiHelpers.setSimlationParamBC(self.form.BCxmax, simulationSettings.params['BCxmax'])
                self.guiHelpers.setSimlationParamBC(self.form.BCymin, simulationSettings.params['BCymin'])
                self.guiHelpers.setSimlationParamBC(self.form.BCymax, simulationSettings.params['BCymax'])
                self.guiHelpers.setSimlationParamBC(self.form.BCzmin, simulationSettings.params['BCzmin'])
                self.guiHelpers.setSimlationParamBC(self.form.BCzmax, simulationSettings.params['BCzmax'])

                self.form.PMLxmincells.setValue(simulationSettings.params['PMLxmincells'])
                self.form.PMLxmaxcells.setValue(simulationSettings.params['PMLxmaxcells'])
                self.form.PMLymincells.setValue(simulationSettings.params['PMLymincells'])
                self.form.PMLymaxcells.setValue(simulationSettings.params['PMLymaxcells'])
                self.form.PMLzmincells.setValue(simulationSettings.params['PMLzmincells'])
                self.form.PMLzmaxcells.setValue(simulationSettings.params['PMLzmaxcells'])

                #
                #   try catch block here due backward compatibility, if error don't do anything about it and left default values set
                #
                try:
                    self.form.genParamMinGridSpacingEnable.setCheckState(QtCore.Qt.Checked if simulationSettings.params.get('min_gridspacing_enable',False) else QtCore.Qt.Unchecked)
                    self.form.genParamMinGridSpacingX.setValue(simulationSettings.params['min_gridspacing_x'])
                    self.form.genParamMinGridSpacingY.setValue(simulationSettings.params['min_gridspacing_y'])
                    self.form.genParamMinGridSpacingZ.setValue(simulationSettings.params['min_gridspacing_z'])

                    self.form.radioButton_octaveType.setChecked(True)                                                       # by default octave type is checked
                    self.form.radioButton_octaveType.setChecked(simulationSettings.params['outputScriptType'] == 'octave')
                    if simulationSettings.params['outputScriptType'] == 'python':
                        self.form.radioButton_pythonType.setChecked(simulationSettings.params['outputScriptType'] == 'python')
                        self.form.radioButton_pythonType.clicked.emit()
                except:
                    pass

                continue  # there is no tree widget to add item to

            elif (re.compile("_OBJECT").search(settingsGroup)):
                print("FreeCadObject item settings found.")
                settings.beginGroup(settingsGroup)
                objParent = settings.value('parent')
                objCategory = settings.value('category')
                objFreeCadId = settings.value('freeCadId')
                print("\t" + objParent)
                print("\t" + objCategory)
                settings.endGroup()

                # adding excitation also into OBJECT ASSIGNMENT WINDOW
                targetGroup = self.form.objectAssignmentRightTreeWidget.findItems(objCategory, QtCore.Qt.MatchExactly)
                print("\t" + str(targetGroup))
                for k in range(len(targetGroup)):
                    print("\t" + targetGroup[k].text(0))
                    for m in range(targetGroup[k].childCount()):
                        print("\t" + targetGroup[k].child(m).text(0))
                        if (targetGroup[k].child(m).text(0) == objParent):
                            settingsItem = FreeCADSettingsItem(itemName)

                            # treeItem = QtGui.QTreeWidgetItem([itemName])
                            treeItem = QtGui.QTreeWidgetItem()
                            treeItem.setText(0, itemName)

                            #
                            #   Check if object valid during load, ie. if object label was changed this will try to find if some other object with
                            #   original label is there, if not then object is found based on its freeCad ID and new label is set.
                            #   If object is under Grid or Material settings also material priority list and mesh priority list must be updated.
                            #
                            errorLoadByName = False
                            try:
                                freeCadObj = App.ActiveDocument.getObjectsByLabel(itemName)[0]
                            except:
                                #
                                #   Object is not available using its label so it found based on it freeCad ID
                                #
                                if objFreeCadId is None:
                                    #
                                    #   If freeCad ID is not provided then don't continue and object will not appears in GUI
                                    #   It will be added to list of missing objects and displayed do user.
                                    #
                                    failedLoadedFreeCadObjects.append(f"{objCategory}, {objParent}, {itemName}")
                                    continue

                                elif len(objFreeCadId) > 0:
                                    freeCadObj = App.ActiveDocument.getObject(objFreeCadId)
                                    if not freeCadObj is None:
                                        #
                                        #   Object was found based on its freeCad ID, icon will be set as warning icon
                                        #
                                        treeItem.setText(0, freeCadObj.Label)  # auto repair name, replace it with current name
                                        errorLoadByName = True

                                        #update mesh priority and object priority list if object is under grid settings, material or port settings
                                        if objCategory == "Grid":
                                            self.renameMeshPriorityItem(objParent, itemName, freeCadObj.Label)
                                        elif objCategory in ["Material", "Port"]:
                                            self.renameObjectsPriorityItem(objCategory, objParent, itemName, freeCadObj.Label)

                                    else:
                                        #
                                        #   Object was not found based on its freeCad ID, probably deleted, added to list of missing objects.
                                        #
                                        failedLoadedFreeCadObjects.append(f"{objCategory}, {objParent}, {itemName}")
                                        continue

                            #
                            #	ERROR - here needs to be checked if freeCadObj was even found based on its Label if no try looking based on its ID from file,
                            #	need to do this this way due backward compatibility
                            #		- also FreeCAD should have set uniqe label for objects in Preferences
                            #
                            # set unique FreeCAD inside name as ID
                            settingsItem.setFreeCadId(freeCadObj.Name)

                            # SAVE settings object into GUI tree item
                            treeItem.setData(0, QtCore.Qt.UserRole, settingsItem)

                            if (freeCadObj.Name.find("Sketch") > -1):
                                treeItem.setIcon(0, QtGui.QIcon("./img/wire.svg"))
                            elif (freeCadObj.Name.find("Discretized_Edge") > -1):
                                treeItem.setIcon(0, QtGui.QIcon("./img/curve.svg"))
                            else:
                                treeItem.setIcon(0, QtGui.QIcon("./img/object.svg"))

                            #
                            #	THERE IS MISMATCH BETWEEN NAME STORED IN IN FILE AND FREECAD NAME
                            #
                            if errorLoadByName:
                                treeItem.setIcon(0, QtGui.QIcon("./img/errorLoadObject.svg"))

                            targetGroup[k].child(m).addChild(treeItem)
                            print("\tItem added")

                continue  # items is already added into tree widget nothing more needed

            elif (re.compile("LUMPEDPART").search(settingsGroup)):
                print("LumpedPart item settings found.")
                settings.beginGroup(settingsGroup)
                categorySettings = LumpedPartSettingsItem()
                categorySettings.name = itemName
                categorySettings.params = json.loads(settings.value('params'))
                settings.endGroup()

            elif (re.compile("PRIORITYLIST-OBJECTS").search(settingsGroup)):
                print("PriorityList group settings found.")

                # start reading priority objects configuration in ini file
                settings.beginGroup(settingsGroup)

                #
                #   Better approach how to add priority into GUI, now priorities doesn't have to be sequential numbers
                #   and can be repeated, yes there will be oreder mistakes, but this is more robust and doesn't crash
                #   when priorities were modified by hand and are repeating.
                #

                #init top item list with zeros, but as key is used order of each key
                topItemsList = {}
                for prioritySettingsKey in settings.childKeys():
                    prioritySettingsOrder = int(settings.value(prioritySettingsKey))
                    #if key number already used increment by 1 to make it unique
                    while (prioritySettingsOrder in list(topItemsList.keys())):
                        prioritySettingsOrder += 1

                    prioritySettingsType = prioritySettingsKey.split(", ")
                    print("Priority list adding item " + prioritySettingsKey)

                    # adding item into priority list
                    topItem = QtGui.QTreeWidgetItem([prioritySettingsKey])
                    topItem.setData(0, QtCore.Qt.UserRole, prioritySettingsType)
                    topItem.setIcon(0, self.freeCADHelpers.getIconByCategory(prioritySettingsType))
                    topItemsList[prioritySettingsOrder] = topItem

                #sort topItemList using its keys
                sortedTopItemsList = []
                for key in sorted(topItemsList):
                    sortedTopItemsList.append(topItemsList[key])

                self.form.objectAssignmentPriorityTreeView.insertTopLevelItems(0, sortedTopItemsList)

                settings.endGroup()
                continue

            elif (re.compile("PRIORITYLIST-MESH").search(settingsGroup)):
                print("PriorityList mesh group settings found.")

                # clear all items from mesh tree widget
                self.guiHelpers.removeAllMeshPriorityItems()

                # start reading priority objects configuration in ini file
                settings.beginGroup(settingsGroup)

                #
                #   Better approach how to add priority into GUI, now priorities doesn't have to be sequential numbers
                #   and can be repeated, yes there will be oreder mistakes, but this is more robust and doesn't crash
                #   when priorities were modified by hand and are repeating.
                #

                #init top item list with zeros, but as key is used order of each key
                topItemsList = {}
                for prioritySettingsKey in settings.childKeys():
                    prioritySettingsOrder = int(settings.value(prioritySettingsKey))
                    #if key number already used increment by 1 to make it unique
                    while (prioritySettingsOrder in list(topItemsList.keys())):
                        prioritySettingsOrder += 1

                    prioritySettingsType = prioritySettingsKey.split(", ")
                    print("Priority list adding item " + prioritySettingsKey)

                    # adding item into priority list
                    topItem = QtGui.QTreeWidgetItem([prioritySettingsKey])
                    topItem.setData(0, QtCore.Qt.UserRole, prioritySettingsType)
                    topItem.setIcon(0, self.freeCADHelpers.getIconByCategory(prioritySettingsType))
                    topItemsList[prioritySettingsOrder] = topItem

                #sort topItemList using its keys
                sortedTopItemsList = []
                for key in sorted(topItemsList):
                    sortedTopItemsList.append(topItemsList[key])

                self.form.meshPriorityTreeView.insertTopLevelItems(0, sortedTopItemsList)
                print("Priority list array initialized with size " + str(len(sortedTopItemsList)))

                settings.endGroup()

                #
                # If grid settings is not set to be top priority lines, therefore it's disabled (because then it's not take into account when generate mesh lines and it's overlapping something)
                #
                self.guiHelpers.updateMeshPriorityDisableItems()

                continue

            elif (re.compile("POSTPROCESSING").search(settingsGroup)):
                print("POSTPROCESSING item settings found.")
                settings.beginGroup(settingsGroup)
                #
                #	In case of error just continue and do nothing to correct values
                #
                try:
                    index = self.form.portNf2ffObjectList.findText(settings.value("nf2ffObject"),
                                                                   QtCore.Qt.MatchFixedString)
                    if index >= 0:
                        self.form.portNf2ffObjectList.setCurrentIndex(index)

                    self.form.portNf2ffThetaStart.setValue(settings.value("nf2ffThetaStart"))
                    self.form.portNf2ffThetaStop.setValue(settings.value("nf2ffThetaStop"))
                    self.form.portNf2ffThetaStep.setValue(settings.value("nf2ffThetaStep"))
                    self.form.portNf2ffPhiStart.setValue(settings.value("nf2ffPhiStart"))
                    self.form.portNf2ffPhiStop.setValue(settings.value("nf2ffPhiStop"))
                    self.form.portNf2ffPhiStep.setValue(settings.value("nf2ffPhiStep"))
                    self.form.portNf2ffFreqCount.setValue(settings.value("nf2ffFreqCount"))
                except:
                    pass

                settings.endGroup()
                continue

            else:
                # if no item recognized then conitnue next run, at the end there is adding into object assignment tab
                # and if category is not known it's need to goes for another one
                continue

            # add all items
            self.guiHelpers.addSettingsItemGui(categorySettings)
            # start with expanded treeWidget
            self.form.objectAssignmentRightTreeWidget.expandAll()

        #
        #   Failed loaded objects name listed in message for user and
        #   will be removed in priority list if they are mesh, material
        #   or port objects
        #
        if len(failedLoadedFreeCadObjects) > 0:
            missingObjects = ""
            auxCounter = 0
            for objName in failedLoadedFreeCadObjects:
                #add object name and place in tree into message for user
                missingObjects += (", " if auxCounter > 0 else "") + "{" + objName + "}"
                auxCounter += 1

                #remove p[articular line for object from priority list if its there
                self.guiHelpers.removePriorityName(objName)

            self.guiHelpers.displayMessage(f"Fail to load:\n{missingObjects}")

        #
        # Send all appropriate signals to GUI to update all needed items.
        #       Like materials for microstrip port combobox.
        #
        if (self.guiSignals):
            self.guiSignals.materialsChanged.emit("update")
        else:
            print(f"{__file__} > read(): no guiSignals defined, probably not passed into constructor, some UI things doesn't have to be populated")

        #
        #   Final message from which file were settings loaded
        #
        self.guiHelpers.displayMessage("Settings loaded from file: " + outFile, forceModal=False)

        return

    def renameMeshPriorityItem(self, gridGroupName, oldName, newName):
        meshItemName = "Grid, " + gridGroupName + ", " + oldName
        meshItemNameNew = "Grid, " + gridGroupName + ", " + newName

        meshPriorityItemsToRename = self.form.meshPriorityTreeView.findItems(meshItemName, QtCore.Qt.MatchExactly)
        for meshItemPriority in meshPriorityItemsToRename:
            meshItemPriority.setText(0, meshItemNameNew)
            meshItemPriority.setIcon(0, QtGui.QIcon("./img/errorLoadObject.svg"))

    def renameObjectsPriorityItem(self, objCategory, objParentItemName, oldName, newName):
        objItemName = objCategory + ", " + objParentItemName + ", " + oldName
        objItemNameNew = objCategory + ", " + objParentItemName + ", " + newName

        objPriorityItemsToRename = self.form.objectAssignmentPriorityTreeView.findItems(objItemName, QtCore.Qt.MatchExactly)
        for objItemPriority in objPriorityItemsToRename:
            objItemPriority.setText(0, objItemNameNew)
            objItemPriority.setIcon(0, QtGui.QIcon("./img/errorLoadObject.svg"))
