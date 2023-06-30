#coding=utf-8
import os
import sys
base_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base_path))
import shutil
import pickle
import numpy as np
import json
import uuid
from opensmile_extraction import batch_extract, logger

__all__ = ["audio_emotion_model"]

class Emotion:

    def __init__(self, sklearn_model_path):
        self.emotion_model = pickle.load(open(sklearn_model_path, 'rb'))
        self.thread = 0.5

    def predict(self, wav_clips_list):
        logger.debug("开始预测，收到输入的音频切片为:{}".format(str(wav_clips_list)))
        logger.info("开始预测，收到输入的音频切片数量为:{}".format(len(wav_clips_list)))

        default_result = {
            "segment": {},
            "total": {
                "score": 0.0,
                "label": 0
            }
        }

        if len(wav_clips_list) == 0:
            logger.info("输入列表为空，返回默认值。")
            return json.dumps(default_result)

        uid = uuid.uuid1()
        temp_dir = os.path.join(base_path, "temp_{}".format(uid))
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)
        logger.info("创建文件夹：{}".format(temp_dir))


        wav_clips = {}
        for clip_path in wav_clips_list:
            clip_name = clip_path.split("/")[-1]
            wav_clips[clip_name] = clip_path

        clips_features = batch_extract(wav_clips, temp_dir)
        result = {
            "segment": {},
            "total": {}
        }
        scores = []
        for clip in clips_features:
            features = clips_features[clip]
            score = self.emotion_model.predict_proba([features])[0][-1]
            if score > self.thread:
                label = 1
            else:
                label = 0
            result["segment"][clip] = {
                "score": score,
                "label": label
            }
            scores.append(score)
        total_score = float(np.mean(scores[:-1]))
        if total_score > self.thread:
            total_label = 1
        else:
            total_label = 0

        result["total"]["score"] = total_score
        result["total"]["label"] = total_label

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info("删除文件夹：{}".format(temp_dir))

        result_str = json.dumps(result)
        logger.debug("预测结束，返回的结果为：{}".format(result_str))
        return result_str


audio_emotion_model = Emotion(os.path.join(base_path, "round_7.pkl"))

