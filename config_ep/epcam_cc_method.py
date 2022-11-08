import json
import os
import shutil

from config import RunConfig
from epcam_api import Configuration, Input, GUI,BASE
from epcam_api.Edition import Job,Matrix

from config_ep.epcam import epcam


Configuration.init(RunConfig.ep_cam_path)
Configuration.set_sys_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\sysattr'))
Configuration.set_user_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\userattr'))

def f1():
    pass
    Input.open_job("eni40021", r"C:\job\test\odb")
    GUI.show_layer("eni40021", "orig", "top")

class MyInput(object):

    @staticmethod
    def is_chinese(string):
        """判断是否有中文
        :param     string(str):所有字符串
        :returns   :False
        :raises    error:
        """
        for ch in string:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    def input_gerber(self,job):
        Job.create_job(job)
        Matrix.create_step(job, 'orig')
        result_file_identify = Input.file_identify(r"C:\Users\cheng.chen\Desktop\760\LAYER2.art")
        # print(result_file_identify)
        Input.file_translate(path = r"C:\Users\cheng.chen\Desktop\760\LAYER2.art",
                             job = job, step = 'orig', layer = 'layer',param = result_file_identify)

        BASE.save_job_as(job,r'C:\job\test\odb')

        GUI.show_layer(job, "orig", "layer")


    def file_identify(self):
        pass

class MyJob(object):
    def my_save_job_odb(self,job):
        # 比图前需要保存料号
        data = {
            'func': 'JOB_SAVE',
            'paras': [{'job': job}]
        }
        epcam.process(json.dumps(data))




if __name__ == "__main__":
    pass
    job_save_path_parent = r'C:\job\test\odb'
    job = r'test'
    cc = MyInput()
    cc.input_gerber(job)

