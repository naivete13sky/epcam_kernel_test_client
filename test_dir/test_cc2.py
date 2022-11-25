import pytest

# 输出参数组合太多啦，这里是通过参数化设置导出参数。这里使用python内置的namedtuple方法来存放参数
from collections import namedtuple
GerberOutputPara = namedtuple('GerberOutputPara',
                              ['resize', 'angle', 'scalingX', 'scalingY','mirror','rotate','scale','cw',
                               'mirrorpointX','mirrorpointY','rotatepointX','rotatepointY',
                               'scalepointX','scalepointY','mirrorX','mirrorY','numberFormatL','numberFormatR',
                               'zeros','unit'])
# 设置默认参数
GerberOutputPara.__new__.__defaults__ = (0, 0,1,1,False,False,False,False,
                                         0,0,0,0,
                                         0,0,False,False,2,4,
                                         2,0)
gerber_output_paras_to_test = (
    GerberOutputPara(0, 0,1,1,False,False,False,False,
                                         0,0,0,0,
                                         0,0,False,False,2,4,
                                         2,0),
    GerberOutputPara(numberFormatR=6),
    GerberOutputPara(numberFormatL=3),
)

def id_func(fixture_value):
    """A function for generating ids."""
    p = fixture_value
    return '''GerberOutputPara({},{},{},{},{},{},{},{},
    {},{},{},{},
    {},{},{},{},{},{},
    {},{})'''.format(p.resize,p.angle,p.scalingX,p.scalingY,p.mirror,p.rotate,p.scale,p.cw,
                     p.mirrorpointX, p.mirrorpointY, p.rotatepointX, p.rotatepointY,
                     p.scalepointX, p.scalepointY, p.mirrorX, p.mirrorY, p.numberFormatL, p.numberFormatR,
                     p.zeros, p.unit)

@pytest.fixture(params=gerber_output_paras_to_test, ids=id_func)
def para_gerber_output(request):
    """Using a function (id_func) to generate ids."""
    return request.param

def test_add_c(para_gerber_output):
    """Use fixture with generated ids."""
    print(para_gerber_output)
    assert 1 == 1
