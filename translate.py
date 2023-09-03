import subprocess
import os
import time
import openai
from tqdm import tqdm
from prompt import system_prompt

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW')
openai.api_key = OPENAI_API_KEY
BLOCK_SIZE = 1



def file_line_count(fname: str) -> int:
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])


def get_completion(prompt: str, model="gpt-3.5-turbo-0613", sys_prompt=system_prompt.SYSTEM_PROMPT_6) -> str:
    messages = [{'role': 'system', 'content': sys_prompt}]
    if isinstance(prompt, str):
            content = {'role': 'user', 'content': prompt}
            messages.append(content)
    elif isinstance(prompt, list):
        for p in prompt:
            content = {'role': 'user', 'content': p}
            messages.append(content)
    else:
        raise ValueError(f'Prompt type not supported')

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["</END>"]
    )
    return response.choices[0].message["content"]


def split_chunks(file, block_size: int=10):
    tmp = []
    block_cnt = 0
    for line in file:
        if line == '\n':
            tmp.append('\n')
            if block_cnt >= block_size-1:
                block_cnt = 0
                yield len(tmp), tmp
                tmp = []
            else:
                block_cnt += 1
        else:
            tmp.append(line)
    
    # Make sure no remain
    if tmp:
        tmp.append('\n')
        yield len(tmp), tmp


def srt_combine(chunk: list, data: str) -> list:
    tmp = chunk[:2]
    tmp.append(f' {data}')
    tmp.extend(chunk[2:])
    return tmp

def convert(filename: str):
    out_filename = filename.replace('.srt', '_out.srt')
    line_cnt = file_line_count(filename)
    progress_bar = tqdm(total=line_cnt, desc="Processing")

    # Read subtitle srt file and translate via OpenAI GPT model
    with open(filename, 'r', encoding='utf-8') as ifile, \
            open(out_filename, 'a+', encoding='utf-8') as ofile:        
        for cnt, chunk in split_chunks(ifile, BLOCK_SIZE):
            res = get_completion(chunk[2], sys_prompt=system_prompt.SYSTEM_PROMPT_8) + '\n'
            res = srt_combine(chunk, res)
            res = ''.join(res)
            tqdm.write(f'Translate: \n {res}')
            ofile.write(res)
            progress_bar.update(cnt)
    
        progress_bar.close()

def main():
    # FILE_PATH = './data/geohot-medium-en.wav.srt'
    FILE_PATH = './sample_2.srt'
    convert(FILE_PATH)


if __name__ == '__main__':
    main()

