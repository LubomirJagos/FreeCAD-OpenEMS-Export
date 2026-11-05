from .SettingsItem import SettingsItem
import json

# Smulation settings
class SimulationSettingsItem(SettingsItem):
	def __init__(self, name = "DefaultSimulationName", params='{"max_timestamps": 1e6, "min_decrement": 0, "BCxmin": "PEC", "BCxmax": "PEC", "BCymin": "PEC", "BCymax": "PEC", "BCzmin": "PEC", "BCzmax": "PEC", "PMLxmincells": 1, "PMLxmaxcells": 1, "PMLymincells": 1, "PMLymaxcells": 1, "PMLzmincells": 1, "PMLzmaxcells": 1, "OverSampling": 1}'):
		self.name = name
		self.params = {}
		self.params = json.loads(params)
		return

class SimulationPalaceSettingsItem(SimulationSettingsItem):
	def __init__(self, name = "DefaultSimulationName", palaceParams='{"problemType": "Driven", "problemVerbose": 3, "problemOutput": "sim_result", "modelMeshName": "mesh/simulation_model.msh", "modelMeshBaseUnits": "mm", "linearSolverType": "SuperLU", "linearSolverKSPType": "GMRES", "linearSolverTolerance": 0.001, "linearSolverMaxIterationCount": 200, "solverOrder": 2, "solverDevice": "CPU"}'):
		self.name = name
		self.palaceParams = {}
		self.palaceParams = json.loads(palaceParams)
		return
