import json
import os
import shutil
import time
from pathlib import Path

import pandas as pd
import psycopg2
from sqlalchemy import create_engine

from config import RunConfig
from epkernel import Configuration, Input, GUI,BASE,Output
from epkernel.Edition import Job,Matrix
from epkernel.Action import Information

from config_ep.epcam import epcam

from cc.cc_method import StringMehtod,DMS,Print

Configuration.init(RunConfig.ep_cam_path)
Configuration.set_sys_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\sysattr'))
Configuration.set_user_attr_path(os.path.join(RunConfig.ep_cam_path,r'config\attr_def\userattr'))

def f1():
    pass
    Input.open_job("eni40021", r"C:\job\test\odb")
    GUI.show_layer("eni40021", "orig", "top")

class MyInput(object):

    def __init__(self,*,folder_path,job,step,job_id,save_path=None):
        self.folder_path = folder_path
        self.job = job
        self.step = step
        self.job_id = job_id
        self.save_path = save_path
        #层名称处理
        self.fix_layer_name_same_to_g()
        #从DMS获取层别信息
        self.get_job_layer_info_from_dms()
        self.input_folder()

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

    def get_job_layer_info_from_dms(self):
        job_id = self.job_id
        sql = '''SELECT a.* from layer a where a.job_id = {}'''.format(job_id)
        engine = create_engine('postgresql+psycopg2://readonly:123456@10.97.80.119/dms')
        pd_job_layer_info = pd.read_sql(sql=sql, con=engine)
        self.pd_job_layer_info = pd_job_layer_info

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
            #如果是孔的话，需要从DMS读取导入参数。是不是孔文件，以及相关参数信息都从DMS获取信息。孔参数信息是要人工确认过的，即层信息状态是published的。
            try:
                pd_job_layer_info_cuurent_layer = self.pd_job_layer_info[(self.pd_job_layer_info['layer'] == each_file)]
                if pd_job_layer_info_cuurent_layer['status'].values[0] ==  'published' and pd_job_layer_info_cuurent_layer['layer_file_type'].values[0] ==  'excellon2':
                    print('need to set the para for drill excellon2'.center(190,'-'))
                    print('原来导入参数'.center(190,'-'))
                    print(result_each_file_identify)
                    result_each_file_identify['parameters']['units'] = pd_job_layer_info_cuurent_layer['units_ep'].values[0]
                    result_each_file_identify['parameters']['zeroes_omitted'] = pd_job_layer_info_cuurent_layer['zeroes_omitted_ep'].values[0]
                    result_each_file_identify['parameters']['Number_format_integer'] = int(pd_job_layer_info_cuurent_layer['number_format_A_ep'].values[0])
                    result_each_file_identify['parameters']['Number_format_decimal'] = int(pd_job_layer_info_cuurent_layer['number_format_B_ep'].values[0])
                    result_each_file_identify['parameters']['tool_units'] = pd_job_layer_info_cuurent_layer['tool_units_ep'].values[0]
                    print('现在导入参数'.center(190, '-'))
                    print(result_each_file_identify)
            except Exception as e:
                print(e)


            Input.file_translate(path=os.path.join(folder_path,each_file),job=job, step='orig', layer=each_file, param=result_each_file_identify)

        #保存料号
        BASE.save_job_as(job, save_path)

