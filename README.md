# FastAPI-HLS
FastAPI HLS streaming test repo



## M3U8 master playlist creator ##
* Uses FFMPEG tool in Python by using a OS command call
* Install FFMPEG for Ubuntu OS using terminal. Follow instructions here: https://tecadmin.net/install-ffmpeg-on-linux/
* Following are explanations of the options used in the FFMPEG tool:
	- `-c:v libx264` is the codec:video. Here we use the x264 codec to have a h264 output format
	- `-crf 20` is the video quality. 51 is the worst quality and 1 the best
	- `-g 5 -keyint_min 5` sets group picture size to 5. Video source is 5 FPS. So each second will start with a new picture group. Create key frame every 5 frames and start new picture group
	- `-sc_threshold 0` indicates don't create key frames on scene change, only according to -g
	- `-hls_time 4` slices the video and audio into segments with a duration of 4 seconds
	- `-hls_flags independent_segments` indicates that all media samples in a Media Segment can be decoded without information from other segments
	- `-b:v:0` sets the bitate for stream 0 (the lower quality)
	- `-filter:v:0 scale=640:360` scales stream 0 to the desired resolution
	- `-map v:x` tells ffmpeg that a new video variant starts. x is the number of input video signal. Since only one video input, index 0 is used here
	- `-f hls` defines the output format HLS
	- `-var_stream_map “v:0 v:1 v:2 v:3”` tells FFmpeg what streams are combined together. A space separates each variant and everything that should be placed together is concatenated with a comma(if audio as well)
	- `-master_pl_name master.m3u8` creates the new master playlist that contains the list of streams
	- `-hls_segment_filename stream_%v/data%03d.ts` sets the name of the segment file. Folder is added named “stream_%v”. %v is the stream variant. The %03d in the filename is a formatted number. 03 means fill the number up with 0 up to 3 digits
	- `-use_localtime_mkdir 1` adds base-url to the playlist files so that the variant streams' segments can be located
* Refer to FFMPEG Documentation for further use or check out this tutorial: https://www.martin-riedl.de/2018/08/24/using-ffmpeg-as-a-hls-streaming-server-part-1/
