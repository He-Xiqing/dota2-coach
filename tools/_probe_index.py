import httpx

url = "https://pypi.tuna.tsinghua.edu.cn/simple/pyinstaller/"
text = httpx.get(url, timeout=60).text
idx = text.find("win_amd64")
print("len", len(text), "idx", idx)
print(repr(text[max(0, idx - 260): idx + 120]))
print("contains .whl:", ".whl" in text)
print("href count:", text.count("href="))
