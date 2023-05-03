#
#   THIS INIT FILE IS WRITTEN FOR BLENDER, THANKS TO THIS IT CAN BE ADDED AS BLENDER ADDON
#

import bpy
from PySide2 import QtGui, QtCore, QtWidgets
from .ExportOpenEMSDialog import *

bl_info = {
    "name": "OpenEMS Simulation",
    "author": "Lubomir Jagos",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Toolbar",
    "warning": "Experimental",
    "category": "Import-Export",
    "description": "GUI addon to specify OpenEMS simulation and generate simulation script.",
}

class PYSIDE_PT_tools_my_panel(bpy.types.Panel):
    bl_label = "Export to OpenEMS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        layout.operator('pyside.display_window')


class PYSIDE_OT_display_window(bpy.types.Operator):
    bl_idname = 'pyside.display_window'
    bl_label = "Show Export Dialog"
    bl_options = {'REGISTER'}

    def execute(self, context):
        self.app = QtWidgets.QApplication.instance()
        if not self.app:
            self.app = QtWidgets.QApplication(['blender'])

        self.event_loop = QtCore.QEventLoop()
        self.widget = ExportOpenEMSDialog()
        self.widget.show()

        return {'FINISHED'}

CLASSES = [PYSIDE_OT_display_window, PYSIDE_PT_tools_my_panel]

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
