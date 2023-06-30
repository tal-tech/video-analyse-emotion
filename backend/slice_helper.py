from backend.utility import g_logger
import uuid
import subprocess
import ffmpy
import os


def interval_gen(asr_content, time1, time2, time3, time4=None):
    '''
    :param asr_content:
    :param time1: 累积长度大于这个长度就开始切分
    :param time2: 片段低于这个长度就抛弃
    :param time3: 静默超过这个时间就切分
    :param time4(option): 片段超过这个长度就抛弃
    :return:
    '''

    accumulate_time = 0
    previous_end = -1
    interval_begin = -1
    interval_end = -1

    interval_result = []
    for i, line in enumerate(asr_content):
        begin = int(line['begin_time'])
        end = int(line['end_time'])

        if i == 0:
            previous_end = begin
            interval_begin = begin
            interval_end = end

        if accumulate_time > (time1 * 1000):  # 如果之前积累的时间超过了time1 秒，则把之前积累的片段切出来
            if time4 is not None:  # 如果设定了片段最长时间
                if accumulate_time <= time4:
                    interval = (interval_begin, interval_end)
                    interval_result.append(interval)

            else:
                interval = (interval_begin, interval_end)
                interval_result.append(interval)

            accumulate_time = 0
            previous_end = begin
            interval_begin = begin
            interval_end = end

        if i != 0:
            if (begin - previous_end) > (time3 * 1000):  # 中间静音超过time3 秒，则不把这段静音包含进去，把前一段切出来
                if accumulate_time > (time2 * 1000):  # 只有前一段积累的时间超过time2 秒才切，否则直接放弃
                    interval = (interval_begin, interval_end)
                    interval_result.append(interval)

                accumulate_time = 0
                previous_end = begin  # 切割之后，放弃这句话和上一句话之间的静音部分。
                interval_begin = begin
                interval_end = end

        # 到此处理完了上一个积累片段的内容。开始处理包含本个asr句子的积累片段。
        # 每次添加的时长，包括本个asr句子的长度还有本句和上一句之间静音部分长度。除非上一个片段切割走了。
        time_length = end - previous_end
        previous_end = end
        interval_end = end
        accumulate_time += time_length

        if i == len(asr_content) - 1:  # 如果是最后一句了
            if accumulate_time > (time2 * 1000):  # 只有前一段积累的时间超过time2 秒才切，否则直接放弃
                if time4 is not None:  # 如果设置了片段最长时间。
                    if accumulate_time <= time4:
                        interval = (interval_begin, interval_end)
                        interval_result.append(interval)

                else:
                    interval = (interval_begin, interval_end)
                    interval_result.append(interval)
    return interval_result


def get_wav_clips(video_task, video_file_path):
    """

    :param video_task:
    :param video_file_path:
    :return: ['/logs/95cc31b2-b06d-11ea-890d-be90d8daf3d0/95cc31b2-b06d-11ea-890d-be90d8daf3d0/1.wav']
    """
    files = []
    try:
        if '.wav' not in video_file_path:
            index = video_file_path.rfind('.')
            tpath = video_file_path[:index] + '.wav'
            ffmpy.FFmpeg(inputs={'{}'.format(video_file_path): None},
                         outputs={'{}'.format(tpath): '-ar 16000 -ac 1'}).run(stderr=subprocess.PIPE,
                                                                              stdout=subprocess.PIPE)
            os.remove(video_file_path)
            video_file_path = tpath

        index = video_file_path.rfind('.')
        fpath = video_file_path[:index]
        os.mkdir(fpath)
        fpath = fpath + '/'
        index = 0

        stime = 0
        duration = 30
        total_duration = int(video_task.media_duration / 1000)
        while stime + duration < total_duration:
            index = index + 1
            fname = fpath + '%d.wav' % index
            ffmpy.FFmpeg(inputs={'{}'.format(video_file_path): '-ss {} -t {}'.format(stime, duration)},
                         outputs={'{}'.format(fname): '-ar 16000 -ac 1'}).run(stderr=subprocess.PIPE,
                                                                              stdout=subprocess.PIPE)
            files.append(fname)
            stime += duration

        duration = total_duration - stime
        if duration > 0:
            index = index + 1
            fname = fpath + '%d.wav' % index
            ffmpy.FFmpeg(inputs={'{}'.format(video_file_path): '-ss {} -t {}'.format(stime, duration)},
                         outputs={'{}'.format(fname): '-ar 16000 -ac 1'}).run(stderr=subprocess.PIPE,
                                                                              stdout=subprocess.PIPE)
            files.append(fname)
    except Exception as e:
        g_logger.error('TaskId:{}, get wav clips error:{}'.format(video_task.task_id, str(e)))
    finally:
        return files


