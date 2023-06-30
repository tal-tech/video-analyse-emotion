#!/usr/bin/env python
# coding: utf-8
import os
import shutil
import subprocess
from backend.utility import g_logger
base_path = os.path.dirname(os.path.realpath(__file__))


# opensmile 
def opensmiler(infile, outfold, config='emobase2010',toolfold=os.path.join(base_path, 'opensmile-2.3.0/'),extension='.txt', max_retry=10):
    '''
    infile: single input file to be extracted
    outfold: where to save the extracted file with the same name
    config: opensmile config file
    toolfold: opensmile tool folder
    extension: ".txt" or ".csv" 
    '''
    # tool and config
    tool = '%sbin/linux_x64_standalone_libstdc6/SMILExtract' %toolfold
    config = '%sconfig/%s.conf' %(toolfold,config)
    
    # get infile and outfile names
    infilename = infile
    outfilename = '%s/%s%s' %(outfold, infile.split('/')[-1].split('.wav')[0], extension)
    cmd = '%s -C %s -I %s -O %s' %(tool,config,infilename,outfilename)
    # execute
    success = False
    retry = 0
    while not success and retry < max_retry:
        if retry > 0:
            g_logger.info("{}重试第{}次".format(infile, retry))

        # if subprocess.call(cmd, shell=True) !=0:
        #     g_logger.error('opensmile extract {} features fail'.format(infile))
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

        success = os.path.exists(outfilename)
        retry += 1
    return outfilename

        
# 批量提取文件夹下所有wav的opensmile特征
def batch_extract(input_wavs, output_path):
    """
    :param input_wavs: dict. key-clip_name, value-clip_path
    :param output_path: temp_dir for txt file from opensmile
    :return: dict. key-clip_name, value-clip_features(1582-dims)
    """

    results = {}
    g_logger.info('提取opensmile特征的音频数量: {}'.format(len(input_wavs)))
    # emobase2010
    outfold = os.path.join(output_path, 'opensmile_txt')
    if os.path.exists(outfold):
        shutil.rmtree(outfold)
    os.makedirs(outfold)

    for clip in input_wavs:
        f = input_wavs[clip]
        txt_file = opensmiler(f, outfold=outfold,config='emobase2010')
        if not os.path.exists(txt_file):
            g_logger.warning("提取{}的opensmile特征失败，使用全0特征。".format(clip))
            results[clip] = [float(0)]*1582
        else:
            f = open(txt_file, 'r')
            last_line = f.readlines()[-1]
            f.close()
            features = last_line.split(',')
            features = features[1:-1]
            features = [float(x) for x in features]
            results[clip] = features

    g_logger.info("opensmile提取完成.")
    return results

     
if __name__ == '__main__':     
    pass

