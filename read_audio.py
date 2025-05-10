import math
import time
from dataclasses import dataclass

import librosa
import wave
from typing import List


@dataclass
class SimpleAudioReader:
    
    target_sr: int = 16000
    
    def read(self, fp:str):
        """
        Reads audio data from a file.
        Args:
            fp (str): The file path to read audio data from.
        Returns:
            audio (np.ndarray): The audio data read from the file.
            sampling_rate (int): The sampling rate of the audio data.
        """
        audio, sampling_rate = librosa.load(fp, sr=None)
        
        if self.target_sr and sampling_rate != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sampling_rate, target_sr=self.target_sr)
            sampling_rate = self.target_sr
            
        return audio, sampling_rate
    
    def stream(self, fp: str, chunk_size: int = 1024, wait: bool = True):
        """
        Streams audio data from a file.
        Args:
            fp (str): The file path to stream audio data from.
            chunk_size (int): The size of each chunk to read from the file. Defaults to 1024.
            wait (bool): Whether to wait between chunks. Defaults to True.
        Yields:
            audio_chunk (np.ndarray): A chunk of audio data read from the file.
            is_final (bool): Whether this is the final chunk.
        """
        audio, _ = self.read(fp)
        
        chunk_seconds = chunk_size / self.target_sr
        num_chunks = math.ceil(len(audio) / chunk_size)
        
        for i in range(num_chunks):
            if wait:
                time.sleep(chunk_seconds)
            start = i * chunk_size
            end = start + chunk_size
            
            # Handle the case where the last chunk might be smaller than chunk_size
            audio_chunk = audio[start:end]
            is_final = i == num_chunks - 1
            yield audio_chunk, is_final
            
    def generate(self, fp:str, chunk_size:int = 1024):
        """
        Generates audio data from a file.
        Args:
            fp (str): The file path to generate audio data from.
            chunk_size (int): The size of each chunk to read from the file. Defaults to 1024.
        Yields:
            audio_chunk (np.ndarray): A chunk of audio data read from the file.
        """
        return self.stream(fp, chunk_size, wait = False)
    
    
@dataclass
class ByteChunkReader:
    """
    ByteChunkReader is a class for reading and splitting audio files into byte chunks.
    Attributes:
        chunk_duration_ms (int): Duration of each chunk in milliseconds. Default is 40ms.
    Methods:
        read(fp: str) -> Tuple[bytes, tuple]:
            Reads the entire PCM data from the given file path and returns it along with the wave file parameters.
            Args:
                fp (str): File path to the audio file.
            Returns:
                Tuple[bytes, tuple]: A tuple containing the PCM data and the wave file parameters.
        read_chunks(fp: str) -> List[bytes]:
            Reads the audio file and splits the PCM data into chunks.
            Args:
                fp (str): File path to the audio file.
            Returns:
                List[bytes]: A list of byte chunks.
    """
    
    chunk_duration_ms:int = 40
    
    def read(self, fp:str):
        with wave.open(fp, 'rb') as wf:
            params = wf.getparams()
            channels, sampwidth, framerate, nframes = params[:4]
            pcm_data = wf.readframes(nframes)
            return pcm_data, params
    
    def _split_chunks(self, pcm_data:bytes, params:list) -> List[bytes]:
        channels, sampwidth, framerate, nframes = params[:4]
        # 每秒16000， 40ms = 0.04s = 40/1000, frames = 16000 * 0.04 = 640, chunksize = frames per chunk * channels * sampwidth
        chunk_size = int(framerate * self.chunk_duration_ms / 1000) * channels * sampwidth
        chunks = [pcm_data[i:i + chunk_size] for i in range(0, len(pcm_data), chunk_size)]
        return chunks
    
    def read_chunks(self, fp:str) -> List[bytes]:
        pcm_data, params = self.read(fp)
        return self._split_chunks(pcm_data, params)

