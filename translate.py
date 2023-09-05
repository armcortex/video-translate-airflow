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

from prompt import system_prompt


BLOCK_SIZE = 1
TMP_FOLDER = 'tmp'
TMP_FILE = 'part_'
RATE_LIMIT = 90000


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
    """Combine Original Content and translated sentences"""
    tmp = chunk[:2]
    data = data.replace('\n', '')
    tmp.append(f' {data}\n')
    tmp.extend(chunk[2:])
    return tmp


def convert(filename: str, verbose: bool=False, cpu_cnt: int=16):
    openai.api_key = os.environ.get('OPENAI_API_KEY_VIDEO_TRANSLATE_AIRFLOW')
    curr_process = multiprocessing.current_process()

    out_filename = filename.replace('.srt', '_out.srt')
    line_cnt = file_line_count(filename)
    progress_bar = tqdm(total=line_cnt, nrows=cpu_cnt, 
                        desc=f'{curr_process.name} {filename} Processing')

    # Read subtitle srt file and translate via OpenAI GPT model
    with open(filename, 'r', encoding='utf-8') as ifile, \
            open(out_filename, 'a+', encoding='utf-8') as ofile:        
        for cnt, chunk in split_chunks(ifile, BLOCK_SIZE):
            res = get_completion(f'#zh-tw {chunk[2]}', sys_prompt=system_prompt.SYSTEM_PROMPT_8) + '\n'
            res = srt_combine(chunk, res)
            res = ''.join(res)
            if verbose:
                tqdm.write(f'{filename=}, {curr_process.name=}, {curr_process.pid=}')
                tqdm.write(f'Translate: \n {res}')
            ofile.write(res)
            progress_bar.update(cnt)
    
        progress_bar.close()


def convert_test(filename: str):
    line_cnt = file_line_count(filename)
    progress_bar = tqdm(total=line_cnt, desc="Processing")

    with open(filename, 'r', encoding='utf-8') as ifile:
        for cnt, chunk in split_chunks(ifile, BLOCK_SIZE):
            # tqdm.write(f'Translate: \n {"".join(chunk)}')
            progress_bar.update(cnt)
            time.sleep(0.5)

def multi_threading_running(func, queries, n=20):
    # @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    def wrapped_function(query, max_try=20):
        try:
            result = func(query)
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
    # if line_cnt % cpu_cnt != 0:
    #     raise ValueError(f'Check {filename} content, it can\'t divide by {cpu_cnt}')
    block_size = line_cnt // cpu_cnt // 4

    # Split into files
    tmp_filenames = []
    with open(filename, 'r', encoding='utf-8') as ifile:
        for i, (cnt, chunk) in enumerate(split_chunks(ifile, block_size)):
            tmp_filename = TMP_FOLDER + f'/{TMP_FILE}{i}.srt'
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
    cmd = ['sed', '-i', '', '$d', f'{os.getcwd()}/{tmp_filenames[-1]}']
    execute_shell_cmd(cmd)
    

    # # Parallel translate via OpenAI
    # results = Parallel(n_jobs=cpu_cnt, verbose=10)(
    #     delayed(convert)(name, False) for name in tmp_filenames)
    
    replies = multi_threading_running(convert, tmp_filenames, n=cpu_cnt)
    print(f'{replies=}')

    # Combine all part_*.srt files
    filename_out = f'{TMP_FOLDER}/' + filename.replace('.srt', '_out.srt')
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
    # FILE_PATH = './data/geohot-medium-en.wav.srt'
    # FILE_PATH = './sample_2.srt'
    # convert(FILE_PATH, verbose=True)
    # FILE_PATH = './2023_EuroLLVM_-_Prototyping_MLIR_in_Python.srt'
    FILE_PATH = './geohot-medium-en.wav.srt'
    convert_parallel(FILE_PATH)
    t1 = time.perf_counter()
    print(f'test2() execute time: {t1-t0:.2f} sec, {(t1-t0)/60:.2f} min')

    # print(f'cnt: {file_line_count(FILE_PATH)}')


if __name__ == '__main__':
    main()



    # import tempfile
    # import os

    # def save_to_temp_files(data_list):
    #     # 分割列表為8等分
    #     chunk_size = len(data_list) // 8
    #     chunks = [data_list[i:i+chunk_size] for i in range(0, len(data_list), chunk_size)]

    #     # 創建臨時資料夾
    #     with tempfile.TemporaryDirectory() as tmpdirname:
    #         print(f"Created temporary directory: {tmpdirname}")
            
    #         # 將每一份數據保存到臨時檔案中
    #         for idx, chunk in enumerate(chunks, 1):
    #             temp_file_path = os.path.join(tmpdirname, f"temp_file_{idx}.txt")
    #             with open(temp_file_path, 'w') as f:
    #                 for item in chunk:
    #                     f.write(f"{item}\n")
    #             print(f"Saved chunk {idx} to {temp_file_path}")

    # # 測試函數
    # data = list(range(1, 101))  # 一個範例列表，包含1到100的整數
    # save_to_temp_files(data)
