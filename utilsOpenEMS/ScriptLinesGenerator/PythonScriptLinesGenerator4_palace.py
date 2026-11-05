#   author: Lubomir Jagos
#
#
import os
from PySide import QtGui, QtCore, QtWidgets
import numpy as np
import re
import math

from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r, _r2
from utilsOpenEMS.GuiHelpers.FactoryCadInterface import FactoryCadInterface
from utilsOpenEMS.ScriptLinesGenerator.PythonScriptLinesGenerator3_emerge import PythonScriptLinesGenerator3_emerge

class PythonScriptLinesGenerator4_palace(PythonScriptLinesGenerator3_emerge):

    _gmshGroupId = {}

    #
    #   constructor, get access to form GUI
    #
    def __init__(self, form, statusBar = None):
        super(PythonScriptLinesGenerator4_palace, self).__init__(form, statusBar)

    def generateSimulationScript(self, outputDir=None):
        self.generatePalaceScript(outputDir)

    def generatePalaceScript(self, outputDir=None):
        self.portBoundaryConditionScriptLinesBuffer = []
        self.createdObjectNameList = []
        self.createdObjectBoundaryNameList = []
        self._gmshGroupId = {}

        # Create outputDir relative to local FreeCAD file if output dir does not exists
        #   if outputDir is set to same value
        #   if outputStr is None then folder with name as FreeCAD file with suffix _openEMS_simulation is created
        outputDir = self.createOuputDir(outputDir)

        # Update status bar to inform user that exporting has begun.
        if self.statusBar is not None:
            self.statusBar.showMessage("Generating Palace script and geometry files ...", 5000)
            QtWidgets.QApplication.processEvents()

        # Constants and variable initialization.
        #
        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        simulationName = self.cadHelpers.getCurrentDocumentFileName()
        simulationOutputMeshFile = self.form.simParamsModelMeshName_palace.text()
        simulationOutputDirectory = self.form.simParamsOutputDirectory_palace.text()
        simParamsVerbose_palace = self.form.simParamsVerbose_palace.value()
        simulationProblemType = self.form.simParamsSimulationTypeList_palace.currentText()
        simParamsModelMeshBaseUnits_palace = self.form.simParamsModelMeshBaseUnits_palace.currentText()

        linearSolverType = self.form.simParamsLinearSolverType_palace.currentText()
        linearSolverTolerance = self.form.simParamsLinearSolverTolerance_palace.value()
        linearSolverMaxIterationCount = self.form.simParamsLinearSolverMaximumIterationCount_palace.value()
        linearSolverKSPType = self.form.simParamsLinearSolverKSPType_palace.currentText()

        solverOrder = self.form.simParamsLinearSolverOrder_palace.value()
        solverDevice = self.form.simParamsSolverDevice_palace.currentText()


        # List categories and items.
        #
        itemsByClassName = self.getItemsByClassName()

        # Write script header.
        #
        genScript = ""

        genScript += "## Palace simulation\n"
        genScript += "#\n"
        genScript += "#\n"
        genScript += "import os\n"

        genScript += "\n"
        genScript += "currDir = os.getcwd()\n"
        genScript += "print(currDir)\n"
        genScript += "\n"
        genScript += "\n"

        genScript += "import gmsh\n"
        genScript += "import os\n"
        genScript += "import json\n"
        genScript += "from basicpalacesolverhelperpackage import BasicMfemMesher\n"
        genScript += "\n"

        genScript += "# --- Unit definitions -----------------------------------------------------\n"
        genScript += "m = 1.0\n"
        genScript += "cm = 0.01\n"
        genScript += "mm = 0.001  # meters per millimeter\n"
        genScript += "um = 0.000001\n"
        genScript += "nm = 0.000000001\n"
        genScript += "\n"

        genScript += "##########################################################################################################\n"
        genScript += "# MAIN PROGRAM\n"
        genScript += "##########################################################################################################\n"
        genScript += "gmsh.initialize()\n"
        genScript += f"gmsh.model.add('{simulationName}')\n"
        genScript += "\n"
        genScript += "mesherObj = BasicMfemMesher()\n"
        genScript += "\n"
        genScript += "# variable to store ID in gmsh to identify groups, these IDs are later used in result .json file for simulation in palace in 'Attributes'\n"
        genScript += "gmshGroupId = {}\n"
        genScript += "\n"

        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir)
        genScript += self.getObjectUsedInSomeCategoryStepImportScriptLines(itemsByClassName.get("BoundaryConditionSettingsItem", None), outputDir)

        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None), outputDir)
        #
        #   Port are added when geometry is created because they must be meshed but then there is also needed to create boundary condition for them
        #
        for portBcScriptLine in self.portBoundaryConditionScriptLinesBuffer:
            genScript += portBcScriptLine
        genScript += "\n"

        genScript += self.getLumpedPartDefinitionsScriptLines(itemsByClassName.get("LumpedPartSettingsItem", None), outputDir)
        genScript += "\n"

        genScript += "##########################################################################################################\n"
        genScript += "# Create continuous mesh, subtract objects between each other based on their priority and\n"
        genScript += "# perform fragmentation, reassing internal gmsh tags to objects\n"
        genScript += "##########################################################################################################\n"
        genScript += "gmsh.model.occ.synchronize()\n"
        genScript += "#mesherObj.cutVolumesInsideModel()\n"
        genScript += "mesherObj.cutOnlyVolumesInModelBetweenEachOther(allowSurfacesToBeCutted=True)\n"
        genScript += "gmsh.model.occ.removeAllDuplicates()\n"
        genScript += "gmsh.model.occ.synchronize()\n"
        genScript += "mesherObj.performFragmentationAndReassignTags()\n"
        genScript += "gmsh.model.occ.synchronize()\n"
        genScript += "gmsh.fltk.run()\n"
        genScript += "\n"
        genScript += "# this is auxiliary method since fragmentation seems to leave some fragments in both objects when they are fragmented\n"
        genScript += "# once when cutting and fragmentation will be done totally right and tested this could be removed without any effect\n"
        genScript += "mesherObj.removeDuplicateTagsInGeometryObjects()\n"
        genScript += "\n"

        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        genScript += "##########################################################################################################\n"
        genScript += "# Define physical groups for volumes and surfaces\n"
        genScript += "#\n"
        genScript += "#\tfor debugging purposes there are also following other methods in mesher object, but use them just\n"
        genScript += "#\tto visualize model, palace solver will not run IF SAME ELEMENT IN MULTIPLE GROUPS!!!\n"
        genScript += "#\t\t- mesherObj.createGroupsForAllImportedObjects()\n"
        genScript += "#\t\t- mesherObj.createGroupsForAllMaterials()\n"
        genScript += "#\t\t- mesherObj.createGroupsForAllBoundaryConditions()\n"
        genScript += "##########################################################################################################\n"
        genScript += "mesherObj.createGroupsForObjectVolumesUsedInMaterials()\n"
        genScript += "mesherObj.createGroupsForObjectSurfacesUsedInBoundaryConditions()\n"
        genScript += "mesherObj.createGroupsForObjectSurfacesUsedInPort()\n"
        genScript += "\n"
        genScript += "## GOOD TO KNOW in case of error during palace simulation preparation in MFEM part:\n"
        genScript += "#\tMFEM Warning: Non - positive attributes on the boundary!\n"
        genScript += "#\t\t... in function: virtual void mfem::Mesh::SetAttributes(bool, bool)\n"
        genScript += "#\t\t... in file: / opt / palace - build / extern / mfem / mesh / mesh.cpp: 1955\n"
        genScript += "#\n"
        genScript += "# EXAPLANATION:\n"
        genScript += "#   You have surfaces without a physical group assigned:\n"
        genScript += "#     When gmsh saves a mesh with physical groups defined, any surface NOT in a physical group gets attribute 0. Palace/MFEM then chokes on it.\n"
        genScript += "#\n"
        genScript += "#   Some surface in simulation object is not part of any group and therefore in MFEM it has tag 0 which causes error, check gmsh model if all surfaces are assigned to object.\n"
        genScript += "#\n"
        genScript += "mesherObj.createGroupsForUntaggedSurfacesAndVolumes()\n"
        genScript += "\n"

        genScript += "##########################################################################################################\n"
        genScript += "# MESH GENERATE\n"
        genScript += "##########################################################################################################\n"
        genScript += "# gmsh directives\n"
        genScript += "gmsh.option.setNumber(\"General.Terminal\", 1)  # print messages\n"
        genScript += "gmsh.option.setNumber(\"Mesh.MshFileVersion\", 2.2)\n"
        genScript += "gmsh.option.setNumber(\"Mesh.Binary\", 0)  # text .msh file\n"
        genScript += "gmsh.option.setNumber(\"Mesh.Algorithm3D\", 1)  # 1: Delaunay, 3: Initial mesh only, 4: Frontal, 7: MMG3D, 9: R-tree, 10: HXT\n"
        genScript += "\n"
        genScript += "gmsh.model.occ.removeAllDuplicates()\n"
        genScript += "gmsh.model.occ.synchronize()\n"
        genScript += "\n"

        genScript += "# Generate mesh\n"
        genScript += "gmsh.model.mesh.generate(3)\n"
        genScript += "try:\n"
        genScript += "\tos.mkdir('mesh')\n"
        genScript += "except:\n"
        genScript += "\tpass\n"
        genScript += f"gmsh.write('{simulationOutputMeshFile}')\n"
        genScript += "\n"
        genScript += f"print('PASS - Mesh generated and saved as {simulationOutputMeshFile}')\n"
        genScript += "\n"

        genScript += "##########################################################################################################\n"
        genScript += "# Open generated msh file\n"
        genScript += "##########################################################################################################\n"
        genScript += "gmsh.fltk.run()\n"
        genScript += "\n"
        genScript += "gmsh.clear()\n"
        genScript += "gmsh.finalize()\n"
        genScript += "\n"
        genScript += "##########################################################################################################\n"
        genScript += "# Generate Palace solver simulation .json file\n"
        genScript += "##########################################################################################################\n"
        genScript += "simulationConfig = {}\n"
        genScript += "\n"
        genScript += 'simulationConfig["Problem"] = {}\n'
        genScript += f'simulationConfig["Problem"]["Type"] = "{simulationProblemType}"\n'
        genScript += f'simulationConfig["Problem"]["Verbose"] = {simParamsVerbose_palace}\n'
        genScript += f'simulationConfig["Problem"]["Output"] = "{simulationOutputDirectory}"\n'
        genScript += '\n'
        genScript += 'simulationConfig["Model"] = {}\n'
        genScript += f'simulationConfig["Model"]["Mesh"] = "{simulationOutputMeshFile}"\n'
        genScript += f'simulationConfig["Model"]["L0"] = {simParamsModelMeshBaseUnits_palace}\n'
        genScript += '\n'

        genScript += 'simulationConfig["Domains"] = {}\n'
        genScript += 'simulationConfig["Domains"]["Materials"] = []\n'
        genScript += 'simulationConfig["Domains"]["Materials"].extend(mesherObj.getAllMaterialObjectForPalace())\n'
        genScript += '\n'
        genScript += 'simulationConfig["Boundaries"] = {}\t#definition is here just to be clear that this is dictionary\n'
        genScript += 'simulationConfig["Boundaries"] = mesherObj.getAllBoundaryConditionsObjectForPalace()\n'

        #
        #   Simulation types using to specify input/output ports:
        #       - Eigenmode     - TODO: Need to be figured out!
        #       - Driven        - LumpedPort
        #       - Electrostatic - Terminal
        #       - Magnetostatic - SurfaceCurrent
        #       - ...
        #
        if simulationProblemType.lower() == "magnetostatic":
            genScript += 'simulationConfig["Boundaries"]["SurfaceCurrent"] = mesherObj.getAllSurfaceCurrentForPortObjectForPalace()\n'
        elif simulationProblemType.lower() == "electrostatic":
            genScript += 'simulationConfig["Boundaries"]["Terminal"] = []\n'
            genScript += 'simulationConfig["Boundaries"]["Terminal"].extend(mesherObj.getAllTerminalForPortObjectForPalace())\n'
        else:
            genScript += 'simulationConfig["Boundaries"]["LumpedPort"] = []\n'
            genScript += 'simulationConfig["Boundaries"]["LumpedPort"].extend(mesherObj.getAllLumpedPortObjectForPalace())\n'

        genScript += '\n'
        genScript += '#\n'
        genScript += '# Linear solver is used for all problem types, here is its specification\n'
        genScript += '#\n'
        genScript += 'simulationConfig["Solver"] = {}\n'
        genScript += 'simulationConfig["Solver"]["Linear"] = {}\n'
        genScript += f'simulationConfig["Solver"]["Linear"]["Type"] = "{linearSolverType}"\n'
        genScript += f'simulationConfig["Solver"]["Linear"]["KSPType"] = "{linearSolverKSPType}"\n'
        genScript += f'simulationConfig["Solver"]["Linear"]["Tol"] = {linearSolverTolerance}\n'
        genScript += f'simulationConfig["Solver"]["Linear"]["MaxIts"] = {linearSolverMaxIterationCount}\n'
        genScript += f'simulationConfig["Solver"]["Order"] = {solverOrder}\n'
        genScript += f'simulationConfig["Solver"]["Device"] = "{solverDevice}"\n'
        genScript += '\n'

        if simulationProblemType.lower() == "magnetostatic":
            genScript += 'simulationConfig["Solver"]["Magnetostatic"] = {}\n'
            genScript += 'simulationConfig["Solver"]["Magnetostatic"]["Save"] = 2\n'
            genScript += '\n'
        elif simulationProblemType.lower() == "electrostatic":
            #help: https://awslabs.github.io/palace/stable/guide/problem/
            #   - need to specify grounded terminal
            #
            genScript += 'simulationConfig["Solver"]["Electrostatic"] = {}\n'
            genScript += 'simulationConfig["Solver"]["Electrostatic"]["Save"] = 2\n'
            genScript += '\n'
        elif simulationProblemType.lower() == "driven":
            genScript += self.getExcitationScriptLines(definitionsOnly=False)
            genScript += '\n'

            if self.form.simParamsUseNf2ff_palace.isChecked():
                boundaryConditionName = self.form.portNf2ffPalaceObjectList.currentText()   #boundary name is like 'Absorbing - airbox'
                boundaryConditionName = boundaryConditionName.split("-")[1].strip()

                NSample = self.form.boundaryNf2ffPalaceNSample.value()
                theta = self.form.boundaryNf2ffPalaceTheta.value()
                phi = self.form.boundaryNf2ffPalacePhi.value()

                genScript += 'simulationConfig["Boundaries"]["Postprocessing"] = {}\n'
                genScript += f'simulationConfig["Boundaries"]["Postprocessing"]["FarField"] = {{"Attributes": [mesherObj.getGmshGroupId("{boundaryConditionName}_2D")], "NSample": {NSample}, "ThetaPhis": [[{theta}, {phi}]]}}\n'
                genScript += '\n'
        elif simulationProblemType.lower() == "transient":
            genScript += self.getExcitationScriptLines(definitionsOnly=False)

        else:
            genScript += f"#INFO: No additional settings generated for simulation type '{simulationProblemType}'\n"
            genScript += "\n"

        currDir, nameBase = self.getCurrDir()

        genScript += f'json.dump(simulationConfig, open("{nameBase}.json", "w"), indent=2)\n'
        genScript += '\n'
        genScript += f'with open("{nameBase}.json", "a") as outfile:\n'
        genScript += '\toutfile.write("\\n\\n")\n'
        genScript += '\toutfile.write("//internal mesher gmsh group table: (group name -> group id)\\n")\n'
        genScript += '\tfor k, v in mesherObj.getGmshGroupIdList().items():\n'
        genScript += '\t\toutfile.write(f"//{k}\\t-> {v}\\n")\n'
        genScript += '\n'

        ##################################################################################
        # Write _OpenEMS.py script file to current directory.
        ##################################################################################
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_palace.py"
        else:
            fileName = f"{currDir}/{nameBase}_palace.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()

        # Show message or update status bar to inform user that exporting has finished.

        self.guiHelpers.displayMessage('Simulation script written to: ' + fileName, forceModal=True)
        print('Simulation script written to: ' + fileName)

        return

    def getMaterialDefinitionsScriptLines(self, items, outputDir=None, generateObjects=True):
        genScript = ""

        genScript += "#######################################################################################################################################\n"
        genScript += "# MATERIALS AND GEOMETRY\n"
        genScript += "#######################################################################################################################################\n"

        # PEC is created by default due it's used when microstrip port is defined, so it's here to have it here.
        # Note that the user will need to create a metal named 'PEC' and populate it to avoid a warning
        # about "no primitives assigned to metal 'PEC'".

        if not items:
            return genScript

        materialCounter = -1    #increment of this variable is at beginning f for loop so start at 0
        simObjectCounter = 0

        # now export material children, if it's object export as STL, if it's curve export as curve
        if (generateObjects):
            for [item, currSetting] in items:

                #
                #   Materials are stored in variables in python script, so this is counter to create universal name ie. material_1, material_2, ...
                #
                materialCounter += 1

                print(currSetting)
                if (currSetting.getName() == 'Material Default'):
                    print("#Material Default")
                    print("---")
                    continue

                print("#")
                print("#MATERIAL")
                print("#name: " + currSetting.getName())
                print("#epsilon, mue, tand, sigma")
                print("#" + str(currSetting.constants['epsilon']) + ", " + str(currSetting.constants['mue']) + ", " + str(currSetting.constants['kappa']) + ", " + str(currSetting.constants['sigma']))

                genScript += f"## MATERIAL - {currSetting.getName()}\n"
                # materialPythonVariable = f"materialList['{currSetting.getName()}']"
                # genScript += materialPythonVariable + " = {}\n"

                if (currSetting.type == 'metal'):

                    #using predefined library with materials
                    genScript += f"mesherObj.addMaterial('{currSetting.getName()}', conductivity=1e30)\n"

                elif (currSetting.type == 'conducting sheet'):
                    genScript += f"mesherObj.addConductivity('{currSetting.getName()}', thickness={str(currSetting.constants['conductingSheetThicknessValue'])}*{str(currSetting.constants['conductingSheetThicknessUnits'])}, conductivity={str(currSetting.constants['conductingSheetConductivity'])}, permeability={str(currSetting.constants['conductingSheetPermeability'])})\n"

                elif (currSetting.type == 'userdefined'):

                    materialArgumentsList = {}
                    if str(currSetting.constants['epsilon']) != "0":
                        materialArgumentsList["er"] = currSetting.constants['epsilon']
                    if str(currSetting.constants['mue']) != "0":
                        materialArgumentsList["ur"] = currSetting.constants['mue']
                    if str(currSetting.constants['tand']) != "0":
                        materialArgumentsList["tand"] = currSetting.constants['tand']
                    if str(currSetting.constants['sigma']) != "0":
                        materialArgumentsList["conductivity"] = currSetting.constants['sigma']

                    materialIndex = 1
                    genScript += f"mesherObj.addMaterial('{currSetting.getName()}', "
                    for materialParamName, materialParamValue in materialArgumentsList.items():
                        genScript += f"{materialParamName}={str(materialParamValue)}{', ' if materialIndex < len(materialArgumentsList) else ''}"
                        materialIndex += 1
                    genScript += ")\n"

                # first print all current material children names
                for k in range(item.childCount()):
                    childName = item.child(k).text(0)
                    print("##Children:")
                    print("\t" + childName)

                # now export material children, if it's object export as STL, if it's curve export as curve
                for k in range(item.childCount()):
                    simObjectCounter += 1               #counter for objects
                    childName = item.child(k).text(0)

                    self.createdObjectNameList.append(childName)    #add this object into list of created objects which will be used to create named group in exported mesh

                    #
                    #	getting item priority
                    #
                    objModelPriorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    objModelPriority = self.getItemPriority(objModelPriorityItemName)

                    # getting reference to FreeCAD object
                    freeCadObj = [i for i in self.cadHelpers.getObjects() if (i.Label) == childName][0]

                    #
                    #   Going through each concrete material items and generate their .step files
                    #
                    currDir, baseName = self.getCurrDir()
                    stepModelFileName = childName + "_gen_model.step"

                    genScript += f"mesherObj.addStepfile('{childName}', os.path.join(currDir, 'stepfiles', '{stepModelFileName}'), priority={objModelPriority})\n"
                    if currSetting.type == 'conducting sheet':
                        genScript += f"mesherObj.addObjectToConductivity('{currSetting.getName()}', '{childName}')\n"
                    else:
                        genScript += f"mesherObj.addObjectToMaterial('{currSetting.getName()}', '{childName}')\n"

                    #output directory path construction, if there is no parameter for output dir then output is in current freecad file dir
                    if (not outputDir is None):
                        stepfileOutputDir = os.path.join(outputDir, 'stepfiles')
                        try:
                            os.makedirs(stepfileOutputDir)
                        except:
                            pass
                        exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)
                    else:
                        stepfileOutputDir = os.path.join(currDir, 'stepfiles')
                        try:
                            os.makedirs(stepfileOutputDir)
                        except:
                            pass
                        exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)

                    self.cadHelpers.exportSTEP([freeCadObj], exportFileName)
                    print("Material object exported as STEP into: " + stepModelFileName)

                genScript += "\n"   #newline after each COMPLETE material category code generated

            genScript += "\n"

        return genScript

    def getObjectUsedInSomeCategoryStepImportScriptLines(self, items, outputDir=None, generateObjects=True):
        genScript = ""

        genScript += "# Imported objects used as boundary conditions\n"
        genScript += "#\n"

        if items == None:
            genScript += "# NO OBJECTS USED, NOTHING TO IMPORT\n"
            return genScript

        # now export material children, if it's object export as STL, if it's curve export as curve
        for [item, currSetting] in items:

            #
            #   Create array of boundary condition boundaryList[<type ie. Absorbing, PEC, ...>] = list[str]
            #       - key must be proper palace boundary name as they are used in palace .json file under {...Boundary{ PEC: {Attributes: [...]...
            #
            print(f"Working on boundary condition named '{currSetting.getName()}' type: '{currSetting.getType()}'")

            # first print all current material children names
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                print("##Children:")
                print("\t" + childName)

            # now export material children, if it's object export as STL, if it's curve export as curve
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                self.createdObjectBoundaryNameList.append(childName)  # add this object into list of created objects which will be used to create named group in exported mesh

                #
                #	getting item priority
                #
                objModelPriorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                objModelPriority = self.getItemPriority(objModelPriorityItemName)

                # getting reference to FreeCAD object
                freeCadObj = [i for i in self.cadHelpers.getObjects() if (i.Label) == childName][0]

                #
                #   Going through each concrete material items and generate their .step files
                #
                currDir, baseName = self.getCurrDir()
                stepModelFileName = childName + "_gen_model.step"

                genScript += f"mesherObj.addStepfile('{childName}', os.path.join(currDir, 'stepfiles', '{stepModelFileName}'), priority={objModelPriority})\n"
                genScript += f"mesherObj.addObjectToBoundaryCondition('{currSetting.getType()}', '{childName}')\n"

                #output directory path construction, if there is no parameter for output dir then output is in current freecad file dir
                if (not outputDir is None):
                    stepfileOutputDir = os.path.join(outputDir, 'stepfiles')
                    try:
                        os.makedirs(stepfileOutputDir)
                    except:
                        pass
                    exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)
                else:
                    stepfileOutputDir = os.path.join(currDir, 'stepfiles')
                    try:
                        os.makedirs(stepfileOutputDir)
                    except:
                        pass
                    exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)



                self.cadHelpers.exportSTEP([freeCadObj], exportFileName)
                print("Boundary condition object exported as STEP into: " + stepModelFileName)

            genScript += "\n"   #newline after each COMPLETE material category code generated

        return genScript

    def getOrderedGridDefinitionsScriptLines(self, items):
        genScript = ""
        meshPrioritiesCount = self.form.meshPriorityTreeView.topLevelItemCount()

        if (not items) or (meshPrioritiesCount == 0):
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "##########################################################################################################\n"
        genScript += "# MESH SIZE DEFINITION\n"
        genScript += "##########################################################################################################\n"

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
            if (gridSettingsInst.getType() in ['FEM Max Size']):
                fcObject = fcObjects.get(FreeCADObjectName, None)
                if (not fcObject):
                    print("Failed to resolve '{}'.".format(FreeCADObjectName))
                    continue

                ### Produce script output.

                #
                #   This should make sure that just real objects have set mesh size
                #       21May2026 - seems not working properly with PCB imported from KiCAD as some real objects don't have Shape and
                #                   therefore no mesh size line is generated, so commented for now!
                #
                # if (not "Shape" in dir(fcObject)):
                #     print(f"\tFailed to find Shape in object {FreeCADObjectName}")
                #     continue

                if gridSettingsInst.femMesh['femUseMaxElementSize'] == True:
                    genScript += f"mesherObj.setSize(\"{FreeCADObjectName}\", {gridSettingsInst.femMesh['femMaxElementSize']}, distance={gridSettingsInst.femMesh['femMaxElementDistance']})\n"
                if gridSettingsInst.femMesh['femUseMaxBoundarySize'] == True:
                    genScript += f"mesherObj.setSizeBoundary(\"{FreeCADObjectName}\", {gridSettingsInst.femMesh['femMaxBoundarySize']})\n"
                if gridSettingsInst.femMesh['femUseMaxFaceSize'] == True:
                    genScript += f"mesherObj.setSizeOnFace(\"{FreeCADObjectName}\", {gridSettingsInst.femMesh['femMaxFaceSize']})\n"
                if gridSettingsInst.femMesh['femUseMaxDomainSize'] == True:
                    genScript += f"mesherObj.setSizeForVolume(\"{FreeCADObjectName}\", {gridSettingsInst.femMesh['femMaxDomainSize']})\n"

                #due backward compatibility older files doesn't have these params when loaded so try/except use to continue program
                try:
                    if gridSettingsInst.femMesh['femUseSurfaceMeshSize'] == True:
                        genScript += f"mesherObj.setSurfaceMeshSize(\"{FreeCADObjectName}\", {gridSettingsInst.femMesh['femSurfaceMeshSizeSizeMin']}, {gridSettingsInst.femMesh['femSurfaceMeshSizeSizeMax']}, {gridSettingsInst.femMesh['femSurfaceMeshSizeDistanceMin']}, {gridSettingsInst.femMesh['femSurfaceMeshSizeDistanceMax']})\n"
                except:
                    pass

                if gridSettingsInst.femMesh['femUseMaxUserDefined'] == True:
                    genScript += gridSettingsInst.femMesh['femMaxUserDefined']+"\n"

        genScript += "\n"
        genScript += "# Set background field automatically using internal field list created during mesh size definition\n"
        genScript += "mesherObj.setBackgroundMinFieldUsingAllDefinedFields()\n"
        genScript += "\n"
        genScript += "# Global limits - use if needed, SET OWN LIMITS!\n"
        genScript += "#gmsh.option.setNumber(\"Mesh.MeshSizeMin\", 0.1)  # Absolute minimum\n"
        genScript += "#gmsh.option.setNumber(\"Mesh.MeshSizeMax\", 10.0)  # Absolute maximum\n"
        genScript += "\n"
        genScript += "# Disable gmsh automatic sizing - enable when needed\n"
        genScript += 'gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)\n'
        genScript += '#gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)\n'
        genScript += '#gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)\n'
        genScript += "\n"

        return genScript

    def getPortDefinitionsScriptLines(self, items, outputDir=None):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # port index counter, they are generated into port{} cell variable for octave, cells index starts at 1
        genScriptPortCount = 1

        genScript += "#######################################################################################################################################\n"
        genScript += "# PORTS\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "port = []\n"
        genScript += "portNamesAndNumbersList = {}\n"
        genScript += "\n"

        for [item, currSetting] in items:

            print(f"#PORT - {currSetting.getName()} - {currSetting.getType()}")

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                self.createdObjectNameList.append(childName)  # add this object into list of created objects which will be used to create named group in exported mesh

                genScript += "## PORT - " + currSetting.getName() + " - " + childName + "\n"

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox
                    print('\tFreeCAD lumped port BoundBox: ' + str(bbCoords))

                    #
                    #	getting item priority
                    #
                    priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    priorityIndex = self.getItemPriority(priorityItemName)

                    #
                    # PORT openEMS GENERATION INTO VARIABLE
                    #
                    if (currSetting.getType() == 'lumped'):

                        if bbCoords.XLength == 0 or bbCoords.YLength == 0 or bbCoords.ZLength == 0:
                            #
                            #   Port is 2D, therefore it's generated as plate
                            #
                            genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords)

                            genScript += f"w = abs(portStart[0] - portStop[0])\n"
                            genScript += f"h = abs(portStart[1] - portStop[1])\n"
                            genScript += f"th = abs(portStart[2] - portStop[2])\n"

                            #
                            #   Create lumped port script line based on its orientation for now supports X,Y,Z axis
                            #
                            if bbCoords.XLength == 0:
                                genScript += f"tags = mesherObj.gmshCreatePlate(origin=portStart, u=[0,h,0], v=[0,0,th])\n"
                            elif bbCoords.YLength == 0:
                                genScript += f"tags = mesherObj.gmshCreatePlate(origin=portStart, u=[w,0,0], v=[0,0,th])\n"
                            elif bbCoords.ZLength == 0:
                                genScript += f"tags = mesherObj.gmshCreatePlate(origin=portStart, u=[w,0,0], v=[0,h,0])\n"

                            genScript += "# add created plate into gmsh model\n"
                            genScript += f"mesherObj.addGmshObjectUsingDimtags('{childName}', [(2, k) for k in tags], priority={priorityIndex}, type='surface')\n\n"
                        else:
                            #
                            #   Port object is not plane polygon therefore use STEP file to import it and later use its surface
                            #
                            currDir, baseName = self.getCurrDir()
                            stepModelFileName = childName + "_gen_model.step"
                            genScript += f"mesherObj.addStepfile('{childName}', os.path.join(currDir, 'stepfiles', '{stepModelFileName}'), priority={priorityIndex})\n"

                            # output directory path construction, if there is no parameter for output dir then output is in current freecad file dir
                            if (not outputDir is None):
                                stepfileOutputDir = os.path.join(outputDir, 'stepfiles')
                                try:
                                    os.makedirs(stepfileOutputDir)
                                except:
                                    pass
                                exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)
                            else:
                                stepfileOutputDir = os.path.join(currDir, 'stepfiles')
                                try:
                                    os.makedirs(stepfileOutputDir)
                                except:
                                    pass
                                exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)

                            self.cadHelpers.exportSTEP([obj], exportFileName)
                            print("Port object exported as STEP into: " + stepModelFileName)

                        #
                        #   Create port definition
                        #
                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount

                        genScript += f"mesherObj.addPort("
                        genScript += f"name='{internalPortName}', "
                        genScript += f"direction='{currSetting.direction}', "
                        genScript += f"R={str(currSetting.R)}*{str(currSetting.getRUnits())}, "
                        if currSetting.isActive:
                            genScript += f"excitation={str(currSetting.excitationAmplitude)}, "
                        genScript += f"type='lumped', "
                        genScript += f"index={genScriptPortCount}"
                        genScript += f")\n"

                        genScript += f"mesherObj.addObjectToPort('{internalPortName}', '{obj.Label}')\n"

                        genScript += f'portNamesAndNumbersList["{internalPortName}"] = {genScriptPortCount}\n'
                        genScriptPortCount += 1

                    #
                    #   ERROR - BELOW STILL NOT REWRITTEN INTO PYTHON!!!
                    #

                    else:
                        genScript += '# Unknown port type. Nothing was generated.\n'
                        genScript += 'raise BaseException("Unknown port type. Nothing was generated.")\n'

            genScript += "\n"

        return genScript

    def getLumpedPartDefinitionsScriptLines(self, items, outputDir):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "#######################################################################################################################################\n"
        genScript += "# LUMPED PART\n"
        genScript += "#   - for palace solver lumped part impedance is sheet impedance using units Ohm/square, Henry/square, Farad/square\n"
        genScript += "#   - it's unitless, relative to square, ie. R=Rs*L/W, if L=W then R=Rs \n"
        genScript += "#######################################################################################################################################\n"

        for [item, currentSetting] in items:
            genScript += "# LUMPED PARTS " + currentSetting.getName() + "\n"

            # traverse through all children item for this particular lumped part settings
            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                print("#LUMPED PART " + currentSetting.getType())

                lumpedPartParams = f"'{currentSetting.getName()}'"
                if ('r' in currentSetting.getType().lower()):
                    lumpedPartParams += f", Rs={currentSetting.getR()}"
                if ('l' in currentSetting.getType().lower()):
                    lumpedPartParams += f", Ls={currentSetting.getL()}"
                if ('c' in currentSetting.getType().lower()):
                    lumpedPartParams += f", Cs={currentSetting.getC()}"

                genScript += f"mesherObj.addLumpedPart({lumpedPartParams})\n"

                freecadObjects = [i for i in objs if (i.Label) == childName]
                for obj in freecadObjects:
                    # obj = FreeCAD Object class

                    #
                    #	getting item priority
                    #
                    priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    priorityIndex = self.getItemPriority(priorityItemName)

                    currDir, baseName = self.getCurrDir()
                    stepModelFileName = childName + "_gen_model.step"

                    #
                    #   Export STEP file for LumpedPart
                    #       - output directory path construction, if there is no parameter for output dir then output is in current freecad file dir
                    #
                    if (not outputDir is None):
                        stepfileOutputDir = os.path.join(outputDir, 'stepfiles')
                        try:
                            os.makedirs(stepfileOutputDir)
                        except:
                            pass
                        exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)
                    else:
                        stepfileOutputDir = os.path.join(currDir, 'stepfiles')
                        try:
                            os.makedirs(stepfileOutputDir)
                        except:
                            pass
                        exportFileName = os.path.join(stepfileOutputDir, stepModelFileName)

                    self.cadHelpers.exportSTEP([obj], exportFileName)
                    print("LumpedPart object exported as STEP into: " + stepModelFileName)

                    genScript += f"mesherObj.addStepfile('{childName}', os.path.join(currDir, 'stepfiles', '{stepModelFileName}'), priority={priorityIndex})\n"
                    genScript += f"mesherObj.addObjectToLumpedPart('{currentSetting.getName()}', '{childName}')\n"

            genScript += "\n"

        return genScript

    def getExcitationScriptLines(self, definitionsOnly=False):
        genScript = ""

        excitationCategory = self.form.objectAssignmentRightTreeWidget.findItems("Excitation", QtCore.Qt.MatchFixedString)
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

                # genScript += "#######################################################################################################################################\n"
                # genScript += "# EXCITATION " + currSetting.getName() + "\n"
                # genScript += "#######################################################################################################################################\n"

                if (currSetting.getType() == 'sweep'):
                    genScript += 'simulationConfig["Solver"]["Driven"] = {}\n'
                    genScript += f'simulationConfig["Solver"]["Driven"]["MinFreq"] = {str(currSetting.sweep["fmin"])} * {str(currSetting.getUnitsAsNumber(currSetting.units))} / 1e9\n'
                    genScript += f'simulationConfig["Solver"]["Driven"]["MaxFreq"] = {str(currSetting.sweep["fmax"])} * {str(currSetting.getUnitsAsNumber(currSetting.units))} / 1e9\n'

                    if currSetting.sweep["fmax"] - currSetting.sweep["fmin"] > 0:
                        genScript += f'simulationConfig["Solver"]["Driven"]["FreqStep"] = (simulationConfig["Solver"]["Driven"]["MaxFreq"] - simulationConfig["Solver"]["Driven"]["MinFreq"]) / {str(currSetting.sweep["npoints"])}\n'
                    else:
                        genScript += f'simulationConfig["Solver"]["Driven"]["FreqStep"] = 0.1\n'

                    genScript += f'simulationConfig["Solver"]["Driven"]["SaveStep"] = {self.form.simParamsSaveStep_palace.value()}\n'
                    genScript += f'simulationConfig["Solver"]["Driven"]["AdaptiveTol"] = 1e-3\n'

                    if self.form.simParamsUseNf2ff_palace.isChecked():
                        genScript += f'simulationConfig["Solver"]["Driven"]["Samples"] = []\n'
                        genScript += f'simulationConfig["Solver"]["Driven"]["Samples"].append({{"Type": "Point", "Freq": [{self.form.boundaryNf2ffPalaceFreq.value()/1e3}], "SaveStep": 1}})\n'

                elif (currSetting.getType() == 'fem_gaussian'):
                    genScript += "import math\n"
                    genScript += "\n"
                    genScript += f'f_center = {str(currSetting.femGaussian["f0"])} * {str(currSetting.getUnitsAsNumber(currSetting.units))} / 1e9\n'
                    genScript += f'f_min = {str(currSetting.femGaussian["f0"] - currSetting.femGaussian["fc"])} * {str(currSetting.getUnitsAsNumber(currSetting.units))} / 1e9\n'
                    genScript += f'f_max = {str(currSetting.femGaussian["f0"] + currSetting.femGaussian["fc"])} * {str(currSetting.getUnitsAsNumber(currSetting.units))} / 1e9\n'
                    genScript += f'BW = f_max - f_min\n'
                    genScript += f'\n'
                    genScript += f'# Gaussian width in time domain\n'
                    genScript += f'# width ≈ 1 / (π * f_max) gives -20dB at f_max\n'
                    genScript += f'width_ns = 1.0 / (math.pi * BW) * 1e9\n'
                    genScript += f'\n'
                    genScript += f'# Simulation must run long enough for the pulse to decay\n'
                    genScript += f'# and for filter ringdown - at least 10 periods at lowest frequency\n'
                    genScript += f'T_min = 1.0 / f_min * 1e9\n'
                    genScript += f'MaxTime = 10 * T_min\n'
                    genScript += f'\n'
                    genScript += f'# Time step must satisfy Nyquist at highest frequency\n'
                    genScript += f'# dt < 1 / (2 * f_max)\n'
                    genScript += f'TimeStep = 1.0 / (2 * f_max) * 1e9 / {str(currSetting.femGaussian["timeOversampling"])}  # time oversampling\n'
                    genScript += f'\n'
                    genScript += f'simulationConfig["Solver"]["Transient"] = {{}}\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["Type"] = "GeneralizedAlpha"\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["Excitation"] = "ModulatedGaussian"  # Gaussian centered at f_center, no DC\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["ExcitationFreq"] = f_center / 1e9\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["ExcitationWidth"] = width_ns\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["MaxTime"] = MaxTime\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["TimeStep"] = TimeStep\n'
                    genScript += f'simulationConfig["Solver"]["Transient"]["SaveStep"] = {self.form.simParamsSaveStep_palace.value()}\n'

                else:
                    genScript += f"# ERROR: Excitation type \"{currSetting.getType()}\" not implemented in script generator!\n"

                genScript += "\n"
            else:
                self.guiHelpers.displayMessage("<font color='#FF0000'><b>Missing excitation, please define one.</b></font>")
                pass
            pass
        return genScript

    def drawS11ButtonClicked(self, outputDir=None, portName=""):
        genScript = ""

        itemsByClassName = self.getItemsByClassName()
        items = itemsByClassName.get("PortSettingsItem", None)

        genScriptPortCount = 1
        portNamesAndNumbersList = {}
        for [item, currSetting] in items:
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                portName = f"{currSetting.name} - {childName}"

                # PORT openEMS GENERATION INTO VARIABLE
                if (currSetting.getType() == 'lumped'):
                    portNamesAndNumbersList[portName] = genScriptPortCount
                    genScriptPortCount += 1

        sourcePortName = self.form.drawS11Port.currentText()
        sourcePortNumber = portNamesAndNumbersList[sourcePortName]

        genScript += f"## Palace simulation - S{sourcePortNumber}{sourcePortNumber}\n"
        genScript += "#\n"
        genScript += "#\n"
        genScript += "import matplotlib.pyplot as plt\n"
        genScript += "import pandas as pd\n"
        genScript += "\n"

        #
        #   Get port names and their numbers from GUI
        #
        genScript += "###############################################################################\n"
        genScript += "# PORT NAME AND THEIR NUMBERS LIST\n"
        genScript += "###############################################################################\n"
        genScript += "portNamesAndNumbersList = {}\n"
        for portName, portNumber in portNamesAndNumbersList.items():
            genScript += f'portNamesAndNumbersList["{portName}"] = {portNumber}\n'
        genScript += "\n"

        genScript += "###############################################################################\n"
        genScript += "# PLOT S DATA\n"
        genScript += "###############################################################################\n"
        genScript += "\n"
        genScript += "# Load the file without header (columns will be numbered 0, 1, 2...)\n"
        genScript += f'df = pd.read_csv("{self.form.simParamsOutputDirectory_palace.text()}/port-S.csv", comment="#", skiprows=1, header=None)\n'
        genScript += "\n"
        genScript += "# Plot: column 0 = Frequency, column 1 = S11\n"
        genScript += 'plt.plot(df.iloc[:, 0], df.iloc[:, 1], marker="o", label="|S11| (dB)")\n'
        genScript += "\n"
        genScript += 'plt.xlabel("Frequency (GHz)")\n'
        genScript += 'plt.ylabel("S11 (dB)")\n'
        genScript += 'plt.title("S11 vs Frequency")\n'
        genScript += 'plt.grid(True)\n'
        genScript += 'plt.legend()\n'
        genScript += 'plt.tight_layout()\n'
        genScript += 'plt.show()\n'
        genScript += '\n'

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_S{sourcePortNumber}{sourcePortNumber}.py"
        else:
            fileName = f"{currDir}/{nameBase}_draw_S{sourcePortNumber}{sourcePortNumber}.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written into: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written into: ' + fileName, forceModal=False)

    def drawS21ButtonClicked(self, outputDir=None, sourcePortName="", targetPortName=""):
        genScript = ""

        itemsByClassName = self.getItemsByClassName()
        items = itemsByClassName.get("PortSettingsItem", None)

        genScriptPortCount = 1
        portNamesAndNumbersList = {}
        for [item, currSetting] in items:
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                portName = f"{currSetting.name} - {childName}"

                # PORT openEMS GENERATION INTO VARIABLE
                if (currSetting.getType() == 'lumped'):
                    portNamesAndNumbersList[portName] = genScriptPortCount
                    genScriptPortCount += 1

        sourcePortName = self.form.drawS11Port.currentText()
        sourcePortNumber = portNamesAndNumbersList[sourcePortName]
        targetPortName = self.form.drawS21Target.currentText()
        targetPortNumber = portNamesAndNumbersList[targetPortName]

        graphSParamName = f"S{targetPortNumber}{sourcePortNumber}"

        #
        # This is for S21 for Driven problem when S-params are stored in file port-S.csv
        #
        if self.form.simParamsSimulationTypeList_palace.currentText().lower() == "driven":
            genScript += f"## Palace simulation - {graphSParamName}\n"
            genScript += f"#\ttransfer from '{sourcePortName}' -> '{targetPortName}'\n"
            genScript += "#\n"
            genScript += "#\n"
            genScript += "import matplotlib.pyplot as plt\n"
            genScript += "import pandas as pd\n"
            genScript += "\n"

            #
            #   Get port names and their numbers from GUI
            #
            genScript += "###############################################################################\n"
            genScript += "# PORT NAME AND THEIR NUMBERS LIST\n"
            genScript += "###############################################################################\n"
            genScript += "portNamesAndNumbersList = {}\n"
            for portName, portNumber in portNamesAndNumbersList.items():
                genScript += f'portNamesAndNumbersList["{portName}"] = {portNumber}\n'
            genScript += "\n"

            genScript += "###############################################################################\n"
            genScript += "# PLOT S DATA\n"
            genScript += "###############################################################################\n"
            genScript += f"sourcePortName = '{sourcePortName}'\n"
            genScript += f"targetPortName = '{targetPortName}'\n"
            genScript += "sourcePortNumber = portNamesAndNumbersList[sourcePortName]\n"
            genScript += "targetPortNumber = portNamesAndNumbersList[targetPortName]\n"
            genScript += "\n"
            genScript += "\n"
            genScript += "# Load the file without header (columns will be numbered 0, 1, 2...)\n"
            genScript += f'df = pd.read_csv("{self.form.simParamsOutputDirectory_palace.text()}/port-S.csv", comment="#", skiprows=1, header=None)\n'
            genScript += "\n"
            genScript += f"# Plot: column 0 = Frequency, column 1 = {graphSParamName}\n"
            genScript += f'plt.plot(df.iloc[:, 0], df.iloc[:, {(targetPortNumber-1)*2+1}], marker="o", label="|{graphSParamName}| (dB)")\n'
            genScript += "\n"
            genScript += 'plt.xlabel("Frequency (GHz)")\n'
            genScript += f'plt.ylabel("{graphSParamName} (dB)")\n'
            genScript += f'plt.title("{graphSParamName} vs Frequency")\n'
            genScript += 'plt.grid(True)\n'
            genScript += 'plt.legend()\n'
            genScript += 'plt.tight_layout()\n'
            genScript += 'plt.show()\n'
            genScript += '\n'

        #
        # This is for S21 for Driven problem when there is file port-V.csv and S-params must be calculated from voltage values on ports
        #
        if self.form.simParamsSimulationTypeList_palace.currentText().lower() == "transient":
            genScript += "import numpy as np\n"
            genScript += "import math\n"
            genScript += "\n"

            #
            #   Get port names and their numbers from GUI
            #
            genScript += "###############################################################################\n"
            genScript += "# PORT NAME AND THEIR NUMBERS LIST\n"
            genScript += "###############################################################################\n"
            genScript += "portNamesAndNumbersList = {}\n"
            for portName, portNumber in portNamesAndNumbersList.items():
                genScript += f'portNamesAndNumbersList["{portName}"] = {portNumber}\n'
            genScript += "\n"

            genScript += f"sourcePortName = '{sourcePortName}'\n"
            genScript += f"targetPortName = '{targetPortName}'\n"
            genScript += "sourcePortNumber = portNamesAndNumbersList[sourcePortName]\n"
            genScript += "targetPortNumber = portNamesAndNumbersList[targetPortName]\n"
            genScript += "\n"

            genScript += "# After simulation, Palace outputs port-V.csv with time, V(t), I(t)\n"
            genScript += "#\n"
            genScript += "data = np.loadtxt('sim_result_transient/port-V.csv', delimiter=',', skiprows=1)\n"
            genScript += "t = data[:, 0]  # time in ns\n"
            genScript += f"V_in = np.sqrt(data[:, sourcePortNumber*2]**2 + data[:, sourcePortNumber*2+1]**2)\n"
            genScript += f"V_out = np.sqrt(data[:, targetPortNumber*2]**2 + data[:, targetPortNumber*2+1]**2)\n"
            genScript += "\n"
            genScript += "dt = t[1] - t[0]\n"
            genScript += "freq = np.fft.rfftfreq(len(t), d=dt * 1e-9)  # Hz\n"
            genScript += "\n"
            genScript += "V_in_f = np.fft.rfft(V_in)\n"
            genScript += "V_out_f = np.fft.rfft(V_out)\n"
            genScript += "\n"
            genScript += "S21 = 20 * np.log10(np.abs(V_out_f / V_in_f))\n"
            genScript += "\n"
            genScript += "import matplotlib.pyplot as plt\n"
            genScript += "mask = (freq >= 20e6) & (freq <= 40e6)\n"
            genScript += "plt.plot(freq[mask] / 1e6, S21[mask])\n"
            genScript += "plt.xlabel('Frequency (MHz)')\n"
            genScript += f"plt.ylabel('{graphSParamName} (dB)')\n"
            genScript += "plt.grid(True)\n"
            genScript += "plt.show()\n"
            genScript += "\n"
            genScript += "plt.subplot(1, 2, 1)\n"
            genScript += "plt.plot(V_in)\n"
            genScript += "plt.subplot(1, 2, 2)\n"
            genScript += "plt.plot(V_out)\n"
            genScript += "plt.show()\n"
            genScript += "\n"

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_{graphSParamName}.py"
        else:
            fileName = f"{currDir}/{nameBase}_draw_{graphSParamName}.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written into: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written into: ' + fileName, forceModal=False)

    #
    #	Write NF2FF Button clicked, generate script to display far field pattern
    #
    def writeNf2ffButtonClicked(self, outputDir=None):
        currDir, nameBase = self.getCurrDir()

        genScript = ""
        genScript += "# Plot far field for structure.\n"
        genScript += "#\n"
        genScript += "import os\n"
        genScript += "from basicpalacesolverhelperpackage import PlotDiagramUtils\n"
        genScript += "\n"

        genScript += "currDir = os.getcwd()\n"
        genScript += "print(currDir)\n"
        genScript += "\n"

        genScript += "#######################################################################################################################################\n"
        genScript += "# Farfield plot and 3D gain generated\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "plotter = PlotDiagramUtils()\n"
        genScript += f'plotter.readFromFileComputeDirectivityRadiationDiagram("{self.form.simParamsOutputDirectory_palace.text()}/farfield-rE.csv", outputfile="{nameBase}_farfield.vtk")\n'
        genScript += "\n"

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_NF2FF.py"
        else:
            fileName = f"{currDir}/{nameBase}_draw_NF2FF.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Script to display far field written into: ' + fileName)
        self.guiHelpers.displayMessage('Script to display far field written into: ' + fileName, forceModal=False)

'''
Notes TODO 20Apr2026:
    + DONE -> FreeCAD addon not saving and loading palace simulation params tab - need to be added
    + creating mesh named group based on what is used, cannot use same elements in multiple groups this cause palace solver error that element in multiple attributes
        + this makes question how to properly create named group for materials??? probably just 3D mesh for them since if material is defined
          on 2D surface it is specified as boundary
        + for boundary generate just 2D surface mesh
        + whole strategy of import STEP files and define mesh on them should be re-think and not to mesh everything just needed objects
    + for Magnetostatic solver SuperLU crash with some error of matrix with zeros or whatever but AMS solver run OK
    + port priority is wrong, take it from FreeCAD widget!
    - forbit multiple assignment same object to multiple material
    - forbit multiple assignment same object to multiple boundaries
    - grid mesh size not working properly
    - grid custom mesh in generated code
    - add custom code snippet into lumped part, this will enable to add conductivity boundary into result code since lumped part is translated as surface
        - or implement Material "conducting sheet" to generate palace simulationConfig["Boundaries"]["Conductivity"] = [{"Attributes": [...], "Conductivity": ..., "Permitivity": ..., "Thickness": ...}]    
    - ...
'''



