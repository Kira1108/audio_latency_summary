import logging

logging.basicConfig(level = logging.INFO)
import asyncio
import os
import json
from pathlib import Path
from typing import List

import websockets

from read_audio import ByteChunkReader
from utils import get_api_uri, make_uid


async def send_audio_chunks(websocket, audio_chunks:List[bytes], results:List, iid:str = None):
    interval = 0.04
    start_time = asyncio.get_event_loop().time()
    chunk_index = 0
    results.append({"action_type":"begin", "timestamp":start_time, "iid":iid})
    
    while True:
        expected_time = start_time + (chunk_index+1) * interval
        now = asyncio.get_event_loop().time()
        await asyncio.sleep(max(0, expected_time - now))
        
        audio_chunk = audio_chunks[chunk_index]
        await websocket.send(audio_chunk)
        results.append({"action_type":"sent", "timestamp":asyncio.get_event_loop().time(), "iid":iid, "chunk_index":chunk_index+1})
        chunk_index += 1
        
        if chunk_index >= len(audio_chunks):
            break
    await websocket.send('{"type": "end"}')
    
async def receive_responses(websocket, results:List, iid:str = None):
    try:
        async for message in websocket:
            data = json.loads(message)
            results.append({"action_type":"recv", "timestamp":asyncio.get_event_loop().time(), "iid":iid, "data":data})
            
            if data.get("final", 0) == 1:
                await websocket.close()
                print("Connection closed normally.")
                break
    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed abnormally.")

        
async def audio_main(audio_chunks:List[bytes], vad_slience:int = 200):
    iid = make_uid()
    uri = get_api_uri(vad_slience=vad_slience)
    
    results = []
    async with websockets.connect(uri) as websocket:
        auth_response = await websocket.recv()
    
        success = json.loads(auth_response)['code'] == 0
        if success:
            logging.info("Connection success")

        send_task = asyncio.create_task(send_audio_chunks(websocket, audio_chunks, results,iid = iid))
        recv_task = asyncio.create_task(receive_responses(websocket, results, iid = iid))

        await asyncio.gather(send_task, recv_task)
        results.append({"action_type":"end", "timestamp":asyncio.get_event_loop().time(), "iid":iid})
        
    return results

def asr_file(fname):
    logging.info(f"Processing {fname}")
    out_dir = Path(__file__).parent / "outputs"
    in_dir = Path(__file__).parent / "data"
    reader = ByteChunkReader(chunk_duration_ms=40)
    fp = in_dir / fname
    chunks = reader.read_chunks(str(fp))
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(audio_main(chunks, vad_slience=240))
    out_fp = out_dir / f"{fp.stem}.json"
    with open(out_fp, "w") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    logging.info(f"Results saved to {out_fp}")
    logging.info(f"Finished processing {fname}")


if __name__ == "__main__":
    fnames = os.listdir("data")
    for fname in fnames:
        asr_file(fname)
    
    
    
