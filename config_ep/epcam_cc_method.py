import os
from config import RunConfig
from epcam_api import Configuration, Input, GUI

Configuration.init(RunConfig.ep_cam_path)
Configuration.set_sys_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\sysattr'))
Configuration.set_user_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\userattr'))

def f1():
    pass
    Input.open_job("eni40021", r"C:\job\test\odb")
    GUI.show_layer("eni40021", "orig", "top")


if __name__ == "__main__":
    pass
    f1()
