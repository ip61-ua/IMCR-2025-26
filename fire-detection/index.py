from roboflow import Roboflow

rf = Roboflow(api_key="<SECRET>")
project = rf.workspace("firesmokehuman").project("fire-and-smoke-industrial")
project.version(10).model.download()
