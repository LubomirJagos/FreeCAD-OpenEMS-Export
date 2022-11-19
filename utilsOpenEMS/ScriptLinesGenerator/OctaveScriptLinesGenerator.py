#   author: Lubomir Jagos
#
#
import os
from PySide import QtGui, QtCore
import FreeCAD as App
import Mesh
import numpy as np

from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

from utilsOpenEMS.SettingsItem.SettingsItem import SettingsItem
from utilsOpenEMS.SettingsItem.PortSettingsItem import PortSettingsItem
from utilsOpenEMS.SettingsItem.ExcitationSettingsItem import ExcitationSettingsItem
from utilsOpenEMS.SettingsItem.LumpedPartSettingsItem import LumpedPartSettingsItem
from utilsOpenEMS.SettingsItem.MaterialSettingsItem import MaterialSettingsItem
from utilsOpenEMS.SettingsItem.SimulationSettingsItem import SimulationSettingsItem
from utilsOpenEMS.SettingsItem.GridSettingsItem import GridSettingsItem
from utilsOpenEMS.SettingsItem.FreeCADSettingsItem import FreeCADSettingsItem

from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers

class OctaveScriptLinesGenerator:

    #
    #   constructor, get access to form GUI
    #
    def __init__(self, form, statusBar = None):
        self.form = form
        self.statusBar = statusBar

        #
        # GUI helpers function like display message box and so
        #
        self.guiHelpers = GuiHelpers(self.form, statusBar = self.statusBar)

    def getUnitLengthFromUI_m(self):
        unitStr = self.form.simParamsDeltaUnitList.currentText()
        return SettingsItem.getUnitsAsNumber(unitStr)

    def getFreeCADUnitLength_m(self):
        # # FreeCAD uses mm internally, so getFreeCADUnitLength_m() should always return 0.001.
        # # Below is one way to retrieve this value from schemaTranslate() without implying it.
        # [qtyStr, standardUnitsPerTargetUnit, targetUnitStr] = App.Units.schemaTranslate( App.Units.Quantity("1.0 m"), App.Units.Scheme.SI2 )
        # return 1.0 / standardUnitsPerTargetUnit # standard unit is mm : return 1.0 / 1000 [m]
        return 0.001

    def getItemsByClassName(self):
        categoryCount = self.form.objectAssignmentRightTreeWidget.invisibleRootItem().childCount()
        categoryNodes = [self.form.objectAssignmentRightTreeWidget.topLevelItem(k) for k in range(categoryCount)]
        itemsByClassName = {}
        for m, categoryNode in enumerate(categoryNodes):  # for each category
            for k in range(categoryNode.childCount()):  # for each child item in a given category
                item = categoryNode.child(k)
                itemData = item.data(0, QtCore.Qt.UserRole)
                if not itemData:
                    continue
                itemClassName = itemData.__class__.__name__
                if not (itemClassName in itemsByClassName):
                    itemsByClassName[itemClassName] = [[item, itemData]]
                else:
                    itemsByClassName[itemClassName].append([item, itemData])

        print("generateOpenEMSScript: Item classes found = " + ", ".join(itemsByClassName.keys()))

        return itemsByClassName

    #
    #	Returns object priority
    #		priorityItemName - string which identifies item by its text in priority tree view widget
    #
    def getItemPriority(self, priorityItemName):
        #
        #	priority is read from tree view
        #
        priorityItemValue = 42
        itemsCount = self.form.objectAssignmentPriorityTreeView.topLevelItemCount()
        for k in range(itemsCount):
            priorityItem = self.form.objectAssignmentPriorityTreeView.topLevelItem(k)
            if priorityItemName in priorityItem.text(0):
                #
                #	THIS IS MY FORMULA TO HAVE AT LEAST TWO 0 AT END AND NOT HAVE PRIORITY INDEX 0 BUT START AT 100 AT LEAST!
                #		ATTENTION: higher number means higher priority so fromual is: (1001 - k)     ...to get item at top of tree view with highest priority numbers!
                #
                priorityItemValue = (100 - k) * 100
                break  # this will break loop SO JUST ONE ITEM FROM PRIORITY LIST IS DELETED

        return priorityItemValue

    def getCurrDir(self):
        programname = os.path.basename(App.ActiveDocument.FileName)
        programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
        programDir = os.path.dirname(App.ActiveDocument.FileName)
        programNameBase = programDir + '/' + programbase

        print('--->' + programNameBase)
        print('--->' + programDir)
        return [programDir, programNameBase]

    def reportFreeCADItemSettings(self, items):
        # "FreeCAD item detection everywhere in Main Tree!!! need to get rid this, now it's tolerated during development!"
        if not items:
            return

        for [item, currSetting] in items:
            #	GET PARENT NODE DATATYPE
            print("#")
            print("#FREECAD OBJ.")
            if (str(item.parent().text(0)) == "Grid"):
                print("name: Grid Default")
                print("type: FreeCADSettingsItem")
                pass
            elif (str(item.parent().text(0)) == "Ports"):
                print("name: Port Default")
                print("type: FreeCADSettingsItem")
                pass
            elif (str(item.parent().text(0)) == "Excitation"):
                print("name: Excitation Default")
                print("type: FreeCADSettingsItem")
                pass
            elif (str(item.parent().text(0)) == "Materials"):
                print("name: Material Default")
                print("type: FreeCADSettingsItem")
                pass
            else:
                print("Parent of FreeCADSettingItem UNKNOWN")
                pass

    def getOctaveExecCommand(self, mFileName, options=""):
        cmd = self.form.octaveExecCommandList.currentText()
        cmd = cmd.format(opt=options, filename=mFileName)
        return cmd

    def getBoundaryConditionsScriptLines(self):
        genScript = ""

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% BOUNDARY CONDITIONS\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        _bcStr = lambda pml_val, text: '\"PML_{}\"'.format(str(pml_val)) if text == 'PML' else '\"{}\"'.format(text)
        strBC = ""
        strBC += _bcStr(self.form.PMLxmincells.value(), self.form.BCxmin.currentText()) + ","
        strBC += _bcStr(self.form.PMLxmaxcells.value(), self.form.BCxmax.currentText()) + ","
        strBC += _bcStr(self.form.PMLymincells.value(), self.form.BCymin.currentText()) + ","
        strBC += _bcStr(self.form.PMLymaxcells.value(), self.form.BCymax.currentText()) + ","
        strBC += _bcStr(self.form.PMLzmincells.value(), self.form.BCzmin.currentText()) + ","
        strBC += _bcStr(self.form.PMLzmaxcells.value(), self.form.BCzmax.currentText())

        genScript += "BC = {" + strBC + "};\n"
        genScript += "FDTD = SetBoundaryCond( FDTD, BC );\n"
        genScript += "\n"

        return genScript

    def getCoordinateSystemScriptLines(self):
        genScript = ""

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% COORDINATE SYSTEM\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        """ # Till now not used, just using rectangular coordination type, cylindrical MUST BE IMPLEMENTED!
        gridCoordsType = self.getModelCoordsType()
        if (gridCoordsType == "rectangular"):
            genScript += "CSX = InitCSX('CoordSystem',0); % Cartesian coordinate system.\n"
        elif (gridCoordsType == "cylindrical"):
            genScript += "CSX = InitCSX('CoordSystem',1); % Cylindrical coordinate system.\n"
        else:
            genScript += "%%%%%% ERROR GRID COORDINATION SYSTEM TYPE UNKNOWN"				
        """
        genScript += "CSX = InitCSX('CoordSystem',0); % Cartesian coordinate system.\n"
        genScript += "mesh.x = []; % mesh variable initialization (Note: x y z implies type Cartesian).\n"
        genScript += "mesh.y = [];\n"
        genScript += "mesh.z = [];\n"
        genScript += "CSX = DefineRectGrid(CSX, unit, mesh); % First call with empty mesh to set deltaUnit attribute.\n"
        genScript += "\n"

        return genScript

    def getMaterialDefinitionsScriptLines(self, items):
        genScript = ""

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% MATERIALS AND GEOMETRY\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        # PEC is created by default due it's used when microstrip port is defined, so it's here to have it here.
        # Note that the user will need to create a metal named 'PEC' and populate it to avoid a warning
        # about "no primitives assigned to metal 'PEC'".
        genScript += "CSX = AddMetal( CSX, 'PEC' );\n"
        genScript += "\n"

        if not items:
            return genScript

        for [item, currSetting] in items:

            print(currSetting)
            if (currSetting.getName() == 'Material Default'):
                print("#Material Default")
                print("---")
                continue

            print("#")
            print("#MATERIAL")
            print("#name: " + currSetting.getName())
            print("#epsilon, mue, kappa, sigma")
            print("#" + str(currSetting.constants['epsilon']) + ", " + str(currSetting.constants['mue']) + ", " + str(
                currSetting.constants['kappa']) + ", " + str(currSetting.constants['sigma']))

            genScript += "%% MATERIAL - " + currSetting.getName() + "\n"

            # when material metal use just AddMetal for simulator
            if (currSetting.type == 'metal'):
                genScript += "CSX = AddMetal( CSX, '" + currSetting.getName() + "' );\n"
            elif (currSetting.type == 'userdefined'):
                genScript += "CSX = AddMaterial( CSX, '" + currSetting.getName() + "' );\n"

                smp_args = ["CSX", "'" + currSetting.getName() + "'"]
                if str(currSetting.constants['epsilon']) != "0":
                    smp_args += ["'Epsilon'", str(currSetting.constants['epsilon'])]
                if str(currSetting.constants['mue']) != "0":
                    smp_args += ["'Mue'", str(currSetting.constants['mue'])]
                if str(currSetting.constants['kappa']) != "0":
                    smp_args += ["'Kappa'", str(currSetting.constants['kappa'])]
                if str(currSetting.constants['sigma']) != "0":
                    smp_args += ["'Sigma'", str(currSetting.constants['sigma'])]

                genScript += "CSX = SetMaterialProperty( " + ", ".join(smp_args) + " );\n"

            # first print all current material children names
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                print("##Children:")
                print("\t" + childName)

            # now export material children, if it's object export as STL, if it's curve export as curve
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                #
                #	getting item priority
                #
                objModelPriorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                objModelPriority = self.getItemPriority(objModelPriorityItemName)

                # getting reference to FreeCAD object
                freeCadObj = [i for i in App.ActiveDocument.Objects if (i.Label) == childName][0]

                if (freeCadObj.Name.find("Discretized_Edge") > -1):
                    #
                    #	Adding discretized curve
                    #

                    curvePoints = freeCadObj.Points
                    genScript += "points = [];\n"
                    for k in range(0, len(curvePoints)):
                        genScript += "points(1," + str(k + 1) + ") = " + str(curvePoints[k].x) + ";"
                        genScript += "points(2," + str(k + 1) + ") = " + str(curvePoints[k].y) + ";"
                        genScript += "points(3," + str(k + 1) + ") = " + str(curvePoints[k].z) + ";"
                        genScript += "\n"

                    genScript += "CSX = AddCurve(CSX,'" + currSetting.getName() + "'," + str(
                        objModelPriority) + ", points);\n"
                    print("Curve added to generated script using its points.")

                elif (freeCadObj.Name.find("Sketch") > -1):
                    #
                    #	Adding JUST LINE SEGMENTS FROM SKETCH, THIS NEED TO BE IMPROVED TO PROPERLY GENERATE CURVE FROM SKETCH,
                    #	there can be circle, circle arc and maybe something else in sketch geometry
                    #

                    for geometryObj in freeCadObj.Geometry:
                        if (str(type(geometryObj)).find("LineSegment") > -1):
                            genScript += "points = [];\n"
                            genScript += "points(1,1) = " + str(geometryObj.StartPoint.x) + ";"
                            genScript += "points(2,1) = " + str(geometryObj.StartPoint.y) + ";"
                            genScript += "points(3,1) = " + str(geometryObj.StartPoint.z) + ";"
                            genScript += "\n"
                            genScript += "points(1,2) = " + str(geometryObj.EndPoint.x) + ";"
                            genScript += "points(2,2) = " + str(geometryObj.EndPoint.y) + ";"
                            genScript += "points(3,2) = " + str(geometryObj.EndPoint.z) + ";"
                            genScript += "\n"
                            genScript += "CSX = AddCurve(CSX,'" + currSetting.getName() + "'," + str(
                                objModelPriority) + ", points);\n"

                    print("Line segments from sketch added.")

                else:
                    #
                    #	Adding part as STL model, first export it into file and that file load using octave openEMS function
                    #

                    currDir, baseName = self.getCurrDir()
                    stlModelFileName = childName + "_gen_model.stl"

                    genScript += "CSX = ImportSTL( CSX, '" + currSetting.getName() + "'," + str(
                        objModelPriority) + ", [currDir '/" + stlModelFileName + "'],'Transform',{'Scale', fc_unit/unit} );\n"

                    #   _____ _______ _                                        _   _
                    #  / ____|__   __| |                                      | | (_)
                    # | (___    | |  | |        __ _  ___ _ __   ___ _ __ __ _| |_ _  ___  _ __
                    #  \___ \   | |  | |       / _` |/ _ \ '_ \ / _ \ '__/ _` | __| |/ _ \| '_ \
                    #  ____) |  | |  | |____  | (_| |  __/ | | |  __/ | | (_| | |_| | (_) | | | |
                    # |_____/   |_|  |______|  \__, |\___|_| |_|\___|_|  \__,_|\__|_|\___/|_| |_|
                    #                           __/ |
                    #                          |___/
                    #
                    # going through each concrete material items and generate their .stl files

                    currDir = os.path.dirname(App.ActiveDocument.FileName)
                    partToExport = [i for i in App.ActiveDocument.Objects if (i.Label) == childName]
                    exportFileName = currDir + "/" + stlModelFileName
                    Mesh.export(partToExport, exportFileName)
                    print("Material object exported as STL into: " + stlModelFileName)

            genScript += "\n"

        return genScript

    def getPortDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # port index counter, they are generated into port{} cell variable for octave, cells index starts at 1
        genScriptPortCount = 1

        # nf2ff box counter, they are stored inside octave cell variable {} so this is to index them properly, in octave cells index starts at 1
        genNF2FFBoxCounter = 1

        baseVectorStr = {'x': '[1 0 0]', 'y': '[0 1 0]', 'z': '[0 0 1]'}
        mslDirStr = {'x': '0', 'y': '1', 'z': '2'}

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% PORTS\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        for [item, currSetting] in items:

            print("#")
            print("#PORT")
            print("#name: " + currSetting.getName())
            print("#type: " + currSetting.getType())

            objs = App.ActiveDocument.Objects
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                genScript += "%% PORT - " + currSetting.getName() + " - " + childName + "\n"

                print("##Children:")
                print("\t" + childName)
                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox
                    print('\tFreeCAD lumped port BoundBox: ' + str(bbCoords))
                    print('\t\tXMin: ' + str(bbCoords.XMin))
                    print('\t\tYMin: ' + str(bbCoords.YMin))
                    print('\t\tZMin: ' + str(bbCoords.ZMin))

                    #
                    #	getting item priority
                    #
                    priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    priorityIndex = self.getItemPriority(priorityItemName)

                    #
                    # PORT openEMS GENERATION INTO VARIABLE
                    #
                    if (currSetting.getType() == 'lumped'):
                        genScript += 'portStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                     _r(sf * bbCoords.YMin),
                                                                                     _r(sf * bbCoords.ZMin))
                        genScript += 'portStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                     _r(sf * bbCoords.YMax),
                                                                                     _r(sf * bbCoords.ZMax))
                        genScript += 'portR = ' + str(currSetting.R) + ';\n'
                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'
                        genScript += 'portDirection = {};\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        print('\tportStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(bbCoords.XMin), _r(bbCoords.YMin),
                                                                                _r(bbCoords.ZMin)))
                        print('\tportStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(bbCoords.XMax), _r(bbCoords.YMax),
                                                                                _r(bbCoords.ZMax)))

                        isActiveStr = {False: '', True: ', true'}

                        genScript += '[CSX port{' + str(genScriptPortCount) + '}] = AddLumpedPort(CSX, ' + \
                                     str(priorityIndex) + ', ' + \
                                     str(genScriptPortCount) + ', ' + \
                                     'portR*portUnits, portStart, portStop, portDirection' + \
                                     isActiveStr.get(currSetting.isActive) + ');\n'

                        genScriptPortCount += 1
                    elif (currSetting.getType() == 'microstrip'):
                        genScript += 'portStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                     _r(sf * bbCoords.YMin),
                                                                                     _r(sf * bbCoords.ZMin))
                        genScript += 'portStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                     _r(sf * bbCoords.YMax),
                                                                                     _r(sf * bbCoords.ZMax))
                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'
                        genScript += 'mslDir = {};'.format(mslDirStr.get(currentSetting.propagation, '?'))
                        genScript += 'mslEVec = {};\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        isActiveMSLStr = {False: "", True: ", 'ExcitePort', true"}

                        genScript_R = ""
                        if (currSetting.R > 0):
                            genScript_R = ", 'Feed_R', " + str(currSettings.R)

                        genScript += "AddMSLPort(CSX, " + \
                                     str(priorityIndex) + " ," + \
                                     str(genScriptPortCount) + " , 'PEC'," + \
                                     portStart + ", " + \
                                     portStop + ", mslDir, mslEVec, " + \
                                     isActiveMSLStr.get(currSetting.isActive) + \
                                     genScript_R + ");\n"

                        genScriptPortCount += 1
                    elif (currSetting.getType() == 'circular waveguide'):
                        genScript += "%% circular port openEMS code should be here\n"
                    elif (currSetting.getType() == 'rectangular waveguide'):
                        genScript += "%% rectangular port openEMS code should be here\n"
                    elif (currSetting.getType() == 'et dump'):
                        genScript += "CSX = AddDump(CSX, '" + currSetting.name + "', 'DumpType', 0, 'DumpMode', 2);\n"
                        genScript += 'dumpStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                     _r(sf * bbCoords.YMin),
                                                                                     _r(sf * bbCoords.ZMin))
                        genScript += 'dumpStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                     _r(sf * bbCoords.YMax),
                                                                                     _r(sf * bbCoords.ZMax))
                        genScript += "CSX = AddBox(CSX, '" + currSetting.name + "', 0, dumpStart, dumpStop );\n"
                    elif (currSetting.getType() == 'ht dump'):
                        genScript += "CSX = AddDump(CSX, '" + currSetting.name + "', 'DumpType', 1, 'DumpMode', 2);\n"
                        genScript += 'dumpStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                     _r(sf * bbCoords.YMin),
                                                                                     _r(sf * bbCoords.ZMin))
                        genScript += 'dumpStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                     _r(sf * bbCoords.YMax),
                                                                                     _r(sf * bbCoords.ZMax))
                        genScript += "CSX = AddBox(CSX, '" + currSetting.name + "', 0, dumpStart, dumpStop );\n"
                    elif (currSetting.getType() == 'nf2ff box'):
                        genScript += 'nf2ffStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                      _r(sf * bbCoords.YMin),
                                                                                      _r(sf * bbCoords.ZMin))
                        genScript += 'nf2ffStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                      _r(sf * bbCoords.YMax),
                                                                                      _r(sf * bbCoords.ZMax))
                        # genScript += 'nf2ffUnit = ' + currSetting.getUnitAsScriptLine() + ';\n'
                        genScript += "[CSX nf2ffBox{" + str(
                            genNF2FFBoxCounter) + "}] = CreateNF2FFBox(CSX, '" + currSetting.name + "', nf2ffStart, nf2ffStop);\n"
                        # NF2FF grid lines are generated below via getNF2FFDefinitionsScriptLines()

                        genNF2FFBoxCounter += 1
                    else:
                        genScript += '% Unknown port type. Nothing was generated. \n'

            genScript += "\n"

        return genScript

    def getLumpedPartDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% LUMPED PART\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        for [item, currSetting] in items:
            genScript += "% LUMPED PARTS " + currSetting.getName() + "\n"

            # traverse through all children item for this particular lumped part settings
            objs = App.ActiveDocument.Objects
            objsExport = []
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                print("#")
                print("#LUMPED PART " + currentSetting.getType())
                print("#name " + currentSetting.getName())
                print("#")

                freecadObjects = [i for i in objs if (i.Label) == childName]
                for obj in freecadObjects:
                    # obj = FreeCAD Object class

                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox

                    # PLACEMENT BOX
                    print(obj.Placement)

                    genScript += 'lumpedPartStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                       _r(sf * bbCoords.YMin),
                                                                                       _r(sf * bbCoords.ZMin))
                    genScript += 'lumpedPartStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                       _r(sf * bbCoords.YMax),
                                                                                       _r(sf * bbCoords.ZMax))

                    lumpedPartName = currentSetting.name
                    lumpedPartParams = ''
                    if ('r' in currentSetting.getType().lower()):
                        lumpedPartParams += ",'R', " + str(currentSetting.getR())
                    if ('l' in currentSetting.getType().lower()):
                        lumpedPartParams += ",'L', " + str(currentSetting.getL())
                    if ('c' in currentSetting.getType().lower()):
                        lumpedPartParams += ",'C', " + str(currentSetting.getC())
                    lumpedPartParams = lumpedPartParams.strip(',')

                    #
                    #	getting item priority
                    #
                    priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    priorityIndex = self.getItemPriority(priorityItemName)

                    # WARNING: Caps param has hardwired value 1, will be generated small metal caps to connect part with circuit !!!
                    genScript += "[CSX] = AddLumpedElement(CSX, '" + lumpedPartName + "', 2, 'Caps', 1, " + lumpedPartParams + ");\n"
                    genScript += "[CSX] = AddBox(CSX, '" + lumpedPartName + "', " + str(
                        priorityIndex) + ", lumpedPartStart, lumpedPartStop);\n"

            genScript += "\n"

        return genScript

    def getNF2FFDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units
        nf2ff_gridlines = {'x': [], 'y': [], 'z': []}

        for [item, currSetting] in items:

            objs = App.ActiveDocument.Objects
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox

                    if (currSetting.getType() == 'nf2ff box'):
                        nf2ff_gridlines['x'].append(sf * bbCoords.XMin)
                        nf2ff_gridlines['x'].append(sf * bbCoords.XMax)
                        nf2ff_gridlines['y'].append(sf * bbCoords.YMin)
                        nf2ff_gridlines['y'].append(sf * bbCoords.YMax)
                        nf2ff_gridlines['z'].append(sf * bbCoords.ZMin)
                        nf2ff_gridlines['z'].append(sf * bbCoords.ZMax)

        writeNF2FFlines = (len(nf2ff_gridlines['x']) > 0) or (len(nf2ff_gridlines['y']) > 0) or (
                    len(nf2ff_gridlines['z']) > 0)

        if writeNF2FFlines:
            genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
            genScript += "% NF2FF PROBES GRIDLINES\n"
            genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

            if (len(nf2ff_gridlines['x']) > 0):
                genScript += "mesh.x = [mesh.x " + " ".join(str(i) for i in nf2ff_gridlines['x']) + "];\n"
            if (len(nf2ff_gridlines['y']) > 0):
                genScript += "mesh.y = [mesh.y " + " ".join(str(i) for i in nf2ff_gridlines['y']) + "];\n"
            if (len(nf2ff_gridlines['z']) > 0):
                genScript += "mesh.z = [mesh.z " + " ".join(str(i) for i in nf2ff_gridlines['z']) + "];\n"

            genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"
            genScript += "\n"

        return genScript

    def getOrderedGridDefinitionsScriptLines(self, items):
        genScript = ""
        meshPrioritiesCount = self.form.meshPriorityTreeView.topLevelItemCount()

        if (not items) or (meshPrioritiesCount == 0):
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% GRID LINES\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "\n"

        # Create lists and dict to be able to resolve ordered list of (grid settings instance <-> FreeCAD object) associations.
        # In its current form, this implies user-defined grid lines have to be associated with the simulation volume.
        _assoc = lambda idx: list(map(str.strip, self.form.meshPriorityTreeView.topLevelItem(idx).text(0).split(',')))
        orderedAssociations = [_assoc(k) for k in reversed(range(meshPrioritiesCount))]
        gridSettingsNodeNames = [gridSettingsNode.text(0) for [gridSettingsNode, gridSettingsInst] in items]
        fcObjects = {obj.Label: obj for obj in App.ActiveDocument.Objects}

        for gridSettingsNodeName in gridSettingsNodeNames:
            print("Grid type : " + gridSettingsNodeName)

        for k, [categoryName, gridName, FreeCADObjectName] in enumerate(orderedAssociations):

            print("Grid priority level {} : {} :: {}".format(k, FreeCADObjectName, gridName))

            if not (gridName in gridSettingsNodeNames):
                print("Failed to resolve '{}'.".format(gridName))
                continue
            itemListIdx = gridSettingsNodeNames.index(gridName)
            gridSettingsInst = items[itemListIdx][1]

            fcObject = fcObjects.get(FreeCADObjectName, None)
            if (not fcObject):
                print("Failed to resolve '{}'.".format(FreeCADObjectName))
                continue

            ### Produce script output.

            if (not "Shape" in dir(fcObject)):
                continue

            bbCoords = fcObject.Shape.BoundBox

            # If generateLinesInside is selected, grid line region is shifted inward by lambda/20.
            if gridSettingsInst.generateLinesInside:
                delta = self.maxGridResolution_m / refUnit
                print("GRID generateLinesInside object detected, setting correction constant to " + str(
                    delta) + " " + refUnitStr)
            else:
                delta = 0

            #
            #	THIS IS HARD WIRED HERE, NEED TO BE CHANGED, LuboJ, September 2022
            #
            # DEBUG - DISABLED - generate grid inside using 1/20 of maximum lambda, it's not that equation,
            #	ie. for 3.4GHz simulation 1/20th is 4mm what is wrong for delta to generate
            #	gridlines inside object, must be much much lower like 10times
            delta = 0
            debugHardLimit = 0.1e-3  # debug hard limit to get gridlines inside STL objects

            xmax = sf * bbCoords.XMax - np.sign(bbCoords.XMax - bbCoords.XMin) * delta - debugHardLimit
            ymax = sf * bbCoords.YMax - np.sign(bbCoords.YMax - bbCoords.YMin) * delta - debugHardLimit
            zmax = sf * bbCoords.ZMax - np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta - debugHardLimit
            xmin = sf * bbCoords.XMin + np.sign(bbCoords.XMax - bbCoords.XMin) * delta + debugHardLimit
            ymin = sf * bbCoords.YMin + np.sign(bbCoords.YMax - bbCoords.YMin) * delta + debugHardLimit
            zmin = sf * bbCoords.ZMin + np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta + debugHardLimit

            # Write grid definition.

            genScript += "%% GRID - " + gridSettingsInst.getName() + " - " + FreeCADObjectName + ' (' + gridSettingsInst.getType() + ")\n"

            if (gridSettingsInst.getType() == 'Fixed Distance'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x(mesh.x >= {0:g} & mesh.x <= {1:g}) = [];\n".format(_r(xmin), _r(xmax))
                    genScript += "mesh.x = [ mesh.x ({0:g}:{1:g}:{2:g}) ];\n".format(_r(xmin), _r(
                        gridSettingsInst.getXYZ(refUnit)['x']), _r(xmax))
                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y(mesh.y >= {0:g} & mesh.y <= {1:g}) = [];\n".format(_r(ymin), _r(ymax))
                    genScript += "mesh.y = [ mesh.y ({0:g}:{1:g}:{2:g}) ];\n".format(_r(ymin), _r(
                        gridSettingsInst.getXYZ(refUnit)['y']), _r(ymax))
                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z(mesh.z >= {0:g} & mesh.z <= {1:g}) = [];\n".format(_r(zmin), _r(zmax))
                    genScript += "mesh.z = [ mesh.z ({0:g}:{1:g}:{2:g}) ];\n".format(_r(zmin), _r(
                        gridSettingsInst.getXYZ(refUnit)['z']), _r(zmax))
                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            elif (gridSettingsInst.getType() == 'Fixed Count'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x(mesh.x >= {0:g} & mesh.x <= {1:g}) = [];\n".format(_r(xmin), _r(xmax))
                    if (not gridSettingsInst.getXYZ()['x'] == 1):
                        genScript += "mesh.x = [ mesh.x linspace({0:g},{1:g},{2:g}) ];\n".format(_r(xmin), _r(xmax), _r(
                            gridSettingsInst.getXYZ(refUnit)['x']))
                    else:
                        genScript += "mesh.x = [ mesh.x {0:g} ];\n".format(_r((xmin + xmax) / 2))

                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y(mesh.y >= {0:g} & mesh.y <= {1:g}) = [];\n".format(_r(ymin), _r(ymax))
                    if (not gridSettingsInst.getXYZ()['y'] == 1):
                        genScript += "mesh.y = [ mesh.y linspace({0:g},{1:g},{2:g}) ];\n".format(_r(ymin), _r(ymax), _r(
                            gridSettingsInst.getXYZ(refUnit)['y']))
                    else:
                        genScript += "mesh.y = [ mesh.y {0:g} ];\n".format(_r((ymin + ymax) / 2))

                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z(mesh.z >= {0:g} & mesh.z <= {1:g}) = [];\n".format(_r(zmin), _r(zmax))
                    if (not gridSettingsInst.getXYZ()['z'] == 1):
                        genScript += "mesh.z = [ mesh.z linspace({0:g},{1:g},{2:g}) ];\n".format(_r(zmin), _r(zmax), _r(
                            gridSettingsInst.getXYZ(refUnit)['z']))
                    else:
                        genScript += "mesh.z = [ mesh.z {0:g} ];\n".format(_r((zmin + zmax) / 2))

                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            elif (gridSettingsInst.getType() == 'User Defined'):
                genScript += "mesh = " + gridSettingsInst.getXYZ() + ";\n"
                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            genScript += "\n"

        return genScript


    def getInitScriptLines(self):
        genScript = ""
        genScript += "% To be run with GNU Octave or MATLAB.\n"
        genScript += "% FreeCAD to OpenEMS plugin by Lubomir Jagos, \n"
        genScript += "% see https://github.com/LubomirJagos/FreeCAD-OpenEMS-Export\n"
        genScript += "%\n"
        genScript += "% This file has been automatically generated. Manual changes may be overwritten.\n"
        genScript += "%\n"
        genScript += "\n"
        genScript += "close all\n"
        genScript += "clear\n"
        genScript += "clc\n"
        genScript += "\n"
        genScript += "%% Change the current folder to the folder of this m-file.\n"
        genScript += "if(~isdeployed)\n"
        genScript += "  mfile_name          = mfilename('fullpath');\n"
        genScript += "  [pathstr,name,ext]  = fileparts(mfile_name);\n"
        genScript += "  cd(pathstr);\n"
        genScript += "end\n"
        genScript += "\n"

        genScript += "%% constants\n"
        genScript += "physical_constants;\n"
        genScript += "unit    = " + str(
            self.getUnitLengthFromUI_m()) + "; % Model coordinates and lengths will be specified in " + self.form.simParamsDeltaUnitList.currentText() + ".\n"
        genScript += "fc_unit = " + str(
            self.getFreeCADUnitLength_m()) + "; % STL files are exported in FreeCAD standard units (mm).\n"
        genScript += "\n"

        return genScript

    def getExcitationScriptLines(self, definitionsOnly=False):
        genScript = ""

        excitationCategory = self.form.objectAssignmentRightTreeWidget.findItems("Excitation",
                                                                                 QtCore.Qt.MatchFixedString)
        if len(excitationCategory) >= 0:
            print("Excitation Settings detected")
            print("#")
            print("#EXCITATION")

            # FOR WHOLE SIMULATION THERE IS JUST ONE EXCITATION DEFINED, so first is taken!
            if (excitationCategory[0].childCount() > 0):
                item = excitationCategory[0].child(0)
                currSetting = item.data(0, QtCore.Qt.UserRole)  # At index 0 is Default Excitation.
                # Currently only 1 excitation is allowed. Multiple excitations could be managed by setting one of them as "selected" or "active", while all others are deactivated.
                # This would help the user to manage different analysis scenarios / excitation ranges.

                print("#name: " + currSetting.getName())
                print("#type: " + currSetting.getType())

                genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                genScript += "% EXCITATION " + currSetting.getName() + "\n"
                genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

                # EXCITATION FREQUENCY AND CELL MAXIMUM RESOLUTION CALCULATION (1/20th of minimal lambda - calculated based on maximum simulation frequency)
                # maximum grid resolution is generated into script but NOT USED IN OCTAVE SCRIPT, instead is also calculated here into python variable and used in bounding box correction
                if (currSetting.getType() == 'sinusodial'):
                    genScript += "f0 = " + str(currSetting.sinusodial['f0']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                    if not definitionsOnly:
                        genScript += "FDTD = SetSinusExcite( FDTD, fc );\n"
                    genScript += "max_res = c0 / f0 / 20;\n"
                    self.maxGridResolution_m = 3e8 / (
                                currSetting.sinusodial['f0'] * currSetting.getUnitsAsNumber(currSetting.units) * 20)
                    pass
                elif (currSetting.getType() == 'gaussian'):
                    genScript += "f0 = " + str(currSetting.gaussian['f0']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                    genScript += "fc = " + str(currSetting.gaussian['fc']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                    if not definitionsOnly:
                        genScript += "FDTD = SetGaussExcite( FDTD, f0, fc );\n"
                    genScript += "max_res = c0 / (f0 + fc) / 20;\n"
                    self.maxGridResolution_m = 3e8 / ((currSetting.gaussian['f0'] + currSetting.gaussian[
                        'fc']) * currSetting.getUnitsAsNumber(currSetting.units) * 20)
                    pass
                elif (currSetting.getType() == 'custom'):
                    f0 = currSetting.custom['f0'] * currSetting.getUnitsAsNumber(currSetting.units)
                    genScript += "f0 = " + str(currSetting.custom['f0']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                    if not definitionsOnly:
                        genScript += "FDTD = SetCustomExcite( FDTD, f0, '" + currSetting.custom['functionStr'].replace(
                            'f0', str(f0)) + "' );\n"
                    genScript += "max_res = 0;\n"
                    self.maxGridResolution_m = 0
                    pass
                pass

                genScript += "\n"
            else:
                self.guiHelpers.displayMessage("Missing excitation, please define one.")
                pass
            pass
        return genScript

    #########################################################################################################################
    #                                  _                       _       _          _ _      _            _
    #                                 | |                     (_)     | |        | (_)    | |          | |
    #   __ _  ___ _ __   ___ _ __ __ _| |_ ___   ___  ___ _ __ _ _ __ | |_    ___| |_  ___| | _____  __| |
    #  / _` |/ _ \ '_ \ / _ \ '__/ _` | __/ _ \ / __|/ __| '__| | '_ \| __|  / __| | |/ __| |/ / _ \/ _` |
    # | (_| |  __/ | | |  __/ | | (_| | ||  __/ \__ \ (__| |  | | |_) | |_  | (__| | | (__|   <  __/ (_| |
    #  \__, |\___|_| |_|\___|_|  \__,_|\__\___| |___/\___|_|  |_| .__/ \__|  \___|_|_|\___|_|\_\___|\__,_|
    #   __/ |                                                   | |
    #  |___/
    #
    #	GENERATE SCRIPT CLICKED - go through object assignment tree categories, output child item data.
    #
    def generateOpenEMSScriptButtonClicked(self):
        # Update status bar to inform user that exporting has begun.

        if self.statusBar is not None:
            self.statusBar.showMessage("Generating OpenEMS script and geometry files ...", 5000)
            QtGui.QApplication.processEvents()

        # Constants and variable initialization.

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # List categories and items.

        itemsByClassName = self.getItemsByClassName()

        # Write script header.

        genScript = ""

        genScript += "% OpenEMS FDTD Analysis Automation Script\n"
        genScript += "%\n"

        genScript += self.getInitScriptLines()

        genScript += "%% switches & options\n"
        genScript += "postprocessing_only = 0;\n"
        genScript += "draw_3d_pattern = 0; % this may take a while...\n"
        genScript += "use_pml = 0;         % use pml boundaries instead of mur\n"
        genScript += "\n"
        genScript += "currDir = strrep(pwd(), '\\', '\\\\');\n"
        genScript += "display(currDir);\n"
        genScript += "\n"

        genScript += "% --no-simulation : dry run to view geometry, validate settings, no FDTD computations\n"
        genScript += "% --debug-PEC     : generated PEC skeleton (use ParaView to inspect)\n"
        openEMS_opt = []
        if self.form.generateDebugPECCheckbox.isChecked():
            openEMS_opt.append('--debug-PEC')
        if self.form.generateJustPreviewCheckbox.isChecked():
            openEMS_opt.append('--no-simulation')
        genScript += "openEMS_opts = '" + " ".join(openEMS_opt) + "';\n"
        genScript += "\n"

        # Write simulation settings.

        genScript += "%% prepare simulation folder\n"
        genScript += "Sim_Path = 'tmp';\n"
        genScript += "Sim_CSX = '" + os.path.splitext(os.path.basename(App.ActiveDocument.FileName))[0] + ".xml';\n"
        genScript += "[status, message, messageid] = rmdir( Sim_Path, 's' ); % clear previous directory\n"
        genScript += "[status, message, messageid] = mkdir( Sim_Path ); % create empty simulation folder\n"
        genScript += "\n"

        genScript += "%% setup FDTD parameter & excitation function\n"
        genScript += "max_timesteps = " + str(self.form.simParamsMaxTimesteps.value()) + ";\n"
        genScript += "min_decrement = " + str(
            self.form.simParamsMinDecrement.value()) + "; % 10*log10(min_decrement) dB  (i.e. 1E-5 means -50 dB)\n"
        genScript += "FDTD = InitFDTD( 'NrTS', max_timesteps, 'EndCriteria', min_decrement );\n"
        genScript += "\n"

        print("======================== REPORT BEGIN ========================\n")

        self.reportFreeCADItemSettings(itemsByClassName.get("FreeCADSettingsItem", None))

        # Write boundary conditions definitions.

        genScript += self.getBoundaryConditionsScriptLines()

        # Write coordinate system definitions.

        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.

        genScript += self.getExcitationScriptLines()

        # Write material definitions.

        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None))

        # Write port definitions.

        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Write grid definitions.

        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write lumped part definitions.

        genScript += self.getLumpedPartDefinitionsScriptLines(itemsByClassName.get("LumpedPartSettingsItem", None))

        # Write NF2FF probe grid definitions.

        genScript += self.getNF2FFDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        print("======================== REPORT END ========================\n")

        # Finalize script.

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% RUN\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        genScript += "WriteOpenEMS( [Sim_Path '/' Sim_CSX], FDTD, CSX );\n"
        genScript += "CSXGeomPlot( [Sim_Path '/' Sim_CSX] );\n"
        genScript += "\n"
        genScript += "if (postprocessing_only==0)\n"
        genScript += "    %% run openEMS\n"
        genScript += "    RunOpenEMS( Sim_Path, Sim_CSX, openEMS_opts );\n"
        genScript += "end\n"

        # Write _OpenEMS.m script file to current directory.

        currDir, nameBase = self.getCurrDir()
        fileName = nameBase + "_openEMS.m"
        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()

        # Show message or update status bar to inform user that exporting has finished.

        self.guiHelpers.displayMessage('Simulation script written to: ' + fileName, forceModal=False)
        print('Simulation script written to: ' + fileName)

        return

    #
    #	Write NF2FF Button clicked, generate script to display far field pattern
    #
    def writeNf2ffButtonClicked(self):
        genScript = ""
        genScript += """close all
clear
clc

Sim_Path = "tmp";
CSX = InitCSX();

"""

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        excitationCategory = self.form.objectAssignmentRightTreeWidget.findItems("Excitation",
                                                                                 QtCore.Qt.MatchFixedString)
        if len(excitationCategory) >= 0:
            # FOR WHOLE SIMULATION THERE IS JUST ONE EXCITATION DEFINED, so first is taken!
            item = excitationCategory[0].child(0)
            currSetting = item.data(0, QtCore.Qt.UserRole)  # at index 0 is Default Excitation

            if (currSetting.getType() == 'sinusodial'):
                genScript += "f0 = " + str(currSetting.sinusodial['f0']) + ";\n"
                pass
            elif (currSetting.getType() == 'gaussian'):
                genScript += "f0 = " + str(currSetting.gaussian['f0']) + "*" + str(
                    currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                genScript += "fc = " + str(currSetting.gaussian['fc']) + "*" + str(
                    currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                pass
            elif (currSetting.getType() == 'custom'):
                genScript += "%custom\n"
                pass
            pass

        genScript += """
freq = linspace( max([0,f0-fc]), f0+fc, 501 );
f_res = f0;
"""
        genScriptPortCount = 1
        genNF2FFBoxCounter = 1
        currentNF2FFBoxIndex = 1

        allItems = []
        childCount = self.form.objectAssignmentRightTreeWidget.invisibleRootItem().childCount()
        for k in range(childCount):
            allItems.append(self.form.objectAssignmentRightTreeWidget.topLevelItem(k))

        for m in range(len(allItems)):
            currItem = allItems[m]

            for k in range(currItem.childCount()):
                item = currItem.child(k)
                itemData = item.data(0, QtCore.Qt.UserRole)
                if (itemData):
                    if (itemData.__class__.__name__ == "PortSettingsItem"):
                        print("Port Settings detected")
                        currSetting = item.data(0, QtCore.Qt.UserRole)
                        print("#")
                        print("#PORT")
                        print("#name: " + currSetting.getName())
                        print("#type: " + currSetting.getType())

                        objs = App.ActiveDocument.Objects
                        for k in range(item.childCount()):
                            childName = item.child(k).text(0)

                            genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                            genScript += "% PORT - " + currSetting.getName() + " - " + childName + "\n"
                            genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

                            print("##Children:")
                            print("\t" + childName)
                            freecadObjects = [i for i in objs if (i.Label) == childName]

                            # print(freecadObjects)
                            for obj in freecadObjects:
                                # BOUNDING BOX
                                bbCoords = obj.Shape.BoundBox

                                #
                                #	getting item priority
                                #
                                priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                                priorityIndex = self.getItemPriority(priorityItemName)

                                #
                                # PORT openEMS GENERATION INTO VARIABLE
                                #
                                if (currSetting.getType() == 'lumped' and currSetting.isActive):
                                    genScript += 'portStart = [' + str(bbCoords.XMin) + ', ' + str(
                                        bbCoords.YMin) + ', ' + str(bbCoords.ZMin) + '];\n'
                                    genScript += 'portStop = [' + str(bbCoords.XMax) + ', ' + str(
                                        bbCoords.YMax) + ', ' + str(bbCoords.ZMax) + '];\n'
                                    genScript += 'portR = ' + str(currSetting.R) + ';\n'
                                    genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'

                                    if (currSetting.direction == 'x'):
                                        genScript += 'portDirection = [1 0 0];\n'
                                    elif (currSetting.direction == 'y'):
                                        genScript += 'portDirection = [0 1 0];\n'
                                    elif (currSetting.direction == 'z'):
                                        genScript += 'portDirection = [0 0 1];\n'

                                    genScript_isActive = ""
                                    if (currSetting.isActive):
                                        genScript_isActive = " , true"

                                    genScript += '[CSX port{' + str(
                                        genScriptPortCount) + '}] = AddLumpedPort(CSX, ' + str(
                                        priorityIndex) + ', ' + str(
                                        genScriptPortCount) + ', portR*portUnits, portStart, portStop, portDirection' + genScript_isActive + ');\n'
                                    genScript += 'port{' + str(genScriptPortCount) + '} = calcPort( port{' + str(
                                        genScriptPortCount) + '}, Sim_Path, freq);\n'

                                    genScriptPortCount += 1
                                elif (currSetting.getType() == 'nf2ff box'):
                                    genScript += 'nf2ffStart = [' + str(bbCoords.XMin) + ', ' + str(
                                        bbCoords.YMin) + ', ' + str(bbCoords.ZMin) + '];\n'
                                    genScript += 'nf2ffStop = [' + str(bbCoords.XMax) + ', ' + str(
                                        bbCoords.YMax) + ', ' + str(bbCoords.ZMax) + '];\n'
                                    genScript += "[CSX nf2ffBox{" + str(
                                        genNF2FFBoxCounter) + "}] = CreateNF2FFBox(CSX, '" + currSetting.name + "', nf2ffStart, nf2ffStop);\n"

                                    # update nf2ffBox index for which far field diagram will be calculated in octave script
                                    if self.form.portNf2ffObjectList.currentText() == currSetting.name:
                                        currentNF2FFBoxIndex = genNF2FFBoxCounter

                                    # increase nf2ff port counter
                                    genNF2FFBoxCounter += 1

        thetaStart = str(self.form.portNf2ffThetaStart.value())
        thetaStop = str(self.form.portNf2ffThetaStop.value())
        thetaStep = str(self.form.portNf2ffThetaStep.value())

        phiStart = str(self.form.portNf2ffPhiStart.value())
        phiStop = str(self.form.portNf2ffPhiStop.value())
        phiStep = str(self.form.portNf2ffPhiStep.value())

        genScript += """
%% NFFF contour plots %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% get accepted antenna power at frequency f0
%
%	WARNING - hardwired 1st port
%
P_in_0 = interp1(freq, port{1}.P_acc, f0);

% calculate the far field at phi=0 degrees and at phi=90 degrees

%thetaRange = unique([0:0.5:90 90:180]);
thetaRange = unique([""" + thetaStart + """:""" + thetaStep + """:""" + thetaStop + """]);

%phiRange = (0:2:360) - 180;
phiRange = (""" + phiStart + """:""" + phiStep + """:""" + phiStop + """) - 180;

disp( 'calculating the 3D far field...' );

%
%	nf2ffBox{index} - index is set based on GUI option choosed which NF2FF box should be calculated
%
%	'Mode',1 - always recalculate data
%		url: https://github.com/thliebig/openEMS/blob/master/matlab/CalcNF2FF.m
%
nf2ff = CalcNF2FF(nf2ffBox{""" + str(currentNF2FFBoxIndex) + """}, Sim_Path, f_res, thetaRange*pi/180, phiRange*pi/180, 'Mode', 1, 'Outfile', '3D_Pattern.h5', 'Verbose', 1);

theta_HPBW = interp1(nf2ff.E_norm{1}(:,1)/max(nf2ff.E_norm{1}(:,1)),thetaRange,1/sqrt(2))*2;

% display power and directivity
disp( ['radiated power: Prad = ' num2str(nf2ff.Prad) ' Watt']);
disp( ['directivity: Dmax = ' num2str(nf2ff.Dmax) ' (' num2str(10*log10(nf2ff.Dmax)) ' dBi)'] );
disp( ['efficiency: nu_rad = ' num2str(100*nf2ff.Prad./P_in_0) ' %']);
disp( ['theta_HPBW = ' num2str(theta_HPBW) ' Â°']);


%%
directivity = nf2ff.P_rad{1}/nf2ff.Prad*4*pi;
directivity_CPRH = abs(nf2ff.E_cprh{1}).^2./max(nf2ff.E_norm{1}(:)).^2*nf2ff.Dmax;
directivity_CPLH = abs(nf2ff.E_cplh{1}).^2./max(nf2ff.E_norm{1}(:)).^2*nf2ff.Dmax;

%%
figure
plot(thetaRange, 10*log10(directivity(:,1)'),'k-','LineWidth',2);
hold on
grid on
xlabel('theta (deg)');
ylabel('directivity (dBi)');
plot(thetaRange, 10*log10(directivity_CPRH(:,1)'),'g--','LineWidth',2);
plot(thetaRange, 10*log10(directivity_CPLH(:,1)'),'r-.','LineWidth',2);
legend('norm','CPRH','CPLH');

%% dump to vtk
DumpFF2VTK([Sim_Path '/3D_Pattern.vtk'],directivity,thetaRange,phiRange,'scale',1e-3);
DumpFF2VTK([Sim_Path '/3D_Pattern_CPRH.vtk'],directivity_CPRH,thetaRange,phiRange,'scale',1e-3);
DumpFF2VTK([Sim_Path '/3D_Pattern_CPLH.vtk'],directivity_CPLH,thetaRange,phiRange,'scale',1e-3);

E_far_normalized = nf2ff.E_norm{1} / max(nf2ff.E_norm{1}(:)) * nf2ff.Dmax;
DumpFF2VTK([Sim_Path '/3D_Pattern_normalized.vtk'],E_far_normalized,thetaRange,phiRange,1e-3);
"""
        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()
        fileName = nameBase + "_draw_NF2FF.m"
        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Script to display far field written into: ' + fileName)

    def drawS11ButtonClicked(self):
        genScript = ""

        excitationCategory = self.form.objectAssignmentRightTreeWidget.findItems("Excitation",
                                                                                 QtCore.Qt.MatchFixedString)
        if len(excitationCategory) >= 0:
            # FOR WHOLE SIMULATION THERE IS JUST ONE EXCITATION DEFINED, so first is taken!
            item = excitationCategory[0].child(0)
            currSetting = item.data(0, QtCore.Qt.UserRole)  # at index 0 is Default Excitation

            if (currSetting.getType() == 'sinusodial'):
                genScript += "f0 = " + str(currSetting.sinusodial['f0']) + ";\n"
                pass
            elif (currSetting.getType() == 'gaussian'):
                genScript += "f0 = " + str(currSetting.gaussian['f0']) + "*" + str(
                    currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                genScript += "fc = " + str(currSetting.gaussian['fc']) + "*" + str(
                    currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                pass
            elif (currSetting.getType() == 'custom'):
                genScript += "%custom\n"
                pass
            pass

        genScript += """%% postprocessing & do the plots
freq = linspace( max([0,f0-fc]), f0+fc, 501 );
U = ReadUI( {'port_ut1','et'}, 'tmp/', freq ); % time domain/freq domain voltage
I = ReadUI( 'port_it1', 'tmp/', freq ); % time domain/freq domain current (half time step is corrected)

% plot time domain voltage
figure
[ax,h1,h2] = plotyy( U.TD{1}.t/1e-9, U.TD{1}.val, U.TD{2}.t/1e-9, U.TD{2}.val );
set( h1, 'Linewidth', 2 );
set( h1, 'Color', [1 0 0] );
set( h2, 'Linewidth', 2 );
set( h2, 'Color', [0 0 0] );
grid on
title( 'time domain voltage' );
xlabel( 'time t / ns' );
ylabel( ax(1), 'voltage ut1 / V' );
ylabel( ax(2), 'voltage et / V' );
% now make the y-axis symmetric to y=0 (align zeros of y1 and y2)
y1 = ylim(ax(1));
y2 = ylim(ax(2));
ylim( ax(1), [-max(abs(y1)) max(abs(y1))] );
ylim( ax(2), [-max(abs(y2)) max(abs(y2))] );

% plot feed point impedance
figure
Zin = U.FD{1}.val ./ I.FD{1}.val;
plot( freq/1e6, real(Zin), 'k-', 'Linewidth', 2 );
hold on
grid on
plot( freq/1e6, imag(Zin), 'r--', 'Linewidth', 2 );
title( 'feed point impedance' );
xlabel( 'frequency f / MHz' );
ylabel( 'impedance Z_{in} / Ohm' );
legend( 'real', 'imag' );

% plot reflection coefficient S11
figure
uf_inc = 0.5*(U.FD{1}.val + I.FD{1}.val * 50);
if_inc = 0.5*(I.FD{1}.val - U.FD{1}.val / 50);
uf_ref = U.FD{1}.val - uf_inc;
if_ref = I.FD{1}.val - if_inc;
s11 = uf_ref ./ uf_inc;
plot( freq/1e6, 20*log10(abs(s11)), 'k-', 'Linewidth', 2 );
grid on
title( 'reflection coefficient S_{11}' );
xlabel( 'frequency f / MHz' );
ylabel( 'reflection coefficient |S_{11}|' );

P_in = 0.5*U.FD{1}.val .* conj( I.FD{1}.val );

%
%   Write S11, real and imag Z_in into CSV file separated by ';'
%
filename = 'openEMS_simulation_s11_dB.csv';
fid = fopen(filename, 'w');
fprintf(fid, 'freq (MHz);s11 (dB);real Z_in (Ohm); imag Z_in (Ohm)\\n');
fclose(fid)
s11_dB = horzcat((freq/1e6)', 20*log10(abs(s11))', real(Zin)', imag(Zin)');
dlmwrite(filename, s11_dB, '-append', 'delimiter', ';');
"""

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()
        fileName = nameBase + "_draw_S11.m"
        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written into: ' + fileName)

        # run octave script using command shell
        cmdToRun = self.getOctaveExecCommand(fileName, '-q --persist')
        print('Running command: ' + cmdToRun)
        result = os.system(cmdToRun)
        #print(result)

    def drawS21ButtonClicked(self):
        genScript = ""
        genScript += "% Plot S11, S21 parameters from OpenEMS results.\n"
        genScript += "%\n"

        genScript += self.getInitScriptLines()

        genScript += "Sim_Path = 'tmp';\n"
        genScript += "CSX = InitCSX('CoordSystem',0);\n"
        genScript += "\n"

        # List categories and items.

        itemsByClassName = self.getItemsByClassName()

        # Write excitation definition.

        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write port definitions.

        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Post-processing and plot generation.

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% POST-PROCESSING AND PLOT GENERATION\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "\n"
        genScript += "freq = linspace( max([0,f0-fc]), f0+fc, 501 );\n"
        genScript += "port = calcPort( port, Sim_Path, freq);\n"
        genScript += "\n"
        genScript += "s11 = port{1}.uf.ref./ port{1}.uf.inc;\n"
        genScript += "s21 = port{2}.uf.ref./ port{1}.uf.inc;\n"
        genScript += "\n"
        genScript += "s11_dB = 20*log10(abs(s11));\n"
        genScript += "s21_dB = 20*log10(abs(s21));\n"
        genScript += "\n"
        genScript += "plot(freq/1e9,s11_dB,'k-','LineWidth',2);\n"
        genScript += "hold on;\n"
        genScript += "grid on;\n"
        genScript += "plot(freq/1e9,s21_dB,'r--','LineWidth',2);\n"
        genScript += "legend('S_{11}','S_{21}');\n"
        genScript += "ylabel('S-Parameter (dB)','FontSize',12);\n"
        genScript += "xlabel('frequency (GHz) \\rightarrow','FontSize',12);\n"
        genScript += "ylim([-40 2]);\n"
        genScript += "\n"

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% SAVE PLOT DATA\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "\n"
        genScript += "save_plot_data = 0;\n"
        genScript += "\n"
        genScript += "if (save_plot_data != 0)\n"
        genScript += "	mfile_name = mfilename('fullpath');\n"
        genScript += "	[pathstr,name,ext] = fileparts(mfile_name);\n"
        genScript += "	output_fn = strcat(pathstr, '/', name, '.csv')\n"
        genScript += "	\n"
        genScript += "	%% write header to file\n"
        genScript += "	textHeader = '#f(Hz)\\tS11(dB)\\tS21(dB)';\n"
        genScript += "	fid = fopen(output_fn, 'w');\n"
        genScript += "	fprintf(fid, '%s\\n', textHeader);\n"
        genScript += "	fclose(fid);\n"
        genScript += "	\n"
        genScript += "	%% write data to end of file\n"
        genScript += "	dlmwrite(output_fn, [abs(freq)', s11_dB', s21_dB'],'delimiter','\\t','precision',6, '-append');\n"
        genScript += "end\n"
        genScript += "\n"

        # Write OpenEMS Script file into current dir.

        currDir, nameBase = self.getCurrDir()
        fileName = nameBase + "_draw_S21.m"
        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written to: ' + fileName)

        # Run octave script using command shell.

        cmdToRun = self.getOctaveExecCommand(fileName, '-q --persist')
        print('Running command: ' + cmdToRun)
        result = os.system(cmdToRun)
        print(result)


    #
    #	Generate Octave script which run openEMS AppCSXCAD to explore model, this is done using octave because path to openEMS folder should be known to octave
    #
    def displaySimulationModelButtonClicked(self):
        runCmd = ""
        runCmd += "modelFile = ['\"' '" + os.path.splitext(os.path.dirname(App.ActiveDocument.FileName))[0] + "/tmp/' '" + \
                  os.path.splitext(os.path.basename(App.ActiveDocument.FileName))[0] + ".xml' '\"'];\n"
        runCmd += 'runFile  = [dir_in_loadpath("openEMS/matlab","all"){1} "/../AppCSXCAD.exe " modelFile];'
        runCmd += "\n";
        runCmd += 'runFile = strrep(runFile, "/", filesep());'
        runCmd += "\n";
        runCmd += 'system(runFile);'
        runCmd += "\n";

        # store octave script to drive
        currDir, nameBase = self.getCurrDir()
        fileName = nameBase + '_runCmd_AppCSXCAD.m'
        f = open(fileName, "w", encoding='utf-8')
        f.write(runCmd)
        f.close()

        # run octave script using command shell
        cmdToRun = self.getOctaveExecCommand(fileName)
        print('Running command: ' + cmdToRun)
        result = os.system(cmdToRun)
        print(result)


    #
    #	Run current model openEMS Simulation Script
    #
    def runSimulationButtonClicked(self):
        currDir, nameBase = self.getCurrDir()
        fileName = nameBase + "_openEMS.m"

        # run octave script using command shell
        cmdToRun = self.getOctaveExecCommand(fileName)
        print('Running command: ' + cmdToRun)
        os.chdir(currDir)
        result = os.system(cmdToRun)
        print(result)
