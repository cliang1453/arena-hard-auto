'''
Pipeline to run the hard arena.
'''
import os
import yaml
import argparse
import time
from azureml.core import Run

def get_endpoints_key_map(endpoints, is_aml_run):
    endpoint_key_map = {}

    if is_aml_run == "True":
        # for aml run, we get AOAI key from keyvault of the AMl workspace.
        run = Run.get_context()
        ws = run.experiment.workspace
        keyvault = ws.get_default_keyvault()

        for endpoint in endpoints:
            endpt_name = endpoint["name"]
            endpt_key_name = endpoint["name"] + "-aoai-key"
            endpt_key = keyvault.get_secret(endpt_key_name)

            endpoint_key_map[endpt_name] = endpt_key
    else:    
        # for debug local run, add mapping here
        pass

    return endpoint_key_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_id", type=str, default="Phi-3-mini-4k-instruct"
    )
    parser.add_argument(
        "--model_name", type=str, help="model name corresponds to vllm server"
    )
    parser.add_argument(
        "--judge_model_name", type=str, help="name of the judge model",
        default="tscience-uks-gpt4-1106", choices=["tscience-uks-gpt4-1106", "tscience-uks-gpt-4o"]
    )
    parser.add_argument(
        "--is_aml_run", type=str, default="True", help="if it is an AML run"
    )
    parser.add_argument(
        "--input_dir", type=str, default="None", help="input dir for AML run"
    )
    parser.add_argument(
        "--output_dir", type=str, default="None", help="output dir for AML run"
    )
    parser.add_argument(
        "--port", type=str, default="8008", help="port for hosting vllm"
    )
    args = parser.parse_args()

    # read the api_config file
    file_path = os.path.join(os.path.dirname(__file__), 'config/api_config.yaml')
    with open(file_path, 'r') as file:
        api_config = yaml.safe_load(file)
    
    judge_model_name = args.judge_model_name
    add_dict = {judge_model_name: 
                    {'model_name': judge_model_name, 
                    'endpoints': [{
                                    'api_base': 'https://aims-oai-research-inference-uks.openai.azure.com/', 
                                    'api_version': '2024-02-01'
                                }],
                    'api_type': 'azure', 
                    'parallel': 8,
                    }
                }
    api_config.update(add_dict)

    # add test model api
    model_id = args.model_id
    model_name = args.model_name

    add_dict = {model_id: 
                    {'model_name': model_name, 
                    'endpoints': [{'api_base': f'http://localhost:{args.port}/v1', 'api_key': 'token-abc123'}], 
                    'api_type': 'openai', 
                    'parallel': 8,
                    }
                }

    api_config.update(add_dict)
    print(api_config)
    file_path = os.path.join(os.path.dirname(__file__), 'config/api_config_test.yaml')
    with open(file_path, 'w') as file:
        yaml.safe_dump(api_config, file, default_flow_style=False)


    # read the gen_answer_config file
    file_path = os.path.join(os.path.dirname(__file__), 'config/gen_answer_config.yaml')
    with open(file_path, 'r') as file:
        gen_answer_config = yaml.safe_load(file)

    gen_answer_config['model_list'] = [model_id]
    gen_answer_config['max_tokens'] = 2048 # reduce this from 4096 to 2048 since phi model has a limit of 4k tokens

    print(gen_answer_config)
    file_path = os.path.join(os.path.dirname(__file__), 'config/gen_answer_config_test.yaml')
    with open(file_path, 'w') as file:
        yaml.safe_dump(gen_answer_config, file, default_flow_style=False)


    # read the judge_config file
    file_path = os.path.join(os.path.dirname(__file__), 'config/judge_config.yaml')
    with open(file_path, 'r') as file:
        judge_config = yaml.safe_load(file)

    judge_config['judge_model'] = judge_model_name
    judge_config['model_list'] = [model_id]

    print(judge_config)
    file_path = os.path.join(os.path.dirname(__file__), 'config/judge_config_test.yaml')
    with open(file_path, 'w') as file:
        yaml.safe_dump(judge_config, file, default_flow_style=False)