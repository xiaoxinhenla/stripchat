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
import logging
import re
import glob
from logging.handlers import RotatingFileHandler


# 设置检测流的超时时间
timeout = 5  # 超时时间，单位秒

# 存储正在监控的流
streams = {}
#取消监控流
cancel_streams={}

# 存储每个流对应的 ffmpeg 进程
ffmpeg_processes = {}

# 存储正在录制的流
recording_streams = set()

live_rooms_name="live_rooms3.json"





# 设置日志文件路径和最大文件大小
log_file = 'log/stream_recording_1.0.log'
max_log_size = 10 * 1024 * 1024  # 10 MB
backup_count = 5  # 保留最近的 5 个日志文件

# 创建 RotatingFileHandler，支持日志文件滚动
handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
handler.setLevel(logging.DEBUG)

# 创建 formatter 并设置给 handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 创建 logger 并添加 handler
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# 配置日志
logging.basicConfig(
    filename='log/stream_recording_v1.0.log',  # 日志文件路径
    level=logging.DEBUG,  # 日志级别（DEBUG 会记录所有级别的日志）
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
    datefmt='%Y-%m-%d %H:%M:%S' # 日期格式
    
)




def generate_random_filename(length):
    # 生成指定长度的随机文件名
    filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return filename


def create_dir(name,url):
    urls=url.split("/")
    #print(urls[4])
    now=datetime.datetime.now()
    year=now.year
    month=now.month
    day=now.day
    nowday="{}{}{}".format(year,month,day)
    #print(nowday)
    path="movie/{}/{}/{}".format(name,urls[4],nowday)
    try:
        os.makedirs(path,exist_ok=True)
        #print("文件创建成功")
        return path
    except OSError as error:
        logger.error("文件创建失败")





# 启动 ffmpeg 录制流的函数
async def start_recording(name, url):
    # 生成录制文件的路径
    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    random_name=generate_random_filename(8)
    pathname=create_dir(name,url)
    #filename=f"{random_name}_{now}_"
    filename=f"{name}_"
    m3u8_name=f"{pathname}/{filename}.m3u8"
    logger.info(f"{m3u8_name}/{filename}")
    #mp4_name=f"{pathname}/{filename}_{now}.mp4"
    # 使用 ffmpeg 录制流
    command = [
        "ffmpeg", 
        "-re", "-rtbufsize", "100M", "-i", url, 
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128K",
        "-f", "hls", "-hls_time", "10",  "-hls_flags", 
        "append_list+independent_segments", 
        "-hls_playlist_type", "event", m3u8_name
    ]

 
    
    ffmpeg_command=r"ffmpeg  -re -rtbufsize 100M -i {}  -c:v copy -c:a aac -b:a 128k -f hls  -hls_time 10 -hls_list_size 4 -hls_flags delete_segments+append_list+independent_segments -hls_segment_type fmp4 -hls_playlist_type event {}/{}.m3u8 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -async 1 -vsync 1 -f mp4 -movflags +faststart  {}/{}.mp4".format(url,pathname,filename,pathname,filename)

    try:
        logger.info(f" 正在录制流 {name}到 {pathname}")
        #process=await asyncio.create_subprocess_exec(*command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process=await asyncio.create_subprocess_exec(*command,stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        #process=await asyncio.create_subprocess_exec(*command)

         # 启动异步任务，读取输出流
        asyncio.create_task(read_output(process))
        ffmpeg_processes[name] = process  # 将进程记录到 ffmpeg_processes 中
        #print(ffmpeg_processes)
        # 等待进程完成，录制结束后恢复监听
        await wait_for_recording_to_finish(name, process)
        
        
        # print("合并文件")
        # # 合并 TS 文件并删除 TS 文件
        # await merge_ts_to_mp4(pathname, filename)
        
        # print("开始删除ts文件")
        # # 删除临时目录中的所有 .ts和m3u8 文件
        # await delete_ts_files(pathname, filename)
        # print("删除ts文件完成")

  # 启动录制进程
    except Exception as e:
        logger.error(f" 启动录制失败: {e}")




