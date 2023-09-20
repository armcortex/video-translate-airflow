import threading
import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import os
import shutil
import time
import openai
from tqdm import tqdm
from joblib import Parallel, delayed
import backoff
import tiktoken
import re


from prompt import system_prompt

API_KEYS = ['OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW', 
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW2',
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW3',
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW4',
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW5',
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW6',
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW7',
            'OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW8',]

BLOCK_SIZE = 1

FILE_BASE = os.getcwd()
TMP_FOLDER = FILE_BASE + '/tmp'
TMP_FILE = '/part_'



class CalcToken:
    def __init__(self) -> None:
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def calc_tokens(self, s: str) -> int:
        return len(self.enc.encode(s))

calc_token = CalcToken()
g_total_tokens = 0
token_lock = threading.Lock()


def execute_shell_cmd(cmds: list):
    p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    if result:
        return int(result.strip().split()[0])


def file_line_count(fname: str) -> int:
    return execute_shell_cmd(['wc', '-l', fname])


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
@backoff.on_exception(backoff.expo, openai.error.ServiceUnavailableError)
@backoff.on_exception(backoff.expo, openai.error.Timeout)
def get_completion(prompt: str, maxtoken=1024, model="gpt-3.5-turbo-16k-0613", sys_prompt=system_prompt.SYSTEM_PROMPT_6) -> str:
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
        max_tokens=maxtoken,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["</END>"]
    )
    return response.choices[0].message["content"]


def clean_str(ss: str) -> str:
    ss = re.sub(r'<[^ ]*', '\n', ss)
    ss = re.sub(r'#zh[^\s\n]+', '\n', ss)
    ss = ss.replace('   ', ' ')
    ss = ss.replace('  ', ' ')

    clean_list = ['```', '"', '>>', '「', '」', '<']
    for c in clean_list:
        if c in ss:
            ss = ss.replace(c, '')

    return ss


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
    """Combine Original Content and translated sentences"""
    tmp = chunk[:2]
    data = data.replace('\n', '')
    tmp.append(f' {data}\n')
    tmp.extend(chunk[2:])
    return tmp


def convert(filename: str, verbose: bool=False, cpu_cnt: int=16):
    api_key = API_KEYS.pop()
    openai.api_key = os.environ.get(api_key)
    curr_process = multiprocessing.current_process()

    out_filename = filename.replace('.srt', '_out.srt')
    line_cnt = file_line_count(filename)
    pbar = tqdm(total=line_cnt, nrows=cpu_cnt)

    cnt_total = 0
    total_tokens = 0
    request_cnt = 0

    # Read subtitle srt file and translate via OpenAI GPT model
    with open(filename, 'r', encoding='utf-8') as ifile, \
            open(out_filename, 'a+', encoding='utf-8') as ofile:        
        for cnt, chunk in split_chunks(ifile, BLOCK_SIZE):
            pbar.set_description(f'{curr_process.name} {filename.split("/")[-1]} Processing')
            en_token_cnt = calc_token.calc_tokens(''.join(chunk[2]))

            res = get_completion(f'```{chunk[2]}```', int(en_token_cnt*3.5), sys_prompt=system_prompt.SYSTEM_PROMPT_9) + '\n'
            res = srt_combine(chunk, res)

            # Calc tokens
            zh_tw_token_cnt = calc_token.calc_tokens(''.join(res[3]))
            total_tokens += (en_token_cnt + zh_tw_token_cnt)

            # Update global variable
            global g_total_tokens
            with token_lock:
                g_total_tokens += (en_token_cnt + zh_tw_token_cnt)

            request_cnt += 1

            # Calculate items per second
            unit = (pbar.format_dict['elapsed'] if pbar.format_dict['elapsed'] > 0 else 1)
            token_per_min = (total_tokens * 60) / unit
            g_token_per_min = (g_total_tokens * 60) / unit
            request_per_min = (request_cnt * 60) / unit


            # Update progress bar with custom postfix
            pbar.set_postfix(TPM=f"{token_per_min:.2f} token/min", 
                                gTPM=f"{g_token_per_min:.2f} token/min",
                                RPM=f"{request_per_min:.2f} token/min",
                                refresh=True)

            # Final process format
            res = ''.join(res)
            res = clean_str(res)
            if verbose:
                tqdm.write(f'{filename=}, {curr_process.name=}, {curr_process.pid=}')
                tqdm.write(f'Translate: \n {res}')
            ofile.write(res)
            cnt_total += cnt
            pbar.update(cnt)
        pbar.close()


