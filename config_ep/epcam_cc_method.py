from epcam_api import Configuration, Input, GUI

Configuration.init(r'C:\cc\ep_local\product\EP-CAM\version\20221031\EP-CAM_beta_2.29.055_s19_jiami\Release')
Configuration.set_sys_attr_path(r'C:\cc\ep_local\product\EP-CAM\version\20221031\EP-CAM_beta_2.29.055_s19_jiami\Release\config\attr_def\sysattr')
Configuration.set_user_attr_path(r'C:\cc\ep_local\product\EP-CAM\version\20221031\EP-CAM_beta_2.29.055_s19_jiami\Release\config\attr_def\userattr')


def f1():
    pass
    Input.open_job("eni40021", r"C:\job\test\odb")
    GUI.show_layer("eni40021", "orig", "top")


if __name__ == "__main__":
    pass
    f1()
