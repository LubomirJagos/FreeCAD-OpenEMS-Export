from .SettingsItem import SettingsItem
import json

# Smulation settings
class SimulationSettingsItem(SettingsItem):
	def __init__(self, name = "DefaultSimlationName", params='{"max_timestamps": 1e6, "min_decrement": 0, "BCxmin": "PEC", "BCxmax": "PEC", "BCymin": "PEC", "BCymax": "PEC", "BCzmin": "PEC", "BCzmax": "PEC", "PMLxmincells": 1, "PMLxmaxcells": 1, "PMLymincells": 1, "PMLymaxcells": 1, "PMLzmincells": 1, "PMLzmaxcells": 1}'):
		self.name = name
		self.params = {}
		self.params = json.loads(params)
		return
