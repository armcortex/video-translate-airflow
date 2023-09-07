import time
import os

from langchain.llms import LlamaCpp
from langchain import PromptTemplate, LLMChain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from prompt import system_prompt


# TW Model
MODEL_BASE_PATH = os.environ.get('LLAMA_CPP_MODEL_TW_PATH')
MODEL_NAME = '/Taiwan-LLaMa-13b-1.0.ggmlv3.q4_K_M.bin'
# MODEL_NAME = '/Taiwan-LLaMa-13b-1.0.ggmlv3.q4_K_M.bin'
# MODEL_NAME = '/Taiwan-LLaMa-13b-1.0.ggmlv3.q4_0.bin'
# MODEL_NAME = '/Taiwan-LLaMa-13b-1.0.ggmlv3.q5_0.bin'

# wizard-vicuna-13B
# MODEL_BASE_PATH = os.environ.get('LLAMA_CPP_MODEL_BASE_PATH')
# MODEL_NAME = '/wizard-vicuna/13B/Wizard-Vicuna-13B-Uncensored.ggmlv3.q4_K_M.bin'
# MODEL_NAME = '/wizard-vicuna/13B/wizard-vicuna-13B.ggmlv3.q4_K_M.bin'

# wizardlm-1.0
# MODEL_NAME = '/wizardlm/13B/wizardlm-1.0-uncensored-llama2-13b.ggmlv3.q4_K_M.bin'

MODEL_PATH = MODEL_BASE_PATH + MODEL_NAME

PROMPT = './prompt/translate-zh-tw-prompt.txt'

def main_1():
    from llama_cpp import Llama

    llm = Llama(model_path=MODEL_PATH, n_gpu_layers=1)
    output = llm("Q: Name the planets in the solar system? A: ", max_tokens=32, stop=["Q:", "\n"], echo=True)
    print(f'LLM Response: {output}')

def main():
    llm = LlamaCpp(
        model_path=MODEL_PATH,
        n_gpu_layers=1,
        n_threads=8,
        n_ctx=2048,
        n_batch=32,
        temperature=0,
        use_mlock=True,
        stop=['</end>'],
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        verbose=True,
    )

    system_template = system_prompt.SYSTEM_PROMPT
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = "{text}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    
    chain = LLMChain(prompt=chat_prompt, llm=llm)
    
    texts = [
        "<Subtitle>:\n24\n00:01:21,720 --> 00:01:23,400\n Just the question of, do you think it's for you?",
        "<Subtitle>:\n25\n00:01:23,400 --> 00:01:25,440\n And if you think it's for you, buy it.",
        "<Subtitle>:\n26\n00:01:25,440 --> 00:01:26,480\n It's a consumer product."]


    t0 = time.perf_counter()
    for t in texts:
        chain.run(text=t)

    t1 = time.perf_counter()
    print(f'Execute Time: {t1-t0:.2f} sec, {(t1-t0)/60:.2f} min')


if __name__ == '__main__':
    main()
