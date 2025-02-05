"""Benchmark the latency of processing a single batch of requests."""
import argparse
import time

import numpy as np
import torch
from tqdm import tqdm

from vllm import LLM, SamplingParams


def main(args: argparse.Namespace):
    print(args)

    # Process all the requests in a single batch if possible.
    # NOTE(woosuk): If the request cannot be processed in a single batch,
    # the engine will automatically process the request in multiple batches.

    draft_llm = LLM(
        model=args.draft_model,
        tokenizer=args.tokenizer,
        quantization=args.quantization,
        tensor_parallel_size=args.tensor_parallel_size,
        max_num_seqs=args.batch_size,
        max_num_batched_tokens=args.batch_size * args.input_len,
        trust_remote_code=args.trust_remote_code,
        dtype=args.dtype,
    )

    sampling_params = SamplingParams(
        n=args.n,
        temperature=0.0 if args.use_beam_search else 1.0,
        top_p=1.0,
        use_beam_search=args.use_beam_search,
        ignore_eos=True,
        max_tokens=args.output_len,
    )
    print(sampling_params)
    dummy_prompt_token_ids = [[0] * args.input_len] * args.batch_size
    
    # Sample prompts.
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ]

    outputs = draft_llm.generate(prompts, sampling_params=sampling_params, use_tqdm=False)
    print(len(outputs))
    # Print the outputs.
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
    
    '''
    def run_to_completion(llm_model, token_ids, profile: bool = False):
        if profile:
            torch.cuda.cudart().cudaProfilerStart()
        start_time = time.perf_counter()

        llm_model.generate(prompt_token_ids=token_ids,
                     sampling_params=sampling_params,
                     use_tqdm=False)

        end_time = time.perf_counter()
        latency = end_time - start_time
        if profile:
            torch.cuda.cudart().cudaProfilerStop()
        return latency

    print("Warming up...")
    run_to_completion(draft_llm, dummy_prompt_token_ids, profile=False)

    # Benchmark.
    draft_latencies = []
    for _ in tqdm(range(args.num_iters), desc="Profiling iterations"):
        draft_latencies.append(run_to_completion(draft_llm, dummy_prompt_token_ids, profile=False))
    print(f'Avg draft latency: {np.mean(draft_latencies)} seconds')
    '''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Benchmark the latency of processing a single batch of '
        'requests till completion.')
    parser.add_argument('--target_model', type=str, default='facebook/opt-6.7b')
    parser.add_argument('--draft_model', type=str, default='facebook/opt-125m')
    parser.add_argument('--tokenizer', type=str, default=None)
    parser.add_argument('--quantization',
                        '-q',
                        choices=['awq', None],
                        default=None)
    parser.add_argument('--tensor-parallel-size', '-tp', type=int, default=1)
    parser.add_argument('--gpu-memory-utilization', '-gputil', type=float, default=0.7)
    parser.add_argument('--input-len', type=int, default=256)
    parser.add_argument('--output-len', type=int, default=512)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--random_seed', type=int, default=1)
    parser.add_argument('--draft_length', type=int, default=4, help='Number of draft tokens.')
    parser.add_argument('--n',
                        type=int,
                        default=1,
                        help='Number of generated sequences per prompt.')
    parser.add_argument('--use-beam-search', action='store_true')
    parser.add_argument('--num-iters',
                        type=int,
                        default=2,
                        help='Number of iterations to run.')
    parser.add_argument('--trust-remote-code',
                        action='store_true',
                        help='trust remote code from huggingface')
    parser.add_argument(
        '--dtype',
        type=str,
        default='auto',
        choices=['auto', 'half', 'float16', 'bfloat16', 'float', 'float32'],
        help='data type for model weights and activations. '
        'The "auto" option will use FP16 precision '
        'for FP32 and FP16 models, and BF16 precision '
        'for BF16 models.')

    args = parser.parse_args()
    main(args)
