import pytest,os, time,json,shutil,sys
from config import RunConfig
from cc.cc_method import GetTestData,DMS,Print,getFlist
from config_ep.epcam_cc_method import MyInput,MyOutput
from config_g.g_cc_method import GInput
from epkernel import Input, GUI
from epkernel.Action import Information


@pytest.mark.input_output
class TestInputOutputBasicGerber274X:
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Input_Output'))
    def test_input_output_gerber274x(self,job_id,prepare_test_job_clean_g):
        '''
        本用例测试Gerber274X（包括Excellon2）的导入与导出功能
        fuck
        fuck
        fuck
        '''

        g = RunConfig.driver_g#拿到G软件

        data = {}#存放比对结果信息
        vs_time_g = str(int(time.time()))#比对时间
        data["vs_time_g"] = vs_time_g#比对时间存入字典
        data["job_id"] = job_id

        # 取到临时目录
        temp_path = RunConfig.temp_path_base + "_" + str(job_id) + "_" + vs_time_g
        temp_gerber_path = os.path.join(temp_path, 'compressed')
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
        customer_para = {}
        customer_para['numberFormatR'] = 6
        MyOutput(temp_path = temp_path, job = job_ep, job_id = job_id,layer_info_from_obj='dms',customer_para = customer_para)


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

        g.gerber_to_odb_batch(job_g2, step, gerberList_path, out_path, job_id, drill_para='epcam_default')
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
        temp_compressed_path = os.path.join(temp_path, 'compressed')
        temp_ep_path = os.path.join(temp_path, 'ep')
        temp_g_path = os.path.join(temp_path, 'g')

        # --------------------------------下载测试资料--tgz文件，并解压完，文件夹名称作为料号名称-------------------------------
        job = DMS().get_file_from_dms_db(temp_path, job_id, field='file_compressed', decompress='tgz')

        # 用悦谱CAM打开料号
        Input.open_job(job, temp_compressed_path)  # 用悦谱CAM打开料号
        all_layers_list_job = Information.get_layers(job)
        print('all_layer_list_job:',all_layers_list_job)
        #区分层别类型
        drill_layers = list(map(lambda x: x['name'], Information.get_layer_info(job, context='board', type=['drill'])))
        rout_layers = list(map(lambda x: x['name'], Information.get_layer_info(job, context='board', type=['rout'])))
        print("fuckyou1124")
        print('drill_layers:',drill_layers)
        print('rout_layers:',rout_layers)
        common_layers = []
        for each in all_layers_list_job:
            if each not in drill_layers:
                common_layers.append(each)
        print('common_layers:', common_layers)


        #导出
        customer_para = {}
        customer_para['numberFormatR'] = 6


        MyOutput(temp_path=temp_path, job=job, job_id=job_id,layer_info_from_obj='job_tgz_file',customer_para = customer_para)


        # ----------------------------------------开始用G软件input--------------------------------------------------------
        ep_out_put_gerber_folder = os.path.join(temp_path, r'output_gerber', job, r'orig')
        job_g2 = os.listdir(temp_compressed_path)[0].lower() + '_g2'  # epcam输出gerber，再用g软件input。
        step = 'orig'
        file_path = os.path.join(temp_path, ep_out_put_gerber_folder)
        gerberList = getFlist(file_path)
        print(gerberList)
        g_temp_path = r'//vmware-host/Shared Folders/share/temp_{}_{}'.format(job_id, vs_time_g)
        gerberList_path = []
        for each in gerberList:
            gerberList_path.append(os.path.join(g_temp_path, r'output_gerber', job, r'orig', each))
        print(gerberList_path)

        temp_out_put_gerber_g_input_path = os.path.join(temp_path, 'g2')
        if os.path.exists(temp_out_put_gerber_g_input_path):
            shutil.rmtree(temp_out_put_gerber_g_input_path)
        os.mkdir(temp_out_put_gerber_g_input_path)
        out_path = temp_out_put_gerber_g_input_path



        GInput(job=job_g2, step=step, gerberList_path=gerberList_path, out_path=out_path, job_id=job_id,
               drill_para='epcam_default',layer_info_from_obj='job_tgz_file',
               layer_list=all_layers_list_job,gerber_layer_list=common_layers,drill_layer_list=drill_layers,rout_layer_list=rout_layers)
        # 输出tgz到指定目录
        g.g_export(job_g2, os.path.join(g_temp_path, r'g2'))

        # ----------------------------------------开始用G软件比图，g与g2---------------------------------------------------
        # 先导入
        job_g_remote_path = r'\\vmware-host\Shared Folders\share/{}/compressed/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, job)
        # 导入要比图的资料
        g.import_odb_folder(job_g_remote_path)

        # 校正孔用
        temp_path_local_info1 = os.path.join(temp_path, 'info1')
        if not os.path.exists(temp_path_local_info1):
            os.mkdir(temp_path_local_info1)
        temp_path_local_info2 = os.path.join(temp_path, 'info2')
        if not os.path.exists(temp_path_local_info2):
            os.mkdir(temp_path_local_info2)

        # 以G转图为主来比对
        # G打开要比图的2个料号g和g2。g就是原始，g2是悦谱输出的gerber又input得到的
        r = g.layer_compare_dms(job_id=job_id, vs_time_g=vs_time_g, temp_path=temp_path,
                                job1=job, all_layers_list_job1=all_layers_list_job, job2=job_g2,
                                all_layers_list_job2=all_layers_list_job, adjust_position=True)
        data["all_result_g"] = r['all_result_g']

        data['g_vs_total_result_flag'] = r['g_vs_total_result_flag']
        Print.print_with_delimiter("断言--看一下G转图中的层是不是都有比对结果")
        assert len(all_layers_list_job) == len(r['all_result_g'])

        # ----------------------------------------开始验证结果--------------------------------------------------------
        Print.print_with_delimiter('比对结果信息展示--开始')
        if data['g_vs_total_result_flag'] == True:
            print("恭喜您！料号导入比对通过！")
        if data['g_vs_total_result_flag'] == False:
            print("Sorry！料号导入比对未通过，请人工检查！")
        Print.print_with_delimiter('分割线', sign='-')
        print('G转图的层：', data["all_result_g"])


        Print.print_with_delimiter('比对结果信息展示--结束')

        Print.print_with_delimiter("断言--开始")
        assert data['g_vs_total_result_flag'] == True
        for key in data['all_result_g']:
            assert data['all_result_g'][key] == "正常"

        Print.print_with_delimiter("断言--结束")



