import os
import ssl
import ssl



os.environ['GOOGLE_API_KEY'] = "AIzaSyBCssMj2I7_vdFiJVYhM9bRhoVwyQjq2I0"

from google import genai
client = genai.Client(http_options= {'api_version': 'v1alpha'})
MODEL = "gemini-2.0-flash-exp"



import asyncio
import base64
import contextlib
import datetime
import os
import json
import wave
import itertools
import logging
from IPython.display import display, Audio

from google import genai
from google.genai import types


async def async_enumerate(it):
  n = 0
  async for item in it:
    yield n, item
    n +=1

logger = logging.getLogger('Live')
logger.setLevel('INFO')

@contextlib.contextmanager
def wave_file(filename, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        yield wf

class AudioLoop:
  def __init__(self, turns=None,  config=None):
    self.session = None
    self.index = 0
    self.turns = turns
    if config is None:
      config={
          "generation_config": {
          "response_modalities": ["AUDIO"]
          }
      }
    self.config = config

  async def run(self):
    logger.debug('connect')
    async with client.aio.live.connect(model=MODEL, config=self.config) as session:
      self.session = session

      async for sent in self.send():
        # Ideally send and recv would be separate tasks.
        await self.recv()

  async def _iter(self):
    if self.turns:
      for text in self.turns:
        print("message >", text)
        yield text
    else:
      print("Type 'q' to quit")
      while True:
        text = await asyncio.to_thread(input, "message > ")

        # If the input returns 'q' quit.
        if text.lower() == 'q':
          break

        yield text
        

  async def send(self):
    async for text in self._iter():
      logger.debug('send')

      # Send the message to the model.
      await self.session.send(text, end_of_turn=True)
      logger.debug('sent')
      yield text

  async def recv(self):
    # Start a new `.wav` file.
    file_name = f"audio_{self.index}.wav"
    with wave_file(file_name) as wav:
      self.index += 1

      logger.debug('receive')

      # Read chunks from the socket.
      turn = self.session.receive()
      async for n, response in async_enumerate(turn):
        logger.debug(f'got chunk: {str(response)}')

        if response.data is None:
          logger.debug(f'Unhandled server message! - {response}')
        else:
          wav.writeframes(response.data)
          if n == 0:
            print(response.server_content.model_turn.parts[0].inline_data.mime_type)
          print('.', end='')

      print('\n<Turn complete>')

    display(Audio(file_name, autoplay=True))
    await asyncio.sleep(2)


async def run_audio_loop():
    await AudioLoop(['Kamu siapa?']).run()




asyncio.run(run_audio_loop())
if __name__ == "__main__":
  asyncio.run(run_audio_loop())