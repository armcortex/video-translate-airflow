#!/bin/bash

MODEL_BASE_PATH=$(echo ${LLAMA_CPP_MODEL_PATH})
MODEL_NAME='Taiwan-LLaMa-13b-1.0.ggmlv3.q4_0.bin'
MODEL=${MODEL_BASE_PATH}/${MODEL_NAME}

echo "Model Path: " ${MODEL}
echo "PWD: " $(pwd)
pipenv run python -m llama_cpp.server \
    --model ${MODEL} \
    --n_gpu_layers 1