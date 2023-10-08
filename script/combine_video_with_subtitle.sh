#!/bin/bash

ORG_VIDEO_PATH='/Users/mcs51/code_playground/llm_embeddings_practice_storge/video/tmp_video/Open_AI_Sam_Altman_AI-MTjb1ps8iVs/Open_AI_Sam_Altman_AI-MTjb1ps8iVs.vod.mp4'
OUTPUT_VIDEO_PATH='/Users/mcs51/code_playground/llm_embeddings_practice_storge/video/tmp_video/Open_AI_Sam_Altman_AI-MTjb1ps8iVs/Open_AI_Sam_Altman_AI-MTjb1ps8iVs.vod-subtitle.mp4'
SUBTITLE_PATH='/Users/mcs51/code_playground/llm_embeddings_practice_storge/video/tmp_video/Open_AI_Sam_Altman_AI-MTjb1ps8iVs/Open_AI_Sam_Altman_AI-MTjb1ps8iVs.vod-resampled.wav_out.srt'

ffmpeg -i "${ORG_VIDEO_PATH}" \
    -hide_banner \
    -loglevel error \
    -vf "subtitles='${SUBTITLE_PATH}':force_style='Alignment=2'" \
    -y "${OUTPUT_VIDEO_PATH}";