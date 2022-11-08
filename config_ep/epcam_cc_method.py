import json
import os
import shutil

from config import RunConfig
from epcam_api import Configuration, Input, GUI,BASE
from epcam_api.Edition import Job,Matrix

from config_ep.epcam import epcam

from cc.cc_method import StringMehtod

Configuration.init(RunConfig.ep_cam_path)
Configuration.set_sys_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\sysattr'))
Configuration.set_user_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\userattr'))

def f1():
    pass
    Input.open_job("eni40021", r"C:\job\test\odb")
    GUI.show_layer("eni40021", "orig", "top")

class MyInput(object):

    def __init__(self,folder_path,job,step,*,save_path=None):
        self.folder_path = folder_path
        self.job = job
        self.step = step
        self.save_path = save_path

    def fix_layer_name_same_to_g(self):
        print('fix_layer_name_same_to_g'.center(190,'-'))
        folder_path = self.folder_path
        # 开始识别文件夹中各个文件的类型，此方只识别单层文件夹中的内容
        file_list = [x for x in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, x))]

        unknown_index = 1

        for file in file_list:
            # 把特殊字符替换成‘-’，比如空格、(、)等。
            os.rename(os.path.join(folder_path, file),os.path.join(folder_path, file.replace(' ', '-').replace('(', '-').replace(')', '-')))
            # 把含有中文字符名称的文件改名成unknown1\unknown2等
            if StringMehtod.is_chinese(file):
                suffix_of_file = os.path.splitext(file)[1]
                os.rename(os.path.join(folder_path,file), os.path.join(folder_path,'unknown' + str(unknown_index) + suffix_of_file))
                # file = 'unknown' + str(unknown_index)
                unknown_index = unknown_index + 1

    def input_folder(self):
        '''
        函数：把指定路径下的所有Gerber274X或Excello2文件全部转换到指定名称的料号，并保存到指定路径。
        命名关键字参数save_path，用来保存料号的路径，未传此参数时，默认路径为r'C:\job\test\odb'。
        '''

        folder_path = self.folder_path
        job = self.job
        step = self.step
        save_path = self.save_path

        #如果未指定保存路径,默认路径为r'C:\job\test\odb'。
        save_path = r'C:\job\test\odb' if not save_path else save_path

        # job若存在则删除
        shutil.rmtree(os.path.join(save_path, job)) if os.path.exists(os.path.join(save_path, job)) else True

        # 创建一个空料号
        Job.create_job(job)

        #创建一个空step
        Matrix.create_step(job, step)

        #开始识别文件夹中各个文件的类型，此方只识别单层文件夹中的内容
        file_list = [x for x in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path,x))]

        for each_file in file_list:
            result_each_file_identify = Input.file_identify(os.path.join(folder_path,each_file))
            Input.file_translate(path=os.path.join(folder_path,each_file),job=job, step='orig', layer=each_file, param=result_each_file_identify)


        BASE.save_job_as(job, save_path)


        GUI.show_layer(job, "orig", "layer")




if __name__ == "__main__":
    folder_path = r"C:\Users\cheng.chen\Desktop\760"
    job = r'test'
    step = r'orig'
    save_path = r'C:\job\test\odb'
    my_input = MyInput(folder_path, job, step)
    my_input.fix_layer_name_same_to_g()
    my_input.input_folder()

