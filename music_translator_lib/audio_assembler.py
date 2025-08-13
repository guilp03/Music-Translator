import os
import math
from pydub import AudioSegment

# Supondo que a classe VoiceGenerator esteja disponível para type hinting
# from voice_generator import VoiceGenerator 

class AudioAssembler:
    """
    Monta uma faixa vocal final a partir de segmentos de texto traduzido,
    alinhando a duração de cada segmento gerado com a duração original.
    """
    
    def __init__(self, tts_generator):
        """
        Inicializa o montador de áudio.
        
        Args:
            tts_generator: Uma instância já carregada da classe VoiceGenerator.
        """
        if not hasattr(tts_generator, 'tts_model') or tts_generator.tts_model is None:
            raise ValueError("Uma instância válida e carregada de VoiceGenerator é necessária.")
        self.tts = tts_generator.tts_model # Acessa o modelo TTS interno do gerador
        print("AudioAssembler pronto para uso.")

    def _speed_change(self, sound, speed=1.0):
        """
        (Privado) Altera a velocidade do áudio via reamostragem (resampling).
        Ótima alternativa ao speedup() do pydub para desaceleração.
        """
        sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed)
        })
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    def assemble_vocal_track(self, 
                             segmentos_traduzidos: list, 
                             audio_referencia_path: str, 
                             output_filename: str = "vocal_final_traduzido_e_alinhado.wav"):
        """
        Gera, alinha e monta a faixa vocal completa.
        
        Args:
            segmentos_traduzidos (list): A lista de segmentos com tempos e textos.
            audio_referencia_path (str): Caminho para o áudio com a voz a ser clonada.
            output_filename (str): Nome do arquivo final a ser exportado.
            
        Returns:
            str: O caminho para o arquivo final gerado, ou None se falhar.
        """
        if not segmentos_traduzidos:
            print("❌ Lista de segmentos traduzidos está vazia. Abortando montagem.")
            return None

        # --- Preparação para a Montagem ---
        duracao_total_musica_ms = math.ceil(segmentos_traduzidos[-1]['fim']) * 1000
        faixa_vocal_final = AudioSegment.silent(duration=duracao_total_musica_ms)
        
        pasta_segmentos_temp = "segmentos_alinhados_temp"
        os.makedirs(pasta_segmentos_temp, exist_ok=True)
        print("\nIniciando geração e alinhamento de cada segmento...")

        # --- Loop Principal de Geração e Montagem ---
        for i, seg in enumerate(segmentos_traduzidos):
            duracao_original_s = seg['fim'] - seg['inicio']

            if duracao_original_s < 0.2:
                print(f"   Segmento {i} pulado (muito curto).")
                continue

            print(f"-> Processando segmento {i}/{len(segmentos_traduzidos)}: '{seg['texto_traduzido']}'")

            # 1. Gera o áudio para o segmento de texto traduzido
            caminho_temp = os.path.join(pasta_segmentos_temp, f"temp_{i}.wav")
            self.tts.tts_to_file(
                text=seg['texto_traduzido'],
                speaker_wav=audio_referencia_path,
                language="pt",
                file_path=caminho_temp
            )

            # 2. Carrega e mede o áudio gerado
            audio_gerado = AudioSegment.from_wav(caminho_temp)
            duracao_gerada_s = len(audio_gerado) / 1000.0
            if duracao_gerada_s == 0: continue

            # 3. Calcula e aplica o ajuste de velocidade
            fator_velocidade = duracao_gerada_s / duracao_original_s
            print(f"   Duração Original: {duracao_original_s:.2f}s | Gerada: {duracao_gerada_s:.2f}s | Fator: {fator_velocidade:.2f}x")

            if fator_velocidade < 1.0:
                audio_alinhado = self._speed_change(audio_gerado, fator_velocidade)
            else:
                audio_alinhado = audio_gerado.speedup(playback_speed=fator_velocidade)

            # 4. Adiciona (overlay) o segmento na faixa final na posição correta
            posicao_inicio_ms = seg['inicio'] * 1000
            faixa_vocal_final = faixa_vocal_final.overlay(audio_alinhado, position=posicao_inicio_ms)

        print("\n✅ Montagem de todos os segmentos concluída!")

        # --- Exportação Final ---
        faixa_vocal_final.export(output_filename, format="wav")
        print(f"✅ Faixa vocal final salva em: '{output_filename}'")
        
        return output_filename