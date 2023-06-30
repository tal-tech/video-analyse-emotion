import os
import re
import uuid
import pickle
import subprocess
import numpy as np
import json
import pandas as pd
import multiprocessing

base_path = os.path.dirname(os.path.realpath(__file__))


def opensmiler(infile, outfold, config='emobase2010', toolfold='./opensmile-2.3.0/', extension='.txt'):
    '''
    infile: single input file to be extracted
    outfold: where to save the extracted file with the same name
    config: opensmile config file
    toolfold: opensmile tool folder
    extension: ".txt" or ".csv"
    '''
    # tool and config
    tool = os.path.join(toolfold, 'bin/linux_x64_standalone_libstdc6/SMILExtract')
    config = os.path.join(toolfold, 'config/{}.conf'.format(config))

    # get infile and outfile names
    infilename = infile
    outfilename = os.path.join(outfold, os.path.basename(infile).split('.wav')[0] + extension)
    cmd = '"%s" -C "%s" -I "%s" -O "%s"' % (tool, config, infilename, outfilename)
    # execute
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    if not os.path.exists(outfilename):
        raise TypeError('something wrong happened')


def opensmiler_from_list(wav_list, txt_root):
    os.makedirs(txt_root, exist_ok=True)
    p = multiprocessing.pool.ThreadPool(processes=10)
    for wav_path in wav_list:
        p.apply_async(
            opensmiler, args=(
                wav_path, txt_root, 'emobase2010',
                os.path.join(base_path, 'opensmile-2.3.0'),
                '.txt'
            )
        )
    p.close()
    p.join()
    result_list = []
    for txt_name in os.listdir(txt_root):
        if '.txt' not in txt_name:
            continue
        txt_path = os.path.join(txt_root, txt_name)
        columns_line = open(txt_path, 'r').readlines()[3:-5]
        features_line = open(txt_path, 'r').readlines()[-1]
        columns = columns_line
        features = features_line.split(',')
        features = features[1:-1]
        features = np.array(features)
        result_list.append(dict([('id', txt_name[:-4])] + list(zip(columns, features))))
        os.remove(txt_path)
    os.rmdir(txt_root)
    if len(result_list) == 0:
        raise TypeError('no opensmil txt generated!')
    target_list = [os.path.basename(x)[:-4] for x in wav_list if '.wav' in x]
    miss_list = list(set(target_list).difference([x['id'] for x in result_list]))
    if len(miss_list) > 0:
        raise Warning('opensmile extract failed for {} clips!'.format(len(miss_list)))
    result_df = pd.DataFrame(result_list)
    return result_df


class rehearsal_emo(object):
    def __init__(self):
        self.male_model = pickle.load(open(os.path.join(base_path, 'model/beike-male_gbdt-online.pkl'), 'rb'))
        self.female_model = pickle.load(open(os.path.join(base_path, 'model/beike-female_gbdt-online.pkl'), 'rb'))
        self.threshold = 0.5

    def inference(self, input_list, is_male=0):
        wav_list = [x['wav_path'] for x in input_list]
        uid = uuid.uuid1()
        op_features = opensmiler_from_list(wav_list, os.path.join(base_path, 'tmp/{}'.format(uid)))
        if is_male == 0:
            probe_result = self.female_model['model'].predict_proba(op_features[self.female_model['feature']])[:, 1]
        elif is_male == 1:
            probe_result = self.male_model['model'].predict_proba(op_features[self.male_model['feature']])[:, 1]
        else:
            raise ValueError('parameter for is_male shoud be 0 or 1!')
        probe_dict = dict(zip(op_features['id'].tolist(), probe_result))
        flag_dict = dict(zip(op_features['id'].tolist(), [int(x > self.threshold) for x in probe_result]))
        output_list = [
            {
                'begin_time': x['begin_time'], 'end_time': x['end_time'],
                'score': probe_dict.get(os.path.basename(x['wav_path'])[:-4], -1),
                'label': flag_dict.get(os.path.basename(x['wav_path'])[:-4], -1)
            } for x in input_list
        ]
        if len([x for x in output_list if x['score'] != -1]) > 0:
            total_score = np.mean([x['score'] for x in output_list if x['score'] != -1])
            total_label = int(total_score > self.threshold)
        else:
            total_score = -1
            total_label = -1
        result = {'segment': output_list, 'total': {'score': total_score, 'label': total_label}}

        return result


RehearsalEmo = rehearsal_emo()


if __name__ == "__main__":
    # input_list = [
    #     {'wav_path': '/workspace/HangLi/class_rehearsal/emo/vegas_data/female/培优备课练课_185_208540-253280.wav',
    #      'begin_time': 0, 'end_time': 1},
    #     {'wav_path': '/workspace/HangLi/class_rehearsal/emo/vegas_data/female/培优备课练课_188_295790-330170.wav',
    #      'begin_time': 1, 'end_time': 2}
    # ]
    input_list = [{'wav_path': '/home/diaoaijie/workspace/video-analyse-emotion/emotion_model/test.wav',
         'begin_time': 0, 'end_time': 1}]
    test_result = RehearsalEmo.inference(input_list, 0)
    print(test_result)
    print(1 + 1)
