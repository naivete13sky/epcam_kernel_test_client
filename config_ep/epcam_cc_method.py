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

    def input_gerber_folder(self,folder_path,job,step,save_path):
        #创建一个空料号
        new_job_path = os.path.join(save_path, job)  # job若存在则删除
        if os.path.exists(new_job_path):
            shutil.rmtree(new_job_path)
        Job.create_job(job)
        #创建一个空step
        Matrix.create_step(job, step)
        #开始识别文件夹中各个文件的类型，此方只识别单层文件夹中的内容
        file_list = [x for x in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path,x))]
        print('file_list:',file_list)
        for each_file in file_list:
            result_each_file_identify = Input.file_identify(os.path.join(folder_path,each_file))
            print(result_each_file_identify)
            Input.file_translate(path=os.path.join(folder_path,each_file),job=job, step='orig', layer=each_file, param=result_each_file_identify)

        BASE.save_job_as(job,r'C:\job\test\odb')

        GUI.show_layer(job, "orig", "layer")

    def file_identify(self):
        pass

    def input_gerber_one_file(self,job):
        Job.create_job(job)
        Matrix.create_step(job, 'orig')
        result_file_identify = Input.file_identify(r"C:\Users\cheng.chen\Desktop\760\LAYER2.art")
        # print(result_file_identify)
        Input.file_translate(path = r"C:\Users\cheng.chen\Desktop\760\LAYER2.art",
                             job = job, step = 'orig', layer = 'layer',param = result_file_identify)

        BASE.save_job_as(job,r'C:\job\test\odb')

        GUI.show_layer(job, "orig", "layer")

    def input_gerber(self,job):
        Job.create_job(job)
        Matrix.create_step(job, 'orig')
        result_file_identify = Input.file_identify(r"C:\Users\cheng.chen\Desktop\760\LAYER2.art")
        # print(result_file_identify)
        Input.file_translate(path = r"C:\Users\cheng.chen\Desktop\760\LAYER2.art",
                             job = job, step = 'orig', layer = 'layer',param = result_file_identify)

        BASE.save_job_as(job,r'C:\job\test\odb')

        GUI.show_layer(job, "orig", "layer")

class MyJob(object):
    def my_save_job_odb(self,job):
        # 比图前需要保存料号
        data = {
            'func': 'JOB_SAVE',
            'paras': [{'job': job}]
        }
        epcam.process(json.dumps(data))




if __name__ == "__main__":

    job_save_path_parent = r'C:\job\test\odb'
    folder_path = r"C:\Users\cheng.chen\Desktop\760"
    job = r'test'
    step = r'orig'
    save_path = r'C:\job\test\odb'
    cc = MyInput()
    cc.input_gerber_folder(folder_path,job,step,save_path)

