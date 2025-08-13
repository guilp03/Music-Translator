import os
import requests
import time
import shutil

class MusicSeparator:
    """
    Uma classe para encapsular a lógica de separação de faixas de áudio
    usando a API api.music.ai.
    """
    
    BASE_API_URL = "https://api.music.ai/v1"

    def __init__(self, api_key: str):
        """
        Inicializa o separador com a chave da API.
        
        Args:
            api_key (str): Sua chave de API para o serviço music.ai.
        """
        if not api_key:
            raise ValueError("A chave da API (api_key) é obrigatória.")
        
        self.api_key = api_key
        self.headers = {
            "Authorization": self.api_key
        }

    def _get_upload_info(self) -> (str, str):
        """(Privado) Pega as URLs de upload e download da API."""
        print("1. Solicitando URLs para upload...")
        res = requests.get(f"{self.BASE_API_URL}/upload", headers=self.headers)
        res.raise_for_status()  # Lança um erro se a requisição falhar
        upload_info = res.json()
        return upload_info['uploadUrl'], upload_info['downloadUrl']

    def _upload_file_to_cloud(self, local_file_path: str, upload_url: str):
        """(Privado) Envia o arquivo local para a URL de upload fornecida."""
        print(f"2. Fazendo upload do arquivo '{local_file_path}' para a nuvem...")
        with open(local_file_path, "rb") as f:
            put_res = requests.put(upload_url, data=f)
            put_res.raise_for_status()
            print(f"   -> Status do upload: {put_res.status_code}")

    def _submit_separation_job(self, download_url: str) -> str:
        """(Privado) Submete o job de separação para a API e retorna o ID do job."""
        print("3. Submetendo o job de separação para a API...")
        payload = {
            "name": "Separar Stems",
            "workflow": "separador_main",
            "params": {
                "inputUrl": download_url
            }
        }
        job_res = requests.post(
            f"{self.BASE_API_URL}/job",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload
        )
        job_res.raise_for_status()
        response_data = job_res.json()
        job_id = response_data['id']
        print(f"   -> Job submetido com sucesso. ID: {job_id}")
        return job_id

    def _poll_and_download_results(self, job_id: str, output_dir: str) -> dict:
        """(Privado) Verifica o status do job e baixa os resultados quando prontos."""
        print(f"4. Aguardando o job '{job_id}' ser concluído (isso pode levar alguns minutos)...")
        
        # O código original usava um loop fixo de 2x com sleep de 30s.
        # Mantendo a mesma lógica. Em um cenário real, um loop com verificação de status seria melhor.
        for i in range(2):
            time.sleep(30)
            print(f"   -> Verificando status (tentativa {i+1}/2)...")
            res = requests.get(f"{self.BASE_API_URL}/job/{job_id}", headers=self.headers)
            res.raise_for_status()
            data = res.json()
            
            # Se a chave 'result' existir, o job terminou e podemos baixar
            if data.get("result"):
                print("   -> Job concluído! Baixando os resultados...")
                os.makedirs(output_dir, exist_ok=True)
                downloaded_files = {}
                for stem, url in data["result"].items():
                    local_path = os.path.join(output_dir, f"{stem}.wav")
                    print(f"      - Baixando {stem} para {local_path}")
                    with requests.get(url, stream=True) as r:
                        r.raise_for_status()
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    downloaded_files[stem] = local_path
                return downloaded_files
        
        print("   -> O job não foi concluído no tempo esperado.")
        return {}

    def separar(self, input_file_path: str, output_directory: str = "output") -> dict:
        """
        Executa o processo completo de separação de faixas.
        
        Args:
            input_file_path (str): O caminho para o arquivo de áudio local a ser processado.
            output_directory (str): O nome da pasta onde os resultados serão salvos.
        
        Returns:
            dict: Um dicionário com os nomes dos stems e os caminhos para os arquivos baixados.
        """
        try:
            upload_url, download_url = self._get_upload_info()
            self._upload_file_to_cloud(input_file_path, upload_url)
            job_id = self._submit_separation_job(download_url)
            resultado = self._poll_and_download_results(job_id, output_directory)
            print("\nProcesso de separação finalizado.")
            return resultado
        except requests.exceptions.RequestException as e:
            print(f"\n[ERRO] Ocorreu um erro de comunicação com a API: {e}")
            return {}
        except Exception as e:
            print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")
            return {}