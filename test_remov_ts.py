import os
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
import re
import glob


#录制完毕后将ts文件合并成mp4
async def merge_ts_to_mp4(pathname, filename):
    # 使用 ffmpeg 合并 TS 文件为 MP4
    output_mp4 = f"{pathname}\\{filename}.mp4"
    command = [
        "ffmpeg", "-y","-i", f"{pathname}\\{filename}.m3u8", "-c", "copy", "-bsf:a","aac_adtstoasc", output_mp4
    ]

    try:
        print(f"合并 TS 文件为 MP4: {output_mp4}")
        process=subprocess.run(command, check=True)

        print(f"成功合并 TS 文件为 MP4: {output_mp4}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 合并 TS 文件失败: {e}")
    except Exception as e:
        print(f"❌ 合并过程中出现错误: {e}")

async def delete_files_by_prefix(directory, prefix):
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

    for file_path in files_to_delete:
        # 检查文件是否以 .mp4 结尾
        if not file_path.endswith('.mp4'):
            try:
                os.remove(file_path)
                print(f"已删除文件: {file_path}")
            except OSError as e:
                print(f"删除文件 {file_path} 时出错: {e}")








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
    #now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    path="movie/{}/{}/{}".format(name,urls[4],nowday)
    try:
        #os.makedirs(path,exist_ok=True)
        print(path)
        return path
    except OSError as error:
        #logger.error("文件创建失败")
        pass


async def get_directories_in_path(path):
    # 获取路径下所有的文件和文件夹
    all_files_and_dirs = os.listdir(path)
    directories=[]
    # 过滤出文件夹
    for filename in all_files_and_dirs:
        if "m3u8" in filename:
            directories.append(filename)
            print(filename)



# filename=generate_random_filename(8)
# print(filename)
#create_dir("xixixx11","https://edge-hls.doppiocdn.live/hls/169566065/master/169566065_auto.m3u8?playlistType=lowLatency")

 # 创建并运行异步任务监控每个流

pathname=f"D:\\python\\stripchat2\\movie2\\Alexa_Duque34\\167303040\\2025215"
#            D:\python\stripchat2\movie\Linda_2k11\152515378\2025214
#D:\个人资料\workspaces\code\python\test\zhchat\movie\Sarah_Xoxo\149352638\2025213

#merge_ts_to_mp4(pathname,filename)
#delete_files_by_prefix(pathname,filename)


# directories=get_directories_in_path(pathname)
# for i in directories:
#     #pathname=f"D:\\python\\stripchat2\\movie1\\Linda_2k11\\152515378\\2025214\\{i}"
#     merge_ts_to_mp4(pathname,i)
#     delete_files_by_prefix(pathname,i)


#所有目录都遍历
async def find_m3u8_directories(root_path):   
    # 遍历指定目录及其子目录
    for dirpath, dirnames, filenames in os.walk(root_path):
        # 查找目录下所有的 .m3u8 文件
        for filename in filenames:
            if filename.endswith('.m3u8'):
                # 获取文件的完整路径
                full_file_path = os.path.join(dirpath, filename)
                # 去除扩展名获取文件名前缀
                file_prefix = os.path.splitext(filename)[0]
                # 将目录路径和文件前缀作为元组添加到结果列表
                print(dirpath,file_prefix)
                await merge_ts_to_mp4(dirpath,file_prefix)
                await delete_files_by_prefix(dirpath,file_prefix)


#指定目录下的m3u8
async def find_m3u8_directories_fordir(root_path):
    # 遍历指定目录及其子目录
    for dirpath, dirnames, filenames in os.walk(root_path):
        # 查找目录下所有的 .m3u8 文件
        for filename in filenames:
            if filename.endswith('.m3u8'):
                # 获取文件的完整路径
                full_file_path = os.path.join(dirpath, filename)
                # 去除扩展名获取文件名前缀
                file_prefix = os.path.splitext(filename)[0]
                print(f"Found .m3u8 file: {dirpath}")
                print(f"File prefix: {file_prefix}")
                # await merge_ts_to_mp4(dirpath,file_prefix)
                # await delete_files_by_prefix(dirpath,file_prefix)
        
    
    print("没有找到m3u8文件")




async def process_directory(dir_path):
    # 在这里处理找到的目录，比如读取文件或其他操作
    #await filetomp4(dir_path)
    print(dir_path)
    await find_m3u8_directories_fordir(dir_path)
    print("over")

async def find_directory(root_path, target_dir_name):
    tasks = []
    # 遍历指定目录及其子目录
    for dirpath, dirnames, filenames in os.walk(root_path):
        if target_dir_name in dirnames:
            target_path = os.path.join(dirpath, target_dir_name)
            print(f"Found directory: {target_path}")
            # 找到目标目录后，进一步处理
            task = asyncio.create_task(process_directory(target_path))
            tasks.append(task)
    # 等待所有任务完成
    if tasks:
        await asyncio.gather(*tasks)  

async def main():
    # 指定目录路径和目标目录名
    root_directory = f"D:\\python\\stripchat2\\movie"  # 替换为你想遍历的目录路径
    target_directory = "2025215"  # 目标目录名
    #await find_m3u8_directories(root_directory)
    await find_directory(root_directory,target_directory)
    await asyncio.sleep(100)

if __name__ == "__main__":
    asyncio.run(main())



