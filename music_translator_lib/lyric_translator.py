import os
import stable_whisper
from openai import OpenAI

class LyricTranslator:
    """
    Encapsula o processo de transcrever um áudio para obter segmentos de
    letras com marcação de tempo e, em seguida, traduzir esses segmentos.
    """

    # O prompt do sistema é uma constante da classe, bem definido aqui.
    _PROMPT_SISTEMA = """
Você é um tradutor especialista em letras de música, traduzindo do Inglês para o Português do Brasil.
Sua tarefa é traduzir a letra a seguir.

Regras importantes:
1.  **Contexto é tudo**: Não traduza literally. Capture a emoção, a poesia e o significado da música.
2.  **Métrica e Ritmo (Regra Adicionada)**: Este é um ponto crucial. Esforce-se para que a contagem de sílabas fonéticas de cada verso em português seja o mais próxima possível da contagem do verso original em inglês. O objetivo é criar uma versão que possa ser cantada, mantendo o fluxo e a cadência da melodia original.
3.  **Consistência no Refrão**: Versos que se repetem (como refrões ou pontes) DEVEM ser traduzidos exatamente da mesma forma todas as vezes que aparecerem.
4.  **Formato de Saída**: A letra está numerada. Retorne a tradução mantendo EXATAMENTE a mesma numeração linha por linha. Não adicione ou remova linhas. O formato deve ser:
    NÚMERO: Tradução da linha

Exemplo de saída esperada:
0: Tradução da primeira linha
1: Tradução da segunda linha
2: Tradução da terceira linha
...
"""

    def __init__(self, openai_api_key: str, whisper_model_name: str = 'medium'):
        """
        Inicializa os modelos necessários para transcrição e tradução.
        
        Args:
            openai_api_key (str): A chave da API da OpenAI.
            whisper_model_name (str): O nome do modelo Stable Whisper a ser carregado (ex: 'medium', 'large-v3').
        """
        print("Inicializando o LyricTranslator...")
        
        # 1. Carregar o modelo Whisper
        print(f"Carregando o modelo Whisper '{whisper_model_name}'...")
        self.whisper_model = stable_whisper.load_model(whisper_model_name)
        print("-> Modelo Whisper carregado.")

        # 2. Configurar o cliente da OpenAI
        if not openai_api_key:
            raise ValueError("A chave da API da OpenAI é obrigatória.")
        self.openai_client = OpenAI(api_key=openai_api_key)
        print("-> Cliente OpenAI pronto.")

    def extrair_letra_com_tempos(self, caminho_audio_vocal: str, language: str = 'en') -> list:
        """
        Transcreve o áudio para extrair os segmentos de texto com seus tempos de início e fim.
        
        Args:
            caminho_audio_vocal (str): O caminho para o arquivo de áudio dos vocais.
            language (str): O idioma do áudio original (ex: 'en', 'pt').
            
        Returns:
            list: Uma lista de objetos de segmento do Stable Whisper.
        """
        print(f"\nTranscrevendo '{caminho_audio_vocal}' para obter o mapa de tempo...")
        resultado_whisper = self.whisper_model.transcribe(caminho_audio_vocal, language=language, regroup=True)
        
        segmentos_originais = resultado_whisper.segments
        print(f"-> Extração de tempo concluída! {len(segmentos_originais)} segmentos de áudio encontrados.")
        
        print("Exemplo dos 3 primeiros segmentos e seus tempos:")
        for i, seg in enumerate(segmentos_originais[:3]):
            print(f"   Segmento {i}: '{seg.text.strip()}' -> Início: {seg.start:.2f}s, Fim: {seg.end:.2f}s")
            
        return segmentos_originais

    def traduzir_segmentos(self, segmentos_originais: list) -> list:
        """
        Traduz uma lista de segmentos de texto usando a API da OpenAI.
        
        Args:
            segmentos_originais (list): A lista de segmentos gerada pelo método extrair_letra_com_tempos.
            
        Returns:
            list: Uma lista de dicionários, cada um contendo os tempos, o texto original e o texto traduzido.
        """
        if not segmentos_originais:
            print("A lista de segmentos originais está vazia. Não há nada para traduzir.")
            return []

        # Formata a letra inteira para uma única chamada de API
        letra_completa_numerada = ""
        for i, seg in enumerate(segmentos_originais):
            letra_completa_numerada += f"{i}: {seg.text.strip()}\n"

        print("\nLetra original formatada para envio à OpenAI:")
        print(letra_completa_numerada)

        print("Iniciando a tradução com a OpenAI... (Isso pode levar um momento)")
        segmentos_traduzidos_final = []
        try:
            resposta_openai = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self._PROMPT_SISTEMA},
                    {"role": "user", "content": letra_completa_numerada}
                ],
                temperature=0.3
            )
            traducao_bruta = resposta_openai.choices[0].message.content

            print("\nTradução recebida. Processando o resultado...")
            traducoes_mapeadas = {}
            for linha in traducao_bruta.strip().split('\n'):
                partes = linha.split(':', 1)
                if len(partes) == 2:
                    try:
                        numero = int(partes[0])
                        texto_traduzido = partes[1].strip()
                        traducoes_mapeadas[numero] = texto_traduzido
                    except ValueError:
                        print(f"Aviso: Ignorando linha mal formatada da IA: '{linha}'")
                        continue
            
            # Monta a lista final combinando dados originais com a tradução
            for i, seg in enumerate(segmentos_originais):
                texto_original = seg.text.strip()
                texto_traduzido = traducoes_mapeadas.get(i, texto_original) # Usa original como fallback

                segmentos_traduzidos_final.append({
                    "inicio": seg.start,
                    "fim": seg.end,
                    "texto_original": texto_original,
                    "texto_traduzido": texto_traduzido
                })
                print(f"   Segmento {i}: '{texto_original}' -> '{texto_traduzido}'")

            print("\nTradução com OpenAI concluída com sucesso!")

        except Exception as e:
            print(f"\n[ERRO] Ocorreu um erro ao chamar a API da OpenAI: {e}")
            print("A lista 'segmentos_traduzidos_final' pode estar vazia ou incompleta.")
            
        return segmentos_traduzidos_final