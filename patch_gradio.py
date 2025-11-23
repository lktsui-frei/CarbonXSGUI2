import os

file_path = "/home/lktsui/anaconda3/envs/carbon_xs_gui/lib/python3.9/site-packages/gradio/oauth.py"

with open(file_path, "r") as f:
    content = f.read()

content = content.replace("from huggingface_hub import HfFolder, whoami", "from huggingface_hub import get_token, whoami")
content = content.replace("token = HfFolder.get_token()", "token = get_token()")

with open(file_path, "w") as f:
    f.write(content)

print("Patched gradio/oauth.py")
