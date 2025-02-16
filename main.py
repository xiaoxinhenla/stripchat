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



# 设置检测流的超时时间
timeout = 5  # 超时时间，单位秒

# 存储正在监控的流
streams = {}

# 存储每个流对应的 ffmpeg 进程
ffmpeg_processes = {}

# 存储正在录制的流
recording_streams = set()




def generate_random_filename(length):
    # 生成指定长度的随机文件名
    filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return filename


def create_dir(name,url,filename):
    urls=url.split("/")
    #print(urls[4])
    now=datetime.datetime.now()
    year=now.year
    month=now.month
    day=now.day
    nowday="{}{}{}".format(year,month,day)
    #print(nowday)
    path="movie/{}/{}/{}/{}".format(name,urls[4],nowday,filename)
    try:
        os.makedirs(path,exist_ok=True)
        #print("文件创建成功")
        return path
    except OSError as error:
        print("文件创建失败")





# 启动 ffmpeg 录制流的函数
async def start_recording(name, url):
    # 生成录制文件的路径
    
    filename=generate_random_filename(8)
    pathname=create_dir(name,url,filename)
    m3u8_name="{}/{}.m3u8".format(pathname,filename)
    mp4_name="{}/{}.mp4".format(pathname,filename)
    # 使用 ffmpeg 录制流
    command = [
        "ffmpeg", 
        "-re", "-rtbufsize", "100M", "-i", url, 
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128K",
        "-f", "hls", "-hls_time", "10",  "-hls_flags", 
        "delete_segments+append_list+independent_segments", 
        "-hls_playlist_type", "event", m3u8_name, "-reconnect", "1"
    ]

 
    
    ffmpeg_command=r"ffmpeg  -re -rtbufsize 100M -i {}  -c:v copy -c:a aac -b:a 128k -f hls  -hls_time 10 -hls_list_size 4 -hls_flags delete_segments+append_list+independent_segments -hls_segment_type fmp4 -hls_playlist_type event {}/{}.m3u8 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -async 1 -vsync 1 -f mp4 -movflags +faststart  {}/{}.mp4".format(url,pathname,filename,pathname,filename)

    try:
        print(f"🎥 正在录制流 {name}到 {pathname}")
        #process=await asyncio.create_subprocess_exec(*command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process=await asyncio.create_subprocess_exec(*command,stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        #process=await asyncio.create_subprocess_exec(*command)

         # 启动异步任务，读取输出流
        asyncio.create_task(read_output(process))

        
        ffmpeg_processes[filename] = process  # 将进程记录到 ffmpeg_processes 中
        # 等待进程完成，录制结束后恢复监听
        #await wait_for_recording_to_finish(name, process)
        print(f"等待流 {name} 的录制结束...")
        await process.wait()
        print(f"流 {name} 录制完毕！")
        # 录制完毕后，从录制流集合中移除
        recording_streams.remove(name)
        del ffmpeg_processes[filename]
        print(f"恢复监听流 {name}...")

  # 启动录制进程
    except Exception as e:
        print(f"❌ 启动录制失败: {e}")



# 异步读取输出流
async def read_output(process):
    stdout, stderr = await process.communicate()  # 获取标准输出和标准错误
    
    if stdout:
        print(f"stdout:\n{stdout.decode()}")
    
    if stderr:
        print(f"stderr:\n{stderr.decode()}")







async def wait_for_recording_to_finish(name, process):
    print(f"等待流 {name} 的录制结束...")
    
    # 使用 subprocess.wait() 等待进程结束
    await process.wait()  # 阻塞直到进程结束
    print(f"流 {name} 录制完毕！")

    # 录制完毕后，从录制流集合中移除
    recording_streams.remove(name)
    print(f"恢复监听流 {name}...")



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
                        else:
                            print(f"❌ {name} 流离线！返回状态码: {response2.status}")
                else:
                    print(f"❌ {name} 主 M3U8 文件无法访问，返回状态码: {response.status}")
                    
    except asyncio.TimeoutError:
        print(f"⚠️ {name} 请求超时！")
    except aiohttp.ClientError as e:
        print(f"⚠️ {name} HTTP 请求失败：{e}")
    except Exception as e:
        print(f"⚠️ {name} 出现意外错误：{e}")


# 从 JSON 文件中读取直播流地址
def read_streams_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

# 更新正在监控的流（新增或删除）
def update_streams(file_path):
    global streams
    print(streams)
    new_streams = read_streams_from_json(file_path)
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
        print(streams)

    return new_streams

# 每个流的状态检查任务
async def monitor_stream(name, url):
    while True:
        if name not in recording_streams:  # 仅对未录制的流进行检测
            await check_stream_online(name, url)
        await asyncio.sleep(180)  # 每 30 秒检测一次



# 主程序：定时检查流是否在线
async def main(file_path):
    global streams
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
                last_mtime = new_mtime

                # 更新监控任务：新增流
                for name, url in streams.items():
                    if name not in [task.get_name() for task in tasks]:  # 如果新的流没有被监控
                        task = asyncio.create_task(monitor_stream(name, url))
                        tasks.append(task)
        
        await asyncio.sleep(1)  # 每 30 秒检查一次文件变化

if __name__ == "__main__":
    # 使用 streams.json 文件中的流地址
    asyncio.run(main("live_rooms.json"))
