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

from config_ep.epcam_cc_method import MyInput

class TestInputGerber274X:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input'))
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

        assert job_id == 511



