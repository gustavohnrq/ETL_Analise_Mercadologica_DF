import os
import importlib.util

def run_script(script_path):
    spec = importlib.util.spec_from_file_location("module.name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

if __name__ == "__main__":
    scripts_to_run = [
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Aguas_Claras.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Asa_Sul.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Asa_Norte.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Guara.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Noroeste.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Park_Sul.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Apartamento_Sudoeste.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Arniqueira.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Guara.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Jardim_Botanico.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Lago_Norte.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Lago_Sul.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Park_Way.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Sobradinho(Alto da boa vista).py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Vicente_Pires.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Sobradinho.py',
        '/Users/macbook/Documents/Cod_ETL_estudos/Casa_Asa_Sul.py'
    ]

    for script in scripts_to_run:
        print(f"Running script: {script}")
        run_script(script)
        print(f"Finished running script: {script}")
