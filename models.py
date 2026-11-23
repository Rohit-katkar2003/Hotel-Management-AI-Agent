from openai import OpenAI

client = OpenAI(
    base_url="https://token.sensenova.ai/v1",
    api_key="sk-dT4KQ7npDneuTrz6gSqHaY4NPoBtv7Jk",
)

models = client.models.list()

for model in models.data:
    print(model.id)