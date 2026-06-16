download ffmpeg from https://ffmpeg.org/download.html
=> Windows => Windows builts by BtbN => ffmpeg-master-latest-win64-gpl-shared.zip

unzip and save to D:\Videos\Tools\ffmpeg 
set even path to D:\Videos\Tools\ffmpeg\bin


ffmpeg -i bowen_1.mp4 ^
-c copy ^
-f hls ^
-hls_time 15 ^
-hls_list_size 0 ^
index.m3u8

Recommended command for your family video server

ffmpeg -i input.mp4 ^
-c:v libx264 ^
-preset medium ^
-crf 24 ^
-c:a aac ^
-b:a 128k ^
-force_key_frames "expr:gte(t,n_forced*10)" ^
-f hls ^
-hls_time 10 ^
-hls_list_size 0 ^
-hls_flags independent_segments ^
index.m3u8


Even better, for internet streaming I would use:

ffmpeg -i bowen_1.mp4 ^
-c:v libx264 ^
-preset medium ^
-crf 23 ^
-c:a aac ^
-b:a 128k ^
-f hls ^
-hls_time 10 ^
-hls_list_size 0 ^
-hls_flags independent_segments ^
index.m3u8



ffmpeg -i bowen_1.mp4 -c:v libx264 -b:v 1500k -c:a aac -b:a 192k -f mpegts output.ts