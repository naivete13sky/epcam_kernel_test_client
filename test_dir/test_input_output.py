import pytest,os, time,json,shutil,sys
from config import RunConfig
from cc.cc_method import GetTestData,DMS,Print,getFlist
from config_ep.epcam_cc_method import MyInput,MyOutput
from epcam_api import Input, GUI
from epcam_api.Action import Information

@pytest.mark.input_output
class TestInputOutputBasicGerber274X:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input_Output'))
    def test_input_output_gerber274x(self,job_id,prepare_test_job_clean_g):
        '''本用例测试Gerber274X（包括Excellon2）的导入与导出功能'''

        g = RunConfig.driver_g#拿到G软件

        data = {}#存放比对结果信息
        vs_time_g = str(int(time.time()))#比对时间
        data["vs_time_g"] = vs_time_g#比对时间存入字典
        data["job_id"] = job_id

        # 取到临时目录
        temp_path = RunConfig.temp_path_base + "_" + str(job_id) + "_" + vs_time_g
        temp_gerber_path = os.path.join(temp_path, 'gerber')
        temp_ep_path = os.path.join(temp_path, 'ep')
        temp_g_path = os.path.join(temp_path, 'g')

        # ----------悦谱转图。先下载并解压原始gerber文件,拿到解压后的文件夹名称，此名称加上_ep就是我们要的名称。然后转图。-------------
        job_ep = DMS().get_file_from_dms_db(temp_path, job_id, field='file_compressed', decompress='rar')
        MyInput(folder_path = os.path.join(temp_gerber_path,os.listdir(temp_gerber_path)[0].lower()),
                job = job_ep,step = r'orig',job_id = job_id,save_path = temp_ep_path)
        all_layers_list_job_ep = Information.get_layers(job_ep)

        # --------------------------------下载G转图tgz，并解压好，获取到文件夹名称，作为g料号名称-------------------------------
        job_g = DMS().get_file_from_dms_db(temp_path, job_id, field='file_odb_g', decompress='tgz')
        Input.open_job(job_g, temp_g_path)#用悦谱CAM打开料号
        all_layers_list_job_g = Information.get_layers(job_g)

        # ----------------------------------------开始比图：G与EP---------------------------------------------------------
        print('比图--G转图VS悦谱转图'.center(190,'-'))
        job_g_remote_path = r'\\vmware-host\Shared Folders\share/{}/g/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, job_g)
        job_ep_remote_path = r'\\vmware-host\Shared Folders\share/{}/ep/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, job_ep)
        # 导入要比图的资料
        g.import_odb_folder(job_g_remote_path)
        g.import_odb_folder(job_ep_remote_path)
        r = g.layer_compare_dms(job_id = job_id, vs_time_g = vs_time_g, temp_path = temp_path,
                            job1 = job_g, all_layers_list_job1 = all_layers_list_job_g, job2 = job_ep, all_layers_list_job2 = all_layers_list_job_ep)
        data["all_result_g"] = r['all_result_g']
        data["all_result"] = r['all_result']
        data['g_vs_total_result_flag'] = r['g_vs_total_result_flag']
        assert len(all_layers_list_job_g) == len(r['all_result_g'])

        # ----------------------------------------开始测试输出gerber功能---------------------------------------------------
        MyOutput(temp_path = temp_path, job = job_ep, job_id = job_id)


        # ----------------------------------------开始用G软件input--------------------------------------------------------
        ep_out_put_gerber_folder = os.path.join(temp_path, r'output_gerber', job_ep, r'orig')
        job_g2 = os.listdir(temp_gerber_path)[0].lower() + '_g2'  # epcam输出gerber，再用g软件input。
        step = 'orig'
        file_path = os.path.join(temp_path, ep_out_put_gerber_folder)
        gerberList = getFlist(file_path)
        print(gerberList)
        g_temp_path = r'//vmware-host/Shared Folders/share/temp_{}_{}'.format(job_id, vs_time_g)
        gerberList_path = []
        for each in gerberList:
            gerberList_path.append(os.path.join(g_temp_path, r'output_gerber', job_ep, r'orig', each))
        print(gerberList_path)

        temp_out_put_gerber_g_input_path = os.path.join(temp_path, 'g2')
        if os.path.exists(temp_out_put_gerber_g_input_path):
            shutil.rmtree(temp_out_put_gerber_g_input_path)
        os.mkdir(temp_out_put_gerber_g_input_path)
        out_path = temp_out_put_gerber_g_input_path

        g.g_Gerber2Odb2_no_django(job_g2, step, gerberList_path, out_path, job_id, drill_para='epcam_default')
        # 输出tgz到指定目录
        g.g_export(job_g2, os.path.join(g_temp_path, r'g2'))

        # ----------------------------------------开始用G软件比图，g1和g2--------------------------------------------------------
        # 再导入一个标准G转图，加个后缀1。
        job_g1 = job_g + "1"
        g.import_odb_folder(job_g_remote_path, job_name=job_g1)
        g1_compare_result_folder = 'g1_compare_result'
        temp_g1_compare_result_path = os.path.join(temp_path, g1_compare_result_folder)
        if not os.path.exists(temp_g1_compare_result_path):
            os.mkdir(temp_g1_compare_result_path)

        #校正孔用
        temp_path_local_info1 = os.path.join(temp_path, 'info1')
        if not os.path.exists(temp_path_local_info1):
            os.mkdir(temp_path_local_info1)
        temp_path_local_info2 = os.path.join(temp_path, 'info2')
        if not os.path.exists(temp_path_local_info2):
            os.mkdir(temp_path_local_info2)

        # 以G1转图为主来比对
        # G打开要比图的2个料号g1和g2。g1就是原始的G转图，g2是悦谱输出的gerber又input得到的
        r = g.layer_compare_dms(job_id=job_id, vs_time_g=vs_time_g, temp_path=temp_path,
                                job1=job_g1, all_layers_list_job1=all_layers_list_job_g, job2=job_g2,
                                all_layers_list_job2=all_layers_list_job_ep,adjust_position=True)
        data["all_result_g1"] = r['all_result_g']
        data["all_result"] = r['all_result']
        data['g1_vs_total_result_flag'] = r['g_vs_total_result_flag']
        Print.print_with_delimiter("断言--看一下G1转图中的层是不是都有比对结果")
        assert len(all_layers_list_job_g) == len(r['all_result_g'])


        # ----------------------------------------开始验证结果--------------------------------------------------------

        Print.print_with_delimiter('比对结果信息展示--开始')
        if data['g_vs_total_result_flag'] == True:
            print("恭喜您！料号导入比对通过！")
        if data['g_vs_total_result_flag'] == False:
            print("Sorry！料号导入比对未通过，请人工检查！")
        Print.print_with_delimiter('分割线', sign='-')
        print('G转图的层：', data["all_result_g"])
        Print.print_with_delimiter('分割线', sign='-')
        print('所有层：', data["all_result"])
        Print.print_with_delimiter('分割线', sign='-')
        print('G1转图的层：', data["all_result_g1"])
        Print.print_with_delimiter('比对结果信息展示--结束')

        Print.print_with_delimiter("断言--开始")
        assert data['g_vs_total_result_flag'] == True
        for key in data['all_result_g']:
            assert data['all_result_g'][key] == "正常"

        assert data['g1_vs_total_result_flag'] == True
        for key in data['all_result_g1']:
            assert data['all_result_g1'][key] == "正常"
        Print.print_with_delimiter("断言--结束")


@pytest.mark.output
class TestOutputGerber274X:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Output'))
    def test_output_gerber274x(self, job_id, prepare_test_job_clean_g):
        '''本用例测试Gerber274X（包括Excellon2）的导入与导出功能'''

        g = RunConfig.driver_g  # 拿到G软件

        data = {}  # 存放比对结果信息
        vs_time_g = str(int(time.time()))  # 比对时间
        data["vs_time_g"] = vs_time_g  # 比对时间存入字典
        data["job_id"] = job_id

        # 取到临时目录
        temp_path = RunConfig.temp_path_base + "_" + str(job_id) + "_" + vs_time_g
        temp_gerber_path = os.path.join(temp_path, 'gerber')
        temp_ep_path = os.path.join(temp_path, 'ep')
        temp_g_path = os.path.join(temp_path, 'g')
