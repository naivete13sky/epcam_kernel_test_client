import os, time,json,shutil,sys
from cc import cc_method
from cc.cc_method import GetTestData,DMS,Print,getFlist
import pytest
from config_g.g_cc_method import G
from config import RunConfig
from pathlib import Path

from epcam_api import Input, GUI
from epcam_api.Action import Information
from epcam_api.Edition import Matrix


from config_ep.epcam import epcam

from config_ep.epcam_cc_method import MyInput

class TestInputOutputGerber274X:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input_Output'))
    def test_input_output_gerber274x(self,job_id,prepare_test_job_clean_g):
        '''本用例测试Gerber274X（包括Excellon2）的导入与导出功能'''

        Print.print_with_delimiter("G软件VS开始啦！")
        # g = G(RunConfig.gateway_path)#拿到G软件
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

        #开始比图啦!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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

        Print.print_with_delimiter("断言--看一下G转图中的层是不是都有比对结果")
        assert len(all_layers_list_job_g) == len(all_result_g)

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



