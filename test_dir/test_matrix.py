import os, time,json,shutil,sys
from cc import cc_method
from cc.cc_method import GetTestData,DMS,Print,getFlist
import pytest
from config_g.g_cc_method import Asw
from config import RunConfig
from pathlib import Path

from epcam_api import Input, GUI
from epcam_api.Action import Information
from epcam_api.Edition import Matrix


from config_ep.epcam import epcam


class TestMatrixLayerCopy:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Matrix'))
    def test_matrix_layer_copy_one_layer(self,job_id,prepare_test_job_clean_g):
        Print.print_with_delimiter("G软件VS开始啦！")
        asw = Asw(RunConfig.gateway_path)#拿到G软件
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

        # 下载G转图tgz，并解压好
        DMS().get_file_from_dms_db(temp_path, job_id, field='file_odb_g', decompress='tgz')
        job = os.listdir(temp_g_path)[0]


        job_parent_path = temp_g_path

        Input.open_job(job, job_parent_path)
        # GUI.show_layer("eni40021", "orig", "top")

        all_layers_list_pre = Information.get_layers(job)
        print('all_layers_list_pre:',all_layers_list_pre)

        result_matrix_copy_layer = Matrix.copy_layer(job, all_layers_list_pre[0])
        print('result_matrix_copy_layer:',result_matrix_copy_layer)

        all_layers_list_post = Information.get_layers(job)
        print('all_layers_list_post:', all_layers_list_post)

        #比图前需要保存料号
        data = {
            'func': 'JOB_SAVE',
            'paras': [{'job': job}]
        }
        epcam.process(json.dumps(data))

        Print.print_with_delimiter('比图操作--开始')
        job_path = r'\\vmware-host\Shared Folders\share/{}/g/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, job)

        # 读取配置文件
        with open(r'C:\cc\python\epwork\epcam_kernel_test_client\config_g\config.json', encoding='utf-8') as f:
            cfg = json.load(f)
        tol = cfg['job_manage']['vs']['vs_tol_g']
        print("tol:", tol)
        map_layer_res = 200
        print("job1:", job, "job2:", job)

        # 导入要比图的资料
        asw.import_odb_folder(job_path)
        # G打开要比图的2个料号,当前情况就是一个料号中的2个层在做比对
        job = job.lower()
        asw.layer_compare_g_open_2_job(job1=job, step='orig', job2=job)
        g_compare_result_folder = 'g_compare_result'
        temp_g_compare_result_path = os.path.join(temp_path, g_compare_result_folder)
        if not os.path.exists(temp_g_compare_result_path):
            os.mkdir(temp_g_compare_result_path)
        temp_path_remote_g_compare_result = r'//vmware-host/Shared Folders/share/{}/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, g_compare_result_folder)
        temp_path_local_g_compare_result = os.path.join(temp_path, g_compare_result_folder)

        map_layer = all_layers_list_pre[0] + '-com'
        result = asw.layer_compare_one_layer(job1=job, step1='orig', layer1=all_layers_list_pre[0], job2=job,
                                             step2='orig', layer2=all_layers_list_post[-1], layer2_ext='_copy', tol=tol,
                                             map_layer=map_layer, map_layer_res=map_layer_res,
                                             result_path_remote=temp_path_remote_g_compare_result,
                                             result_path_local=temp_path_local_g_compare_result,
                                             temp_path=temp_path)

        if result != "正常":
            g_vs_total_result_flag = False
        print('compare result:',result)

        Print.print_with_delimiter('比图操作--完成')




        Print.print_with_delimiter('断言--开始')
        assert all_layers_list_pre[0] + '+1' == all_layers_list_post[-1]
        Print.print_with_delimiter('断言--完成')

