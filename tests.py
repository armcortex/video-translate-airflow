import time
from tqdm import tqdm
from translate import get_completion
from prompt import system_prompt


def parse_srt(chunk):
    return [part.strip() for part in chunk.split("\n\n") if part.strip()]


def test1():
    contents = """
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

    srts = parse_srt(contents)
    for srt in tqdm(srts):
        res = get_completion(srt)
        tqdm.write(f'Original: \n {srt}')
        tqdm.write(f'{"-"*5} \n')
        tqdm.write(f'Translate: \n {res}')
        tqdm.write(f'\n\n')

def test2():
    t0 = time.perf_counter()
    contents = ["Hey everyone, welcome to the LatentSpace podcast.",
                "This is Swix, writer and editor of LatentSpace, and Alessio is taking over with the intros",
                "Alessio's partner and CTO and residents at Decibel Partners.",
                "Hey everyone, today we have GeoHot on the podcast, aka George Hotz for the human name.",
                "Everybody knows George, so I'm not going to do a big intro.",
                "A couple of things that people might have missed.",
                "So you were the first to unlock the iPhone.",
                "You traded the first ever unlocked iPhone for a Nissan 350Z and three new iPhones.",
                "You were then one of the first people to break into the PS3 around arbitrary code.",
                "You got sued by Sony, you wrote a rap song to fight against that, which is still live"]

    for srt in tqdm(contents):
        res = get_completion(srt, sys_prompt=system_prompt.SYSTEM_PROMPT_8)
        tqdm.write(f'Original: \n {srt}')
        tqdm.write(f'Translate: \n {res}')
        tqdm.write(f'{"-"*5} \n')
    t1 = time.perf_counter()
    print(f'test2() execute time: {t1-t0:.2f} sec')

def test3():
    t0 = time.perf_counter()
    contents = ["Hey everyone, welcome to the LatentSpace podcast.",
                "This is Swix, writer and editor of LatentSpace, and Alessio is taking over with the intros",
                "Alessio's partner and CTO and residents at Decibel Partners.",
                "Hey everyone, today we have GeoHot on the podcast, aka George Hotz for the human name.",
                "Everybody knows George, so I'm not going to do a big intro.",
                "A couple of things that people might have missed.",
                "So you were the first to unlock the iPhone.",
                "You traded the first ever unlocked iPhone for a Nissan 350Z and three new iPhones.",
                "You were then one of the first people to break into the PS3 around arbitrary code.",
                "You got sued by Sony, you wrote a rap song to fight against that, which is still live"]

    res = get_completion(contents, sys_prompt=system_prompt.SYSTEM_PROMPT_8)
    tqdm.write(f'Original: \n {contents}')
    tqdm.write(f'Translate: \n {res}')
    tqdm.write(f'{"-"*5} \n')
    
    t1 = time.perf_counter()
    print(f'test2() execute time: {t1-t0:.2f} sec')

if __name__ == '__main__':
    # test1()
    test2()
    test3()
