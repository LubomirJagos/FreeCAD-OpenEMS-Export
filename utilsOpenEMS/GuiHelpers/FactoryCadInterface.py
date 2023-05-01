from utilsOpenEMS.GuiHelpers.CadInterface import CadInterface

class FactoryCadInterface:

    @staticmethod
    def createHelper(APP_DIR = ""):
        interfaceInstance = CadInterface()
        if interfaceInstance.type == "FreeCAD":
            from  utilsOpenEMS.GuiHelpers.FreeCADHelpers import FreeCADHelpers
            return FreeCADHelpers(APP_DIR)
        elif interfaceInstance.type == "Blender":
            from utilsOpenEMS.GuiHelpers.BlenderHelpers import BlenderHelpers
            return BlenderHelpers(APP_DIR)
        else:
            return CadInterface(APP_DIR)
            #raise Exception("Cannot recognize CAD interface nor FreeCAD or Blender.")