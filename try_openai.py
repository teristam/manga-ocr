from openai import OpenAI

client = OpenAI()

response = client.audio.speech.create(
    model="tts-1-hd",
    voice="alloy",
    input="今は、この都市のガードに追われている",
)

response.stream_to_file("output.mp3")