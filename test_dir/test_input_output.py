import os, time,json,shutil,sys
from cc import cc_method
from cc.cc_method import GetTestData,DMS,Print,getFlist
import pytest
from config_g.g_cc_method import G
from config import RunConfig
from pathlib import Path

from epcam_api import Input, GUI,Output,BASE
from epcam_api.Action import Information
from epcam_api.Edition import Matrix,Job


from config_ep.epcam import epcam

from config_ep.epcam_cc_method import MyInput

class TestInputOutputGerber274X:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input_Output'))
    def test_input_output_gerber274x(self,job_id,prepare_test_job_clean_g):
        '''本用例测试Gerber274X（包括Excellon2）的导入与导出功能'''

        g = RunConfig.driver_g#拿到G软件

        data = {}#存放当前测试料号的每一层的比对结果。
        g_vs_total_result_flag = True  # True表示最新一次G比对通过
        vs_time_g = str(int(time.time()))#比对时间
        data["vs_time_g"] = vs_time_g#比对时间存入字典
        data["job_id"] = job_id

        # 取到临时目录
        temp_path = RunConfig.temp_path_base + "_" + str(job_id) + "_" + vs_time_g
        temp_gerber_path = os.path.join(temp_path, 'gerber')
        temp_ep_path = os.path.join(temp_path, 'ep')
        temp_g_path = os.path.join(temp_path, 'g')

        # 悦谱转图。先下载并解压原始gerber文件。然后转图。
        DMS().get_file_from_dms_db(temp_path, job_id, field='file_compressed', decompress='rar')
        folder_path = os.path.join(temp_gerber_path,os.listdir(temp_gerber_path)[0].lower())
        job_ep = os.listdir(temp_gerber_path)[0].lower()  + '_ep'
        step = r'orig'
        save_path = temp_ep_path
        MyInput(folder_path, job_ep, step,job_id,save_path=save_path)

        # 获取 job_ep 的层别信息
        print("job_ep:", job_ep)
        all_layers_list_job_ep = Information.get_layers(job_ep)
        if len(all_layers_list_job_ep) == 0:
            g_vs_total_result_flag = False
            print("最新-EP-ODB++打开失败！！！！！")
        else:
            print('悦谱软件tgz中的层信息：', all_layers_list_job_ep)


        # GUI.show_layer(job, "orig", "layer")

        # 下载G转图tgz，并解压好
        DMS().get_file_from_dms_db(temp_path, job_id, field='file_odb_g', decompress='tgz')
        job_g = os.listdir(temp_g_path)[0].lower()
        Input.open_job(job_g, temp_g_path)
        all_layers_list_job_g = Information.get_layers(job_g)
        if len(all_layers_list_job_g) == 0:
            g_vs_total_result_flag = False
            print("G-ODB++打开失败！！！！！")
        else:
            print('G软件tgz中的层信息：', all_layers_list_job_g)

        # ----------------------------------------开始比图：G与EP--------------------------------------------------------
        print('比图--G转图VS悦谱转图'.center(190,'-'))
        job_g_remote_path = r'\\vmware-host\Shared Folders\share/{}/g/{}'.format('temp' + "_" + str(job_id) + "_" + vs_time_g, job_g)
        job_ep_remote_path = r'\\vmware-host\Shared Folders\share/{}/ep/{}'.format('temp' + "_" + str(job_id) + "_" + vs_time_g, job_ep)


        # 读取配置文件
        with open(r'C:\cc\python\epwork\epcam_kernel_test_client\config_g\config.json', encoding='utf-8') as f:
            cfg = json.load(f)
        tol = cfg['job_manage']['vs']['vs_tol_g']
        print("tol:", tol)
        map_layer_res = 200
        # 导入要比图的资料
        g.import_odb_folder(job_g_remote_path)
        g.import_odb_folder(job_ep_remote_path)
        # G打开要比图的2个料号
        g.layer_compare_g_open_2_job(job1=job_g, step='orig', job2=job_ep)
        g_compare_result_folder = 'g_compare_result'
        temp_g_compare_result_path = os.path.join(temp_path, g_compare_result_folder)
        if not os.path.exists(temp_g_compare_result_path):
            os.mkdir(temp_g_compare_result_path)
        temp_path_remote_g_compare_result = r'//vmware-host/Shared Folders/share/{}/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, g_compare_result_folder)
        temp_path_local_g_compare_result = os.path.join(temp_path, g_compare_result_folder)

        all_result_g = {}
        for layer in all_layers_list_job_g:
            if layer in all_layers_list_job_ep:
                map_layer = layer + '-com'
                result = g.layer_compare_one_layer(job1=job_g, step1='orig', layer1=layer, job2=job_ep,
                                                     step2='orig', layer2=layer, layer2_ext='_copy', tol=tol,
                                                     map_layer=map_layer, map_layer_res=map_layer_res,
                                                     result_path_remote=temp_path_remote_g_compare_result,
                                                     result_path_local=temp_path_local_g_compare_result,
                                                     temp_path=temp_path)
                all_result_g[layer] = result
                if result != "正常":
                    g_vs_total_result_flag = False
            else:
                print("悦谱转图中没有此层")
        g.save_job(job_g)
        g.save_job(job_ep)
        g.layer_compare_close_job(job1=job_g, job2=job_ep)


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

        data["all_result_g"] = all_result_g
        data["all_result"] = all_result
        assert len(all_layers_list_job_g) == len(all_result_g)

        # ----------------------------------------开始测试输出gerber功能--------------------------------------------------------
        g1_vs_total_result_flag = True
        out_put = []
        job_result = {}
        out_json = ''

        # 建立output_gerber文件夹，里面用来放epcam输出的gerber。
        temp_out_put_gerber_path = os.path.join(temp_path, 'output_gerber')
        if os.path.exists(temp_out_put_gerber_path):
            shutil.rmtree(temp_out_put_gerber_path)
        os.mkdir(temp_out_put_gerber_path)

        # 设置导出参数
        with open(RunConfig.config_ep_output, 'r') as cfg:
            infos_ = json.load(cfg)['paras']  # (json格式数据)字符串 转化 为字典
            _type = infos_['type']
            resize = infos_['resize']
            gdsdbu = infos_['gdsdbu']
            angle = infos_['angle']
            scalingX = infos_['scalingX']
            scalingY = infos_['scalingY']
            isReverse = infos_['isReverse']
            mirror = infos_['mirror']
            rotate = infos_['rotate']
            scale = infos_['scale']
            profiletop = infos_['profiletop']
            cw = infos_['cw']
            cutprofile = infos_['cutprofile']
            mirrorpointX = infos_['mirrorpointX']
            mirrorpointY = infos_['mirrorpointY']
            rotatepointX = infos_['rotatepointX']
            rotatepointY = infos_['rotatepointY']
            scalepointX = infos_['scalepointX']
            scalepointY = infos_['scalepointY']
            mirrordirection = infos_['mirrordirection']
            cut_polygon = infos_['cut_polygon']
            mirrorX = infos_['mirrorX']
            mirrorY = infos_['mirrorY']


        layers = Information.get_layers(job_ep)
        steps = Information.get_steps(job_ep)
        file_path = os.path.join(temp_out_put_gerber_path,job_ep)
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
                            DMS().get_job_layer_drill_from_dms_db_pandas_one_job(job_id)['layer']]
            rout_layers = [each.lower() for each in
                           DMS().get_job_layer_rout_from_dms_db_pandas_one_job(job_id)['layer']]
            print("drill_layers:", drill_layers)

            #common_layers_list是非孔类型的文件
            common_layers_list = []
            layer_result = {}

            for each_layer in layers:
                if each_layer not in drill_layers:
                    common_layers_list.append(each_layer)

            # 输出gerber
            for layer in common_layers_list:
                layer_stime = (int(time.time()))
                filename = os.path.join(step_path,layer)# 当前step下的每个层的gerber文件路径
                ret = Output.save_gerber(job_ep, step, layer, filename, resize, angle, scalingX,scalingY,mirror, rotate, scale,cw,
                                         mirrorpointX,mirrorpointY,rotatepointX,rotatepointY, scalepointX, scalepointY, mirrorX, mirrorY)
                layer_etime = (int(time.time()))
                layer_time = layer_etime - layer_stime
                value[layer] = layer_time

            # 输出excellon2
            for drill_layer in drill_layers:

                layer_stime = (int(time.time()))

                drill_out_path = os.path.join(step_path,drill_layer)

                if drill_layer in rout_layers:
                    Print.print_with_delimiter("我是rout")
                    Matrix.change_matrix_row(job_ep, drill_layer, 'board', 'rout', drill_layer)
                    drill_info = Output.save_rout(job_ep, step, drill_layer, drill_out_path, number_format_l=2, number_format_r=4, zeroes=2, unit=0,
                                                  tool_unit=1, x_scale=1, y_scale=1, x_anchor=0, y_anchor=0, break_arcs = False)
                else:
                    Print.print_with_delimiter("我是drill啊")
                    Matrix.change_matrix_row(job_ep, drill_layer, 'board', 'drill', drill_layer)
                    # drill_info = Output.save_drill(job_ep, step, drill_layer, drill_out_path)
                    drill_info = BASE.drill2file(job_ep, step, drill_layer,drill_out_path,isMetric = False,number_format_l=2,number_format_r=4,
                    zeroes=2,unit=0,x_scale=1,y_scale=1,x_anchor=0,y_anchor=0, manufacator = '', tools_order = [])
                    print("drill_info:",drill_info)
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
        Job.close_job(job_ep)

        Print.print_with_delimiter('输出gerber完成')

        # ----------------------------------------开始测试输出gerber功能--------------------------------------------------------



        # ----------------------------------------开始验证结果--------------------------------------------------------

        Print.print_with_delimiter('比对结果信息展示--开始')
        if g_vs_total_result_flag == True:
            print("恭喜您！料号导入比对通过！")
        if g_vs_total_result_flag == False:
            print("Sorry！料号导入比对未通过，请人工检查！")
        Print.print_with_delimiter('分割线', sign='-')
        print('G转图的层：', all_result_g)
        Print.print_with_delimiter('分割线', sign='-')
        print('所有层：', all_result)
        Print.print_with_delimiter('分割线', sign='-')
        # print('G1转图的层：', all_result_g1)
        Print.print_with_delimiter('比对结果信息展示--结束')

        Print.print_with_delimiter("断言--开始")
        assert g_vs_total_result_flag == True
        for key in all_result_g:
            assert all_result_g[key] == "正常"

        # assert g1_vs_total_result_flag == True
        # for key in all_result_g1:
        #     assert all_result_g1[key] == "正常"
        Print.print_with_delimiter("断言--结束")



