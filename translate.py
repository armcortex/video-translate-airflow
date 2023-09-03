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


def get_completion(prompt: str, model="gpt-3.5-turbo-0613") -> str:
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


def split_chunks(file, block_size: int=10):
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
        tmp.append('\n')
        yield len(tmp), ''.join(tmp)


def convert(filename: str):
    out_filename = filename.replace('.srt', '_out.srt')
    line_cnt = file_line_count(filename)
    progress_bar = tqdm(total=line_cnt, desc="Processing")

    with open(filename, 'r', encoding='utf-8') as ifile, \
            open(out_filename, 'a+', encoding='utf-8') as ofile:        
        for cnt, chunk in split_chunks(ifile, BLOCK_SIZE):
            res = get_completion(chunk) + '\n'
            tqdm.write(f'Translate: \n {res}')
            # tqdm.write(f'\n\n')
            ofile.write(res)
            progress_bar.update(cnt)
    
        progress_bar.close()

def main():
    FILE_PATH = './data/geohot-medium-en.wav.srt'
    # FILE_PATH = './sample_2.srt'
    convert(FILE_PATH)


if __name__ == '__main__':
    main()

#     srt_content = """
# 1
# 00:00:00,000 --> 00:00:05,040
#  Hey everyone, welcome to the LatentSpace podcast.

# 2
# 00:00:05,040 --> 00:00:10,180
#  This is Swix, writer and editor of LatentSpace, and Alessio is taking over with the intros

# 3
# 00:00:10,180 --> 00:00:12,800
#  Alessio's partner and CTO and residents at Decibel Partners.
# """

#     srts = parse_srt(srt_content)
#     for srt in tqdm(srts):
#         res = get_completion(srt)
#         tqdm.write(f'Original: \n {srt}')
#         tqdm.write(f'{"-"*5} \n')
#         tqdm.write(f'Translate: \n {res}')
#         tqdm.write(f'\n\n')
            