


from sqlalchemy import create_engine
import pandas as pd






def my_print():
    # '^'字符表示中心
    print('{0:*^198}'.format('MENU'))
    print('{0:*^198}'.format('你好啊，你在哪里啊啊发发！'))
    print('MENU'.center(198, '*'))

class DMS(object):

    def get_job_layer_info_from_dms(self,job_id):

        sql = '''SELECT a.* from layer a where a.job_id = {}'''.format(job_id)
        engine = create_engine('postgresql+psycopg2://readonly:123456@10.97.80.119/dms')
        pd_job_layer_info = pd.read_sql(sql=sql, con=engine)
        self.pd_job_layer_info = pd_job_layer_info
        return pd_job_layer_info



def pp():
    pass
    print('abc')





if __name__ == '__main__':
    pass
    # cc = DMS()
    # df = cc.get_job_layer_info_from_dms(997)
    # data = df[(df['layer'] == 'Znn-2786693_.drl')]
    # print(data)
    # data1 =  df[(df['layer'] == 'Znn-2786693_.drl')]['units_ep'].values[0]
    # print(data1)
    # print(data1)


