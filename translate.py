import subprocess
import os
import time
import openai
from tqdm import tqdm
from prompt import system_prompt

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW')
openai.api_key = OPENAI_API_KEY
BLOCK_SIZE = 10



def file_line_count(fname):
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])


def get_completion(prompt, model="gpt-3.5-turbo-0613"):
    messages = [{'role': 'system', 'content': system_prompt.SYSTEM_PROMPT_6},
                {'role': 'user', 'content': prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=BLOCK_SIZE*100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["</END>"]
    )
    return response.choices[0].message["content"]


def parse_srt(chunk):
    return [part.strip() for part in chunk.split("\n\n") if part.strip()]


def main():
    srt_content = """
1
00:00:00,000 --> 00:00:05,040
 Hey everyone, welcome to the LatentSpace podcast.

2
00:00:05,040 --> 00:00:10,180
 This is Swix, writer and editor of LatentSpace, and Alessio is taking over with the intros

3
00:00:10,180 --> 00:00:12,800
 Alessio's partner and CTO and residents at Decibel Partners.
"""

    srts = parse_srt(srt_content)
    for srt in tqdm(srts):
        res = get_completion(srt)
        tqdm.write(f'Original: \n {srt}')
        tqdm.write(f'{"-"*5} \n')
        tqdm.write(f'Translate: \n {res}')
        tqdm.write(f'\n\n')


    # res = get_completion(srt_content)
    # print(res)


def split_chunks(file, block_size=10):
    tmp = []
    block_cnt = 0
    for line in file:
        if line == '\n':
            tmp.append('\n')
            if block_cnt >= block_size-1:
                block_cnt = 0
                yield len(tmp), ''.join(tmp)
                tmp = []
            else:
                block_cnt += 1
        else:
            tmp.append(line)
    
    # Make sure no remain
    if tmp:
        yield len(tmp), ''.join(tmp)


if __name__ == '__main__':
    # main()

    FILE_PATH = './sample_1.srt'
    line_cnt = file_line_count(FILE_PATH)
    progress_bar = tqdm(total=line_cnt, desc="Processing")

    with open(FILE_PATH, 'r', encoding='utf-8') as ifile, \
            open('./sample_1_out.srt', 'w', encoding='utf-8') as ofile:
        
        for cnt, chunk in split_chunks(ifile, BLOCK_SIZE):
            # tqdm.write(f'Chunk: \n{chunk}')
            # tqdm.write(f'{"-"*5} \n')

            res = get_completion(chunk)
            # tqdm.write(f'Original: \n {srt}')
            # tqdm.write(f'{"-"*5} \n')
            tqdm.write(f'Translate: \n {res}')
            tqdm.write(f'\n\n')

            ofile.write(chunk)
            progress_bar.update(cnt)
            # time.sleep(1)
            