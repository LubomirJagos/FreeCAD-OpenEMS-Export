#   author: Lubomir Jagos
#
#
import os
from PySide2 import QtGui, QtCore, QtWidgets
import numpy as np
import re
import math

from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r
from utilsOpenEMS.SettingsItem.SettingsItem import SettingsItem
from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers
from utilsOpenEMS.GuiHelpers.FactoryCadInterface import FactoryCadInterface

class OctaveScriptLinesGenerator:

    #
    #   constructor, get access to form GUI
    #
    def __init__(self, form, statusBar = None):
        self.form = form
        self.statusBar = statusBar

        self.internalPortIndexNamesList = {}
        self.internalNF2FFIndexNamesList = {}

        #
        # GUI helpers function like display message box and so
        #
        self.guiHelpers = GuiHelpers(self.form, statusBar = self.statusBar)
        self.cadHelpers = FactoryCadInterface.createHelper()

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

    #
    #   Returns current FreeCAD file:
    #       - absolute directory
    #       - name without extension
    #
    def getCurrDir(self):
        programname = os.path.basename(self.cadHelpers.getCurrDocumentFileName())
        programDir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())
        programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
        return [programDir, programbase]

    #
    #   Creates output dir in current FreeCAD file directory if not exists.
    #       outputDir - absolute path to directory where folder with simulation files should be created
    #
    def createOuputDir(self, outputDir):
        programname = os.path.basename(self.cadHelpers.getCurrDocumentFileName())     # FreeCAD filename with extension
        programdir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())       # FreeCAD file directory
        programbase, ext = os.path.splitext(programname)                # FreeCAD filename without extension

        #
        #   Simulation files will be saved in folder named based on FreeCAD filename and suffix _openEMS_simulation
        #       If parameter outputDir is not set this folder will be generated in the same folder as FreeCAD file.
        #       If outputDir is set folder with simulation folder with files is genenrated next to .ini file
        #
        if outputDir is None or outputDir == False:
            absoluteOutputDir = f"{programdir}/{programbase}_openEMS_simulation"
        else:
            absoluteOutputDir = outputDir

        if not os.path.exists(absoluteOutputDir):
            os.makedirs(absoluteOutputDir)
            print(f"Created directory for simulation: {outputDir}")

        return absoluteOutputDir

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

    def getModelCoordsType(self):
        """
        Returns current coordinate system, as there can be just rectangular or just cylindrical for all grid items it's enough to look at first grid item.
        :return: string (rectangular, cylindrical)
        """
        if self.form.gridSettingsTreeView.topLevelItemCount() > 0:
            coordsType = self.form.gridSettingsTreeView.topLevelItem(0).data(0, QtCore.Qt.UserRole).coordsType
        else:
            coordsType = "rectangular"
        return coordsType

    def getCoordinateSystemScriptLines(self):
        genScript = ""

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% COORDINATE SYSTEM\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        gridCoordsType = self.getModelCoordsType()
        if (gridCoordsType == "rectangular"):
            genScript += "CSX = InitCSX('CoordSystem', 0); % Cartesian coordinate system.\n"
        elif (gridCoordsType == "cylindrical"):
            genScript += "CSX = InitCSX('CoordSystem', 1); % Cylindrical coordinate system.\n"
        else:
            genScript += "%%%%%% ERROR GRID COORDINATION SYSTEM TYPE UNKNOWN"				

        genScript += "mesh.x = []; % mesh variable initialization (Note: x y z implies type Cartesian).\n"
        genScript += "mesh.y = [];\n"
        genScript += "mesh.z = [];\n"
        genScript += "CSX = DefineRectGrid(CSX, unit, mesh); % First call with empty mesh to set deltaUnit attribute.\n"
        genScript += "\n"

        return genScript

    def getMaterialDefinitionsScriptLines(self, items, outputDir=None, generateObjects=True):
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

            print(f"#MATERIAL generates {currSetting.getName()}, {str(currSetting.constants)}")
            genScript += "%% MATERIAL - " + currSetting.getName() + "\n"

            # when material metal use just AddMetal for simulator
            if (currSetting.type == 'metal'):
                genScript += "CSX = AddMetal(CSX, '" + currSetting.getName() + "');\n"
            elif (currSetting.type == 'userdefined'):
                genScript += "CSX = AddMaterial(CSX, '" + currSetting.getName() + "');\n"

                smp_args = ["CSX", "'" + currSetting.getName() + "'"]
                if str(currSetting.constants['epsilon']) != "0":
                    smp_args += ["'Epsilon'", str(currSetting.constants['epsilon'])]
                if str(currSetting.constants['mue']) != "0":
                    smp_args += ["'Mue'", str(currSetting.constants['mue'])]
                if str(currSetting.constants['kappa']) != "0":
                    smp_args += ["'Kappa'", str(currSetting.constants['kappa'])]
                if str(currSetting.constants['sigma']) != "0":
                    smp_args += ["'Sigma'", str(currSetting.constants['sigma'])]

                genScript += "CSX = SetMaterialProperty(" + ", ".join(smp_args) + ");\n"
            elif (currSetting.type == 'conducting sheet'):
                genScript += "CSX = AddConductingSheet(CSX, '" + currSetting.getName() + "', " + str(currSetting.constants["conductingSheetConductivity"]) + ", " + str(currSetting.constants["conductingSheetThicknessValue"]) + "*" + str(currSetting.getUnitsAsNumber(currSetting.constants["conductingSheetThicknessUnits"])) + ");\n"

            # first print all current material children names
            print(f"assigned objects: {[item.child(k).text(0) for k in range(item.childCount())]}")

            # now export material children, if it's object export as STL, if it's curve export as curve
            if (generateObjects):
                for k in range(item.childCount()):
                    childName = item.child(k).text(0)

                    #
                    #	getting item priority
                    #
                    objModelPriorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    objModelPriority = self.getItemPriority(objModelPriorityItemName)

                    # getting reference to FreeCAD object
                    freeCadObj = [i for i in self.cadHelpers.getObjects() if (i.Label) == childName][0]

                    #
                    #   HERE IS OBJECT GENERATOR THERE ARE FEW SPECIAL CASES WHICH ARE HANDLED FIRST AND IF OBJECT IS NORMAL STRUCTURE AT THE END IS GENERATED AS .stl FILR:
                    #       - conducting sheet = just plane is generated, in case of 3D object shell of object bounding box is generated
                    #       - discretized edge = curve from line is generated
                    #       - sketch           = curve is generated from it's vertices
                    #
                    if (currSetting.type == 'conducting sheet'):
                        #
                        #   Here comes object generator for conducting sheet. It's possible to define it as plane in XY, XZ, YZ plane in cartesian coords and XY plane in cylindrical coords.
                        #   So in case of conducting sheet no .stl is generated, it will be generated rectangle based on bounding box.
                        #
                        genScript += "%conducting sheet object\n"
                        genScript += f"%object Label: {freeCadObj.Label}\n"
                        bbCoords = freeCadObj.Shape.BoundBox

                        if (freeCadObj.Name.find("Sketch") > -1):
                            #
                            #   Sketch is added as polygon into conducting sheet material
                            #
                            normDir = ""
                            elevation = ""
                            if (bbCoords.XMin == bbCoords.XMax):
                                normDir = "x"
                                elevation = bbCoords.XMin

                                pointIndex = 1
                                genScript += "points = [];\n"
                                for geometryObj in freeCadObj.Geometry:
                                    if (str(type(geometryObj)).find("LineSegment") > -1):
                                        genScript += f"points(1,{pointIndex}) = " + str(_r(geometryObj.StartPoint.y)) + ";"
                                        genScript += f"points(2,{pointIndex}) = " + str(_r(geometryObj.StartPoint.z)) + ";"
                                        genScript += "\n"
                                        pointIndex += 1

                            elif (bbCoords.YMin == bbCoords.YMax):
                                normDir = "y"
                                elevation = bbCoords.YMin

                                pointIndex = 1
                                genScript += "points = [];\n"
                                for geometryObj in freeCadObj.Geometry:
                                    if (str(type(geometryObj)).find("LineSegment") > -1):
                                        genScript += f"points(1,{pointIndex}) = " + str(_r(geometryObj.StartPoint.x)) + ";"
                                        genScript += f"points(2,{pointIndex}) = " + str(_r(geometryObj.StartPoint.z)) + ";"
                                        genScript += "\n"
                                        pointIndex += 1

                            elif (bbCoords.ZMin == bbCoords.ZMax):
                                normDir = "z"
                                elevation = bbCoords.ZMin

                                pointIndex = 1
                                genScript += "points = [];\n"
                                for geometryObj in freeCadObj.Geometry:
                                    if (str(type(geometryObj)).find("LineSegment") > -1):
                                        genScript += f"points(1,{pointIndex}) = " + str(_r(geometryObj.StartPoint.x)) + ";"
                                        genScript += f"points(2,{pointIndex}) = " + str(_r(geometryObj.StartPoint.y)) + ";"
                                        genScript += "\n"
                                        pointIndex += 1

                            else:
                                normDir = "ERROR: sketch not lay in coordinate plane"

                            genScript += f"CSX = AddPolygon(CSX, '{currSetting.getName()}', {str(objModelPriority)}, '{normDir}', {_r(elevation)}, points);\n"

                            print("polygon into conducting sheet added.")

                        elif (bbCoords.XMin == bbCoords.XMax or bbCoords.YMin == bbCoords.YMax or bbCoords.ZMin == bbCoords.ZMax):
                            #
                            # Adding planar object into conducting sheet, if it consiss from faces then each face is added as polygon.
                            #

                            if (len(freeCadObj.Shape.Faces) > 0):

                                normDir = ""
                                elevation = ""
                                if (bbCoords.XMin == bbCoords.XMax):
                                    normDir = "x"
                                    elevation = bbCoords.XMin

                                    for face in freeCadObj.Shape.Faces:
                                        pointIndex = 1
                                        genScript += "points = [];\n"
                                        for vertex in face.Vertexes:
                                            genScript += f"points(1,{pointIndex}) = " + str(_r(vertex.Y)) + ";"
                                            genScript += f"points(2,{pointIndex}) = " + str(_r(vertex.Z)) + ";"
                                            genScript += "\n"
                                            pointIndex += 1
                                        genScript += f"CSX = AddPolygon(CSX, '{currSetting.getName()}', {str(objModelPriority)}, '{normDir}', {_r(elevation)}, points);\n"

                                elif (bbCoords.YMin == bbCoords.YMax):
                                    normDir = "y"
                                    elevation = bbCoords.YMin

                                    for face in freeCadObj.Shape.Faces:
                                        pointIndex = 1
                                        genScript += "points = [];\n"
                                        for vertex in face.Vertexes:
                                            genScript += f"points(1,{pointIndex}) = " + str(_r(vertex.X)) + ";"
                                            genScript += f"points(2,{pointIndex}) = " + str(_r(vertex.Z)) + ";"
                                            genScript += "\n"
                                            pointIndex += 1
                                        genScript += f"CSX = AddPolygon(CSX, '{currSetting.getName()}', {str(objModelPriority)}, '{normDir}', {_r(elevation)}, points);\n"

                                elif (bbCoords.ZMin == bbCoords.ZMax):
                                    normDir = "z"
                                    elevation = bbCoords.ZMin

                                    for face in freeCadObj.Shape.Faces:
                                        pointIndex = 1
                                        genScript += "points = [];\n"
                                        for vertex in face.Vertexes:
                                            genScript += f"points(1,{pointIndex}) = " + str(_r(vertex.X)) + ";"
                                            genScript += f"points(2,{pointIndex}) = " + str(_r(vertex.Y)) + ";"
                                            genScript += "\n"
                                            pointIndex += 1
                                        genScript += f"CSX = AddPolygon(CSX, '{currSetting.getName()}', {str(objModelPriority)}, '{normDir}', {_r(elevation)}, points);\n"

                            else:
                                genScript += f"%\tObject is planar as it should be.\n"
                                genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMin)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMin)}],[{_r(bbCoords.XMax)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMax)}]);\n"
                        else:
                            genScript += f"%\tObject is 3D so there are sheets on its boundary box generated.\n"
                            genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMin)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMin)}],[{_r(bbCoords.XMax)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMin)}]);\n"
                            genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMin)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMin)}],[{_r(bbCoords.XMax)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMax)}]);\n"
                            genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMin)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMin)}],[{_r(bbCoords.XMin)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMax)}]);\n"
                            genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMin)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMax)}],[{_r(bbCoords.XMax)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMax)}]);\n"
                            genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMin)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMin)}],[{_r(bbCoords.XMax)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMax)}]);\n"
                            genScript += f"CSX = AddBox(CSX,'{currSetting.getName()}',{str(objModelPriority)},[{_r(bbCoords.XMax)} {_r(bbCoords.YMin)} {_r(bbCoords.ZMin)}],[{_r(bbCoords.XMax)} {_r(bbCoords.YMax)} {_r(bbCoords.ZMax)}]);\n"

                    elif (freeCadObj.Name.find("Discretized_Edge") > -1):
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

                        genScript += "CSX = ImportSTL(CSX, '" + currSetting.getName() + "', " + str(
                            objModelPriority) + ", [currDir '/" + stlModelFileName + "'], 'Transform', {'Scale', fc_unit/unit});\n"

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

                        currDir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())
                        partToExport = [i for i in self.cadHelpers.getObjects() if (i.Label) == childName]

                        #output directory path construction, if there is no parameter for output dir then output is in current freecad file dir
                        if (not outputDir is None):
                            exportFileName = f"{outputDir}/{stlModelFileName}"
                        else:
                            exportFileName = f"{currDir}/{stlModelFileName}"

                        self.cadHelpers.exportSTL(partToExport, exportFileName)
                        print("Material object exported as STL into: " + exportFileName)

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

        #
        #   This here generates string for port excitation field, ie. for z+ generates [0 0 1], for y- generates [0 -1 0]
        #       Options for select field x,y,z were removed from GUI, but left here due there could be saved files from previous versions
        #       with these options so to keep backward compatibility they are treated as positive direction in that directions.
        #
        baseVectorStr = {'x': '[1 0 0]', 'y': '[0 1 0]', 'z': '[0 0 1]', 'x+': '[1 0 0]', 'y+': '[0 1 0]', 'z+': '[0 0 1]', 'x-': '[-1 0 0]', 'y-': '[0 -1 0]', 'z-': '[0 0 -1]', 'XY plane, top layer': '[0 0 -1]', 'XY plane, bottom layer': '[0 0 1]', 'XZ plane, front layer': '[0 -1 0]', 'XZ plane, back layer': '[0 1 0]', 'YZ plane, right layer': '[-1 0 0]', 'YZ plane, left layer': '[1 0 0]',}
        mslDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        coaxialDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        coplanarDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        striplineDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        probeDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% PORTS\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "portNamesAndNumbersList = containers.Map();\n\n"

        for [item, currSetting] in items:

            print(f"#PORT - {currSetting.getName()} - {currSetting.getType()}")

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                genScript += "%% PORT - " + currSetting.getName() + " - " + childName + "\n"

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    print(f"\t{obj.Label}")
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox
                    print(f'\t\t{bbCoords}')

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

                        if currSetting.infiniteResistance:
                            genScript += 'portR = inf;\n'
                        else:
                            genScript += 'portR = ' + str(currSetting.R) + ';\n'

                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'
                        genScript += "portExcitationAmplitude = " + str(currSetting.excitationAmplitude) + ";\n"
                        genScript += 'portDirection = {}*portExcitationAmplitude;\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        print('\t\tportStart = [ {0:g}, {1:g}, {2:g} ];'.format(_r(bbCoords.XMin), _r(bbCoords.YMin),_r(bbCoords.ZMin)))
                        print('\t\tportStop  = [ {0:g}, {1:g}, {2:g} ];'.format(_r(bbCoords.XMax), _r(bbCoords.YMax),_r(bbCoords.ZMax)))

                        isActiveStr = {False: '', True: ', true'}

                        genScript += '[CSX port{' + str(genScriptPortCount) + '}] = AddLumpedPort(CSX, ' + \
                                     str(priorityIndex) + ', ' + \
                                     str(genScriptPortCount) + ', ' + \
                                     'portR*portUnits, portStart, portStop, portDirection' + \
                                     isActiveStr.get(currSetting.isActive) + ');\n'

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'microstrip'):

                        #
                        #   It's important to generate microstrip port right, that means where is placed microstrip line, because microstrip consists from ground plane and trace
                        #       This is just playing with X,Y,Z coordinates of boundary box for microstrip port for min, max coordinates.
                        #
                        portStartX = _r(sf * bbCoords.XMin)
                        portStartY = _r(sf * bbCoords.YMin)
                        portStartZ = _r(sf * bbCoords.ZMin)
                        portStopX = _r(sf * bbCoords.XMax)
                        portStopY = _r(sf * bbCoords.YMax)
                        portStopZ = _r(sf * bbCoords.ZMax)

                        if (currSetting.direction == "XY plane, top layer"):
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.direction == "YZ plane, right layer"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                        elif (currSetting.direction == "XZ plane, front layer"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)

                        if (currSetting.mslPropagation == "z-"):
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.mslPropagation == "x-"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                        elif (currSetting.mslPropagation == "y-"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)

                        genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, portStartY, portStartZ)
                        genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, portStopY, portStopZ)

                        if currSetting.infiniteResistance:
                            genScript += 'portR = inf;\n'
                        else:
                            genScript += 'portR = ' + str(currSetting.R) + ';\n'

                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'
                        genScript += "portExcitationAmplitude = " + str(currSetting.excitationAmplitude) + ";\n"

                        genScript += 'mslDir = {};\n'.format(mslDirStr.get(currSetting.mslPropagation[0], '?')) #use just first letter of propagation direction
                        genScript += 'mslEVec = {}*portExcitationAmplitude;\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        feedShiftStr = {False: "", True: ", 'FeedShift', " + str(_r(currSetting.mslFeedShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.mslFeedShiftUnits)))}
                        measPlaneStr = {False: "", True: ", 'MeasPlaneShift', " + str(_r(currSetting.mslMeasPlaneShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.mslMeasPlaneShiftUnits)))}

                        isActiveMSLStr = {False: "", True: ", 'ExcitePort', true"}

                        genScript_R = ", 'Feed_R', portR*portUnits"

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddMSLPort(CSX," + \
                                     str(priorityIndex) + "," + \
                                     str(genScriptPortCount) + "," + \
                                     "'" + currSetting.mslMaterial + "'," + \
                                     "portStart, portStop, mslDir, mslEVec" + \
                                     isActiveMSLStr.get(currSetting.isActive) + \
                                     feedShiftStr.get(currSetting.mslFeedShiftValue > 0) + \
                                     measPlaneStr.get(currSetting.mslMeasPlaneShiftValue > 0) + \
                                     genScript_R + ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'circular waveguide'):
                        portStartX = _r(sf * bbCoords.XMin)
                        portStartY = _r(sf * bbCoords.YMin)
                        portStartZ = _r(sf * bbCoords.ZMin)
                        portStopX = _r(sf * bbCoords.XMax)
                        portStopY = _r(sf * bbCoords.YMax)
                        portStopZ = _r(sf * bbCoords.ZMax)

                        if (currSetting.waveguideCircDir == "z-"):
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.waveguideCircDir == "x-"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                        elif (currSetting.waveguideCircDir == "y-"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)

                        genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, portStartY, portStartZ)
                        genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, portStopY, portStopZ)

                        #
                        #   Based on port excitation direction which is not used at waveguide due it has modes, but based on that height and width are resolved.
                        #
                        waveguideRadius = 0
                        if (currSetting.direction[0] == "z"):
                            waveguideRadius = min(abs(portStartX - portStopX), abs(portStartY - portStopY))
                        elif (currSetting.direction[0] == "x"):
                            waveguideRadius = min(abs(portStartY - portStopY), abs(portStartZ - portStopZ))
                        elif (currSetting.direction[0] == "y"):
                            waveguideRadius = min(abs(portStartX - portStopX), abs(portStartZ - portStopZ))

                        genScript += "%% circular port openEMS code should be here\n"

                        #
                        #   This is .m file modified by me, due original from openEMS installation has hardwired value dir to 'z' direction so had to modify it to add dir parameter and copy
                        #   evaluation for Ex,Ey,Ez,Hx,Hy,Hz from rectangular waveguide
                        #
                        #[CSX,port] = AddCircWaveGuidePort2( CSX, prio, portnr, start, stop, dir, radius, mode_name, pol_ang, exc_amp, varargin )

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddCircWaveGuidePort2(CSX," + \
                                     str(priorityIndex) + "," + \
                                     str(genScriptPortCount) + "," + \
                                     "portStart,portStop," + \
                                     "'" + currSetting.waveguideCircDir[0] + "',"  + \
                                     str(waveguideRadius) + "',"  + \
                                     "'" + currSetting.modeName+ "'," + \
                                     str(currSetting.polarizationAngle) + "',"  + \
                                     (str(currSetting.excitationAmplitude) if currSetting.isActive else "0") + ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'rectangular waveguide'):
                        portStartX = _r(sf * bbCoords.XMin)
                        portStartY = _r(sf * bbCoords.YMin)
                        portStartZ = _r(sf * bbCoords.ZMin)
                        portStopX = _r(sf * bbCoords.XMax)
                        portStopY = _r(sf * bbCoords.YMax)
                        portStopZ = _r(sf * bbCoords.ZMax)

                        if (currSetting.waveguideRectDir == "z-"):
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.waveguideRectDir == "x-"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                        elif (currSetting.waveguideRectDir == "y-"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)

                        genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, portStartY, portStartZ)
                        genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, portStopY, portStopZ)

                        #
                        #   Based on port excitation direction which is not used at waveguide due it has modes, but based on that height and width are resolved.
                        #
                        waveguideWidth = 0
                        waveguideHeight = 0
                        if (currSetting.direction[0] == "z"):
                            waveguideWidth = abs(portStartX - portStopX)
                            waveguideHeight = abs(portStartY - portStopY)
                        elif (currSetting.direction[0] == "x"):
                            waveguideWidth = abs(portStartY - portStopY)
                            waveguideHeight = abs(portStartZ - portStopZ)
                        elif (currSetting.direction[0] == "y"):
                            waveguideWidth = abs(portStartX - portStopX)
                            waveguideHeight = abs(portStartZ - portStopZ)

                        genScript += "%% rectangular port openEMS code should be here\n"
                        #[CSX,port] = AddRectWaveGuidePort( CSX, prio, portnr, start, stop, dir, a, b, mode_name, exc_amp, varargin )

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddRectWaveGuidePort(CSX," + \
                                     str(priorityIndex) + "," + \
                                     str(genScriptPortCount) + "," + \
                                     "portStart,portStop," + \
                                     "'" + currSetting.waveguideRectDir[0] + "',"  + \
                                    str(waveguideWidth) + ", " + str(waveguideHeight) + "," + \
                                    "'" + currSetting.modeName+ "'," + \
                                    (str(currSetting.excitationAmplitude) if currSetting.isActive else "0") + ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'coaxial'):
                        portStartX = _r(sf * bbCoords.XMin)
                        portStartY = _r(sf * bbCoords.YMin)
                        portStartZ = _r(sf * bbCoords.ZMin)
                        portStopX = _r(sf * bbCoords.XMax)
                        portStopY = _r(sf * bbCoords.YMax)
                        portStopZ = _r(sf * bbCoords.ZMax)

                        if (currSetting.direction[1] == "-"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStartY = _r(sf * bbCoords.YMax)
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopX = _r(sf * bbCoords.XMin)
                            portStopY = _r(sf * bbCoords.YMin)
                            portStopZ = _r(sf * bbCoords.ZMin)

                        #calculate coaxial port radius, it's smaller dimension from width, height
                        coaxialRadius = 0.0
                        if (currSetting.direction[0] == "z"):
                            coaxialRadius = min(abs(portStartX - portStopX), abs(portStartY - portStopY))
                        elif (currSetting.direction[0] == "x"):
                            coaxialRadius = min(abs(portStartY - portStopY), abs(portStartZ - portStopZ))
                        elif (currSetting.direction[0] == "y"):
                            coaxialRadius = min(abs(portStartX - portStopX), abs(portStartZ - portStopZ))

                        #
                        #   This is important, radius is calculated from bounding box coordinates from FreeCAD so must be multiplied by metric units used in FreeCAD.
                        #   LuboJ ERROR: not sure if scaling done right
                        #
                        coaxialRadius = coaxialRadius/2 * self.getFreeCADUnitLength_m() / self.getUnitLengthFromUI_m()

                        #
                        #   LuboJ ERROR: not sure if scaling done right
                        #
                        coaxialInnerRadius = _r(currSetting.coaxialInnerRadiusValue * currSetting.getUnitsAsNumber(currSetting.coaxialInnerRadiusUnits) / self.getUnitLengthFromUI_m())
                        coaxialShellThickness = _r(currSetting.coaxialShellThicknessValue * currSetting.getUnitsAsNumber(currSetting.coaxialShellThicknessUnits) / self.getUnitLengthFromUI_m())
                        coaxialFeedShift = _r(currSetting.coaxialFeedpointShiftValue * currSetting.getUnitsAsNumber(currSetting.coaxialFeedpointShiftUnits) / self.getUnitLengthFromUI_m())
                        coaxialMeasPlaneShift = _r(currSetting.coaxialMeasPlaneShiftValue * currSetting.getUnitsAsNumber(currSetting.coaxialMeasPlaneShiftUnits) / self.getUnitLengthFromUI_m())

                        #
                        #   LuboJ ERROR: FeedShift and MeasPlaneShift doesn't seem to be working properly, it's not moving anything, error is somewhere here in code
                        #
                        feedShiftStr = {False: "", True: ", 'FeedShift', " + str(coaxialFeedShift)}
                        measPlaneStr = {False: "", True: ", 'MeasPlaneShift', " + str(coaxialMeasPlaneShift)}

                        #
                        #   Port start and end need to be shifted into middle of feed plane
                        #
                        if (currSetting.direction[0] == "z"):
                            genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format((portStartX+portStopX)/2, (portStartY+portStopY)/2, portStartZ)
                            genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format((portStartX+portStopX)/2, (portStartY+portStopY)/2, portStopZ)
                        elif (currSetting.direction[0] == "x"):
                            genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, (portStartY+portStopY)/2, (portStartZ+portStopZ)/2)
                            genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, (portStartY+portStopY)/2, (portStartZ+portStopZ)/2)
                        elif (currSetting.direction[0] == "y"):
                            genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format((portStartX+portStopX)/2, portStartY, (portStartZ+portStopZ)/2)
                            genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format((portStartX+portStopX)/2, portStopY, (portStartZ+portStopZ)/2)

                        genScript += 'coaxialDir = {};\n'.format(coaxialDirStr.get(currSetting.direction))

                        genScript += 'r_i = ' + str(coaxialInnerRadius) + ';\n'
                        genScript += 'r_o = ' + str(coaxialRadius - coaxialShellThickness) + ';\n'
                        genScript += 'r_os = ' + str(coaxialRadius) + ';\n'

                        genScript_R = ""
                        if not _bool(currSetting.infiniteResistance):
                            genScript += 'portR = ' + str(currSetting.R) + ';\n'
                            genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'
                            genScript_R = ", 'Feed_R', portR*portUnits"

                        genScript += "portExcitationAmplitude = " + str(currSetting.excitationAmplitude) + ";\n"

                        isActiveCoaxialStr = {
                            False:  "",
                            True:   ", 'ExcitePort', true, 'ExciteAmp', portExcitationAmplitude"
                        }

                        #feed resistance is NOT IMPLEMENTED IN openEMS AddCoaxialPort()

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddCoaxialPort(CSX," + \
                                     str(priorityIndex) + "," + \
                                     str(genScriptPortCount) + "," + \
                                     "'" + currSetting.coaxialConductorMaterial + "'," + \
                                     "'" + currSetting.coaxialMaterial + "'," + \
                                     "portStart,portStop,coaxialDir, r_i, r_o, r_os" + \
                                     isActiveCoaxialStr.get(currSetting.isActive) + \
                                     feedShiftStr.get(currSetting.coaxialFeedpointShiftValue > 0) + \
                                     measPlaneStr.get(currSetting.coaxialMeasPlaneShiftValue > 0) + \
                                     genScript_R + \
                                     ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'coplanar'):

                        gapWidth = currSetting.coplanarGapValue * currSetting.getUnitsAsNumber(currSetting.coplanarGapUnits) / self.getUnitLengthFromUI_m()
                        gapWidth_freeCAD_units = currSetting.coplanarGapValue * currSetting.getUnitsAsNumber(currSetting.coplanarGapUnits) / self.getFreeCADUnitLength_m()
                        genScript += 'gap_width = ' + str(gapWidth) + ';\n'

                        #
                        #   1. set all coords to max or min, this means where coplanar waveguide is placed if on top or bottom of object but we don't know orientation now
                        #
                        portStartX = _r(sf * bbCoords.XMin)
                        portStartY = _r(sf * bbCoords.YMin)
                        portStartZ = _r(sf * bbCoords.ZMin)
                        portStopX = _r(sf * bbCoords.XMax)
                        portStopY = _r(sf * bbCoords.YMax)
                        portStopZ = _r(sf * bbCoords.ZMax)

                        #
                        #   2. set coordinates of coplanar based on plane, height must be same
                        #
                        if (currSetting.direction == "XY plane, top layer"):
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMax)
                        elif (currSetting.direction == "XY plane, bottom layer"):
                            portStartZ = _r(sf * bbCoords.ZMin)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.direction == "YZ plane, right layer"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMax)
                        elif (currSetting.direction == "YZ plane, left layer"):
                            portStartX = _r(sf * bbCoords.XMin)
                            portStopX = _r(sf * bbCoords.XMin)
                        elif (currSetting.direction == "XZ plane, front layer"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMax)
                        elif (currSetting.direction == "XZ plane, back layer"):
                            portStartY = _r(sf * bbCoords.YMin)
                            portStopY = _r(sf * bbCoords.YMin)

                        #
                        #   3. set coplanar direcion based on propagation
                        #
                        if (currSetting.coplanarPropagation == "z-"):
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.coplanarPropagation == "x-"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                        elif (currSetting.coplanarPropagation == "y-"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)
                        elif (currSetting.coplanarPropagation == "z+"):
                            portStartZ = _r(sf * bbCoords.ZMin)
                            portStopZ = _r(sf * bbCoords.ZMax)
                        elif (currSetting.coplanarPropagation == "x+"):
                            portStartX = _r(sf * bbCoords.XMin)
                            portStopX = _r(sf * bbCoords.XMax)
                        elif (currSetting.coplanarPropagation == "y+"):
                            portStartY = _r(sf * bbCoords.YMin)
                            portStopY = _r(sf * bbCoords.YMax)

                        genScript += 'coplanarDir = {};\n'.format(coplanarDirStr.get(currSetting.coplanarPropagation[0], '?'))  # use just first letter of propagation direction

                        if (currSetting.direction[0:2] == "XY" and currSetting.coplanarPropagation[0] == "x"):
                            genScript += 'coplanarEVec = [0 1 0];\n'
                            portStartY += gapWidth_freeCAD_units
                            portStopY -= gapWidth_freeCAD_units
                        elif (currSetting.direction[0:2] == "XY" and currSetting.coplanarPropagation[0] == "y"):
                            genScript += 'coplanarEVec = [1 0 0];\n'
                            portStartX += gapWidth_freeCAD_units
                            portStopX -= gapWidth_freeCAD_units
                        elif (currSetting.direction[0:2] == "XZ" and currSetting.coplanarPropagation[0] == "x"):
                            genScript += 'coplanarEVec = [0 0 1];\n'
                            portStartZ += gapWidth_freeCAD_units
                            portStopZ -= gapWidth_freeCAD_units
                        elif (currSetting.direction[0:2] == "XZ" and currSetting.coplanarPropagation[0] == "z"):
                            genScript += 'coplanarEVec = [1 0 0];\n'
                            portStartX += gapWidth_freeCAD_units
                            portStopX -= gapWidth_freeCAD_units
                        elif (currSetting.direction[0:2] == "YZ" and currSetting.coplanarPropagation[0] == "y"):
                            genScript += 'coplanarEVec = [0 0 1];\n'
                            portStartZ += gapWidth_freeCAD_units
                            portStopZ -= gapWidth_freeCAD_units
                        elif (currSetting.direction[0:2] == "YZ" and currSetting.coplanarPropagation[0] == "z"):
                            genScript += 'coplanarEVec = [0 1 0];\n'
                            portStartY += gapWidth_freeCAD_units
                            portStopY -= gapWidth_freeCAD_units
                        else:
                            genScript += 'display("ERROR cannot evaluate right direction check your simulation settings for coplanar port");\n'
                            genScript += 'coplanarEVec = %ERROR cannot evaluate right direction check your simulation settings ;\n'

                        if currSetting.excitationAmplitude != 0:
                            genScript += "portExcitationAmplitude = " + str(currSetting.excitationAmplitude) + ";\n"
                            genScript += f"coplanarEVec = coplanarEVec * portExcitationAmplitude;\n"

                        genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, portStartY, portStartZ)
                        genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, portStopY, portStopZ)

                        if currSetting.infiniteResistance:
                            genScript += 'portR = inf;\n'
                        else:
                            genScript += 'portR = ' + str(currSetting.R) + ';\n'
                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'

                        isActiveStr = {False: "", True: ", 'ExcitePort', true"}
                        feedShiftStr = {False: "", True: ", 'FeedShift', " + str(_r(currSetting.coplanarFeedpointShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.coplanarFeedpointShiftUnits)))}
                        measPlaneStr = {False: "", True: ", 'MeasPlaneShift', " + str(_r(currSetting.coplanarMeasPlaneShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.coplanarMeasPlaneShiftUnits)))}
                        genScript_R = ", 'Feed_R', portR*portUnits"

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddCPWPort(CSX," + \
                                     str(priorityIndex) + "," + \
                                     str(genScriptPortCount) + "," + \
                                     "'" + currSetting.coplanarMaterial + "'," + \
                                     "portStart,portStop,gap_width,coplanarDir, coplanarEVec" + \
                                     isActiveStr.get(currSetting.isActive) + \
                                     feedShiftStr.get(currSetting.coplanarFeedpointShiftValue > 0) + \
                                     measPlaneStr.get(currSetting.coplanarMeasPlaneShiftValue > 0) + \
                                     genScript_R + ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'stripline'):
                        portStartX = _r(sf * (bbCoords.XMin + bbCoords.XMax)/2)
                        portStartY = _r(sf * (bbCoords.YMin + bbCoords.YMax)/2)
                        portStartZ = _r(sf * (bbCoords.ZMin + bbCoords.ZMax)/2)
                        portStopX = _r(sf * (bbCoords.XMin + bbCoords.XMax)/2)
                        portStopY = _r(sf * (bbCoords.YMin + bbCoords.YMax)/2)
                        portStopZ = _r(sf * (bbCoords.ZMin + bbCoords.ZMax)/2)

                        if (currSetting.striplinePropagation in ["x+", "y+"] and currSetting.direction == "XY plane"):
                            portStartX = _r(sf * bbCoords.XMin)
                            portStopX = _r(sf * bbCoords.XMax)
                            portStartY = _r(sf * bbCoords.YMin)
                            portStopY = _r(sf * bbCoords.YMax)
                        elif (currSetting.striplinePropagation in ["x+", "z+"] and currSetting.direction == "XZ plane"):
                            portStartX = _r(sf * bbCoords.XMin)
                            portStopX = _r(sf * bbCoords.XMax)
                            portStartZ = _r(sf * bbCoords.ZMin)
                            portStopZ = _r(sf * bbCoords.ZMax)
                        elif (currSetting.striplinePropagation in ["y+", "z+"] and currSetting.direction == "YZ plane"):
                            portStartY = _r(sf * bbCoords.YMin)
                            portStopY = _r(sf * bbCoords.YMax)
                            portStartZ = _r(sf * bbCoords.ZMin)
                            portStopZ = _r(sf * bbCoords.ZMax)
                        elif (currSetting.striplinePropagation in ["x-", "y-"] and currSetting.direction == "XY plane"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)
                        elif (currSetting.striplinePropagation in ["x-", "z-"] and currSetting.direction == "XZ plane"):
                            portStartX = _r(sf * bbCoords.XMax)
                            portStopX = _r(sf * bbCoords.XMin)
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)
                        elif (currSetting.striplinePropagation in ["y-", "z-"] and currSetting.direction == "YZ plane"):
                            portStartY = _r(sf * bbCoords.YMax)
                            portStopY = _r(sf * bbCoords.YMin)
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopZ = _r(sf * bbCoords.ZMin)

                        striplineHeight =  0
                        if (currSetting.direction == "YZ plane"):
                            striplineHeight = _r(sf * (bbCoords.XMax - bbCoords.XMin)/2)
                            genScript += 'striplineEVec = {};\n'.format(baseVectorStr.get('x'))
                        elif (currSetting.direction == "XZ plane"):
                            striplineHeight = _r(sf * (bbCoords.YMax - bbCoords.YMin)/2)
                            genScript += 'striplineEVec = {};\n'.format(baseVectorStr.get('y'))
                        elif (currSetting.direction == "XY plane"):
                            striplineHeight = _r(sf * (bbCoords.ZMax - bbCoords.ZMin)/2)
                            genScript += 'striplineEVec = {};\n'.format(baseVectorStr.get('z'))

                        if currSetting.excitationAmplitude != 0:
                            genScript += "portExcitationAmplitude = " + str(currSetting.excitationAmplitude) + ";\n"
                            genScript += 'striplineEVec = striplineEVec * portExcitationAmplitude;\n'

                        genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, portStartY, portStartZ)
                        genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, portStopY, portStopZ)

                        genScript += 'striplineDir = {};\n'.format(striplineDirStr.get(currSetting.striplinePropagation[0], '?'))  # use just first letter of propagation direction
                        genScript += 'striplineHeight = ' + str(striplineHeight) + ';\n'

                        isActiveStr = {False: "", True: ", 'ExcitePort', true"}
                        feedShiftStr = {False: "", True: ", 'FeedShift', " + str(_r(currSetting.striplineFeedpointShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.striplineFeedpointShiftUnits)))}
                        measPlaneStr = {False: "", True: ", 'MeasPlaneShift', " + str(_r(currSetting.striplineMeasPlaneShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.striplineMeasPlaneShiftUnits)))}

                        if currSetting.infiniteResistance:
                            genScript += 'portR = inf;\n'
                        else:
                            genScript += 'portR = ' + str(currSetting.R) + ';\n'
                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + ';\n'
                        genScript_R = ", 'Feed_R', portR*portUnits"

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddStripLinePort(CSX," + \
                                     str(priorityIndex) + "," + \
                                     str(genScriptPortCount) + "," + \
                                     "'PEC'," + \
                                     "portStart,portStop,striplineHeight,striplineDir, striplineEVec" + \
                                     isActiveStr.get(currSetting.isActive) + \
                                     feedShiftStr.get(currSetting.striplineFeedpointShiftValue > 0) + \
                                     measPlaneStr.get(currSetting.striplineMeasPlaneShiftValue > 0) + \
                                     genScript_R + ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'curve'):
                        if (_bool(currSetting.direction) == False):
                            portStartX = _r(sf * bbCoords.XMin)
                            portStartY = _r(sf * bbCoords.YMin)
                            portStartZ = _r(sf * bbCoords.ZMin)
                            portStopX = _r(sf * bbCoords.XMax)
                            portStopY = _r(sf * bbCoords.YMax)
                            portStopZ = _r(sf * bbCoords.ZMax)
                        else:
                            portStartX = _r(sf * bbCoords.XMax)
                            portStartY = _r(sf * bbCoords.YMax)
                            portStartZ = _r(sf * bbCoords.ZMax)
                            portStopX = _r(sf * bbCoords.XMin)
                            portStopY = _r(sf * bbCoords.YMin)
                            portStopZ = _r(sf * bbCoords.ZMin)

                        genScript += 'portStart  = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStartX, portStartY, portStartZ)
                        genScript += 'portStop = [ {0:g}, {1:g}, {2:g} ];\n'.format(portStopX, portStopY, portStopZ)

                        isActiveStr = {False: "", True: ", true"}
                        genScript_R = str(currSetting.R) + "*" + str(currSetting.getRUnits())

                        genScript += "[CSX port{" + str(genScriptPortCount) + "}] = AddCurvePort(CSX," + \
                                     str(priorityIndex) + ", " + \
                                     str(genScriptPortCount) + ", " + \
                                     genScript_R + ", " + \
                                     "portStart, portStop" + \
                                     isActiveStr.get(currSetting.isActive) + ");\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList("{obj.Label}") = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    else:
                        genScript += '% Unknown port type. Nothing was generated. \n'

                    genScript += "\n"

            genScript += "\n"

        return genScript

    def getProbeDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # nf2ff box counter, they are stored inside octave cell variable nf2ff{} so this is to index them properly, in octave cells index starts at 1
        genNF2FFBoxCounter = 1

        #
        #   This here generates string for port excitation field, ie. for z+ generates [0 0 1], for y- generates [0 -1 0]
        #       Options for select field x,y,z were removed from GUI, but left here due there could be saved files from previous versions
        #       with these options so to keep backward compatibility they are treated as positive direction in that directions.
        #
        baseVectorStr = {'x': '[1 0 0]', 'y': '[0 1 0]', 'z': '[0 0 1]', 'x+': '[1 0 0]', 'y+': '[0 1 0]', 'z+': '[0 0 1]', 'x-': '[-1 0 0]', 'y-': '[0 -1 0]', 'z-': '[0 0 -1]', 'XY plane, top layer': '[0 0 -1]', 'XY plane, bottom layer': '[0 0 1]', 'XZ plane, front layer': '[0 -1 0]', 'XZ plane, back layer': '[0 1 0]', 'YZ plane, right layer': '[-1 0 0]', 'YZ plane, left layer': '[1 0 0]',}
        probeDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}

        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
        genScript += "% PROBES\n"
        genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

        for [item, currSetting] in items:

            print(f"#PROBE - {currSetting.getName()} - {currSetting.getType()}")

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                genScript += "%% PROBE - " + currSetting.getName() + " - " + childName + "\n"

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    print(f"\t{obj.Label}")
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox
                    print(f"\t\t{bbCoords}")

                    #
                    # PROBE openEMS GENERATION INTO VARIABLE
                    #
                    if (currSetting.getType() == "probe"):
                        probeName = f"{currSetting.name}_{childName}"
                        genScript += 'probeDirection = {};\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        if currSetting.probeType == "voltage":
                            genScript += 'probeType = 0;\n'
                        elif currSetting.probeType == "current":
                            genScript += 'probeType = 1;\n'
                        else:
                            genScript += 'probeType = ?;    #ERROR probe code generate don\'t know type\n'

                        argStr = ""
                        if not (bbCoords.XMin == bbCoords.XMax or bbCoords.YMin == bbCoords.YMax or bbCoords.ZMin == bbCoords.ZMax):
                            argStr += ", 'NormDir', probeDirection"

                        if (currSetting.probeDomain == "frequency"):
                            argStr += ", 'frequency', ["

                            if (len(currSetting.probeFrequencyList) > 0):
                                for freqStr in currSetting.probeFrequencyList:
                                    freqStr = freqStr.strip()
                                    result = re.search(r"([+,\,\-,.,0-9]+)([A-Za-z]+)$", freqStr)
                                    if result:
                                        freqValue = float(result.group(1))
                                        freqUnits = result.group(2)
                                        freqValue = freqValue * currSetting.getUnitsAsNumber(freqUnits)
                                        argStr += str(freqValue) + ","
                                argStr += "]"
                            else:
                                argStr += "f0]#{ERROR NO FREQUENCIES FOR PROBE FOUND, SO INSTEAD USED f0#}"
                                self.cadHelpers.printWarning(f"probe octave code generator error, no frequencies defined for '{probeName}', using f0 instead\n")

                        genScript += "CSX = AddProbe(CSX, '" + probeName + "', probeType" + argStr + ");\n"
                        genScript += 'probeStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin), _r(sf * bbCoords.YMin), _r(sf * bbCoords.ZMin))
                        genScript += 'probeStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax), _r(sf * bbCoords.YMax), _r(sf * bbCoords.ZMax))
                        genScript += "CSX = AddBox(CSX, '" + probeName + "', 0, probeStart, probeStop );\n"
                        genScript += "\n"

                    elif (currSetting.getType() == "dumpbox"):
                        dumpboxName = f"{currSetting.name}_{childName}"

                        if currSetting.dumpboxDomain == "time":
                            if currSetting.dumpboxType == "E field":
                                genScript += 'dumpboxType = 0;\n'
                            elif currSetting.dumpboxType == "H field":
                                genScript += 'dumpboxType = 1;\n'
                            elif currSetting.dumpboxType == "J field":
                                genScript += 'dumpboxType = 3;\n'
                            elif currSetting.dumpboxType == "D field":
                                genScript += 'dumpboxType = 4;\n'
                            elif currSetting.dumpboxType == "B field":
                                genScript += 'dumpboxType = 5;\n'
                            else:
                                genScript += 'dumpboxType = ?;    #ERROR probe code generate don\'t know type\n'
                        elif currSetting.dumpboxDomain == "frequency":
                            if currSetting.dumpboxType == "E field":
                                genScript += 'dumpboxType = 10;\n'
                            elif currSetting.dumpboxType == "H field":
                                genScript += 'dumpboxType = 11;\n'
                            elif currSetting.dumpboxType == "J field":
                                genScript += 'dumpboxType = 13;\n'
                            elif currSetting.dumpboxType == "D field":
                                genScript += 'dumpboxType = 14;\n'
                            elif currSetting.dumpboxType == "B field":
                                genScript += 'dumpboxType = 15;\n'
                            else:
                                genScript += 'dumpboxType = ?;    #ERROR probe code generate don\'t know type\n'
                        else:
                            genScript += "dumboxType = ?;   #code generator cannot find domain (time/frequency)\n"

                        argStr = ""
                        #
                        #   dump file type:
                        #       0 = vtk (default)
                        #       1 = hdf5
                        #
                        if (currSetting.dumpboxFileType == "hdf5"):
                            argStr += f", 'FileType', 1"

                        emptyFrequencyListError = False
                        if (currSetting.dumpboxDomain == "frequency"):
                            argStr += ", 'Frequency', ["

                            if (len(currSetting.dumpboxFrequencyList) > 0):
                                for freqStr in currSetting.dumpboxFrequencyList:
                                    freqStr = freqStr.strip()
                                    result = re.search(r"([+,\,\-,.,0-9]+)([A-Za-z]+)$", freqStr)
                                    if result:
                                        freqValue = float(result.group(1))
                                        freqUnits = result.group(2)
                                        freqValue = freqValue * currSetting.getUnitsAsNumber(freqUnits)
                                        argStr += str(freqValue) + ","
                                argStr += "]"
                            else:
                                emptyFrequencyListError = True
                                argStr += "f0]"
                                self.cadHelpers.printWarning(f"dumpbox octave code generator error, no frequencies defined for '{dumpboxName}', using f0 instead\n")

                        #if error put note about it into script
                        if emptyFrequencyListError:
                            genScript += "CSX = AddDump(CSX, '" + dumpboxName + "', 'DumpType', dumpboxType" + argStr + "); % ERROR script generation no frequencies for dumpbox, therefore using f0\n"
                        else:
                            genScript += "CSX = AddDump(CSX, '" + dumpboxName + "', 'DumpType', dumpboxType" + argStr + ");\n"

                        genScript += 'dumpboxStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin), _r(sf * bbCoords.YMin), _r(sf * bbCoords.ZMin))
                        genScript += 'dumpboxStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax), _r(sf * bbCoords.YMax), _r(sf * bbCoords.ZMax))
                        genScript += "CSX = AddBox(CSX, '" + dumpboxName + "', 0, dumpboxStart, dumpboxStop );\n"
                        genScript += "\n"

                    elif (currSetting.getType() == 'et dump'):
                        dumpboxName = f"{currSetting.name}_{childName}"

                        genScript += "CSX = AddDump(CSX, '" + dumpboxName + "', 'DumpType', 0, 'DumpMode', 2);\n"
                        genScript += 'dumpStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                     _r(sf * bbCoords.YMin),
                                                                                     _r(sf * bbCoords.ZMin))
                        genScript += 'dumpStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                     _r(sf * bbCoords.YMax),
                                                                                     _r(sf * bbCoords.ZMax))
                        genScript += "CSX = AddBox(CSX, '" + dumpboxName + "', 0, dumpStart, dumpStop );\n"

                    elif (currSetting.getType() == 'ht dump'):
                        dumpboxName = f"{currSetting.name}_{childName}"

                        genScript += "CSX = AddDump(CSX, '" + dumpboxName + "', 'DumpType', 1, 'DumpMode', 2);\n"
                        genScript += 'dumpStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                     _r(sf * bbCoords.YMin),
                                                                                     _r(sf * bbCoords.ZMin))
                        genScript += 'dumpStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                     _r(sf * bbCoords.YMax),
                                                                                     _r(sf * bbCoords.ZMax))
                        genScript += "CSX = AddBox(CSX, '" + dumpboxName + "', 0, dumpStart, dumpStop );\n"

                    elif (currSetting.getType() == 'nf2ff box'):
                        dumpboxName = f"{currSetting.name} - {childName}"
                        dumpboxName = dumpboxName.replace(" ", "_")

                        genScript += 'nf2ffStart = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMin),
                                                                                      _r(sf * bbCoords.YMin),
                                                                                      _r(sf * bbCoords.ZMin))
                        genScript += 'nf2ffStop  = [ {0:g}, {1:g}, {2:g} ];\n'.format(_r(sf * bbCoords.XMax),
                                                                                      _r(sf * bbCoords.YMax),
                                                                                      _r(sf * bbCoords.ZMax))
                        # genScript += 'nf2ffUnit = ' + currSetting.getUnitAsScriptLine() + ';\n'
                        genScript += "[CSX nf2ffBox{" + str(genNF2FFBoxCounter) + "}] = CreateNF2FFBox(CSX, '" + dumpboxName + "', nf2ffStart, nf2ffStop);\n"
                        # NF2FF grid lines are generated below via getNF2FFDefinitionsScriptLines()

                        #
                        #   ATTENTION this is NF2FF box counter
                        #
                        self.internalNF2FFIndexNamesList[dumpboxName] = genNF2FFBoxCounter
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

        for [item, currentSetting] in items:
            genScript += "% LUMPED PARTS " + currentSetting.getName() + "\n"

            # traverse through all children item for this particular lumped part settings
            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                print(f"#LUMPED PART {currentSetting.getType()} - {currentSetting.getName()}")

                freecadObjects = [i for i in objs if (i.Label) == childName]
                for obj in freecadObjects:
                    # obj = FreeCAD Object class
                    print(f"\t{obj.Label}")

                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox

                    # PLACEMENT BOX
                    print(f"\t\t{bbCoords}")

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
                    genScript += "[CSX] = AddBox(CSX, '" + lumpedPartName + "', " + str(priorityIndex) + ", lumpedPartStart, lumpedPartStop);\n"

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

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox

                    #THIS HERE MUST BE !!!EXACTLY SAME!!! AS GRIDLINES IN PROBES, otherwise near field is not captured
                    if (currSetting.getType() == 'nf2ff box'):
                        nf2ff_gridlines['x'].append("{0:g}".format(_r(sf * bbCoords.XMin)))
                        nf2ff_gridlines['x'].append("{0:g}".format(_r(sf * bbCoords.XMax)))
                        nf2ff_gridlines['y'].append("{0:g}".format(_r(sf * bbCoords.YMin)))
                        nf2ff_gridlines['y'].append("{0:g}".format(_r(sf * bbCoords.YMax)))
                        nf2ff_gridlines['z'].append("{0:g}".format(_r(sf * bbCoords.ZMin)))
                        nf2ff_gridlines['z'].append("{0:g}".format(_r(sf * bbCoords.ZMax)))

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
        fcObjects = {obj.Label: obj for obj in self.cadHelpers.getObjects()}

        for gridSettingsNodeName in gridSettingsNodeNames:
            print("Grid type : " + gridSettingsNodeName)

        for k, [categoryName, gridName, FreeCADObjectName] in enumerate(orderedAssociations):

            print("Grid priority level {} : {} :: {}".format(k, FreeCADObjectName, gridName))

            if not (gridName in gridSettingsNodeNames):
                print("Failed to resolve '{}'.".format(gridName))
                continue
            itemListIdx = gridSettingsNodeNames.index(gridName)

            #GridSettingsItem object from GUI
            gridSettingsInst = items[itemListIdx][1]

            #Grid category object from GUI
            gridCategoryObj = items[itemListIdx][0]

            #
            #   Fixed Distance, Fixed Count mesh boundaries coords obtain
            #
            if (gridSettingsInst.getType() in ['Fixed Distance', 'Fixed Count']):
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
                    delta = self.maxGridResolution_m * sf * 0.001   #LuboJ, added multiply by 0.001 because still lambda/20 for 4GHz is 3.75mm too much
                    print("GRID generateLinesInside object detected, setting correction constant to " + str(delta) + "m (meters)")
                else:
                    delta = 0

                xmax = sf * bbCoords.XMax - np.sign(bbCoords.XMax - bbCoords.XMin) * delta
                ymax = sf * bbCoords.YMax - np.sign(bbCoords.YMax - bbCoords.YMin) * delta
                zmax = sf * bbCoords.ZMax - np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta
                xmin = sf * bbCoords.XMin + np.sign(bbCoords.XMax - bbCoords.XMin) * delta
                ymin = sf * bbCoords.YMin + np.sign(bbCoords.YMax - bbCoords.YMin) * delta
                zmin = sf * bbCoords.ZMin + np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta

                # Write grid definition.
                genScript += "%% GRID - " + gridSettingsInst.getName() + " - " + FreeCADObjectName + ' (' + gridSettingsInst.getType() + ")\n"

            #
            #   Smooth Mesh boundaries coords obtain
            #
            elif (gridSettingsInst.getType() == "Smooth Mesh"):

                xList = []
                yList = []
                zList = []

                #iterate over grid smooth mesh category freecad children
                for k in range(gridCategoryObj.childCount()):
                    FreeCADObjectName = gridCategoryObj.child(k).text(0)

                    fcObject = fcObjects.get(FreeCADObjectName, None)
                    if (not fcObject):
                        print("Smooth Mesh - Failed to resolve '{}'.".format(FreeCADObjectName))
                        continue

                    ### Produce script output.

                    if (not "Shape" in dir(fcObject)):
                        continue

                    bbCoords = fcObject.Shape.BoundBox

                    # If generateLinesInside is selected, grid line region is shifted inward by lambda/20.
                    if gridSettingsInst.generateLinesInside:
                        delta = self.maxGridResolution_m * sf * 0.001  # LuboJ, added multiply by 0.001 because still lambda/20 for 4GHz is 3.75mm too much
                        print("GRID generateLinesInside object detected, setting correction constant to " + str(delta) + "m (meters)")
                    else:
                        delta = 0

                    #append boundary coordinates into list
                    xList.append(sf * bbCoords.XMax - np.sign(bbCoords.XMax - bbCoords.XMin) * delta)
                    yList.append(sf * bbCoords.YMax - np.sign(bbCoords.YMax - bbCoords.YMin) * delta)
                    zList.append(sf * bbCoords.ZMax - np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta)
                    xList.append(sf * bbCoords.XMin + np.sign(bbCoords.XMax - bbCoords.XMin) * delta)
                    yList.append(sf * bbCoords.YMin + np.sign(bbCoords.YMax - bbCoords.YMin) * delta)
                    zList.append(sf * bbCoords.ZMin + np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta)

                    # Write grid definition.
                    genScript += "%% GRID - " + gridSettingsInst.getName() + " - " + FreeCADObjectName + ' (' + gridSettingsInst.getType() + ")\n"

                #order from min -> max coordinates in each list
                xList.sort()
                yList.sort()
                zList.sort()

            #
            #   Real octave mesh lines code generate starts here
            #

            #in case of cylindrical coordinates convert xyz to theta,r,z
            if (gridSettingsInst.coordsType == "cylindrical"):
                #FROM GUI ARE GOING DEGREES

                polarXMin = (xmin ** 2 + ymin ** 2) ** .5                  #r
                polarXMax = (xmax ** 2 + ymax ** 2) ** .5                  #r
                polarYMin = math.atan2(ymin, xmax)           #theta
                polarYMax = math.atan2(ymax, xmin)           #theta

                #just for safety to have it right
                xmin = min(polarXMin, polarXMax)
                xmax = max(polarXMin, polarXMax)
                ymin = min(polarYMin, polarYMax)
                ymax = max(polarYMin, polarYMax)

                if (gridSettingsInst.getType() == 'Smooth Mesh' and gridSettingsInst.unitsAngle == "deg"):
                    yParam = math.radians(gridSettingsInst.smoothMesh['yMaxRes'])
                elif (gridSettingsInst.getType() == 'Fixed Distance' and gridSettingsInst.unitsAngle == "deg"):
                    yParam = math.radians(gridSettingsInst.getXYZ(refUnit)['y'])
                elif (gridSettingsInst.getType() == 'User Defined'):
                    pass  # user defined is jaust text, doesn't have ['y']
                else:
                    yParam = gridSettingsInst.getXYZ(refUnit)['y']

                #z coordinate stays as was

            else:
                if (gridSettingsInst.getType() == 'Smooth Mesh'):
                    yParam = gridSettingsInst.smoothMesh['yMaxRes']
                elif (gridSettingsInst.getType() == 'User Defined'):
                    pass                                                #user defined is jaust text, doesn't have ['y']
                else:
                    yParam = gridSettingsInst.getXYZ(refUnit)['y']

            if (gridSettingsInst.getType() == 'Fixed Distance'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x(mesh.x >= {0:g} & mesh.x <= {1:g}) = [];\n".format(_r(xmin), _r(xmax))
                    genScript += "mesh.x = [ mesh.x ({0:g}:{1:g}:{2:g}) ];\n".format(_r(xmin), _r(gridSettingsInst.getXYZ(refUnit)['x']), _r(xmax))
                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y(mesh.y >= {0:g} & mesh.y <= {1:g}) = [];\n".format(_r(ymin), _r(ymax))
                    genScript += "mesh.y = [ mesh.y ({0:g}:{1:g}:{2:g}) ];\n".format(_r(ymin), _r(yParam), _r(ymax))
                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z(mesh.z >= {0:g} & mesh.z <= {1:g}) = [];\n".format(_r(zmin), _r(zmax))
                    genScript += "mesh.z = [ mesh.z ({0:g}:{1:g}:{2:g}) ];\n".format(_r(zmin), _r(gridSettingsInst.getXYZ(refUnit)['z']), _r(zmax))
                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            elif (gridSettingsInst.getType() == 'Fixed Count'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x(mesh.x >= {0:g} & mesh.x <= {1:g}) = [];\n".format(_r(xmin), _r(xmax))
                    if (not gridSettingsInst.getXYZ()['x'] == 1):
                        genScript += "mesh.x = [ mesh.x linspace({0:g},{1:g},{2:g}) ];\n".format(_r(xmin), _r(xmax), _r(gridSettingsInst.getXYZ(refUnit)['x']))
                    else:
                        genScript += "mesh.x = [ mesh.x {0:g} ];\n".format(_r((xmin + xmax) / 2))

                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y(mesh.y >= {0:g} & mesh.y <= {1:g}) = [];\n".format(_r(ymin), _r(ymax))
                    if (not gridSettingsInst.getXYZ()['y'] == 1):
                        genScript += "mesh.y = [ mesh.y linspace({0:g},{1:g},{2:g}) ];\n".format(_r(ymin), _r(ymax), _r(yParam))
                    else:
                        genScript += "mesh.y = [ mesh.y {0:g} ];\n".format(_r((ymin + ymax) / 2))

                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z(mesh.z >= {0:g} & mesh.z <= {1:g}) = [];\n".format(_r(zmin), _r(zmax))
                    if (not gridSettingsInst.getXYZ()['z'] == 1):
                        genScript += "mesh.z = [ mesh.z linspace({0:g},{1:g},{2:g}) ];\n".format(_r(zmin), _r(zmax), _r(gridSettingsInst.getXYZ(refUnit)['z']))
                    else:
                        genScript += "mesh.z = [ mesh.z {0:g} ];\n".format(_r((zmin + zmax) / 2))

                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            elif (gridSettingsInst.getType() == 'User Defined'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x(mesh.x >= {0:g} & mesh.x <= {1:g}) = [];\n".format(_r(xmin), _r(xmax))
                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y(mesh.y >= {0:g} & mesh.y <= {1:g}) = [];\n".format(_r(ymin), _r(ymax))
                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z(mesh.z >= {0:g} & mesh.z <= {1:g}) = [];\n".format(_r(zmin), _r(zmax))

                genScript += "xmin = {0:g};\n".format(_r(xmin))
                genScript += "xmax = {0:g};\n".format(_r(xmax))
                genScript += "ymin = {0:g};\n".format(_r(ymin))
                genScript += "ymax = {0:g};\n".format(_r(ymax))
                genScript += "zmin = {0:g};\n".format(_r(zmin))
                genScript += "zmax = {0:g};\n".format(_r(zmax))
                genScript += gridSettingsInst.getXYZ() + "\n"
                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            elif (gridSettingsInst.getType() == 'Smooth Mesh'):
                genScript += "smoothMesh = {};\n"
                if gridSettingsInst.xenabled:

                    #when top priority lines setting set, remove lines between min and max in ax direction
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x(mesh.x >= {0:g} & mesh.x <= {1:g}) = [];\n".format(_r(xList[0]), _r(xList[-1]))

                    genScript += f"smoothMesh.x = {str(xList)};\n"
                    if gridSettingsInst.smoothMesh['xMaxRes'] == 0:
                        genScript += "smoothMesh.x = AutoSmoothMeshLines(smoothMesh.x, max_res/unit); %max_res calculated in excitation part\n"
                    else:
                        genScript += f"smoothMesh.x = AutoSmoothMeshLines(smoothMesh.x, {gridSettingsInst.smoothMesh['xMaxRes']});\n"
                    genScript += "mesh.x = [mesh.x smoothMesh.x];\n"
                if gridSettingsInst.yenabled:

                    #when top priority lines setting set, remove lines between min and max in ax direction
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y(mesh.y >= {0:g} & mesh.y <= {1:g}) = [];\n".format(_r(yList[0]), _r(yList[-1]))

                    genScript += f"smoothMesh.y = {str(yList)};\n"
                    if gridSettingsInst.smoothMesh['yMaxRes'] == 0:
                        genScript += "smoothMesh.y = AutoSmoothMeshLines(smoothMesh.y, max_res/unit); %max_res calculated in excitation part\n"
                    else:
                        genScript += f"smoothMesh.y = AutoSmoothMeshLines(smoothMesh.y, {yParam});\n"
                    genScript += "mesh.y = [mesh.y smoothMesh.y];\n"
                if gridSettingsInst.zenabled:

                    #when top priority lines setting set, remove lines between min and max in ax direction
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z(mesh.z >= {0:g} & mesh.z <= {1:g}) = [];\n".format(_r(zList[0]), _r(zList[-1]))

                    genScript += f"smoothMesh.z = {str(zList)};\n"
                    if gridSettingsInst.smoothMesh['zMaxRes'] == 0:
                        genScript += "smoothMesh.z = AutoSmoothMeshLines(smoothMesh.z, max_res/unit); %max_res calculated in excitation part\n"
                    else:
                        genScript += f"smoothMesh.z = AutoSmoothMeshLines(smoothMesh.z, {gridSettingsInst.smoothMesh['zMaxRes']});\n"
                    genScript += "mesh.z = [mesh.z smoothMesh.z];\n"

                genScript += "CSX = DefineRectGrid(CSX, unit, mesh);\n"

            genScript += "\n"

        return genScript

    def getMinimalGridlineSpacingScriptLines(self):
        genScript = ""

        if (self.form.genParamMinGridSpacingEnable.isChecked()):
            minSpacingX = self.form.genParamMinGridSpacingX.value() / 1000 / self.getUnitLengthFromUI_m()
            minSpacingY = self.form.genParamMinGridSpacingY.value() / 1000 / self.getUnitLengthFromUI_m()
            minSpacingZ = self.form.genParamMinGridSpacingZ.value() / 1000 / self.getUnitLengthFromUI_m()

            genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
            genScript += "% MINIMAL GRIDLINES SPACING, removing gridlines which are closer as defined in GUI\n"
            genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
            genScript += 'mesh.x = sort(mesh.x);\n'
            genScript += 'mesh.y = sort(mesh.y);\n'
            genScript += 'mesh.z = sort(mesh.z);\n'
            genScript += '\n'
            genScript += 'for k = 1:length(mesh.x)-1\n'
            genScript += '  if (mesh.x(k) ~= inf && abs(mesh.x(k+1)-mesh.x(k)) <= ' + str(minSpacingX) + ')\n'
            genScript += '    display(["Removnig line at x: " num2str(mesh.x(k+1))]);\n'
            genScript += '    mesh.x(k+1) = inf;\n'
            genScript += '   end\n'
            genScript += 'end\n'
            genScript += '\n'
            genScript += 'for k = 1:length(mesh.y)-1\n'
            genScript += '  if (mesh.y(k) ~= inf && abs(mesh.y(k+1)-mesh.y(k)) <= ' + str(minSpacingY) + ')\n'
            genScript += '    display(["Removnig line at y: " num2str(mesh.y(k+1))]);\n'
            genScript += '    mesh.y(k+1) = inf;\n'
            genScript += '   end\n'
            genScript += 'end\n'
            genScript += '\n'
            genScript += 'for k = 1:length(mesh.z)-1\n'
            genScript += '  if (mesh.z(k) ~= inf && abs(mesh.z(k+1)-mesh.z(k)) <= ' + str(minSpacingZ) + ')\n'
            genScript += '    display(["Removnig line at z: " num2str(mesh.z(k+1))]);\n'
            genScript += '    mesh.z(k+1) = inf;\n'
            genScript += '   end\n'
            genScript += 'end\n'
            genScript += '\n'
            genScript += 'mesh.x(isinf(mesh.x)) = [];\n'
            genScript += 'mesh.y(isinf(mesh.y)) = [];\n'
            genScript += 'mesh.z(isinf(mesh.z)) = [];\n'
            genScript += '\n'
            genScript += 'CSX = DefineRectGrid(CSX, unit, mesh);\n'
            genScript += '\n'

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

            # FOR WHOLE SIMULATION THERE IS JUST ONE EXCITATION DEFINED, so first is taken!
            if (excitationCategory[0].childCount() > 0):
                item = excitationCategory[0].child(0)
                currSetting = item.data(0, QtCore.Qt.UserRole)  # At index 0 is Default Excitation.
                # Currently only 1 excitation is allowed. Multiple excitations could be managed by setting one of them as "selected" or "active", while all others are deactivated.
                # This would help the user to manage different analysis scenarios / excitation ranges.

                print(f"#EXCITATION - {currSetting.getName()} - {currSetting.getType()}")

                genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"
                genScript += "% EXCITATION " + currSetting.getName() + "\n"
                genScript += "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n"

                # EXCITATION FREQUENCY AND CELL MAXIMUM RESOLUTION CALCULATION (1/20th of minimal lambda - calculated based on maximum simulation frequency)
                # maximum grid resolution is generated into script but NOT USED IN OCTAVE SCRIPT, instead is also calculated here into python variable and used in bounding box correction
                if (currSetting.getType() == 'sinusodial'):
                    genScript += "f0 = " + str(currSetting.sinusodial['f0']) + "*" + str(currSetting.getUnitsAsNumber(currSetting.units)) + ";\n"
                    genScript += "fc = 0;\n"
                    if not definitionsOnly:
                        genScript += "FDTD = SetSinusExcite( FDTD, f0 );\n"
                    genScript += "max_res = c0 / f0 / 20;\n"
                    self.maxGridResolution_m = 3e8 / (currSetting.sinusodial['f0'] * currSetting.getUnitsAsNumber(currSetting.units) * 20)
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
                    genScript += "fc = 0.0;\n"
                    if not definitionsOnly:
                        genScript += "FDTD = SetCustomExcite( FDTD, f0, '" + currSetting.custom['functionStr'].replace(
                            'f0', str(f0)) + "' );\n"
                    genScript += "max_res = 0;\n"
                    self.maxGridResolution_m = 0
                    pass
                elif (currSetting.getType() == 'dirac'):
                    if not definitionsOnly:
                        genScript += "FDTD = SetDiracExcite(FDTD);\n"
                    pass
                elif (currSetting.getType() == 'step'):
                    if not definitionsOnly:
                        genScript += "FDTD = SetStepExcite(FDTD);\n"
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
    def generateOpenEMSScript(self, outputDir=None):

        # Create outputDir relative to local FreeCAD file if output dir does not exists
        #   if outputDir is set to same value
        #   if outputStr is None then folder with name as FreeCAD file with suffix _openEMS_simulation is created
        outputDir = self.createOuputDir(outputDir)

        # Write _OpenEMS.m script file to current directory.
        currDir, nameBase = self.getCurrDir()
        nameBase = nameBase.replace(" ", "_")               #IMPORTANT! openEMS function to run simulation cannot handle spaces in name of .m file
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_openEMS.m"
        else:
            fileName = f"{currDir}/{nameBase}_openEMS.m"

        # Update status bar to inform user that exporting has begun.
        if self.statusBar is not None:
            self.statusBar.showMessage("Generating OpenEMS script and geometry files ...", 5000)
            QtWidgets.QApplication.processEvents()

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
        genScript += "postprocessing_only = " + ('1' if self.form.generateJustPreviewCheckbox.isChecked() else '0')+ ";\n"
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
        genScript += "Sim_Path = 'simulation_output';\n"

        #genScript += "Sim_CSX = '" + os.path.splitext(os.path.basename(self.cadHelpers.getCurrDocumentFileName()))[0] + ".xml';\n"
        genScript += "Sim_CSX = '" + nameBase + ".xml';\n"

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
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write port definitions, due microstrip ports it must be defined after grid.
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Write lumped part definitions.
        genScript += self.getLumpedPartDefinitionsScriptLines(itemsByClassName.get("LumpedPartSettingsItem", None))

        # Write probes definitions
        genScript += self.getProbeDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write NF2FF probe grid definitions.
        genScript += self.getNF2FFDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

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
    def writeNf2ffButtonClicked(self, outputDir=None, nf2ffBoxName="", nf2ffBoxInputPortName="", plotFrequency=0, freqCount=501):
        genScript = ""
        genScript += "% Plot far field for structure.\n"
        genScript += "%\n"

        genScript += self.getInitScriptLines()

        genScript += "Sim_Path = 'simulation_output';\n"
        genScript += "currDir = strrep(pwd(), '\\', '\\\\');\n"
        genScript += "display(currDir);\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write port definitions:
        #    - must be after gridlines definitions
        #    - must be before nf2ff
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Write probes definitions
        genScript += self.getProbeDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write NF2FF probe grid definitions. THIS NEEDS TO BE DONE TO FILL self.internalNF2FFIndexNamesList[] with keys and indexes, key = "[nf2ff probe category name] - [object label]"
        genScript += self.getNF2FFDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

        #
        #   Current NF2FF box index
        #
        print(f"writeNf2ffButtonClicked() > geerate script, getting nf2ff box index for '{nf2ffBoxName}'")
        currentNF2FFBoxIndex = self.internalNF2FFIndexNamesList[nf2ffBoxName.replace(" ", "_")]
        currentNF2FFInputPortIndex = self.internalPortIndexNamesList[nf2ffBoxInputPortName]

        thetaStart = str(self.form.portNf2ffThetaStart.value())
        thetaStop = str(self.form.portNf2ffThetaStop.value())
        thetaStep = str(self.form.portNf2ffThetaStep.value())

        phiStart = str(self.form.portNf2ffPhiStart.value())
        phiStop = str(self.form.portNf2ffPhiStop.value())
        phiStep = str(self.form.portNf2ffPhiStep.value())

        #
        #   ATTENTION THIS IS SPECIFIC FOR FAR FIELD PLOTTING, plotFrequency and frequencies count
        #
        genScript += "freq = linspace(max([0,f0-fc]), f0+fc, " + str(freqCount) + ");\n"
        genScript += f"plotFrequency = [{plotFrequency}];\n"
        genScript += "port{" + str(currentNF2FFInputPortIndex) + "} = calcPort(port{" + str(currentNF2FFInputPortIndex) + "}, Sim_Path, freq);\n"
        genScript += "\n"

        genScript += """
%% NFFF contour plots %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% get accepted antenna power at frequency f0
%
%	WARNING - hardwired 1st port
%
P_in_0 = interp1(freq, port{""" + str(currentNF2FFInputPortIndex) + """}.P_acc, f0);

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
nf2ff = CalcNF2FF(nf2ffBox{""" + str(currentNF2FFBoxIndex) + """}, Sim_Path, plotFrequency, thetaRange*pi/180, phiRange*pi/180, 'Mode', 1, 'Outfile', '3D_Pattern.h5', 'Verbose', 1);

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

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_NF2FF.m"
        else:
            fileName = f"{currDir}/{nameBase}_draw_NF2FF.m"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Script to display far field written into: ' + fileName)
        self.guiHelpers.displayMessage('Script to display far field written into: ' + fileName, forceModal=False)

    def drawS11ButtonClicked(self, outputDir=None, portName=""):
        genScript = ""
        genScript += "% Plot S11\n"
        genScript += "%\n"

        genScript += self.getInitScriptLines()

        genScript += "Sim_Path = 'simulation_output';\n"
        genScript += "currDir = strrep(pwd(), '\\', '\\\\');\n"
        genScript += "display(currDir);\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

        # Write port definitions.
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        genScript += """%% postprocessing & do the plots
freq = linspace( max([0,f0-fc]), f0+fc, 501 );

port = calcPort( port, Sim_Path, freq);
s11 = port{""" + str(self.internalPortIndexNamesList[portName]) + """}.uf.ref./ port{""" + str(self.internalPortIndexNamesList[portName]) + """}.uf.inc;
s11_dB = 20*log10(abs(s11));

plot( freq/1e6, 20*log10(abs(s11)), 'k-', 'Linewidth', 2 );
grid on
title( 'reflection coefficient S_{11}' );
xlabel( 'frequency f / MHz' );
ylabel( 'reflection coefficient |S_{11}|' );

%
%   Write S11, real and imag Z_in into CSV file separated by ';'
%
filename = 'openEMS_simulation_s11_dB.csv';
fid = fopen(filename, 'w');
fprintf(fid, 'freq (MHz);s11 (dB);\\n');
fclose(fid)
s11_dB = horzcat((freq/1e6)', s11_dB');
dlmwrite(filename, s11_dB, '-append', 'delimiter', ';');
"""

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_S11.m"
        else:
            fileName = f"{currDir}/{nameBase}_draw_S11.m"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written into: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written into: ' + fileName, forceModal=False)

    def drawS11ButtonClicked_2(self, outputDir=None, portName=""):
        """
        This was previous function calculate S11 for port{1} hardwired using data from files from time domain.
        It was obsolete as there are after calcPort() values in P_ref and P_inc which are used to calculate S11
        :param outputDir:
        :param portName:
        :return: Octave scriptlines for openEMS to calculate S11 for port{1}
        """
        genScript = ""
        genScript += "% Plot S11\n"
        genScript += "%\n"

        genScript += self.getInitScriptLines()

        genScript += "Sim_Path = 'simulation_output';\n"
        genScript += "currDir = strrep(pwd(), '\\', '\\\\');\n"
        genScript += "display(currDir);\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None),
                                                            outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write port definitions.
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        genScript += """%% postprocessing & do the plots
freq = linspace( max([0,f0-fc]), f0+fc, 501 );
U = ReadUI( {'port_ut""" + str(self.internalPortIndexNamesList[portName]) + """','et'}, 'simulation_output/', freq ); % time domain/freq domain voltage
I = ReadUI( 'port_it""" + str(self.internalPortIndexNamesList[portName]) + """', 'simulation_output/', freq ); % time domain/freq domain current (half time step is corrected)

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

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_S11.m"
        else:
            fileName = f"{currDir}/{nameBase}_draw_S11.m"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written into: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written into: ' + fileName,
                                       forceModal=False)

    def drawS21ButtonClicked(self, outputDir=None, sourcePortName="", targetPortName=""):
        genScript = ""
        genScript += "% Plot S11, S21 parameters from OpenEMS results.\n"
        genScript += "%\n"

        genScript += self.getInitScriptLines()

        genScript += "Sim_Path = 'simulation_output';\n"
        genScript += "currDir = strrep(pwd(), '\\', '\\\\');\n"
        genScript += "display(currDir);\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

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
        genScript += "s11 = port{" + str(self.internalPortIndexNamesList[sourcePortName]) + "}.uf.ref./ port{" + str(self.internalPortIndexNamesList[sourcePortName]) + "}.uf.inc;\n"
        genScript += "s21 = port{" + str(self.internalPortIndexNamesList[targetPortName]) + "}.uf.ref./ port{" + str(self.internalPortIndexNamesList[sourcePortName]) + "}.uf.inc;\n"
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

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_S21.m"
        else:
            fileName = f"{currDir}/{nameBase}_draw_S21.m"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written to: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written to: ' + fileName, forceModal=False)