class MyOutput(object):

    def __init__(self,*,temp_path,job,job_id):
        pass
        self.temp_path = temp_path
        self.job = job
        self.job_id = job_id

        self.set_para()

        self.out_put()


    def set_para(self):

        # 设置导出参数
        with open(RunConfig.config_ep_output, 'r') as cfg:
            infos_ = json.load(cfg)['paras']  # (json格式数据)字符串 转化 为字典
            self._type = infos_['type']
            self.resize = infos_['resize']
            self.gdsdbu = infos_['gdsdbu']
            self.angle = infos_['angle']
            self.scalingX = infos_['scalingX']
            self.scalingY = infos_['scalingY']
            self.isReverse = infos_['isReverse']
            self.mirror = infos_['mirror']
            self.rotate = infos_['rotate']
            self.scale = infos_['scale']
            self.profiletop = infos_['profiletop']
            self.cw = infos_['cw']
            self.cutprofile = infos_['cutprofile']
            self.mirrorpointX = infos_['mirrorpointX']
            self.mirrorpointY = infos_['mirrorpointY']
            self.rotatepointX = infos_['rotatepointX']
            self.rotatepointY = infos_['rotatepointY']
            self.scalepointX = infos_['scalepointX']
            self.scalepointY = infos_['scalepointY']
            self.mirrordirection = infos_['mirrordirection']
            self.cut_polygon = infos_['cut_polygon']
            self.mirrorX = infos_['mirrorX']
            self.mirrorY = infos_['mirrorY']


    def out_put(self):
        out_put = []
        job_result = {}
        out_json = ''



        # 建立output_gerber文件夹，里面用来放epcam输出的gerber。
        temp_out_put_gerber_path = os.path.join(self.temp_path, 'output_gerber')
        if os.path.exists(temp_out_put_gerber_path):
            shutil.rmtree(temp_out_put_gerber_path)
        os.mkdir(temp_out_put_gerber_path)


        #导出Gerber274X参数
        _type = self._type
        resize = self.resize
        gdsdbu = self.gdsdbu
        angle = self.angle
        scalingX = self.scalingX
        scalingY = self.scalingY
        isReverse = self.isReverse
        mirror = self.mirror
        rotate = self.rotate
        scale = self.scale
        profiletop = self.profiletop
        cw = self.cw
        cutprofile = self.cutprofile
        mirrorpointX = self.mirrorpointX
        mirrorpointY = self.mirrorpointY
        rotatepointX = self.rotatepointX
        rotatepointY = self.rotatepointY
        scalepointX = self.scalepointX
        scalepointY = self.scalepointY
        mirrordirection = self.mirrordirection
        cut_polygon = self.cut_polygon
        mirrorX = self.mirrorX
        mirrorY = self.mirrorY

        layers = Information.get_layers(self.job)
        steps = Information.get_steps(self.job)
        file_path = os.path.join(temp_out_put_gerber_path, self.job)
        file_path_file = Path(file_path)
        if file_path_file.exists():
            shutil.rmtree(file_path_file)  # 已存在gerber文件夹删除掉，再新建
        os.mkdir(file_path)

        for step in steps:
            value = {}
            # 开始时间
            start_time = (int(time.time()))
            # 创建料的step文件夹
            step_path = os.path.join(file_path, step)
            os.mkdir(step_path)

            drill_layers = [each.lower() for each in
                            DMS().get_job_layer_drill_from_dms_db_pandas_one_job(self.job_id)['layer']]
            rout_layers = [each.lower() for each in
                           DMS().get_job_layer_rout_from_dms_db_pandas_one_job(self.job_id)['layer']]
            print("drill_layers:", drill_layers)

            # common_layers_list是非孔类型的文件
            common_layers_list = []
            layer_result = {}

            for each_layer in layers:
                if each_layer not in drill_layers:
                    common_layers_list.append(each_layer)

            # 输出gerber
            for layer in common_layers_list:
                layer_stime = (int(time.time()))
                filename = os.path.join(step_path, layer)  # 当前step下的每个层的gerber文件路径
                ret = Output.save_gerber(self.job, step, layer, filename, resize, angle, scalingX, scalingY, mirror,
                                         rotate, scale, cw,
                                         mirrorpointX, mirrorpointY, rotatepointX, rotatepointY, scalepointX,
                                         scalepointY, mirrorX, mirrorY)
                layer_etime = (int(time.time()))
                layer_time = layer_etime - layer_stime
                value[layer] = layer_time

            # 输出excellon2
            for drill_layer in drill_layers:

                layer_stime = (int(time.time()))

                drill_out_path = os.path.join(step_path, drill_layer)

                if drill_layer in rout_layers:
                    Print.print_with_delimiter("我是rout")
                    Matrix.change_matrix_row(self.job, drill_layer, 'board', 'rout', drill_layer)
                    drill_info = Output.save_rout(self.job, step, drill_layer, drill_out_path, number_format_l=2,
                                                  number_format_r=4, zeroes=2, unit=0,
                                                  tool_unit=1, x_scale=1, y_scale=1, x_anchor=0, y_anchor=0,
                                                  break_arcs=False)
                else:
                    Print.print_with_delimiter("我是drill啊")
                    Matrix.change_matrix_row(self.job, drill_layer, 'board', 'drill', drill_layer)
                    # drill_info = Output.save_drill(job_ep, step, drill_layer, drill_out_path)
                    drill_info = BASE.drill2file(self.job, step, drill_layer, drill_out_path, isMetric=False,
                                                 number_format_l=2, number_format_r=4,
                                                 zeroes=2, unit=0, x_scale=1, y_scale=1, x_anchor=0, y_anchor=0,
                                                 manufacator='', tools_order=[])
                    # print("drill_info:",drill_info)
                layer_etime = (int(time.time()))
                layer_time = layer_etime - layer_stime
                value[layer] = layer_time

        # 记录下输出step的时间
        end_time = (int(time.time()))
        time_time = end_time - start_time
        value["step_time"] = time_time
        job_result[step] = value
        print('job_result:', job_result)
        out_put.append(job_result)
        print('out_put:', out_put)
        out_path = os.path.join(temp_out_put_gerber_path, 'out_put' + '.json')
        if out_json == '':
            with open(out_path, 'w+') as f:  # 不能是a,w+会覆盖原有的，a只会追加
                f.write(json.dumps(out_put, sort_keys=True, indent=4, separators=(',', ': ')))
        else:
            with open(out_json, 'r') as h:
                ret_json = json.load(h)
                ret_json.append(job_result)
                with open(out_json, 'w+') as hh:
                    hh.write(json.dumps(ret_json, sort_keys=True, indent=4, separators=(',', ': ')))

        # GUI.show_layer(job_ep, "orig", "layer")
        Job.close_job(self.job)

        Print.print_with_delimiter('输出gerber完成')


if __name__ == "__main__":
    folder_path = r"C:\Users\cheng.chen\Desktop\760"
    job = r'test'
    step = r'orig'
    save_path = r'C:\job\test\odb'
    my_input = MyInput(folder_path, job, step)
    my_input.fix_layer_name_same_to_g()
    my_input.input_folder()

