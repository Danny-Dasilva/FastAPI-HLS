ffmpeg -i my_video.mp4                    \
       -c:v libx264                       \
       -b:v 3000k                         \
       -bufsize:v 6000k                   \
       -maxrate:v 6000k                   \
       -c:a aac                           \
       -b:a 128k                          \
       -hls_list_size 0                   \
       -hls_time 6                        \
       video.m3u8


# ffmpeg -i my_video.mp4                    \
#        -c:v libx264                       \
#        -b:v 3000k                         \
#        -bufsize:v 6000k                   \
#        -maxrate:v 6000k                   \
#        -c:a aac                           \
#        -b:a 128k                          \
#        -hls_list_size 0                   \
#        -hls_time 6                        \
#        -hls_base_url "{{ video_path }}/"  \
#        video.m3u8