# 输出参数组合太多啦，这里是通过参数化设置导出参数。这里使用python内置的namedtuple方法来存放参数
from collections import namedtuple
GerberOutputPara = namedtuple('GerberOutputPara',
                              ['resize', 'angle', 'scalingX', 'scalingY', 'mirror', 'rotate', 'scale', 'cw',
                               'mirrorpointX', 'mirrorpointY', 'rotatepointX', 'rotatepointY',
                               'scalepointX', 'scalepointY', 'mirrorX', 'mirrorY', 'numberFormatL', 'numberFormatR',
                               'zeros', 'unit'])
# 设置默认参数
GerberOutputPara.__new__.__defaults__ = (0, 0, 1, 1, False, False, False, False,
                                         0, 0, 0, 0,
                                         0, 0, False, False, 2, 4,
                                         2, 0)
gerber_output_paras_to_test = (
    GerberOutputPara(0, 0, 1, 1, False, False, False, False,
                     0, 0, 0, 0,
                     0, 0, False, False, 2, 4,
                     2, 0),
    GerberOutputPara(numberFormatR=6),
    GerberOutputPara(numberFormatL=3),
)

def id_func(fixture_value):
    """A function for generating ids."""
    p = fixture_value
    return '''GerberOutputPara({},{},{},{},{},{},{},{},
        {},{},{},{},
        {},{},{},{},{},{},
        {},{})'''.format(p.resize, p.angle, p.scalingX, p.scalingY, p.mirror, p.rotate, p.scale, p.cw,
                         p.mirrorpointX, p.mirrorpointY, p.rotatepointX, p.rotatepointY,
                         p.scalepointX, p.scalepointY, p.mirrorX, p.mirrorY, p.numberFormatL, p.numberFormatR,
                         p.zeros, p.unit)

@pytest.fixture(params=gerber_output_paras_to_test, ids=id_func)
def para_gerber_output(request):
    """Using a function (id_func) to generate ids."""
    return request.param

