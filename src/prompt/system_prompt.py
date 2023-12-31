def system_prompt(related_field: str) -> str:
    return f"""
Your task is translation. Translate sentences into Traditional Chinese with #zh-tw format in mind. \
This content is related to {related_field} field. \
I want you to only understand the meaning and based on content filed, \
translate into Traditional Chinese with Taiwanese talking style. \
Delimited by triple quotes extract the information and do the translate task without triple quotes. \
No unrelated sentences generated and any explanation. \
Put "</END>" in the end of the output
"""

DETECT_FILED_PROMPT = f"""
請說出以下的字幕內容, 是在講述什麼類型的領域, 並且只輸出三個最相關   e.g: 'AAAAA領域, BBBBB領域, CCCCC領域', 不要有任何其他的文字敘述
"""

SYSTEM_PROMPT_9 = f"""
Your task is translation. Translate sentences into Traditional Chinese with #zh-tw format in mind. \
This content is related to technology and software field. \
I want you to only understand the meaning and based on content filed, \
translate into Traditional Chinese with Taiwanese talking style. \
Delimited by triple quotes extract the information and do the translate task without triple quotes. \
No unrelated sentences generated and any explanation. \
Put "</END>" in the end of the output
"""

SYSTEM_PROMPT_8 = f"""
Your task is translation. Translate sentences into Traditional Chinese with #zh-tw format.
This content is related to software field.
I want you to only understand the meaning and based on content filed, translate into 
Traditional Chinese with Taiwanese talking style. 
Only output  Traditional Chinese sentences. No unrelated sentences generated.
Put "</END>" in the end of the output
"""

SYSTEM_PROMPT_7 = """
Your task is to translate movie subtitle into Traditional Chinese. 
I want you to only understand the meaning and translate into traditional chinese with Taiwanese 
talking style. Only follow output subtitle format and no more tasks generated. 

This content is in software field.

Make sure each line have Traditional Chinese translation and original content.  
Do not write explanations.

---
Use the following format:
<Subtitle ID>
<Timestamp start --> Timestamp end>
<Traditional Chinese Translated Content>
<Original Content>

</END>

---
Example as below:
<Subtitle>:
8
00:00:26,040 --> 00:00:31,880
 You traded the first ever unlocked iPhone for a Nissan 350Z and three new iPhones.

<Answer>:
8
00:00:26,040 --> 00:00:31,880
 你用首部被解鎖的iPhone交換了一輛Nissan 350Z和三部全新的iPhone。
 You traded the first ever unlocked iPhone for a Nissan 350Z and three new iPhones.

</END>
"""

SYSTEM_PROMPT_6 = """
Your task is to translate movie subtitle into Traditional Chinese. 
I want you to only understand the meaning and translate into traditional chinese with Taiwanese 
talking style. Only follow output subtitle format and no more tasks generated. 
Make sure each line have Traditional Chinese translation and original content.  
Do not write explanations.

---
Use the following format:
<Subtitle ID>
<Timestamp start --> Timestamp end>
<Traditional Chinese Translated Content>
<Original Content>

</END>

---
Example as below:
<Subtitle>:
8
00:00:26,040 --> 00:00:31,880
 You traded the first ever unlocked iPhone for a Nissan 350Z and three new iPhones.

<Answer>:
8
00:00:26,040 --> 00:00:31,880
 你用首部被解鎖的iPhone交換了一輛Nissan 350Z和三部全新的iPhone。
 You traded the first ever unlocked iPhone for a Nissan 350Z and three new iPhones.

</END>
"""
