import os
from pydub import AudioSegment

class FinalMixer:
    """
    Uma classe responsável por mixar uma faixa vocal e uma faixa instrumental
    para criar a música final completa.
    """

    def __init__(self):
        """
        Inicializa o mixer de áudio.
        """
        print("FinalMixer pronto para juntar as faixas.")

    def mixar_faixas(self, 
                       caminho_vocal: str, 
                       caminho_instrumental: str, 
                       caminho_saida: str,
                       ajuste_volume_vocal_db: float = 0.0):
        """
        Carrega, ajusta o volume e mixa as faixas vocal e instrumental.

        Args:
            caminho_vocal (str): O caminho para o arquivo .wav da faixa vocal.
            caminho_instrumental (str): O caminho para o arquivo .wav da faixa instrumental.
            caminho_saida (str): O caminho onde a música final será salva.
            ajuste_volume_vocal_db (float): O ajuste de volume em dB a ser aplicado na faixa vocal. 
                                            Valores positivos aumentam, negativos diminuem.

        Returns:
            str: O caminho para o arquivo final mixado, ou None em caso de erro.
        """
        print("\nIniciando a junção da faixa vocal com o instrumental...")

        # 1. Verificação de Segurança
        if not os.path.exists(caminho_vocal):
            print(f"❌ ERRO: O arquivo do vocal não foi encontrado em '{caminho_vocal}'")
            return None
        if not os.path.exists(caminho_instrumental):
            print(f"❌ ERRO: O arquivo instrumental não foi encontrado em '{caminho_instrumental}'")
            return None

        try:
            # 2. Carregamento dos Arquivos
            print("Carregando arquivos de áudio...")
            instrumental = AudioSegment.from_wav(caminho_instrumental)
            vocal = AudioSegment.from_wav(caminho_vocal)

            # 3. Ajuste de Volume (Mixagem)
            print(f"Ajustando volume do vocal em: {ajuste_volume_vocal_db} dB")
            vocal_ajustado = vocal + ajuste_volume_vocal_db

            # 4. Junção (Overlay)
            print("Mixando as faixas...")
            musica_final = instrumental.overlay(vocal_ajustado)

            # 5. Exportação do Resultado Final
            musica_final.export(caminho_saida, format="wav")
            print(f"\n✅ Sucesso! Sua música completa foi salva em: '{caminho_saida}'")

            return caminho_saida

        except Exception as e:
            print(f"❌ ERRO durante a mixagem: {e}")
            return None