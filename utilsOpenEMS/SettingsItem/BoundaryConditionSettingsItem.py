from .SettingsItem import SettingsItem

class BoundaryConditionSettingsItem(SettingsItem):
    def __init__(
        self,
        name="",
        type="",
        customType="",
        surfaceImpedance={"material":None, "conductance":0.0, "roughness":0.0, "roughnessUnits":"nm", "thickness":0.0, "thicknessUnits":"um"},
        thinConductor={"material":None, "conductance":0.0, "roughness":0.0, "roughnessUnits":"nm", "thickness":0.0, "thicknessUnits":"um"},
        openemsAbsorber={"AbsorbingBoundaryType":"MUR_1ST", "NormalSignPositive":True, "PhaseVelocity_material_er":1.0, "PhaseVelocity_material_muer":1.0},
        userDefined=""
    ):
        self.name = name
        self.type = type
        self.customType = customType
        self.surfaceImpedance = surfaceImpedance
        self.thinConductor = thinConductor
        self.openemsAbsorber = openemsAbsorber
        self.userDefined = userDefined

        return

    def getName(self):
        return self.name

    def getType(self):
        if self.type == "custom":
            return self.customType
        else:
            return self.type
