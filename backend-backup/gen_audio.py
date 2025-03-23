from csm_mlx import CSM, csm_1b, generate, Segment
import mlx.core as mx
from pathlib import Path
from huggingface_hub import hf_hub_download

from mlx_lm.utils import make_sampler

import audiofile
import audresample
import numpy as np

def read_audio(audio_path, sampling_rate=24000) -> mx.array:
    signal, original_sampling_rate = audiofile.read(audio_path, always_2d=True)
    signal = audresample.resample(signal, original_sampling_rate, sampling_rate)

    signal = mx.array(signal)

    if signal.shape[0] >= 1:
        signal = signal.mean(axis=0)
    else:
        signal = signal.squeeze(0)

    return signal  # (audio_length, )

# Initialize the model
csm = CSM(csm_1b())
weight = hf_hub_download(repo_id="senstella/csm-1b-mlx", filename="ckpt.safetensors")
csm.load_weights(weight)



# Create previous conversation segments
context = [
    Segment(
        speaker=0,
        text="I wanted to be Judy Garland when I was uhm, when I was growing up. My mom was, is an enormous cinephile, I grew up with all the movies of the golden age, and musicals, Rogers and Hammerstein musicals - That I",
        audio=read_audio(Path("videoplayback.wav"), 24_000), # Previous audio for this segment
    ),

]

# Generate a response in the conversation
sampler = make_sampler(
    temp=0.8,
    top_p=0.0,
    min_p=0.05,
    top_k=-1,
    min_tokens_to_keep=1,
)

import sys

audio = generate(
    csm,
    # text="So, um, honey bees have this fascinating way of communicating called the 'waggle dance' - it's just... it's probably one of the most sophisticated forms of communication in the animal kingdom outside of human language. When a bee finds a good source of food, it returns to the hive and does this specific dance pattern that tells the other bees exactly where the food is. The angle of the dance shows the direction relative to the sun, and the duration indicates the distance. Isn't that amazing? They're basically giving coordinates! And they maintain this incredible social structure with, like, 50,000 bees in a single hive, all with different jobs. The queen lays up to, I think, 2,000 eggs a day? The whole system is just so... so perfectly organized. And get this - a single bee might visit, um, like 100 flowers in one trip, and they'll make about a twelfth of a teaspoon of honey in their entire lifetime. Makes you appreciate that jar of honey a lot more, doesn't it?",
    text=sys.stdin.read(),
    speaker=0,
    context=context,
    max_audio_length_ms=50 * 1000,
    sampler=sampler
)

# Save the generated audio to a file
output_path = sys.argv[1] if len(sys.argv) > 1 else "generated_audio.wav"
audio_np = np.array(audio.tolist())
audiofile.write(output_path, audio_np, 24000)
print(f"Audio saved to {output_path}")
