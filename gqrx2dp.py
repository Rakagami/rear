import time, logging
from datetime import datetime
import threading, collections, queue, os, os.path
import deepspeech
import numpy as np
import pyaudio
import wave
import webrtcvad
from halo import Halo
from scipy import signal
import socket

import collections

logging.basicConfig(filename="test.log", level=logging.DEBUG)

sampleRate = 48000
ip = "127.0.0.1"
port = 7355
nchannels = 1
bps = 16 # bit per sample

def listener():
    # Create a UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = (ip, port)
    s.bind(server_address)
    print("Start Listening")

    frames_per_buffer = 1920
    tmpbuf = b""

    global buf
    while True:
        if(buf.qsize() > 100):
            logging.debug(f"High Queue size: {buf.qsize()}")
        data, address = s.recvfrom(4096)
        ##bytesum += len(data)
        if(len(tmpbuf)>frames_per_buffer):
            buf.put(tmpbuf[:frames_per_buffer])
            tmpbuf = tmpbuf[frames_per_buffer:] + data
        elif((len(tmpbuf) + len(data)) > frames_per_buffer):
            tmpbuf = tmpbuf + data
            buf.put(tmpbuf[:frames_per_buffer])
            tmpbuf = tmpbuf[frames_per_buffer:]
        else:
            tmpbuf = tmpbuf + data

class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    # Network/VAD rate-space
    RATE_PROCESS = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    def __init__(self, callback=None, device=None, input_rate=RATE_PROCESS, file=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            #pylint: disable=unused-argument
            #global buf
            #while(len(buf) == 0):
            #    pass
            #if len(buf) > 0:
            #    in_data = buf.popleft()
            #else:
            #    in_data = b"\0\0" * 960
            #callback(in_data)
            in_data = b"\0\0" * 960
            return (None, pyaudio.paContinue)
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data)
        self.buffer_queue = queue.Queue()
        self.device = device
        self.input_rate = input_rate
        self.sample_rate = self.RATE_PROCESS
        self.block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
        self.block_size_input = int(self.input_rate / float(self.BLOCKS_PER_SECOND))
        self.pa = pyaudio.PyAudio()

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.input_rate,
            'frames_per_buffer': self.block_size_input,
            'input': True,
            'stream_callback': proxy_callback,
        }

        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

    def resample(self, data, input_rate):
        """
        Microphone may not support our native processing sampling rate, so
        resample from input_rate to RATE_PROCESS here for webrtcvad and
        deepspeech

        Args:
            data (binary): Input audio stream
            input_rate (int): Input audio rate to resample from
        """
        data16 = np.frombuffer(buffer=data, dtype=np.int16)
        resample_size = int(len(data16) / self.input_rate * self.RATE_PROCESS)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tobytes()

    def read_resampled(self):
        """Return a block of audio data resampled to 16000hz, blocking if necessary."""
        global buf
        data = buf.get()
        return self.resample(data=data,
                             input_rate=self.input_rate)
        #return self.resample(data=self.buffer_queue.get(),
        #                     input_rate=self.input_rate)

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        global buf
        data = buf.get()
        return data
        #return self.buffer_queue.get()

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def write_wav(self, filename, data):
        logging.info("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close()


class VADAudio(Audio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, aggressiveness=3, device=None, input_rate=None, file=None):
        super().__init__(device=device, input_rate=input_rate, file=file)
        self.vad = webrtcvad.Vad(aggressiveness)

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        if self.input_rate == self.RATE_PROCESS:
            while True:
                yield self.read()
        else:
            while True:
                yield self.read_resampled()

    def vad_collector(self, padding_ms=300, ratio=0.75, frames=None):
        """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None: frames = self.frame_generator()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            if len(frame) < 640:
                print("length of frame")
                return

            is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

def main(ARGS):
    # Load DeepSpeech model
    if os.path.isdir(ARGS.model):
        model_dir = ARGS.model
        ARGS.model = os.path.join(model_dir, 'output_graph.pb')
        ARGS.scorer = os.path.join(model_dir, ARGS.scorer)

    print('Initializing model...')
    logging.info("ARGS.model: %s", ARGS.model)
    model = deepspeech.Model(ARGS.model)
    if ARGS.scorer:
        logging.info("ARGS.scorer: %s", ARGS.scorer)
        model.enableExternalScorer(ARGS.scorer)

    global buf
    #buf = collections.deque(maxlen=1000)
    buf = queue.Queue()

    # Start listener thread
    print("Starting listener thread")
    t1 = threading.Thread(target=listener)
    t1.start()

    # Start audio with VAD
    vad_audio = VADAudio(aggressiveness=ARGS.vad_aggressiveness,
                         device=None,
                         input_rate=ARGS.rate,
                         file=None)
    frames = vad_audio.vad_collector()

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    if not ARGS.nospinner:
        spinner = Halo(spinner='line')
    stream_context = model.createStream()
    cnt = 0
    for frame in frames:
        if frame is not None and cnt < 1000:
            cnt = cnt + 1
            if spinner: spinner.start()
            logging.debug("streaming frame")
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
        else:
            cnt = 0
            if spinner: spinner.stop()
            logging.debug("end utterence")
            text = stream_context.finishStream()
            print("Recognized: %s" % text)
            stream_context = model.createStream()

    #while True:
    #    for _ in range(1000):
    #        stream_context.feedAudioContent(np.frombuffer(buf.get(), np.int16))
    #    text = stream_context.finishStream()
    #    print("Recognized: %s" % text)
    #    stream_context = model.createStream()
        #if frame is not None:
        #    stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
        #else:
        #    text = stream_context.finishStream()
        #    print("Recognized: %s" % text)
        #stream_context = model.createStream()

if __name__ == '__main__':
    DEFAULT_SAMPLE_RATE = 16000

    import argparse
    parser = argparse.ArgumentParser(description="Stream from GQRX udp output to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=3,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: 3")
    parser.add_argument('--nospinner', action='store_true',
                        help="Disable spinner")

    parser.add_argument('-m', '--model', required=True,
                        help="Path to the model (protocol buffer binary file, or entire directory containing all standard-named files for model)")
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.")
    parser.add_argument('-r', '--rate', type=int, default=DEFAULT_SAMPLE_RATE,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100.")

    parser.add_argument('-i', '--ip', type=str, default="localhost",
                        help="IP Address of UDP source. Default is localhost")

    parser.add_argument('-p', '--port', type=str, default=None, required=True,
                        help="Port of UDP source.")

    ARGS = parser.parse_args()
    main(ARGS)
