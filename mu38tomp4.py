import os
import time
import asyncio
from datetime import datetime, timedelta
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
import re
import glob

# 设置监控的目录路径
directory_path = 'D:\\python\\stripchat2\\movie'  # 你需要监控的目录路径

# 设置停止更新时间的阈值
time_threshold = timedelta(hours=2)  # 2小时后

# 获取文件的最后更新时间
async def get_last_modified_time(file_path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception as e:
        print(f"获取文件最后修改时间时出错: {e}")
        return None

# 检查文件是否停止更新超过2小时
async def check_file_update(file_path):
    #print(file_path)
    last_modified_time = await get_last_modified_time(file_path)
    if last_modified_time is None:
        return False
    
    current_time = datetime.now()
    if current_time - last_modified_time > time_threshold:
        return True
    return False

# 异步修改文件名
async def rename_file(file_path):
    print(file_path)
    
    try:
        new_name = file_path.replace('.mp4', f'_stale_{int(time.time())}.mp4')  # 例如加上时间戳
        os.rename(file_path, new_name)
        print(f"文件已重命名为: {new_name}")
    except Exception as e:
        print(f"重命名文件时出错: {e}")
    

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

        return output_mp4
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
                #print(f"Found .m3u8 file: {dirpath}")
                #print(f"File prefix: {file_prefix}")
                file_name=f"{dirpath}\\{file_prefix}.m3u8"
                is_stop_live_tolong = await check_file_update(file_name)
                
                if is_stop_live_tolong:
                    print("找到停播超过2个小时的")
                    print(f"{file_name} : {is_stop_live_tolong}")
                    output_mp4_name=await merge_ts_to_mp4(dirpath,file_prefix)
                    await delete_files_by_prefix(dirpath,file_prefix)
                    #修改mp4名字
                    await rename_file(output_mp4_name)

                else:
                    print(f"{file_name} : {is_stop_live_tolong}")

        
    


async def find_directory(root_path, target_dir_name):
    tasks = []
    # 遍历指定目录及其子目录
    for dirpath, dirnames, filenames in os.walk(root_path):
        if target_dir_name in dirnames:
            target_path = os.path.join(dirpath, target_dir_name)
            #print(f"Found directory: {target_path}") #找到含有指定目标的目录
            ## 找到指定目录下面的m3u8文件
            #print(target_path)
            #await find_m3u8_directories_fordir(target_path)
            #检查指定目标文件的更新时间是否超过2个小时
            
            #找到目标目录后，进一步处理
            task = asyncio.create_task(find_m3u8_directories_fordir(target_path))
            tasks.append(task)
    # # 等待所有任务完成
    if tasks:
        await asyncio.gather(*tasks)  


 
async def main():
    while True:
        now=datetime.now()
        year=now.year
        month=now.month
        day=now.day
        
        # 指定目录路径和目标目录名
        root_directory = f"D:\\python\\stripchat2\\movie"  # 替换为你想遍历的目录路径
        target_directory = "2025216"  # 目标目录名
        # 获取今天的日期格式，例如 2025216
        today_prefix = "{}{}{}".format(year,month,day)
        yesteday=datetime.now()-timedelta(days=1)
        yesterday_prefix=f"{yesteday.year}{yesteday.month}{yesteday.day}"
        #print(yesteday_prefix)
        #today_prefix = datetime.now().strftime('%Y%m%d')[2:]  # 获取形如 2025216 的格式
        #yesterday_prefix = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')[2:]  # 获取类似 2025215
       # print(today_prefix)
        #await find_m3u8_directories(root_directory)
        #await find_directory(root_directory,target_directory)
        await find_directory(root_directory,today_prefix)
        #查找前一天的
        #print(yesterday_prefix)
        await find_directory(root_directory,yesterday_prefix)

        #await asyncio.sleep(100)
        await asyncio.sleep(7200)

if __name__ == "__main__":
    asyncio.run(main())