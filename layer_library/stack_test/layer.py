from __future__ import print_function, division, absolute_import

from builtins import super
import logging

from layerstack.args import Arg, Kwarg
from layerstack.layer import ModelLayerBase

logger = logging.getLogger('ditto.layers.Stack_Test')


class Stack_Test(ModelLayerBase):
    name = "Stack_test"
    desc = "Test Layer for Stack developement"
    model_type = 1

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_1', description='test_arg_1', parser=None,
                            choices=None, nargs=None))
        arg_list.append(Arg('arg_2', description='test_arg_2', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['kwarg_1'] = Kwarg(default='kwarg_1', description='test_kwarg_1',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['kwarg_2'] = Kwarg(default=None, description='test_kwarg_2',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        print(args)
        print(kwargs.items())
        return model


if __name__ == '__main__':
    # Arguments:
    #     - log_format (str) - set this to override the format of the default
    #           console logging output
    #
    Stack_Test.main()
