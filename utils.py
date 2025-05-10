import logging
logging.basicConfig(level = logging.INFO)
import base64
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
import random
import time
from uuid import uuid4

BASE_URL = "wss://asr.cloud.tencent.com/asr/v2/1259304765?"
PART_URL = "asr.cloud.tencent.com/asr/v2/1259304765?"

def make_uid():
    return base64.urlsafe_b64encode(uuid4().bytes).rstrip(b'=').decode('ascii')

def url_encode(component: str) -> str:
    return urllib.parse.quote(component)

def generate_hmac_sha1(
    message: str, 
    secret_key: str="") -> str:
    hmac_obj = hmac.new(secret_key.encode(), message.encode(), hashlib.sha1)
    hmac_digest = hmac_obj.digest()
    hmac_base64 = base64.b64encode(hmac_digest).decode('utf-8')
    return hmac_base64

def get_api_uri(vad_slience:int = 1000) -> str:
    params = [
        "engine_model_type=16k_zh",
        "needvad=1",
        f"timestamp={int(time.time())}",
        f"vad_silence={str(vad_slience)}",
        "secretid=",
        f"expired={int((datetime.now() + timedelta(days=1)).timestamp())}",
        f"voice_id={str(make_uid())}",
        "voice_format=1",
        "nonce=" + str(random.randint(100000, 999999)),
        
    ]
    params.sort()
    
    data = "&".join(params)
    
    # 用入参生成签名(原文档和明魁对)
    signature = generate_hmac_sha1(PART_URL + data)
    # 将签名进行url编码(原文档和明魁对)
    signature = url_encode(signature)
    # 拼接签名到入参字符串的最后(原文档和明魁对)
    info = data + f"&signature={signature}"
    # 拼接接口地址，这里调用的测试环境的接口(原文档和明魁对)
    return BASE_URL + info