def clip_wav(asr_result: list, video_file_path, _type='fluency') -> list:
    """
    :param asr_result: list [{'begin_time':0,'end_time':100,'text':'the result returned by asr api'},]
    :param video_file_path:
    :param _type:
    :return: [{"wav_path":"path/to/your/clips/1.wav", "begin_time":0, "end_time":1000},]
    """
    if _type != "fluency":
        intervals = interval_gen(asr_result, 12, 8, 4)
    else:
        intervals = interval_gen(asr_result, 30, 20, 5)
    if '.wav' not in video_file_path:
        index = video_file_path.rfind('.')
        tpath = video_file_path[:index] + uuid.uuid4().hex + '.wav'
        ffmpy.FFmpeg(inputs={'{}'.format(video_file_path): None},
                     outputs={'{}'.format(tpath): '-ar 16000 -ac 1'}).run(stderr=subprocess.PIPE,
                                                                          stdout=subprocess.PIPE)
        # os.remove(video_file_path)
        video_file_path = tpath
    index = video_file_path.rfind('.')
    wav_dir_path = video_file_path[:index]
    if not os.path.exists(wav_dir_path):
        os.mkdir(wav_dir_path)
    g_logger.debug(f"video_path:{video_file_path}, wav_dir_path:{wav_dir_path}, exist:"
                   f"{os.path.exists(wav_dir_path)}")
    ret = []
    for item in intervals:
        st, ed = item
        wav_name = os.path.join(wav_dir_path, uuid.uuid4().hex) + '.wav'
        ffmpy.FFmpeg(inputs={'{}'.format(video_file_path): '-ss {} -t {}'.format(st / 1000, (ed - st) / 1000)},
                     outputs={'{}'.format(wav_name): '-ar 16000 -ac 1'}).run(stderr=subprocess.PIPE,
                                                                             stdout=subprocess.PIPE)
        ret.append({"wav_path": wav_name, "begin_time": st, "end_time": ed})
    if os.path.exists(video_file_path):
        os.remove(video_file_path)
    return ret


def get_pics_from_video(video_task, video_file_path):
    pics_path = []
    g_logger.info("TaskId:{}, get pics from videofile".format(video_task.task_id))
    try:
        if not os.path.exists(os.path.join("/logs", video_task.task_id)):
            os.mkdir(os.path.join("/logs", video_task.task_id))
        mydir = os.path.join("/logs", video_task.task_id, 'pic')
        if not os.path.exists(mydir):
            os.mkdir(mydir)
        pic_name = mydir + '/%0000d.jpg'
        cmd = 'ffmpeg -i {0} -vf fps=1 {1}'.format(video_file_path, pic_name)
        subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()
        for item in os.listdir(mydir):
            pics_path.append(os.path.join(mydir, item))
    except Exception as e:
        g_logger.error("TaskId:{}, draw frame error:{}".format(video_task.task_id, str(e)))
    finally:
        return pics_path


if __name__ == "__main__":
    # for emotion classification
    asr_content = [{'begin_time': 0, 'end_time': 100, 'text': 'the result returned by asr api'}, ]
    time1, time2, time3 = 30, 20, 5
    print(interval_gen(asr_content, time1, time2, time3))
    # for fluency classification
    asr_content = [{'begin_time': 0, 'end_time': 100, 'text': 'the result returned by asr api'}, ]
    time1, time2, time3 = 12, 8, 4
