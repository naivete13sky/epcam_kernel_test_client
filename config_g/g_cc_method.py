import json
import os,shutil
import subprocess
import time
from cc.cc_method import Print,DMS
from config import RunConfig

LAYER_COMPARE_JSON = 'layer_compare.json'

class G():
    def __init__(self,gateway_path):
        self.gateway_path=gateway_path
        command0 = 'SET GENESIS_DIR=C:/Program Files/shareg'
        command = '{} 1'.format(self.gateway_path)
        self.process = subprocess.Popen(command0 + "&" + command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    def __del__(self):
        os.system('taskkill /f /im gateway.exe')

    def exec_cmd(self, cmd):
        self.process.stdin.write((cmd + '\n').encode())
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        ret = int(line.decode().strip())
        return ret

    def import_odb_folder(self, jobpath,*args,**kwargs):
        Print.print_with_delimiter('import job')
        results=[]
        self.jobpath = jobpath
        if "job_name" in kwargs:
            job_name = kwargs['job_name']
        else:
            job_name = os.path.basename(self.jobpath)
        cmd_list = [
            'COM import_job,db=genesis,path={},name={},analyze_surfaces=no'.format(jobpath, job_name.lower()),
        ]
        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            results=results.append(ret)
        return results

    def layer_compare_g_open_2_job(self, *args,**kwargs):
        Print.print_with_delimiter('comare_open_2_job')
        job1 = kwargs['job1']
        step = kwargs['step']
        job2 = kwargs['job2']
        cmd_list = [
            'COM check_inout,mode=out,type=job,job={}'.format(job1),
            'COM clipb_open_job,job={},update_clipboard=view_job'.format(job1),
            'COM open_job,job={}'.format(job1),
            'COM open_entity,job={},type=step,name={},iconic=no'.format(job1, step),
            'COM units,type=inch',
            'COM open_job,job={}'.format(job2),
        ]
        results = []
        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            results.append(ret)

    def layer_compare_one_layer(self, *args,**kwargs):
        Print.print_with_delimiter("do_comare")
        results_cmd = []
        result = '未比对'#比对结果
        self.job1 = kwargs['job1']
        self.step1 = kwargs['step1']
        self.layer1 = kwargs['layer1']
        self.job2 = kwargs['job2']
        self.step2 = kwargs['step2']
        self.layer2 = kwargs['layer2']
        self.layer2_ext = kwargs['layer2_ext']
        self.tol = kwargs['tol']
        self.map_layer = kwargs['map_layer']
        self.map_layer_res = kwargs['map_layer_res']
        layer_cp = self.layer2 + self.layer2_ext
        result_path_remote = kwargs['result_path_remote']
        result_path_local = kwargs['result_path_local']
        if "layer_type" in kwargs:
            layer_type=kwargs['layer_type']
        else:
            layer_type=""
        temp_path=kwargs['temp_path']

        cmd_list = [
            'COM compare_layers,layer1={},job2={},step2={},layer2={},layer2_ext={},tol={},area=global,consider_sr=yes,ignore_attr=,map_layer={},map_layer_res={}'.format(
                self.layer1, self.job2, self.step2, self.layer2, self.layer2_ext, self.tol, self.map_layer, self.map_layer_res),
            'COM info, out_file={}/{}.txt,args=  -t layer -e {}/{}/{} -m script -d EXISTS'.format(
                result_path_remote,self.layer1,self.job1,self.step1,self.layer1 + self.layer2_ext
            ),
            # 'COM info, out_file={}/{}_com_features_count.txt,args=  -t layer -e {}/{}/{} -m display -d FEAT_HIST\nsource {}/{}_com_features_count.txt'.format(
            #     result_path_remote,self.layer1,self.job1,self.step1,self.layer1+'-com',result_path_remote,self.layer1
            # ),

        ]
        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print('ret:',ret)
            results_cmd.append(ret)
            # if ret == 44011:
            if ret != 0:
                result = '比对异常！未能正常比对！请人工检查'
                return result


        # time.sleep(1)
        # # 先看一下-com层是不是空的，如果是空的说明比对操作失败。
        # with open(os.path.join(result_path_local,self.layer1 + '_com_features_count.txt'), 'r') as f:
        #     comp_result_count = f.readlines()[0].split(",")[-1].strip()
        # if comp_result_count == 'total=0':
        #     print("比对异常！未能比对！")
        #     result = '错误'
        #     return result

        # 再看一下是否存在_copy层，如果存在说明比对结果有差异。通过info功能。
        with open(os.path.join(result_path_local,self.layer1 + '.txt'), 'r') as f:
            comp_result_text = f.readlines()[0].split(" ")[-1].strip()
        if comp_result_text == 'no':
            result = '正常'
        elif comp_result_text == 'yes':
            result = '错误'
            Print.print_with_delimiter("第一次比图未通过")
            if layer_type == 'drill' and kwargs['adjust_position']:
                Print.print_with_delimiter("再给一次较正孔位置的机会！")
                #先获取坐标，算出偏移量，然后用G移。
                temp_path_local_g_info1_folder = r'{}\info1'.format(temp_path)
                temp_path_remote_g_info1_folder = r'\\vmware-host\Shared Folders\share\{}\info1'.format(os.path.basename(temp_path))
                temp_path_local_g_info2_folder = r'{}\info2'.format(temp_path)
                temp_path_remote_g_info2_folder = r'\\vmware-host\Shared Folders\share\{}\info2'.format(os.path.basename(temp_path))
                coor_1 = self.get_info_layer_features_first_coor(job=self.job1, step=self.step1, layer=self.layer1,
                                                              temp_path_local_g_info_folder=temp_path_local_g_info1_folder,
                                                              temp_path_remote_g_info_folder=temp_path_remote_g_info1_folder)
                coor_2 = self.get_info_layer_features_first_coor(job=self.job2, step=self.step2, layer=self.layer2,
                                                                 temp_path_local_g_info_folder=temp_path_local_g_info2_folder,
                                                                 temp_path_remote_g_info_folder=temp_path_remote_g_info2_folder)
                x1 = float(coor_1[0])
                y1 = float(coor_1[1])
                x2 = float(coor_2[0])
                y2 = float(coor_2[1])
                dx = x2 - x1
                dy = y2 - y1
                # print("dx:", dx, "dy:", dy)
                #开始移
                self.move_one_layer_by_x_y(layer=self.layer1, dx=dx, dy=dy)
                Print.print_with_delimiter("已经移了孔位置！")
                #再比一次图
                cmd_list = [
                    'COM compare_layers,layer1={},job2={},step2={},layer2={},layer2_ext={},tol={},area=global,consider_sr=yes,ignore_attr=,map_layer={},map_layer_res={}'.format(
                        self.layer1, self.job2, self.step2, self.layer2, "_copy2", self.tol, self.map_layer,
                        self.map_layer_res),
                    'COM info, out_file={}/{}_2.txt,args=  -t layer -e {}/{}/{} -m script -d EXISTS'.format(
                        result_path_remote, self.layer1, self.job1, self.step1, self.layer1 + "_copy2"
                    ),
                ]
                for cmd in cmd_list:
                    print(cmd)
                    ret = self.exec_cmd(cmd)
                    results_cmd.append(ret)

                with open(os.path.join(result_path_local, self.layer1 + '_2.txt'), 'r') as f:
                    comp_result_text = f.readlines()[0].split(" ")[-1].strip()
                if comp_result_text == 'no':
                    result = '正常'
                elif comp_result_text == 'yes':
                    result = '错误'

                Print.print_with_delimiter("第二次比图结束！结果是：",result)

        print("比对结果：",result)
        return result

    def layer_compare_do_compare(self, *args,**kwargs):
        Print.print_with_delimiter("do_comare")
        results = []
        try:
            self.step1 = kwargs['step1']
            self.layer1 = kwargs['layer1']
            self.job2 = kwargs['job2']
            self.step2 = kwargs['step2']
            self.layer2 = kwargs['layer2']
            self.layer2_ext = kwargs['layer2_ext']
            self.tol = kwargs['tol']
            self.map_layer = kwargs['map_layer']
            self.map_layer_res = kwargs['map_layer_res']
        except Exception as e:
            print(e)
            print("*" * 100)
            return results



        layer_cp = self.layer2 + self.layer2_ext

        cmd_list1 = [
            'COM compare_layers,layer1={},job2={},step2={},layer2={},layer2_ext={},tol={},area=global,consider_sr=yes,ignore_attr=,map_layer={},map_layer_res={}'.format(
                self.layer1, self.job2, self.step2, self.layer2, self.layer2_ext, self.tol, self.map_layer, self.map_layer_res),

        ]

        cmd_list2 = [

        ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            if ret != 0:
                print('inner error:',ret)
                return 'inner error'

        time.sleep(1)

    def save_job(self, job):
        Print.print_with_delimiter("save")
        results = []

        cmd_list1 = [
            'COM save_job,job={},override=no'.format(job),
        ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            if ret != 0:
                print('inner error')
                return results

        time.sleep(1)

    def get_info_layer_features_first_coor(self,*args,**kwargs):
        Print.print_with_delimiter('get_info_layer_features_first_coor')
        results = []
        temp_path_local_g_info_folder = kwargs['temp_path_local_g_info_folder']
        temp_path_remote_g_info_folder = kwargs['temp_path_remote_g_info_folder']
        job = kwargs['job']
        step = kwargs['step']
        layer = kwargs['layer']

        cmd_list = [
            'COM info, out_file={}/{}.txt,args=  -t layer -e {}/{}/{} -m script -d FEATURES'.format(
                temp_path_remote_g_info_folder,layer,job,step,layer),

        ]
        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            results.append(ret)

        with open(os.path.join(temp_path_local_g_info_folder,layer + '.txt'), 'r') as f:
            features_info_first_all_data = f.readlines()[1]
            coor_x = features_info_first_all_data.split(" ")[1].strip()
            coor_y = features_info_first_all_data.split(" ")[2].strip()
        # print(coor_x,coor_y)
        return (coor_x,coor_y)

    def move_one_layer_by_x_y(self, *args,**kwargs):
        Print.print_with_delimiter('move_one_layer_by_x_y')
        results=[]
        layer = kwargs['layer']
        dx = kwargs['dx']
        dy = kwargs['dy']

        cmd_list = [
            'COM display_layer,name={},display=yes,number=1'.format(layer),
            'COM work_layer,name={}'.format(layer),
            'COM sel_move,dx={},dy={}'.format(dx,dy),
        ]
        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            results.append(ret)

    def layer_compare_analysis(self, jobpath1,step1,layer1,jobpath2,step2,layer2,layer2_ext,tol,map_layer,map_layer_res):
        print("*" * 100, "comare")
        results = []
        try:
            self.jobpath1 = jobpath1
            # self.job_name_1=self.jobpath1.split("\\")[-1]
            self.step1 = step1
            self.layer1 = layer1
            self.jobpath2 = jobpath2
            self.step2 = step2
            self.layer2 = layer2
            self.layer2_ext = layer2_ext
            self.tol = tol
            self.map_layer = map_layer
            self.map_layer_res = map_layer_res
        except Exception as e:
            print(e)
            print("*" * 100)
            return results

        job1 = os.path.basename(jobpath1)
        job2 = os.path.basename(jobpath2)
        layer_cp = layer2 + layer2_ext

        temp_path = r'C:\cc\share\temp'

        # if os.path.exists(os.path.join(temp_path, str(job.file_odb_g).split('/')[-1])):
        #     os.remove(os.path.join(temp_g_path, str(job.file_odb_g).split('/')[-1]))
        # print("g_tgz_file_now:", os.listdir(temp_g_path)[0])


        features = (r"{}\{}\steps\{}\layers\{}\features".format(temp_path,job1, step1,self.map_layer))
        features_Z = (r"{}\{}\steps\{}\layers\{}\features.Z".format(temp_path,job1, step1,self.map_layer))
        print(features, "\n", features_Z)
        if os.path.isfile(features_Z):
            pass
            compress = Compress()
            compress.uncompress_z(features_Z)

        try:
            f = open(features, "r")
        except Exception as e:
            print("未能比对！！！请重新执行比对！！！")
            result = "未比对"


        # shutil.copytree(r"C:\genesis\fw\jobs\{}".format(job_name_1),r"C:\cc\jobs\{}".format(job_name_1))
        # time.sleep(15)
        try:
            with open(features, "r") as f:
                s = f.readlines()
                print(s[3])
            if "r0" in s[3]:
                print("比对发现有差异！！！！！！")
                result = "错误"
            else:
                print("恭喜！比对通过！！！")
                result = "正常"

                try:
                    diff = False
                    matrix_path = r"{}\{}\matrix\matrix".format(temp_path,job1)
                    print('matrix_path:',matrix_path)
                    with open(matrix_path, 'r') as f:
                        for var in f.readlines():
                            line = var.strip()
                            if len(line) == 0:
                                continue
                            attr = line.split('=')
                            if len(attr) == 2:
                                # print(attr)
                                if attr[0] == 'NAME' and attr[1].lower() == layer_cp:
                                    diff = True
                                    break
                    if diff == True:
                        print('Difference were found')
                        result = "错误"
                    else:
                        print('Layers Match')
                        result = "正常"
                except:
                    print("matrix查看方法失败")

        except:
            print("查看结果失败！")
            result='未比对'

        return result

    def layer_compare_analysis_temp_path(self, *args,**kwargs):
        results = []
        job = kwargs['job']
        step=kwargs['step']
        layer_cp = kwargs['layer2'] + kwargs['layer2_ext']
        map_layer=kwargs['map_layer']
        temp_path = kwargs['temp_path']

        features = (r"{}\{}\steps\{}\layers\{}\features".format(temp_path,job, step,map_layer))
        features_Z = (r"{}\{}\steps\{}\layers\{}\features.Z".format(temp_path,job, step,map_layer))
        # print(features, "\n", features_Z)
        if os.path.isfile(features_Z):
            pass
            compress = Compress()
            compress.uncompress_z(features_Z)

        try:
            f = open(features, "r")
        except Exception as e:
            print("未能比对！！！请重新执行比对！！！")
            result = "未比对"

        try:
            with open(features, "r") as f:
                s = f.readlines()
                # print(s[3])
            if "r0" in s[3]:
                # print("比对发现有差异！！！！！！")
                result = "错误"
            else:
                # print("恭喜！比对通过！！！")
                result = "正常"

                #再通过matrix方法来校验一下比图结果
                try:
                    diff = False
                    matrix_path = r"{}\{}\matrix\matrix".format(temp_path,job)
                    # print('matrix_path:',matrix_path)
                    with open(matrix_path, 'r') as f:
                        for var in f.readlines():
                            line = var.strip()
                            if len(line) == 0:
                                continue
                            attr = line.split('=')
                            if len(attr) == 2:
                                # print(attr)
                                if attr[0] == 'NAME' and attr[1].lower() == layer_cp:
                                    diff = True
                                    break
                    if diff == True:
                        print('Difference were found')
                        result = "错误"

                except:
                    print("matrix查看方法失败")

        except:
            print("查看结果失败！")
            result='未比对'
        # print("*" * 80, layer2,":查看比图结果--结束", "*" * 80,'\n')

        return result

    def layer_compare_close_job(self, *args,**kwargs):
        Print.print_with_delimiter('close job',sign='-')
        results = []
        self.job1 = kwargs['job1']
        self.job2 = kwargs['job2']

        cmd_list1 = [
            'COM editor_page_close',
            'COM check_inout,mode=out,type=job,job={}'.format(self.job1),
            'COM close_job,job={}'.format(self.job1),
            'COM close_form,job={}'.format(self.job1),
            'COM close_flow,job={}'.format(self.job1),

            'COM close_job,job={}'.format(self.job2),
            'COM close_form,job={}'.format(self.job2),
            'COM close_flow,job={}'.format(self.job2)
        ]

        cmd_list2 = [
        ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            if ret != 0:
                print('inner error')
                return results
        time.sleep(1)

    def layer_compare_dms(self,*args,job_id,vs_time_g,temp_path,job1,all_layers_list_job1,job2,all_layers_list_job2,adjust_position=False,**kwargs):
        global g_vs_total_result_flag
        adjust_position = adjust_position


        data_g = {}
        g_vs_total_result_flag = True  # True表示最新一次G比对通过
        # 读取配置文件
        with open(r'C:\cc\python\epwork\epcam_kernel_test_client\config_g\config.json', encoding='utf-8') as f:
            cfg = json.load(f)
        tol = cfg['job_manage']['vs']['vs_tol_g']
        map_layer_res = cfg['job_manage']['vs']['map_layer_res']


        # G打开要比图的2个料号
        self.layer_compare_g_open_2_job(job1=job1, step='orig', job2=job2)
        g_compare_result_folder = job1 + '_compare_result'
        temp_g_compare_result_path = os.path.join(temp_path, g_compare_result_folder)
        if not os.path.exists(temp_g_compare_result_path):
            os.mkdir(temp_g_compare_result_path)
        temp_path_remote_g_compare_result = r'//vmware-host/Shared Folders/share/{}/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, g_compare_result_folder)
        temp_path_local_g_compare_result = os.path.join(temp_path, g_compare_result_folder)

        drill_layers = [each.lower() for each in DMS().get_job_layer_drill_from_dms_db_pandas_one_job(job_id)['layer']]

        all_result_g = {}
        for layer in all_layers_list_job1:
            if layer in all_layers_list_job2:
                layer_type = ""
                if layer in drill_layers:
                    print("我是孔层哈！")
                    layer_type = 'drill'


                map_layer = layer + '-com'
                result = self.layer_compare_one_layer(job1=job1, step1='orig', layer1=layer, job2=job2,
                                                   step2='orig', layer2=layer, layer2_ext='_copy', tol=tol,
                                                   map_layer=map_layer, map_layer_res=map_layer_res,
                                                   result_path_remote=temp_path_remote_g_compare_result,
                                                   result_path_local=temp_path_local_g_compare_result,
                                                   layer_type=layer_type,adjust_position=adjust_position,
                                                      temp_path=temp_path)
                all_result_g[layer] = result
                if result != "正常":
                    g_vs_total_result_flag = False
            else:
                print("悦谱转图中没有此层")
        data_g['all_result_g'] = all_result_g
        self.save_job(job1)
        self.save_job(job2)
        self.layer_compare_close_job(job1=job1, job2=job2)

        # 开始查看比对结果
        # 获取原始层文件信息，最全的
        all_layer_from_org = [each for each in DMS().get_job_layer_fields_from_dms_db_pandas(job_id, field='layer_org')]
        all_result = {}  # all_result存放原始文件中所有层的比对信息
        for layer_org in all_layer_from_org:
            layer_org_find_flag = False
            layer_org_vs_value = ''
            for each_layer_g_result in all_result_g:
                if each_layer_g_result == str(layer_org).lower().replace(" ", "-").replace("(", "-").replace(")", "-"):
                    layer_org_find_flag = True
                    layer_org_vs_value = all_result_g[each_layer_g_result]
            if layer_org_find_flag == True:
                all_result[layer_org] = layer_org_vs_value
            else:
                all_result[layer_org] = 'G转图中无此层'
        data_g['all_result'] = all_result

        data_g['g_vs_total_result_flag'] = g_vs_total_result_flag

        return data_g

    def clean_g(self, paras):
        print("begin clean!")
        try:
            jobpath1 = paras['jobpath1']
            job_name_1=jobpath1.split("\\")[-1]
            step1 = paras['step1']
            layer1 = paras['layer1']
            jobpath2 = paras['jobpath2']
            step2 = paras['step2']
            layer2 = paras['layer2']
            layer2_ext = paras['layer2_ext']
            tol = paras['tol']
            map_layer = paras['map_layer']
            map_layer_res = paras['map_layer_res']
        except Exception as e:
            print(e)
            return

        job1 = os.path.basename(jobpath1)
        job2 = os.path.basename(jobpath2)
        # layer_cp = layer2 + layer2_ext



        cmd_list2 = [
            # 'COM editor_page_close',
            # 'COM check_inout,mode=in,type=job,job={}'.format(job1),
            # 'COM close_job,job={}'.format(job1),
            # 'COM close_form,job={}'.format(job1),
            # 'COM close_flow,job={}'.format(job1),
            'COM close_job,job={}'.format(job1),
            'COM close_form,job={}'.format(job1),
            'COM close_flow,job={}'.format(job1),
            'COM delete_entity,job=,type=job,name={}'.format(job1),
            'COM close_form,job={}'.format(job1),
            'COM close_flow,job={}'.format(job1),
            'COM close_job,job={}'.format(job2),
            'COM close_form,job={}'.format(job2),
            'COM close_flow,job={}'.format(job2),
            'COM close_form,job={}'.format(job2),
            'COM close_flow,job={}'.format(job2),
            'COM delete_entity,job=,type=job,name={}'.format(job2)
        ]

        # for cmd in cmd_list1:
        #     # print(cmd)
        #     ret = self.exec_cmd(cmd)
        #     if ret != 0:
        #         print('inner error')
        #         return

        # time.sleep(1)

        for cmd in cmd_list2:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print(ret)
            if ret != 0:
                print('inner error')
                # return
        return "clean finish!"

    def delete_job(self,job_name):
        pass
        cmd_list = [
            'COM close_job,job={}'.format(job_name),
            'COM close_form,job={}'.format(job_name),
            'COM close_flow,job={}'.format(job_name),
            'COM delete_entity,job=,type=job,name={}'.format(job_name),
            'COM close_form,job={}'.format(job_name),
            'COM close_flow,job={}'.format(job_name)
        ]

        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print(ret)
            if ret != 0:
                print('inner error')
                # return
        return "clean finish!"

    def clean_g_all(self):
        pass
        cmd_list = [
            'COM info,args=-t root -m display -d JOBS_LIST,out_file=C:/tmp/job_list.txt,write_mode=replace,units=inch'
        ]

        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print(ret)
            if ret != 0:
                print('inner error')
                # return

        with open(r"C:/tmp/job_list.txt", "r") as f:
            s = f.readlines()
        print(s)

        for each_job in s:

            job_name = each_job.split("=")[1]
            self.delete_job(job_name)

        return "clean finish!"

    def clean_g_all_pre_get_job_list(self,job_list_path):
        pass
        cmd_list = [
            'COM info,args=-t root -m display -d JOBS_LIST,out_file={},write_mode=replace,units=inch'.format(job_list_path)
        ]

        for cmd in cmd_list:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print(ret)
            if ret != 0:
                print('inner error')
        return "已生成job_list!"

    def clean_g_all_do_clean(self,job_list_path):
        with open(job_list_path, "r") as f:
            s = f.readlines()
        print(s)

        for each_job in s:

            job_name = each_job.split("=")[1]
            self.delete_job(job_name)

        return "clean finish!"


    def Create_Entity(self, job, step):
        print("*"*100,job,step)
        cmd_list1 = [
            # 'COM abc',
            'COM create_entity,job=,is_fw=no,type=job,name={},db=genesis,fw_type=form'.format(job),
            'COM create_entity,job={},is_fw=no,type=step,name={},db=genesis,fw_type=form'.format(job, step),
            'COM save_job,job={},override=no'.format(job)
        ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print("*"*100,ret)
            if ret != 0:
                print('inner error')
                return False
        return True

    def Gerber2ODB(self, paras, _type):
        # print("*"*100,"gerber2odb")
        try:
            path = paras['path']
            job = paras['job']
            step = paras['step']
            format = paras['format']
            data_type = paras['data_type']
            units = paras['units']
            coordinates = paras['coordinates']
            zeroes = paras['zeroes']
            nf1 = paras['nf1']
            nf2 = paras['nf2']
            decimal = paras['decimal']
            separator = paras['separator']
            tool_units = paras['tool_units']
            layer = paras['layer']
            print("layer"*10,layer)
            layer=layer.replace(' ','-').replace('(', '-').replace(')', '-')
            print("layer" * 10, layer)
            wheel = paras['wheel']
            wheel_template = paras['wheel_template']
            nf_comp = paras['nf_comp']
            multiplier = paras['multiplier']
            text_line_width = paras['text_line_width']
            signed_coords = paras['signed_coords']
            break_sr = paras['break_sr']
            drill_only = paras['drill_only']
            merge_by_rule = paras['merge_by_rule']
            threshold = paras['threshold']
            resolution = paras['resolution']
        except Exception as e:
            print(e)
            return False

        # print("p"*100,path)

        # if not os.path.exists(path):
        #     print('{} does not exist'.format(path))
        #     return False

        trans_COM = 'COM input_manual_set,'
        trans_COM += 'path={},job={},step={},format={},data_type={},units={},coordinates={},zeroes={},'.format(path.replace("\\","/"),
                                                                                                               job,
                                                                                                               step,
                                                                                                               format,
                                                                                                               data_type,
                                                                                                               units,
                                                                                                               coordinates,
                                                                                                               zeroes)
        trans_COM += 'nf1={},nf2={},decimal={},separator={},tool_units={},layer={},wheel={},wheel_template={},'.format(
            nf1, nf2, decimal, separator, tool_units, layer, wheel, wheel_template)
        trans_COM += 'nf_comp={},multiplier={},text_line_width={},signed_coords={},break_sr={},drill_only={},'.format(
            nf_comp, multiplier, text_line_width, signed_coords, break_sr, drill_only)
        trans_COM += 'merge_by_rule={},threshold={},resolution={}'.format(merge_by_rule, threshold, resolution)

        cmd_list1 = []
        cmd_list2 = []
        # trans_COM = 'COM input_manual_set,path=C:/Users/EPSZ15/Desktop/2222/YH-DT3.9-FM1921_64X64-8SF2-04.GTL,job=6566,step=777,format=Gerber274x,data_type=ascii,units=mm,coordinates=absolute,zeroes=leading,nf1=4,nf2=4,decimal=no,separator=*,tool_units=inch,layer=yh-dt3.9-fm1921_64x64-8sf2-04.gtl,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3'
        if _type == 0:
            cmd_list1 = [
                'COM input_manual_reset',
                # 'COM input_manual_set,path={},job={},step={},format={},data_type{},units={},coordinates={},zeroes={},nf1={},nf2={},decimal={},separator={},\
                #     tool_units={},layer={},wheel={},wheel_template={},nf_comp={},multiplier={},text_line_width={},signed_coords={},break_sr={},drill_only={},\
                #     merge_by_rule={},threshold={},resolution={}'.format(path, job, step, format, data_type, units, coordinates, zeroes, nf1, nf2, decimal,
                #     separator, tool_units, layer, wheel, wheel_template, nf_comp, multiplier, text_line_width, signed_coords, break_sr, drill_only, merge_by_rule,
                #     threshold, resolution),
                trans_COM,
                ('COM input_manual,script_path={}'.format(''))
            ]
            cmd_list2 = [
                'COM input_manual_reset',
                trans_COM,
                'COM input_manual,script_path={}'.format('')
            ]
        else:
            cmd_list1 = [
                'COM save_job,job={},override=no'.format(job)
            ]
            cmd_list2 = [
                'COM save_job,job={},override=no'.format(job)
            ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            if ret != 0:
                print('inner error')
                return False
        return True



    def gerber_to_odb_one_file(self, paras, _type,job_id,*args,**kwargs):
        # print("*"*100,"gerber2odb")
        try:
            path = paras['path']
            job = paras['job']
            step = paras['step']
            format = paras['format']
            data_type = paras['data_type']
            units = paras['units']
            coordinates = paras['coordinates']
            zeroes = paras['zeroes']
            nf1 = paras['nf1']
            nf2 = paras['nf2']
            decimal = paras['decimal']
            separator = paras['separator']
            tool_units = paras['tool_units']
            layer = paras['layer']
            print("layer"*10,layer)
            layer=layer.replace(' ','-').replace('(', '-').replace(')', '-')
            print("layer" * 10, layer)
            wheel = paras['wheel']
            wheel_template = paras['wheel_template']
            nf_comp = paras['nf_comp']
            multiplier = paras['multiplier']
            text_line_width = paras['text_line_width']
            signed_coords = paras['signed_coords']
            break_sr = paras['break_sr']
            drill_only = paras['drill_only']
            merge_by_rule = paras['merge_by_rule']
            threshold = paras['threshold']
            resolution = paras['resolution']
        except Exception as e:
            print(e)
            return False


        try:
            Print.print_with_delimiter("开始定位")
            # layer_all = [each for each in DMS().get_job_layer_fields_from_dms_db_pandas(job_id, field='layer')]
            # print("layer_all []:",layer_all)
            print(path.replace(' ', '-').replace('(', '-').replace(')', '-'))
            print(os.path.basename(path).replace(' ', '-').replace('(', '-').replace(')', '-'))
            print("fuck!")

            layer_e2=DMS().get_job_layer_fields_from_dms_db_pandas_one_layer(job_id,filter=os.path.basename(path).replace(' ', '-').replace('(', '-').replace(')', '-'))

            # print('*'*50,'\n',"layer_e2:",layer_e2)

            # print("*"*50,'\n','layer_e2.status:',layer_e2.status.values[0],'layer_e2.layer_file_type:',layer_e2.layer_file_type.values[0])
            if layer_e2.status.values[0] == 'published' and layer_e2.layer_file_type.values[0]=='excellon2':
                print("我是Excellon2!!!!!")
                format='Excellon2'
                if 'drill_para' in kwargs:
                    # print("drill_para2:", kwargs['drill_para'])
                    if kwargs['drill_para'] == 'epcam_default':
                        units = 'inch'
                        zeroes = 'none'
                        nf1 = "2"
                        nf2 = "4"
                        tool_units = 'mm'
                    elif kwargs['drill_para'] == 'from_dms':
                        units=layer_e2.units_g.values[0].lower()
                        zeroes=layer_e2.zeroes_omitted_g.values[0].lower()
                        nf1 = int(layer_e2.number_format_A_g.values[0])
                        nf2 = int(layer_e2.number_format_B_g.values[0])
                        #g软件的tool_units没有mils选项
                        if layer_e2.tool_units_g.values[0].lower() == 'mils':
                            tool_units = 'inch'
                        else:
                            tool_units = layer_e2.tool_units_g.values[0].lower()

                separator='nl'
            else:
                print("我不是孔Excellon2!")

            Print.print_with_delimiter("结束定位")
        except:
            print("有异常啊！")




        trans_COM = 'COM input_manual_set,'
        trans_COM += 'path={},job={},step={},format={},data_type={},units={},coordinates={},zeroes={},'.format(path.replace("\\","/"),
                                                                                                               job,
                                                                                                               step,
                                                                                                               format,
                                                                                                               data_type,
                                                                                                               units,
                                                                                                               coordinates,
                                                                                                               zeroes)
        trans_COM += 'nf1={},nf2={},decimal={},separator={},tool_units={},layer={},wheel={},wheel_template={},'.format(
            nf1, nf2, decimal, separator, tool_units, layer, wheel, wheel_template)
        trans_COM += 'nf_comp={},multiplier={},text_line_width={},signed_coords={},break_sr={},drill_only={},'.format(
            nf_comp, multiplier, text_line_width, signed_coords, break_sr, drill_only)
        trans_COM += 'merge_by_rule={},threshold={},resolution={}'.format(merge_by_rule, threshold, resolution)

        cmd_list1 = []
        cmd_list2 = []

        if _type == 0:
            cmd_list1 = [
                'COM input_manual_reset',
                trans_COM,
                ('COM input_manual,script_path={}'.format(''))
            ]
            cmd_list2 = [
                'COM input_manual_reset',
                trans_COM,
                'COM input_manual,script_path={}'.format('')
            ]
        else:
            cmd_list1 = [
                'COM save_job,job={},override=no'.format(job)
            ]
            cmd_list2 = [
                'COM save_job,job={},override=no'.format(job)
            ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            if ret != 0:
                print('inner error')
                return False
        return True

    def g_Gerber2Odb(self,gerberList, job, step):
        paras = {}
        paras['path'] = ''
        paras['job'] = job
        paras['step'] = step
        paras['format'] = 'Gerber274x'
        paras['data_type'] = 'ascii'
        paras['layer'] = ''
        paras['units'] = 'mm'
        paras['coordinates'] = 'absolute'
        paras['zeroes'] = 'leading'
        paras['nf1'] = '4'
        paras['nf2'] = '4'
        paras['decimal'] = 'no'
        paras['separator'] = '*'
        paras['tool_units'] = 'inch'
        paras['wheel'] = ''
        paras['wheel_template'] = ''
        paras['nf_comp'] = '0'
        paras['multiplier'] = '1'
        paras['text_line_width'] = '0.0024'
        paras['signed_coords'] = 'no'
        paras['break_sr'] = 'yes'
        paras['drill_only'] = 'no'
        paras['merge_by_rule'] = 'no'
        paras['threshold'] = '200'
        paras['resolution'] = '3'
        # 先创建job, step
        jobpath = r'C:\genesis\fw\jobs' + '/' + job
        # print("jobpath"*30,jobpath)
        results = []
        if os.path.exists(jobpath):
            shutil.rmtree(jobpath)
        self.Create_Entity(job, step)
        for gerberPath in gerberList:
            # print("g"*100,gerberPath)
            result = {'gerber': gerberPath}
            paras['path'] = gerberPath
            paras['layer'] = os.path.basename(gerberPath).lower()
            ret = self.Gerber2ODB(paras, 0)
            result['result'] = ret
            results.append(result)
        self.Gerber2ODB(paras, 1)
        return results

    def g_Gerber2Odb2(self,job_name, step, gerberList_path, out_path,job_id):
        paras = {}
        paras['path'] = ''
        paras['job'] = job_name
        paras['step'] = step
        paras['format'] = 'Gerber274x'
        paras['data_type'] = 'ascii'
        paras['layer'] = ''
        paras['units'] = 'mm'
        paras['coordinates'] = 'absolute'
        paras['zeroes'] = 'leading'
        paras['nf1'] = '4'
        paras['nf2'] = '4'
        paras['decimal'] = 'no'
        paras['separator'] = '*'
        paras['tool_units'] = 'inch'
        paras['wheel'] = ''
        paras['wheel_template'] = ''
        paras['nf_comp'] = '0'
        paras['multiplier'] = '1'
        paras['text_line_width'] = '0.0024'
        paras['signed_coords'] = 'no'
        paras['break_sr'] = 'yes'
        paras['drill_only'] = 'no'
        paras['merge_by_rule'] = 'no'
        paras['threshold'] = '200'
        paras['resolution'] = '3'
        # 先创建job, step
        jobpath = r'C:\genesis\fw\jobs' + '/' + job_name
        # print("jobpath"*30,jobpath)
        results = []
        if os.path.exists(jobpath):
            shutil.rmtree(jobpath)
        self.Create_Entity(job_name, step)
        for gerberPath in gerberList_path:
            # print("g"*100,gerberPath)
            result = {'gerber': gerberPath}
            paras['path'] = gerberPath
            paras['layer'] = os.path.basename(gerberPath).lower()
            ret = self.Gerber2ODB2(paras, 0,job_id)
            result['result'] = ret
            results.append(result)
        self.Gerber2ODB2(paras, 1,job_id)#保存
        return results

    def gerber_to_odb_batch(self,job_name, step, gerberList_path, out_path,job_id,*args,**kwargs):
        paras = {}
        paras['path'] = ''
        paras['job'] = job_name
        paras['step'] = step
        paras['format'] = 'Gerber274x'
        paras['data_type'] = 'ascii'
        paras['layer'] = ''
        paras['units'] = 'mm'
        paras['coordinates'] = 'absolute'
        paras['zeroes'] = 'leading'
        paras['nf1'] = '4'
        paras['nf2'] = '4'
        paras['decimal'] = 'no'
        paras['separator'] = '*'
        paras['tool_units'] = 'inch'
        paras['wheel'] = ''
        paras['wheel_template'] = ''
        paras['nf_comp'] = '0'
        paras['multiplier'] = '1'
        paras['text_line_width'] = '0.0024'
        paras['signed_coords'] = 'no'
        paras['break_sr'] = 'yes'
        paras['drill_only'] = 'no'
        paras['merge_by_rule'] = 'no'
        paras['threshold'] = '200'
        paras['resolution'] = '3'
        # 先创建job, step
        jobpath = r'C:\genesis\fw\jobs' + '/' + job_name
        # print("jobpath"*30,jobpath)
        results = []
        if os.path.exists(jobpath):
            shutil.rmtree(jobpath)
        self.Create_Entity(job_name, step)
        for gerberPath in gerberList_path:
            # print("g"*100,gerberPath)
            result = {'gerber': gerberPath}
            paras['path'] = gerberPath
            paras['layer'] = os.path.basename(gerberPath).lower()
            ret = self.gerber_to_odb_one_file(paras, 0,job_id,*args,**kwargs)
            result['result'] = ret
            results.append(result)
        self.gerber_to_odb_one_file(paras, 1,job_id,*args,**kwargs)#保存
        return results

    def g_export(self,job,export_to_path):
        Print.print_with_delimiter("导出--开始")
        cmd_list1 = [
            'COM export_job,job={},path={},mode=tar_gzip,submode=full,overwrite=yes'.format(job,export_to_path),
        ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)

            if ret != 0:
                print('inner error')
                return False
        Print.print_with_delimiter("导出--结束")
        return True

    def get_info_by_info(self,job,*,step='orig',out_file=r'//vmware-host/Shared Folders/share/temp_info/info.txt'):

        cmd_list1 = [
            'COM info, out_file={},args=  -t step -e {}/{} -m script -d LAYERS_LIST'.format(out_file,job,step),
        ]

        for cmd in cmd_list1:
            print(cmd)
            ret = self.exec_cmd(cmd)
            print('ret:',ret)
            if ret != 0:
                return False


class GInput(object):
    def __init__(self, *, job: str,step='orig',gerberList_path:list,out_path, job_id, drill_para,
                 layer_info_from_obj='dms',
                 layer_list:list,gerber_layer_list:list,drill_layer_list:list,rout_layer_list:list):
        self.g = RunConfig.driver_g
        self.job = job
        self.step = step
        self.gerberList_path = gerberList_path
        self.out_path = out_path
        self.job_id = job_id
        self.drill_para = drill_para
        self.layer_info_from_obj = layer_info_from_obj

        if layer_info_from_obj == 'job_tgz_file':
            self.layers = layer_list
            self.gerber_layers = gerber_layer_list
            self.drill_layers = drill_layer_list
            self.rout_layers = rout_layer_list

        self.get_current_job_layer_type(layer_info_from_obj)

        self.set_para_default()

        kw = {}
        kw['layer_info_from_obj'] = self.layer_info_from_obj
        kw['drill_para'] = self.drill_para
        self.in_put(self.job,self.step,self.gerberList_path,self.out_path,self.job_id,self.drill_para,self.layer_info_from_obj,**kw)

    def set_para_default(self):
        # 设置默认导入参数
        with open(RunConfig.config_g_input, 'r') as cfg:
            self.para = json.load(cfg)['input']  # (json格式数据)字符串 转化 为字典
            print("self.para::",self.para)

    def set_para_customer(self,customer_para:dict):
        pass
        print('customer_para:',customer_para)
        for each in customer_para:
            print(each)
            self.para[each] = customer_para[each]
        print(self.para)
        print("cc")

    def get_current_job_layer_type(self,layer_info_from_obj):
        if layer_info_from_obj == 'dms':
            pass

    def in_put(self,job_name, step, gerberList_path, out_path,job_id,*args,**kwargs):
        # 先创建job, step
        jobpath = r'C:\genesis\fw\jobs' + '/' + job_name
        results = []
        if os.path.exists(jobpath):
            shutil.rmtree(jobpath)
        self.g.Create_Entity(job_name, step)
        for gerberPath in gerberList_path:
            result = {'gerber': gerberPath}
            self.para['path'] = gerberPath
            self.para['layer'] = os.path.basename(gerberPath).lower()
            ret = self.gerber_to_odb_one_file(job_id,*args,**kwargs)
            result['result'] = ret
            results.append(result)
        self.g.save_job(self.job)
        return results

    def gerber_to_odb_one_file(self, job_id,*args,**kwargs):
        self.para['job'] = self.job
        self.para['step'] = self.step
        self.para['format'] = 'Gerber274x'
        self.para['separator'] = '*'
        self.para['layer']=self.para['layer'].replace(' ','-').replace('(', '-').replace(')', '-')

        print("iamcc",'kwargs:',kwargs)
        layer_info_from_obj = kwargs.get('layer_info_from_obj', None)
        if layer_info_from_obj == 'job_tgz_file':
            print(layer_info_from_obj)
            print('layer:',self.para['layer'])
            if self.para['layer'] not in self.gerber_layers:
                print("iamdrill")
                self.para['format'] = 'Excellon2'
                if 'drill_para' in kwargs:
                    if kwargs['drill_para'] == 'epcam_default':
                        self.para['units'] = 'inch'
                        self.para['zeroes'] = 'none'
                        self.para['nf1'] = "2"
                        self.para['nf2'] = "4"
                        self.para['tool_units'] = 'mm'
                        self.para['separator'] = 'nl'

        if layer_info_from_obj == 'dms':
            try:
                Print.print_with_delimiter("开始定位")
                print(self.para['path'].replace(' ', '-').replace('(', '-').replace(')', '-'))
                print(os.path.basename(self.para['path']).replace(' ', '-').replace('(', '-').replace(')', '-'))
                layer_e2=DMS().get_job_layer_fields_from_dms_db_pandas_one_layer(job_id,filter=os.path.basename(self.para['path']).replace(' ', '-').replace('(', '-').replace(')', '-'))
                if layer_e2.status.values[0] == 'published' and layer_e2.layer_file_type.values[0]=='excellon2':
                    print("我是Excellon2!!!!!")
                    format='Excellon2'
                    if 'drill_para' in kwargs:
                        # print("drill_para2:", kwargs['drill_para'])
                        if kwargs['drill_para'] == 'epcam_default':
                            self.para['units'] = 'inch'
                            self.para['zeroes'] = 'none'
                            self.para['nf1'] = "2"
                            self.para['nf2'] = "4"
                            self.para['tool_units'] = 'mm'
                            self.para['separator'] = 'nl'
                        elif kwargs['drill_para'] == 'from_dms':
                            self.para['units']=layer_e2.units_g.values[0].lower()
                            self.para['zeroes']=layer_e2.zeroes_omitted_g.values[0].lower()
                            self.para['nf1'] = int(layer_e2.number_format_A_g.values[0])
                            self.para['nf2'] = int(layer_e2.number_format_B_g.values[0])
                            #g软件的tool_units没有mils选项
                            if layer_e2.tool_units_g.values[0].lower() == 'mils':
                                self.para['tool_units'] = 'inch'
                            else:
                                self.para['tool_units'] = layer_e2.tool_units_g.values[0].lower()

                    self.para['separator']='nl'
                else:
                    print("我不是孔Excellon2!")

                Print.print_with_delimiter("结束定位")
            except:
                print("有异常啊！")


        trans_COM = 'COM input_manual_set,'
        trans_COM += 'path={},job={},step={},format={},data_type={},units={},coordinates={},zeroes={},'.format(
            self.para['path'].replace("\\","/"),
            self.para['job'],
            self.para['step'],
            self.para['format'],
            self.para['data_type'],
            self.para['units'],
            self.para['coordinates'],
            self.para['zeroes'])
        trans_COM += 'nf1={},nf2={},decimal={},separator={},tool_units={},layer={},wheel={},wheel_template={},'.format(
            self.para['nf1'],
            self.para['nf2'],
            self.para['decimal'],
            self.para['separator'],
            self.para['tool_units'],
            self.para['layer'],
            self.para['wheel'],
            self.para['wheel_template'])
        trans_COM += 'nf_comp={},multiplier={},text_line_width={},signed_coords={},break_sr={},drill_only={},'.format(
            self.para['nf_comp'],
            self.para['multiplier'],
            self.para['text_line_width'],
            self.para['signed_coords'],
            self.para['break_sr'],
            self.para['drill_only'])
        trans_COM += 'merge_by_rule={},threshold={},resolution={}'.format(
            self.para['merge_by_rule'],
            self.para['threshold'],
            self.para['resolution'])



        cmd_list1 = [
            'COM input_manual_reset',
            trans_COM,
            ('COM input_manual,script_path={}'.format(''))
        ]


        for cmd in cmd_list1:
            print(cmd)
            ret = self.g.exec_cmd(cmd)
            if ret != 0:
                print('inner error')
                return False
        return True


class Compress():


    def uncompress_z(self,file_full_name):
        # command = r'gzip.exe -d C:\cc\else\test\features.Z'
        #需要设置环境变量。需要win32gnu.dll
        command=r'gzip.exe -d {}'.format(file_full_name)
        print(command)
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,stderr=subprocess.STDOUT, shell=True)
        # self.process.stdin.flush()
        line = self.process.stdout.readline()
        ret = (line.decode().strip())
        print(ret)
        return "uncompress finish!"


def getFlist(path):
    for root, dirs, files in os.walk(path):
        print('root_dir:', root)  #当前路径
        print('sub_dirs:', dirs)   #子文件夹
        print('files:', files)     #文件名称，返回list类型
    return files



if __name__ == '__main__':
    from config import RunConfig
    g = G(RunConfig.gateway_path)

    #删除所有料号
    # g.clean_g_all_pre_get_job_list(r'//vmware-host/Shared Folders/share/job_list.txt')
    # g.clean_g_all_do_clean(r'C:\cc\share\job_list.txt')
    g.import_odb_folder(r'Z:/share/temp_502_1666269720/g/500a001w1-r.g')
    # g.import_odb_folder(r'')
