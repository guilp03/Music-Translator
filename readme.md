# Music Translator AI 🤖

[](https://www.python.org/downloads/)
[](https://opensource.org/licenses/MIT)

**Music Translator AI** é uma aplicação completa que utiliza um pipeline de múltiplas ferramentas de Inteligência Artificial para traduzir uma música de um idioma para outro (ex: Inglês para Português-BR), mantendo a cadência e o ritmo para que a nova versão possa ser cantada.

A aplicação separa a faixa vocal da instrumental, transcreve a letra com marcações de tempo precisas, traduz a letra de forma inteligente, clona a voz original para cantar a nova letra e, por fim, junta tudo em uma nova faixa de áudio. Tudo isso é controlado através de uma interface web simples e interativa criada com Gradio.

## ✨ Funcionalidades Principais

  - **Separação de Faixas:** Isola os vocais do acompanhamento instrumental usando a API da [Music.ai](http://music.ai).
  - **Transcrição com Timestamps:** Utiliza o `stable-whisper` para transcrever a letra original e obter o tempo exato de cada palavra/segmento.
  - **Tradução Inteligente:** Emprega modelos de linguagem avançados (GPT-4o via API da OpenAI) com prompts especializados para traduzir a letra, focando na métrica e na "cantabilidade".
  - **Clonagem de Voz e Síntese:** Usa o modelo `XTTS-v2` da Coqui TTS para gerar a nova faixa vocal em português, utilizando a voz do cantor original como referência.
  - **Alinhamento de Tempo:** Ajusta a velocidade de cada segmento vocal sintetizado para que ele se encaixe perfeitamente na duração do segmento original.
  - **Mixagem Final:** Junta a nova faixa vocal traduzida com a faixa instrumental original, com ajuste de volume.
  - **Interface Web Interativa:** Uma UI simples construída com Gradio para fazer o upload da música e acompanhar o processo passo a passo.

## 🏗️ Arquitetura do Projeto

O projeto é construído com uma arquitetura modular e orientada a objetos para garantir a separação de responsabilidades, facilidade de manutenção e testabilidade.

  - **Lógica de Negócio (`music_translator_lib/`):** Cada etapa principal do pipeline (separação, tradução, geração de voz, etc.) é encapsulada em sua própria classe Python.
  - **Orquestrador/UI (`app.py`):** Um script principal que contém a classe da aplicação Gradio. Ele é responsável por importar, instanciar e chamar os métodos das classes de lógica na sequência correta, atualizando a interface do usuário em tempo real.

<!-- end list -->

```
music-translator/
|
|-- .env                     # Armazena suas chaves de API
|-- .gitignore               # Ignora arquivos desnecessários
|-- requirements.txt         # Lista de dependências Python
|-- app.py                   # Ponto de entrada da aplicação Gradio
|
|-- music_translator_lib/      # Pacote com toda a lógica
|   |-- __init__.py          # Torna a pasta um pacote Python
|   |-- music_separator.py   # Classe MusicSeparator
|   |-- lyric_translator.py  # Classe LyricTranslator
|   |-- voice_generator.py   # Classe VoiceGenerator
|   |-- audio_assembler.py   # Classe AudioAssembler
|   +-- final_mixer.py       # Classe FinalMixer
|
+-- venv/                    # Pasta do ambiente virtual (ignorada pelo Git)
```

## 🚀 Instalação e Configuração

Siga estes passos para configurar e rodar o projeto em sua máquina local.

### Pré-requisitos

  - [Python](https://www.python.org/downloads/) 3.9 ou superior
  - [Git](https://git-scm.com/downloads/)
  - Acesso às APIs da [OpenAI](https://openai.com/api/) e [Music.ai](http://music.ai/)

### Passos de Instalação

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/music-translator-ai.git
    cd music-translator-ai
    ```

2.  **Crie e ative um ambiente virtual:**

      * No Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
      * No macOS e Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Instale as dependências:**
    Todas as bibliotecas necessárias estão listadas no `requirements.txt`. Instale-as com um único comando:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure suas chaves de API:**
    Crie uma cópia do arquivo de exemplo `.env.example` (se você o criou) ou crie um novo arquivo chamado `.env` na raiz do projeto. Adicione suas chaves de API secretas a ele.

    **Arquivo: `.env`**

    ```
    # Cole suas chaves secretas aqui
    MUSIC_AI_API_KEY="sua-chave-secreta-da-music-ai"
    OPENAI_API_KEY="sua-chave-secreta-da-openai"
    ```

    > ⚠️ **Importante:** O arquivo `.env` está listado no `.gitignore` e NUNCA deve ser enviado para o seu repositório público.

## ▶️ Como Rodar a Aplicação

Com o ambiente virtual ativado e as dependências instaladas, inicie a aplicação com um único comando:

```bash
python app.py
```

O terminal exibirá mensagens de inicialização e, em seguida, fornecerá as URLs para acessar a interface Gradio:

```
Running on local URL:  http://127.0.0.1:7860
Running on public URL: https://[hash-aleatorio].gradio.live
```

  - Abra a **URL Local** no seu navegador para usar a aplicação.
  - Use a **URL Pública** para compartilhar o acesso à sua aplicação com qualquer pessoa pela internet (válido por 72 horas, enquanto o script estiver rodando).

## 🔧 Como Funciona (O Pipeline)

1.  **Upload:** O usuário envia um arquivo de áudio (`.mp3`, `.wav`, etc.) pela interface do Gradio.
2.  **Separação:** A classe `MusicSeparator` é chamada, enviando o áudio para a API da Music.ai e recebendo de volta duas faixas: `vocals.wav` e `accompaniment.wav`.
3.  **Tradução:**
      - A classe `LyricTranslator` usa o `stable-whisper` para transcrever o `vocals.wav`, gerando a letra e os tempos de cada segmento.
      - Em seguida, ela envia a letra formatada para a API da OpenAI (GPT-4o), que a traduz para português seguindo as regras de métrica e contexto.
4.  **Montagem Vocal:**
      - A classe `AudioAssembler` itera sobre cada segmento de letra traduzida.
      - Para cada segmento, ela usa a classe `VoiceGenerator` (com o modelo XTTS) para sintetizar o áudio daquela linha, usando a voz do `vocals.wav` original como referência.
      - A duração do áudio sintetizado é ajustada (acelerada ou desacelerada) para corresponder perfeitamente à duração do segmento original na música.
      - Todos os segmentos alinhados são juntados para formar uma nova faixa vocal completa em português.
5.  **Mixagem Final:** A classe `FinalMixer` pega a nova faixa vocal e a sobrepõe à faixa instrumental original (`accompaniment.wav`), permitindo um ajuste final de volume.
6.  **Resultado:** A música final completa é disponibilizada na interface Gradio para o usuário ouvir e baixar.

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

> **Aviso:** As dependências, especialmente o Coqui TTS, possuem suas próprias licenças (CPML) que devem ser respeitadas. Certifique-se de concordar com os termos de uso antes de utilizar o software.