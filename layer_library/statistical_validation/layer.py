from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID
import subprocess
import os

from layerstack.args import Arg, Kwarg
from ditto.dittolayers import DiTToLayerBase

logger = logging.getLogger('layerstack.layers.Statistical_Validation')


def subprocess_cmd(command):
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print(proc_stdout)

class Statistical_Validation(DiTToLayerBase):
    name = "statistical_validation"
    uuid = UUID("f698017d-3d92-4a01-8a92-9a64882815fa")
    version = '0.1.0'
    desc = "Run R scripts that create statisical validation histograms"

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        kwarg_dict = super().kwargs()
        kwarg_dict['input_folder'] = Kwarg(default=None, description='path to input folder where file metrics.csv is located',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        kwarg_dict['output_folder'] = Kwarg(default=None, description='path to output folder where report cards and histograms are put',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['output_name'] = Kwarg(default=None, description='Name of the metrics set being used',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        kwarg_dict['rscript_folder'] = Kwarg(default=None, description='Location of smartdsR-analysis-lite folder',
                                         parser=None, choices=None,
                                         nargs=None, action=None)

        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        if 'input_folder' in kwargs:
            input_folder = os.path.abspath(kwargs['input_folder'])
        else:
            raise ValueError('no input provided')
        
        if 'output_folder' in kwargs:
            output_folder = os.path.abspath(kwargs['output_folder'])
        else:
            output_folder='.'
        if 'output_name' in kwargs:
            output_name = kwargs['output_name']
        else:
            output_name = 'default'
        if 'rscript_folder' in kwargs:
            rscript_folder = kwargs['rscript_folder']
        else:
            raise ValueError('no smartdsR location provided')
        partitioned_file = 'partitioned_generation.R'
        non_partitioned_file = 'non_partitioned_generation.R'
        partitioned_command = 'module purge; module load conda; cd {smartdsR}; Rscript {rscript} {input} {output} {name}'.format(smartdsR=rscript_folder, rscript=partitioned_file, input=input_folder, output=output_folder, name=output_name)
        non_partitioned_command = 'module purge; module load conda; cd {smartdsR}; Rscript {rscript} {input} {output} {name}'.format(smartdsR=rscript_folder, rscript=non_partitioned_file, input=input_folder, output=output_folder, name=output_name)
        subprocess_cmd(non_partitioned_command)
        subprocess_cmd(partitioned_command)
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    Statistical_Validation.main()

    
