# app.py

import gradio as gr
import os
from dotenv import load_dotenv

# --- 1. IMPORTAÇÃO DE TODAS AS SUAS FERRAMENTAS ---
# app.py

import gradio as gr
import os
from dotenv import load_dotenv

# --- 1. IMPORTAÇÃO CORRETA DAS SUAS FERRAMENTAS ---
from music_translator_lib.music_separator import MusicSeparator
from music_translator_lib.lyric_translator import LyricTranslator
from music_translator_lib.voice_generator import VoiceGenerator
from music_translator_lib.audio_assembler import AudioAssembler
from music_translator_lib.final_mixer import FinalMixer

# ... o resto da sua classe MusicTranslatorApp e o código do Gradio continuam aqui ...


class MusicTranslatorApp:
    """
    Encapsula toda a aplicação Gradio para a tradução de músicas.
    Esta classe constrói a UI e orquestra as chamadas para as classes de lógica.
    """
    
    CSS = """
    .status-container { display: flex; justify-content: space-around; align-items: center; width: 100%; gap: 10px; }
    .status-step { text-align: center; font-weight: bold; color: #888; padding: 10px; border: 3px solid #DDD; border-radius: 15px; flex: 1; transition: all 0.3s ease-in-out; }
    .status-step.active { border-color: #3B82F6; color: #3B82F6; transform: scale(1.05); }
    .status-step.completed { border-color: #16A34A; color: #16A34A; }
    .status-step.error { border-color: #EF4444; color: #EF4444; }
    .status-step .icon { font-size: 2em; }
    .status-step .text { font-size: 0.9em; }
    """

    def __init__(self, separator, translator, generator, assembler, mixer):
        """
        Inicializa a aplicação com todas as dependências (as classes de lógica).
        """
        self.separator = separator
        self.translator = translator
        self.generator = generator
        self.assembler = assembler
        self.mixer = mixer
        self.demo = self._build_ui()

    def _create_status_html(self, icon, text, css_class=""):
        return f'<div class="status-step {css_class}"><div class="icon">{icon}</div><div class="text">{text}</div></div>'

    def _main_pipeline(self, audio_path, ajuste_volume_db=0):
        """
        O coração da orquestração. Esta função é um gerador (yield) que
        executa o pipeline passo a passo e atualiza a UI.
        """
        if not audio_path:
            yield {self.status_main: gr.update(value="Erro: Nenhum arquivo de áudio enviado.")}
            return

        try:
            # --- ETAPA 1: SEPARAÇÃO ---
            yield {
                self.status_separation: gr.update(value=self._create_status_html("🎵✂️", "Separação", "active")),
                self.status_main: gr.update(value="Iniciando separação de vocais e instrumental...")
            }
            stems = self.separator.separar(audio_path)
            if not stems or 'vocals' not in stems or 'accompaniment' not in stems:
                raise Exception("A separação de faixas falhou ou não retornou os arquivos esperados.")
            caminho_vocal, caminho_instrumental = stems['vocals'], stems['accompaniment']

            # --- ETAPA 2: TRADUÇÃO ---
            yield {
                self.status_separation: gr.update(value=self._create_status_html("🎵✂️", "Separação", "completed")),
                self.status_translation: gr.update(value=self._create_status_html("🌐", "Tradução", "active")),
                self.status_main: gr.update(value="Transcrevendo e traduzindo a letra...")
            }
            segmentos_originais = self.translator.extrair_letra_com_tempos(caminho_vocal)
            segmentos_traduzidos = self.translator.traduzir_segmentos(segmentos_originais)
            if not segmentos_traduzidos:
                raise Exception("A tradução da letra falhou.")

            # --- ETAPA 3: MONTAGEM DO NOVO VOCAL ---
            yield {
                self.status_translation: gr.update(value=self._create_status_html("🌐", "Tradução", "completed")),
                self.status_assembly: gr.update(value=self._create_status_html("🎤", "Montagem Vocal", "active")),
                self.status_main: gr.update(value="Gerando e alinhando a nova faixa vocal...")
            }
            caminho_vocal_novo = self.assembler.assemble_vocal_track(
                segmentos_traduzidos=segmentos_traduzidos,
                audio_referencia_path=caminho_vocal
            )
            if not caminho_vocal_novo:
                raise Exception("A montagem do novo vocal falhou.")

            # --- ETAPA 4: MIXAGEM FINAL ---
            yield {
                self.status_assembly: gr.update(value=self._create_status_html("🎤", "Montagem Vocal", "completed")),
                self.status_mixing: gr.update(value=self._create_status_html("🎚️", "Mixagem Final", "active")),
                self.status_main: gr.update(value="Mixando novo vocal com o instrumental...")
            }
            caminho_musica_final = self.mixer.mixar_faixas(
                caminho_vocal=caminho_vocal_novo,
                caminho_instrumental=caminho_instrumental,
                caminho_saida="musica_final_traduzida.wav",
                ajuste_volume_vocal_db=ajuste_volume_db
            )
            if not caminho_musica_final:
                raise Exception("A mixagem final falhou.")

            # --- ETAPA 5: RESULTADO ---
            yield {
                self.status_mixing: gr.update(value=self._create_status_html("🎚️", "Mixagem Final", "completed")),
                self.status_result: gr.update(value=self._create_status_html("🎶", "Resultado", "active")),
                self.status_main: gr.update(value="Processo concluído com sucesso!"),
                self.audio_output: gr.update(value=caminho_musica_final, visible=True),
                self.process_button: gr.update(visible=False),
                self.download_audio_button: gr.update(visible=True)
            }

        except Exception as e:
            # Lida com qualquer erro no pipeline e atualiza a UI
            print(f"ERRO NO PIPELINE: {e}")
            yield {self.status_main: gr.update(value=f"Erro: {e}")}


    def _reset_ui(self):
        """Reseta a interface para o estado inicial."""
        return {
            self.status_separation: gr.update(value=self._create_status_html("🎵✂️", "Separação")),
            self.status_translation: gr.update(value=self._create_status_html("🌐", "Tradução")),
            self.status_assembly: gr.update(value=self._create_status_html("🎤", "Montagem Vocal")),
            self.status_mixing: gr.update(value=self._create_status_html("🎚️", "Mixagem Final")),
            self.status_result: gr.update(value=self._create_status_html("🎶", "Resultado")),
            self.audio_output: gr.update(visible=False, value=None),
            self.process_button: gr.update(visible=True),
            self.download_audio_button: gr.update(visible=False),
            self.status_main: gr.update(value="Aguardando arquivo de áudio...")
        }

    def _build_ui(self):
        """Constrói a interface do Gradio."""
        with gr.Blocks(css=self.CSS, theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🤖 Music Translator AI")
            gr.Markdown("### Faça o upload de uma música e deixe a IA criar uma versão em português!")
            
            with gr.Row(elem_classes="status-container"):
                self.status_separation = gr.HTML(self._create_status_html("🎵✂️", "Separação"))
                self.status_translation = gr.HTML(self._create_status_html("🌐", "Tradução"))
                self.status_assembly = gr.HTML(self._create_status_html("🎤", "Montagem Vocal"))
                self.status_mixing = gr.HTML(self._create_status_html("🎚️", "Mixagem Final"))
                self.status_result = gr.HTML(self._create_status_html("🎶", "Resultado"))

            self.status_main = gr.Textbox(label="Status do Processo", value="Aguardando arquivo de áudio...", interactive=False)
            
            with gr.Row():
                self.audio_input = gr.Audio(type="filepath", label="Faça o Upload da sua Música")
                self.audio_output = gr.Audio(label="Música Traduzida", visible=False)

            with gr.Row():
                self.volume_slider = gr.Slider(minimum=-12, maximum=12, value=0, step=1, label="Ajuste de Volume do Vocal (dB)")
                self.process_button = gr.Button("Iniciar Processamento", variant="primary")
                self.download_audio_button = gr.Button("Baixar Música Traduzida ⬇️", visible=False)

            # --- Eventos da Interface ---
            self.process_button.click(
                fn=self._main_pipeline,
                inputs=[self.audio_input, self.volume_slider],
                outputs=[
                    self.status_separation, self.status_translation, self.status_assembly,
                    self.status_mixing, self.status_result, self.audio_output,
                    self.process_button, self.download_audio_button, self.status_main
                ]
            )

            self.audio_input.upload(
                fn=self._reset_ui,
                inputs=None,
                outputs=[
                    self.status_separation, self.status_translation, self.status_assembly,
                    self.status_mixing, self.status_result, self.audio_output,
                    self.process_button, self.download_audio_button, self.status_main
                ]
            )
        return demo

    def launch(self):
        """Inicia a aplicação Gradio."""
        self.demo.launch(debug=True)


if __name__ == "__main__":
    # --- PONTO DE ENTRADA DA APLICAÇÃO ---
    
    print("Carregando configurações...")
    load_dotenv()
    
    # Carrega as chaves de API do arquivo .env
    MUSIC_AI_KEY = os.getenv("MUSIC_AI_API_KEY")
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

    print("Inicializando todos os módulos de processamento...")
    try:
        # Instancia todas as classes de lógica
        separator = MusicSeparator(api_key=MUSIC_AI_KEY)
        translator = LyricTranslator(openai_api_key=OPENAI_KEY)
        generator = VoiceGenerator()
        assembler = AudioAssembler(tts_generator=generator)
        mixer = FinalMixer()

        # Instancia e inicia a aplicação Gradio, injetando as dependências
        app = MusicTranslatorApp(separator, translator, generator, assembler, mixer)
        app.launch()
        
    except Exception as e:
        print(f"\n[ERRO FATAL] Não foi possível inicializar a aplicação: {e}")
        print("Verifique suas chaves de API no arquivo .env e se todos os modelos necessários estão acessíveis.")