def multi_threading_running(func, queries, n=4):
    def wrapped_function(query, max_try=20):
        try:
            result = func(query, True)
            return result
        except (openai.error.RateLimitError, openai.error.APIError) as e:
            if not isinstance(e, openai.error.RateLimitError):
                if isinstance(e, openai.error.APIError):
                    print("API Error")
                else:
                    print("found a error:", e)
            if max_try > 0:
                return wrapped_function(query, max_try-1)

    pool = ThreadPool(n)
    replies = pool.map(wrapped_function, queries)
    return replies


def convert_parallel(filename: str):
    # Check folder 
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
        print(f'Folder "{TMP_FOLDER}" created!')
    else:
        print(f'Folder "{TMP_FOLDER}" already exists!')
        shutil.rmtree(TMP_FOLDER)
        os.makedirs(TMP_FOLDER)

    # Calc Parallel needed info
    line_cnt = file_line_count(filename)
    cpu_cnt = multiprocessing.cpu_count()
    block_size = line_cnt // cpu_cnt // 4

    # Split into files
    tmp_filenames = []
    with open(filename, 'r', encoding='utf-8') as ifile:
        for i, (cnt, chunk) in enumerate(split_chunks(ifile, block_size)):
            tmp_filename = TMP_FOLDER + f'{TMP_FILE}{i}.srt'
            tmp_filenames.append(tmp_filename)
            with open(tmp_filename, 'w', encoding='utf-8') as ofile:
                ofile.write(''.join(chunk))

    # Make sure tmp_filenames % cpu_cnt == 0
    with open(tmp_filenames[cpu_cnt-1], 'a', encoding='utf-8') as ofile:
        for f in tmp_filenames[cpu_cnt:]:
            with open(f, 'r', encoding='utf-8') as ifile:
                ofile.write(ifile.read())
            os.remove(f)
            tmp_filenames.pop()
            
    # Delete the last line
    cmd = ['sed', '-i', '', '$d', f'{tmp_filenames[-1]}']
    execute_shell_cmd(cmd)
    

    # # Parallel translate via OpenAI
    # results = Parallel(n_jobs=cpu_cnt, verbose=10)(
    #     delayed(convert)(name, False) for name in tmp_filenames)
    
    replies = multi_threading_running(convert, tmp_filenames, n=cpu_cnt)
    print(f'{replies=}')

    # Combine all part_*.srt files
    filename_out = f'{TMP_FOLDER}/' + filename.split('/')[-1].replace('.srt', '_out.srt')
    with open(filename_out, 'w', encoding='utf-8') as ofile:
        for tmp_filename in tmp_filenames:
            tmp_filename = tmp_filename.replace('.srt', '_out.srt')

            # Open part_*.srt file and combine into 1 file
            with open(tmp_filename, 'r', encoding='utf-8') as ifile:
                while True:
                    chunk = ifile.read(4096)
                    if not chunk:
                        break
                    ofile.write(chunk)


def main():
    t0 = time.perf_counter()

    # FILE_PATH = FILE_BASE + '/sample/geohot-medium-en.wav.srt'
    FILE_PATH = FILE_BASE + '/sample/sample_1.srt'
    # FILE_PATH = FILE_BASE + '/sample/2023_EuroLLVM_-_Prototyping_MLIR_in_Python.srt'
    
    # convert(FILE_PATH, verbose=True)
    convert_parallel(FILE_PATH)
    t1 = time.perf_counter()
    print(f'execute time: {t1-t0:.2f} sec, {(t1-t0)/60:.2f} min')


if __name__ == '__main__':
    main()
    
