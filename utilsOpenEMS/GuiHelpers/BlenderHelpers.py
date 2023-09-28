import os
from utilsOpenEMS.GuiHelpers.CadInterface import CadInterface

import bpy

import bmesh
import numpy as np
from mathutils import Vector

class BlenderToCadObject:
    def __init__(self, blenderObj):
        super(BlenderHelpers, self).__init__(APP_DIR)

        self.Label = blenderObj.name
        try:
            self.Name = blenderObj['freeCadId']
        except:
            self.Name = blenderObj.name
        self.Shape = BlenderToCadShapeObject(blenderObj)

class BlenderToCadShapeObject:
    def __init__(self, blenderObj):
        self.BoundBox = BlenderToCadBoundBoxObject(blenderObj)

class BlenderToCadBoundBoxObject:
    def __init__(self, blenderObj):
        bbCoordMin, bbCoordMax = self.getBoundaryBox(blenderObj)

        self.XMin = bbCoordMin[0]
        self.YMin = bbCoordMin[1]
        self.ZMin = bbCoordMin[2]
        self.XMax = bbCoordMax[0]
        self.YMax = bbCoordMax[1]
        self.ZMax = bbCoordMax[2]

    def getBoundaryBox(self, obj):
        """
        Returns boundary box for object. There is main problem that object has parameters like translation, rotation, it's needed to recalculate it for real world, ...
        There was found on internet some function from forum and cleaned and put here, so maybe it's not right one.

        Till now this was running at first glance in result file.

        source: https://blender.stackexchange.com/questions/274134/how-to-calculate-bounds-of-all-selected-objects-but-follow-the-active-objects-r?rq=1
        :param obj: Blender Mesh object
        :return: two tuples bbCoordMin, bbCoordMax - (xmin,ymin,zmin),(xmax,ymax,zmax)
        """
        q_invert = obj.rotation_quaternion.inverted()
        verts = []

        obj_mat = obj.matrix_world
        if obj.type != 'MESH':
            return (None,None,None), (None,None,None)
        verts += [q_invert @ (obj_mat @ v.co) for v in obj.data.vertices]

        if not verts: return None

        v_z = [co.z for co in verts]
        v_y = [co.y for co in verts]
        v_x = [co.x for co in verts]

        z_max = max(v_z)
        z_min = min(v_z)
        y_max = max(v_y)
        y_min = min(v_y)
        x_max = max(v_x)
        x_min = min(v_x)

        box_verts = (
            (x_min, y_min, z_min),
            (x_min, y_max, z_min),
            (x_max, y_max, z_min),
            (x_max, y_min, z_min),
            (x_max, y_min, z_max),
            (x_min, y_min, z_max),
            (x_min, y_max, z_max),
            (x_max, y_max, z_max),
        )

        return box_verts[0], box_verts[7]


class BlenderHelpers(CadInterface):
    #
    #   __init__() must be REPAIRED!!!
    #
    def __init__(self, APP_DIR=""):
        #
        #   ERROR this is not running, need to figure out but with this in Blender UI is not opened!!!
        #       NEED TO BE REPAIRED!!!
        #       HOTFIX for now Sep2023 to comment it and need to test GUI in Blender if it's running
        #
        #super(BlenderHelpers, self).__init__(APP_DIR)
        return

    #########################################################################################################################
    #   BLENDER SPECIFIC FUNCTIONS
    #########################################################################################################################

    def getObjects(self):
        #print(f"{__file__} > getObjects()")

        #
        #   Simple class to have same members for rest of GUI application, it expecting items to have obj.Name, obj.Label items
        #
        objList = []
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                objList.append(BlenderToCadObject(obj))

        return objList

    def getObjectsByLabel(self, objLabel):
        #print(f"{__file__} > getObjectsByLabel()")

        objList = []
        try:
            obj = bpy.context.scene.objects[objLabel]
            obj = BlenderToCadObject(obj)
            objList.append(obj)
        except:
            pass
        return objList

    def getObjectById(self, objId):
        #print(f"{__file__} > getObjectById()")

        try:
            obj = bpy.context.scene.objects[objId]
            return BlenderToCadObject(obj)
        except:
            for obj in bpy.context.scene.objects:
                if 'freeCadId' in obj.keys() and obj['freeCadId'] == objId:
                    return BlenderToCadObject(obj)
            return None

    def exportSTL(self, partToExport, exportFileName):
        context = bpy.context
        scene = context.scene
        viewlayer = context.view_layer

        obs = [o for o in scene.objects if o.type == 'MESH' and o.name == partToExport[0].Label]
        bpy.ops.object.select_all(action='DESELECT')

        for ob in obs:
            viewlayer.objects.active = ob
            ob.select_set(True)

            #
            #   HERE MUST BE TEMPORARY OBJECT OVERRIDE WHEN RUNNING THIS IN SCRIPT OTHERWISE IT'S NOT GENERATING STL FILES
            #       when was developing addon using main thread of blender it was running normal, but when running in separate thread
            #       context override is needed
            #       https://docs.blender.org/api/current/bpy.ops.html
            #
            #       export STL function: https://docs.blender.org/api/current/bpy.ops.export_mesh.html
            #           there is probably problem with units, Blender by default wants to set cm and we want mm
            #
            override = bpy.context.copy()
            override["selected_objects"] = [ob]
            with bpy.context.temp_override(**override):
                bpy.ops.export_mesh.stl(
                    filepath=str(exportFileName),
                    use_selection=True,
                    ascii=True,
                    use_mesh_modifiers=True
                )

            ob.select_set(False)

    def getCurrDocumentFileName(self):
        currentFile = bpy.data.filepath
        #print(f"{__file__} > getCurrDocumentFileName() > {currentFile}")
        return currentFile

    def removeObject(self, objName):
        """
        Remove object from Blender, used mainly to remove generated gridlines, since gridlines generate to Blender is not used till now this method should never be used.
        :param objName:
        :return:
        """
        for o in bpy.context.scene.objects:
            if o.name == objName:
                o.select_set(True)

        # Call the operator only once
        bpy.ops.object.delete()