import functools
import os
import shutil
import time
from backend.slice_helper import clip_wav
from emotion_model.rehearsal_emo import RehearsalEmo
from multiprocessing.pool import ThreadPool
from config import Config
from backend.utility import EvaEx, Const, get_internal_url, http_download, make_callback, try_post_json, g_logger


def run_in_pool(pool: ThreadPool):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = pool.apply_async(func, args=args)
            return result.get()
        return wrapper
    return decorator


class Pipeline:
    def __init__(self, input_dict):
        self.input_dict = input_dict
        self.output_dict = {}
        self.uid = input_dict['requestId']
        self.video_file = os.path.join(Config.TMP_FOLDER, self.uid)
        self.tmp_folder = os.path.join(Config.TMP_FOLDER, self.uid+"_video")

    def run(self):
        try:
            self._download()
            self._cut()
            self._ai()
            self._callback()
        except EvaEx as e:
            g_logger.error("{} - eva error: {}".format(self.uid, e))
            self._callback(e.msg)
        except Exception as e:
            g_logger.error("{} - unknown error: {}".format(self.uid, e))
            self._callback(Const.INTERNAL_ERR)

    def _download(self):
        g_logger.debug(f'{self.uid} - download')
        self.internal_url = get_internal_url(self.input_dict['video_url'], self.uid)
        if self.internal_url != self.input_dict['video_url']:
            self.input_dict['internal_url'] = self.internal_url
        http_download(self.internal_url, self.video_file, self.uid)
        if not os.path.exists(self.video_file):
            raise EvaEx(Const.DOWNLOAD_ERR)

    def _cut(self):
        g_logger.debug('{} - cut'.format(self.uid))
        os.mkdir(self.tmp_folder)
        self.wav_clips = clip_wav(self.input_dict['asr_result'], self.video_file, "emotion")

    def _ai(self):
        g_logger.debug('{} - ai'.format(self.uid))
        emotions = RehearsalEmo.inference(self.wav_clips, int(self.input_dict.get('gender')))
        self.output_dict.update({"emotion": emotions})

    def _callback(self, status=Const.SUCCESS):
        g_logger.info("{} - callback:{}".format(self.uid, status))
        if os.path.exists(self.video_file):
            os.remove(self.video_file)
        if os.path.exists(self.tmp_folder):
            shutil.rmtree(self.tmp_folder)
        if os.path.exists('/'.join(self.wav_clips[0].get('wav_path').split('/')[:-1])):
            shutil.rmtree('/'.join(self.wav_clips[0].get('wav_path').split('/')[:-1]))
        if status == Const.SUCCESS:
            ret_data = make_callback(Const.SUCCESS, self.uid, self.output_dict)
        else:
            self.output_dict = {"emotion": None}
            ret_data = make_callback(status, self.uid, self.output_dict)
        g_logger.debug("{} - return data: {}".format(self.uid, ret_data))
        ret = try_post_json(self.input_dict['callback'], ret_data, self.uid)
        g_logger.info("{} - callback return:{}".format(self.uid, ret))


if __name__ == '__main__':
    p = Pipeline({"requestId": "123", "callback": "http://39.96.87.60:8002/recv-json",
        "video_url": "http://oss-dolphin.oss-cn-beijing.aliyuncs.com/test.mp4?OSSAccessKeyId=LTAI4FhANPsGZoKQFxVZvry3&Expires=1597793140&Signature=qR6tYSbZ4sU33B6SI0txdnih7M8%3D"})
    print(p.run())
