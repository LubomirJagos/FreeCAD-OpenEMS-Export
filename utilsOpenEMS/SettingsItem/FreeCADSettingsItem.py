from .SettingsItem import SettingsItem

# FreeCAD part class
#
class FreeCADSettingsItem(SettingsItem):
	def __init__(self, name = "", type = "FreeCADSettingItem", freeCadId = ""):
		self.name = name
		self.type = type
		self.freeCadId = freeCadId
		return
	def setFreeCadId(self, idStr):
		self.freeCadId = idStr
		return

	def getFreeCadId(self):
		return self.freeCadId

