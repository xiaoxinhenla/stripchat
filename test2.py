import subprocess
url="https://edge-hls.doppiocdn.live/hls/184345968/master/184345968_auto.m3u8?playlistType=lowLatency"
m3u8_name="out.m3u8"
command = [
        "ffmpeg", 
        "-re", "-rtbufsize", "100M", "-i", url, 
        "-c:v", "copy","-c:a", "aac", "-b:a", "128K",
        "-f", "hls", "-hls_time", "10",  "-hls_flags", 
        "append_list+independent_segments", 
        "-hls_playlist_type", "event", m3u8_name, "-reconnect", "1","-reconnect_streamed","1","-reconnect_delay_max","5"
    ]

command2 = [
        "ffmpeg", 
        "-re", "-rtbufsize", "100M", "-i", url, 
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128K",
        "-f", "hls", "-hls_time", "10",  "-hls_flags", 
        "delete_segments+append_list+independent_segments", 
        "-hls_playlist_type", "event", m3u8_name
    ]
ffmpeg_command=" ".join(command2)
print(ffmpeg_command)
process=subprocess.Popen(ffmpeg_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
stdout,stderr=process.communicate()