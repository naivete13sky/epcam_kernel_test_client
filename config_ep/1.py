from epcam_api import Configuration, Input, GUI


Configuration.init(r'C:\cc\ep_local\product\EP-CAM\version\20221031\EP-CAM_beta_2.29.055_s19_jiami\Release')
Input.open_job("eni40021", r"C:\job\test\odb")
GUI.show_layer("eni40021", "orig", "top")