async def wait_for_recording_to_finish(name, process):
    print(f"等待流 {name} 的录制结束...")
    
    # 使用 subprocess.wait() 等待进程结束
    await process.wait()  # 阻塞直到进程结束
    print(f"流 {name} 录制完毕！")

    # 录制完毕后，从录制流集合中移除
    recording_streams.remove(name)
    #录制完毕后，从录制进程中移除
    del ffmpeg_processes[name]
    #print(f"恢复监听流 {name}...")
    

    

    






# 异步读取输出流
async def read_output(process):
    stdout, stderr = await process.communicate()  # 获取标准输出和标准错误
    
    if stdout:
        logger.info(f"stdout:\n{stdout.decode()}")
    
    if stderr:
        logger.error(f"stderr:\n{stderr.decode()}")











def get_stream(m3u_content):
    # 将内容按行分割
    lines = m3u_content.splitlines()
    
    # 查找包含 "1080p" 的行
    for i, line in enumerate(lines):
        if "http" in line:
            # 找到对应的流信息
            stream_info = lines[i-1]  # 获取上面一行的 EXT-X-STREAM-INF 信息
            stream_url = line  # 当前行是对应的流 URL
            return stream_info, stream_url
    
    # 如果没有找到 1080p 流
    return None, None



# 检测流是否在线的异步函数
async def check_stream_online(name, url):
    # 检查该流是否已在录制中，如果是，跳过检查
    if name in recording_streams:
        print(f"❌ {name} 已在录制中，跳过在线检查")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            # 第一步：请求主 M3U8 文件
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    stream_info, stream_url = get_stream(content)
                    if not stream_url:
                        print(f"❌ {name} 没有找到有效的流 URL")
                        return
                    
                    # 第二步：请求实际视频流
                    async with session.get(stream_url, timeout=timeout) as response2:
                        if response2.status == 200:
                            print(f"✅ {name} 流在线！")
                            recording_streams.add(name)  # 将流加入录制集合
                            await start_recording(name, url)  # 启动录制
                            recording_streams.remove(name)  # 录制完毕后移除
                            logger.info(f"流 {name} 录制完毕！")

                            
                        else:
                            logger.info(f" {name} 流离线！返回状态码: {response2.status}")
                else:
                    logger.info(f" {name} 主 M3U8 文件无法访问，返回状态码: {response.status}")
                    
    except asyncio.TimeoutError:
        logger.error(f" {name} 请求超时！")
    except aiohttp.ClientError as e:
        logger.error(f" {name} HTTP 请求失败：{e}")
    except Exception as e:
        logger.error(f" {name} 出现意外错误：{e}")



#录制完毕后将ts文件合并成mp4
async def merge_ts_to_mp4(pathname, filename):
    print(f"正在合并文件{pathname}/{filename}")
    # 使用 ffmpeg 合并 TS 文件为 MP4
    output_mp4 = f"{pathname}/{filename}.mp4"
    command = [
        "ffmpeg", "-y","-i", f"{pathname}/{filename}.m3u8", "-c", "copy", "-bsf:a","aac_adtstoasc", output_mp4
    ]

    #print(command)

    try:
        logger.info(f"合并 TS 文件为 MP4: {output_mp4}")
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        # 启动异步任务，读取输出
        asyncio.create_task(read_output(process))

        # 等待合并完成
        await process.wait()
        print("ts文件转mp4已完成")
        logger.info(f"成功合并 TS 文件为 MP4: {output_mp4}")
    except subprocess.CalledProcessError as e:
        logger.error(f" 合并 TS 文件失败: {e}")
    except Exception as e:
        logger.error(f" 合并过程中出现错误: {e}")




#合并完mp4后将ts文件删除
async def delete_ts_files(directory, prefix):
    """
    删除指定目录下所有以指定前缀开头的文件。

    参数:
    directory (str): 目标文件夹路径。
    prefix (str): 文件名前缀。
    """
    # 构建匹配模式，匹配以指定前缀开头的文件
    pattern = os.path.join(directory, f'{prefix}*')

    # 使用 glob 模块获取匹配的文件列表
    files_to_delete = glob.glob(pattern)

    # 遍历文件列表并删除每个文件
    logger.info(files_to_delete)
    for file_path in files_to_delete:
        # 检查文件是否以 .mp4 结尾
        if not file_path.endswith('.mp4'):
            try:
                os.remove(file_path)
                logger.info(f"已删除文件: {file_path}")
            except OSError as e:
                logger.error(f"删除文件 {file_path} 时出错: {e}")




