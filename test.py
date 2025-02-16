
import aiohttp
import asyncio
import json
import os
import time
import subprocess
import random
import string
import sys
import datetime

def generate_random_filename(length):
    # 生成指定长度的随机文件名
    filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return filename


def create_dir(url,filename):
    urls=url.split("/")
    print(urls[4])
    now=datetime.datetime.now()
    year=now.year
    month=now.month
    day=now.day
    nowday="{}{}{}".format(year,month,day)
    print(nowday)
    path="movie/{}/{}/{}".format(urls[4],nowday,filename)
    try:
        os.makedirs(path,exist_ok=True)
        print("文件创建成功")
        return path
    except OSError as error:
        print("文件创建失败")
def start_recording(name, url):
    # 生成录制文件的路径
    
    filename=generate_random_filename(8)
    pathname=create_dir(url,filename)
    m3u8_name="{}/{}.m3u8".format(pathname,filename)
    mp4_name="{}/{}.mp4".format(pathname,filename)
    # 使用 ffmpeg 录制流
    command = [
        "ffmpeg", 
        "-rf","-rtbufsize","100M",
        "-i", url, 
        "-c:v", "copy", 
        "-c:a","aac",
        "-b:a","128K",
        "-f","hls","-hls_time","10","-hls_list_size","4","hls_flags",
        "-hls_flags delete_segments+append_list+independent_segments","-hls_segment_type",
        "fmp4","-hls_playlist_type","event",m3u8_name,"-reconnect","1","-reconnect_streamed","1",
        "-reconnect_delay_max","5","-async","1","-vsync","1","-f","mp4","-movflags","+faststart",mp4_name
    ]
    

    # 使用 ffmpeg 录制流
    command1 = [
        "ffmpeg", 
        "-i", url, 
        "-c", "copy", 
        "-f", "mp4", 
        "-t", "3600",  # 录制 1 小时（可以根据需要调整）
        m3u8_name
    ]

# 存储每个流对应的 ffmpeg 进程
    ffmpeg_processes = {}
    print(command1)
    print(f"🎥 正在录制流 {name}到 {pathname}")
    ffmpeg_command=r"ffmpeg  -re -rtbufsize 100M -i {}  -c:v copy -c:a aac -b:a 128k -f hls  -hls_time 10 -hls_list_size 4 -hls_flags delete_segments+append_list+independent_segments -hls_segment_type fmp4 -hls_playlist_type event {}/{}.m3u8 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -async 1 -vsync 1 -f mp4 -movflags +faststart  {}/{}.mp4".format(url,pathname,filename,pathname,filename)
    print(ffmpeg_command)
    process=subprocess.Popen(ffmpeg_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    #process=subprocess.Popen(ffmpeg_command)
    ffmpeg_processes[name] = process  # 将进程记录到 ffmpeg_processes 中
    #stdout,stderr=process.communicate()
    # 等待进程完成，录制结束后恢复监听
    await wait_for_recording_to_finish(name, process)
    



# 等待录制进程结束
async def wait_for_recording_to_finish(name, process):
    print(f"等待流 {name} 的录制结束...")
    
    # 使用 subprocess.wait() 等待进程结束
    process.wait()  # 阻塞直到进程结束
    print(f"流 {name} 录制完毕！")

    # 录制完毕后，从录制流集合中移除
    recording_streams.remove(name)
    print(f"恢复监听流 {name}...")

    # 恢复监听
    streams[name] = streams[name]  # 触发恢复监控任务
    await check_stream_online(name, streams[name])  # 重新启动对该流的监听



#start_recording("aaa","https://edge-hls.doppiocdn.live/hls/162696696/master/162696696_auto.m3u8?playlistType=lowLatency")
url="https://edge-hls.doppiocdn.live/hls/162696696/master/162696696_auto.m3u8?playlistType=lowLatency"
m3u8_name="out.m3u8"
command = [
        "ffmpeg", 
        "-re", "-rtbufsize", "100M", "-i", url, 
        "-c:v", "copy", "-copyts","-c:a", "aac", "-b:a", "128K",
        "-f", "hls", "-hls_time", "10",  "-hls_flags", 
        "delete_segments+append_list+independent_segments", 
        "-hls_playlist_type", "event", m3u8_name, "-reconnect", "1","-reconnect_streamed","1","-reconnect_delay_max","5"
    ]

print(command)