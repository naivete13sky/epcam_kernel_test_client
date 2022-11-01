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

class TestMatrixLayerCopy:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input'))
    def test_matrix_layer_copy_one_layer(self,job_id,prepare_test_job_clean_g):
        Print.print_with_delimiter("G软件VS开始啦！")
        asw = Asw(RunConfig.gateway_path)#拿到G软件
        data = {}#存放当前测试料号的每一层的比对结果。
        g_vs_total_result_flag = True  # True表示最新一次G比对通过
        vs_time_g = str(int(time.time()))#比对时间
        data["vs_time_g"] = vs_time_g#比对时间存入字典
        data["job_id"] = job_id

        job = 'eni40021'
        job_parent_path = r'C:\job\test\odb'

        Input.open_job(job, job_parent_path)
        # GUI.show_layer("eni40021", "orig", "top")

        all_layers_list_pre = Information.get_layers(job)
        print('all_layers_list_pre:',all_layers_list_pre)

        result_matrix_copy_layer = Matrix.copy_layer(job, all_layers_list_pre[0])
        print('result_matrix_copy_layer:',result_matrix_copy_layer)

        all_layers_list_post = Information.get_layers(job)
        print('all_layers_list_post:', all_layers_list_post)

        Print.print_with_delimiter('开始断言')
        assert all_layers_list_pre[0] + '+1' == all_layers_list_post[-1]
        Print.print_with_delimiter('完成断言')

