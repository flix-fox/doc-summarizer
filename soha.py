from TTS.utils.manage import ModelManager

model_name = "tts_models/multilingual/multi-dataset/your_tts"
manager = ModelManager()
path = manager.download_model(model_name)
print(f"Model downloaded to: {path}")