@pytest.mark.cc
class TestOutputGerber274XParas():
    @pytest.mark.parametrize("job_id", GetTestData().get_job_id('Output'))
    def test_output_gerber274x(self, job_id, prepare_test_job_clean_g,para_gerber_output):
        '''本用例测试Gerber274X（包括Excellon2）的导入与导出功能'''
        print('分割线'.center(192, "-"))
        print(para_gerber_output)

        g = RunConfig.driver_g  # 拿到G软件

        data = {}  # 存放比对结果信息
        vs_time_g = str(int(time.time()))  # 比对时间
        data["vs_time_g"] = vs_time_g  # 比对时间存入字典
        data["job_id"] = job_id

        # 取到临时目录
        temp_path = RunConfig.temp_path_base + "_" + str(job_id) + "_" + vs_time_g
        temp_compressed_path = os.path.join(temp_path, 'compressed')
        temp_ep_path = os.path.join(temp_path, 'ep')
        temp_g_path = os.path.join(temp_path, 'g')

        # --------------------------------下载测试资料--tgz文件，并解压完，文件夹名称作为料号名称-------------------------------
        job = DMS().get_file_from_dms_db(temp_path, job_id, field='file_compressed', decompress='tgz')

        # 用悦谱CAM打开料号
        Input.open_job(job, temp_compressed_path)  # 用悦谱CAM打开料号
        all_layers_list_job = Information.get_layers(job)
        print('all_layer_list_job:', all_layers_list_job)
        # 区分层别类型
        drill_layers = list(map(lambda x: x['name'], Information.get_layer_info(job, context='board', type=['drill'])))
        rout_layers = list(map(lambda x: x['name'], Information.get_layer_info(job, context='board', type=['rout'])))
        print("fuckyou1124")
        print('drill_layers:', drill_layers)
        print('rout_layers:', rout_layers)
        common_layers = []
        for each in all_layers_list_job:
            if each not in drill_layers:
                common_layers.append(each)
        print('common_layers:', common_layers)

        # 导出
        customer_para = {}
        customer_para['numberFormatL'] = para_gerber_output.numberFormatL
        customer_para['numberFormatR'] = para_gerber_output.numberFormatR

        MyOutput(temp_path=temp_path, job=job, job_id=job_id, layer_info_from_obj='job_tgz_file',
                 customer_para=customer_para)

        # ----------------------------------------开始用G软件input--------------------------------------------------------
        ep_out_put_gerber_folder = os.path.join(temp_path, r'output_gerber', job, r'orig')
        job_g2 = os.listdir(temp_compressed_path)[0].lower() + '_g2'  # epcam输出gerber，再用g软件input。
        step = 'orig'
        file_path = os.path.join(temp_path, ep_out_put_gerber_folder)
        gerberList = getFlist(file_path)
        print(gerberList)
        g_temp_path = r'//vmware-host/Shared Folders/share/temp_{}_{}'.format(job_id, vs_time_g)
        gerberList_path = []
        for each in gerberList:
            gerberList_path.append(os.path.join(g_temp_path, r'output_gerber', job, r'orig', each))
        print(gerberList_path)

        temp_out_put_gerber_g_input_path = os.path.join(temp_path, 'g2')
        if os.path.exists(temp_out_put_gerber_g_input_path):
            shutil.rmtree(temp_out_put_gerber_g_input_path)
        os.mkdir(temp_out_put_gerber_g_input_path)
        out_path = temp_out_put_gerber_g_input_path

        GInput(job=job_g2, step=step, gerberList_path=gerberList_path, out_path=out_path, job_id=job_id,
               drill_para='epcam_default', layer_info_from_obj='job_tgz_file',
               layer_list=all_layers_list_job, gerber_layer_list=common_layers, drill_layer_list=drill_layers,
               rout_layer_list=rout_layers)
        # 输出tgz到指定目录
        g.g_export(job_g2, os.path.join(g_temp_path, r'g2'))

        # ----------------------------------------开始用G软件比图，g与g2---------------------------------------------------
        # 先导入
        job_g_remote_path = r'\\vmware-host\Shared Folders\share/{}/compressed/{}'.format(
            'temp' + "_" + str(job_id) + "_" + vs_time_g, job)
        # 导入要比图的资料
        g.import_odb_folder(job_g_remote_path)

        # 校正孔用
        temp_path_local_info1 = os.path.join(temp_path, 'info1')
        if not os.path.exists(temp_path_local_info1):
            os.mkdir(temp_path_local_info1)
        temp_path_local_info2 = os.path.join(temp_path, 'info2')
        if not os.path.exists(temp_path_local_info2):
            os.mkdir(temp_path_local_info2)

        # 以G转图为主来比对
        # G打开要比图的2个料号g和g2。g就是原始，g2是悦谱输出的gerber又input得到的
        r = g.layer_compare_dms(job_id=job_id, vs_time_g=vs_time_g, temp_path=temp_path,
                                job1=job, all_layers_list_job1=all_layers_list_job, job2=job_g2,
                                all_layers_list_job2=all_layers_list_job, adjust_position=True)
        data["all_result_g"] = r['all_result_g']

        data['g_vs_total_result_flag'] = r['g_vs_total_result_flag']
        Print.print_with_delimiter("断言--看一下G转图中的层是不是都有比对结果")
        assert len(all_layers_list_job) == len(r['all_result_g'])

        # ----------------------------------------开始验证结果--------------------------------------------------------
        Print.print_with_delimiter('比对结果信息展示--开始')
        if data['g_vs_total_result_flag'] == True:
            print("恭喜您！料号导入比对通过！")
        if data['g_vs_total_result_flag'] == False:
            print("Sorry！料号导入比对未通过，请人工检查！")
        Print.print_with_delimiter('分割线', sign='-')
        print('G转图的层：', data["all_result_g"])

        Print.print_with_delimiter('比对结果信息展示--结束')

        Print.print_with_delimiter("断言--开始")
        assert data['g_vs_total_result_flag'] == True
        for key in data['all_result_g']:
            assert data['all_result_g'][key] == "正常"

        Print.print_with_delimiter("断言--结束")