# 从 JSON 文件中读取直播流地址
def read_streams_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data= json.load(file)
    
    """
    从 JSON 文件中读取直播流地址，并返回一个字典。
    假设被注释的直播间名称以 '#' 开头。
    """
    streams = {}
    for stream_name, url in data.items():
        if not stream_name.startswith('#'):
            streams[stream_name] = url
    
    return streams


# 更新正在监控的流（新增或删除）
def update_streams(file_path):
    global streams
    new_streams = read_streams_from_json(file_path)
    logger.info(new_streams)
    current_streams = set(streams.keys())
    new_streams_set = set(new_streams.keys())
    
    # 新增的流
    added_streams = new_streams_set - current_streams
    for stream_name in added_streams:
        url = new_streams[stream_name]
        print(f"✅ 新增流监控：{stream_name}")
        streams[stream_name] = url
        
    
    # 删除的流
    removed_streams = current_streams - new_streams_set
    for stream_name in removed_streams:
        print(f"❌ 删除流监控：{stream_name}")        
        del streams[stream_name]
        
        # 取消录制进程

        if stream_name in ffmpeg_processes:
            process = ffmpeg_processes[stream_name]
            process.terminate()  # 或 process.kill()
            print(f"已终止流 {stream_name} 的录制进程。")
            del ffmpeg_processes[stream_name]
        
        
        

    # 取消被注释的流的录制
    commented_streams = [stream_name for stream_name in new_streams if stream_name.startswith('#')]
    for stream_name in commented_streams:
        print(f"❌ 取消录制：{stream_name}")
        # 在此添加取消录制的逻辑，例如停止相关的录制进程
        # 取消录制进程
        if stream_name in ffmpeg_processes:
            process = ffmpeg_processes[stream_name]
            process.terminate()  # 或 process.kill()
            print(f"已终止流 {stream_name} 的录制进程。")
            del ffmpeg_processes[stream_name]

        cancel_streams=stream_name

    

    return new_streams

# 每个流的状态检查任务
async def monitor_stream(name, url):
    while True:
        
        # with open(live_rooms_name, "r", encoding="utf-8") as file:
        #     data= json.load(file)
    
        # """
        # 从 JSON 文件中读取直播流地址，并返回一个字典。
        # 假设被注释的直播间名称以 '#' 开头。
        # """
        # for stream_name, url in data.items():
        #     if not stream_name.startswith('#'):
        if name not in recording_streams:  # 仅对未录制的流进行检测
            
            await check_stream_online(name, url)
            print(f"✅ {name} 未开播,3分钟后重新检测")

        await asyncio.sleep(180)  # 每 30 秒检测一次



# 更新录制流的时长
def update_duration(streams):
    global recording_streams
    # 如果有录制中的流
    if recording_streams:
        for i, (name, start_time) in enumerate(recording_streams.items()):
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(int(elapsed_time), 60)
            hours, minutes = divmod(minutes, 60)
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            print(name)
            
    else:
        print( "没有正在录制的流.")
        print(streams)


        









# 主程序：定时检查流是否在线
async def main(file_path):
    global streams
    global cancel_streams
    last_mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
    
    # 初次读取文件并加载流
    streams = update_streams(file_path)
    # 创建并运行异步任务监控每个流
    tasks = []
    for name, url in streams.items():
        task = asyncio.create_task(monitor_stream(name, url))
        tasks.append(task)

    

    
    while True:
        # 检查文件是否有更新
        if os.path.exists(file_path):
            new_mtime = os.path.getmtime(file_path)
            if new_mtime != last_mtime:  # 文件有变化
                print("📂 检测到 `streams.json` 变化，更新监测列表...")
                streams = update_streams(file_path)
                logger.info(f"监控流{streams}")
                
                last_mtime = new_mtime

                # 更新监控任务：新增流
                for name, url in streams.items():
                    if name not in [task.get_name() for task in tasks]:  # 如果新的流没有被监控
                        task = asyncio.create_task(monitor_stream(name, url))
                        tasks.append(task)

        
        
        await asyncio.sleep(1)  # 每 30 秒检查一次文件变化








if __name__ == "__main__":

    
    asyncio.run(main(live_rooms_name))
