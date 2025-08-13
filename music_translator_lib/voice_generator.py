import os
import torch
from TTS.api import TTS

class VoiceGenerator:
    """
    Encapsula o modelo Coqui XTTS para síntese de voz.
    """
    
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        """
        Inicializa e carrega o modelo de Text-to-Speech.
        
        Args:
            model_name (str): O nome do modelo TTS a ser carregado.
        """
        print("Inicializando o VoiceGenerator...")

        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # Configura o dispositivo (GPU se disponível, senão CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Usando o dispositivo: {self.device}")
        
        # Carrega o modelo
        print(f"Carregando o modelo XTTS '{model_name}'...")
        try:
            self.tts_model = TTS(model_name).to(self.device)
            print("✅ Modelo carregado e pronto para ser usado!")
        except Exception as e:
            print(f"❌ Erro ao carregar o modelo: {e}")
            self.tts_model = None

    def sintetizar_voz(self, texto: str, audio_referencia_path: str, output_path: str):
        """
        Gera um áudio a partir do texto, usando um áudio de referência para clonar a voz.
        
        Args:
            texto (str): O texto que será falado.
            audio_referencia_path (str): Caminho para o arquivo de áudio com a voz a ser clonada.
            output_path (str): Caminho onde o arquivo de áudio gerado será salvo.
        """
        if not self.tts_model:
            print("❌ O modelo TTS não foi carregado corretamente. Não é possível sintetizar.")
            return

        print(f"\nSintetizando o texto: '{texto}'")
        print(f"Usando a voz de referência de: '{audio_referencia_path}'")
        try:
            # Usa o método tts_to_file para gerar e salvar o áudio
            self.tts_model.tts_to_file(
                text=texto,
                speaker_wav=audio_referencia_path,
                language="pt", # Defina o idioma do texto aqui
                file_path=output_path
            )
            print(f"✅ Áudio sintetizado e salvo em: '{output_path}'")
        except Exception as e:
            print(f"❌ Erro durante a síntese de voz: {e}")