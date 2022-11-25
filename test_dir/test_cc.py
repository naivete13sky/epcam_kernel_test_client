import pytest


from collections import namedtuple
Task = namedtuple('Task',['summary','owner','done','id'])
Task.__new__.__defaults__ = (None,None,False,None)
tasks_to_try = (Task('sleep', done=True),
                Task('wake', 'brian'),
                Task('breathe', 'BRIAN', True),
                Task('exercise', 'BrIaN', False))

task_ids = ['Task({},{},{})'.format(t.summary, t.owner, t.done)
            for t in tasks_to_try]


@pytest.fixture(params=tasks_to_try)
def a_task(request):
    return request.param

@pytest.fixture(params=tasks_to_try, ids=task_ids)
def b_task(request):
    return request.param

pytest.mark.test
def test_add_a(a_task):
    pass
    print(a_task)
    assert 1==1


def test_add_b(b_task):
    print(a_task)
    assert 1 == 1

def id_func(fixture_value):
    """A function for generating ids."""
    t = fixture_value
    return 'Task({},{},{})'.format(t.summary, t.owner, t.done)


@pytest.fixture(params=tasks_to_try, ids=id_func)
def c_task(request):
    """Using a function (id_func) to generate ids."""
    return request.param


def test_add_c(c_task):
    """Use fixture with generated ids."""
    print(a_task)
    assert 1 == 1