import os, time,json,shutil,sys
from cc import cc_method
from cc.cc_method import GetTestData,DMS,Print,getFlist
import pytest
from config_g.g_cc_method import Asw
from config import RunConfig
from pathlib import Path

from epcam_api import Input, GUI



@pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input'))
def test_gerber_to_odb_ep_local_convert_drill_none_2_4(job_id,prepare_test_job_clean_g):
    Print.print_with_delimiter("G软件VS开始啦！")
    asw = Asw(RunConfig.gateway_path)#拿到G软件
    data = {}#存放当前测试料号的每一层的比对结果。
    g_vs_total_result_flag = True  # True表示最新一次G比对通过
    vs_time_g = str(int(time.time()))#比对时间
    data["vs_time_g"] = vs_time_g#比对时间存入字典
    data["job_id"] = job_id

    Input.open_job("eni40021", r"C:\job\test\odb")
    GUI.show_layer("eni40021", "orig", "top")

    assert 1 == 1


