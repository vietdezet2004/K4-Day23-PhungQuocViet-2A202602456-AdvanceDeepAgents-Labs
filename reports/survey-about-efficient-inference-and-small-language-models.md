# Survey on Efficient Inference and Small Language Models

## TL;DR
- Efficient inference in small language models is achieved through techniques like pruning, quantization, and knowledge distillation [1][2].
- Various architectures such as TinyBERT, DistilBERT, and MobileBERT significantly enhance performance while reducing resource requirements [3][4].
- Current evaluation metrics face challenges in assessing generalization and adaptability in small language models [5][6].

## Background
Small language models (SLMs) are designed to perform tasks traditionally handled by larger counterparts while maintaining efficiency. These models are significant in deploying natural language processing applications in resource-constrained environments and have been popular due to increasing computational demands. Their foundational techniques include various inference optimization strategies that enable effective performance even with reduced model sizes [2][7].

## Efficient Inference Strategies
Efficient inference encompasses various methods like pruning, quantization, and knowledge distillation, which improve the speed and reduce the memory footprint of small language models. For instance, studies indicate that quantization can maintain performance while reducing model size, enhancing the applicability of these models in real-time applications [1][8]. Furthermore, techniques such as instruction retrieval provide structured reasoning at inference time, allowing small models to perform comparably to their larger counterparts without additional training [1][2].

## Prominent Architectures for Small Language Models
Several noteworthy architectures include TinyBERT, DistilBERT, and MobileBERT, each tailored for efficiency in specific contexts. TinyBERT achieves a favorable balance between size and performance, while MobileBERT excels in mobile deployments by optimizing the model's depth and width [3][4]. DistilBERT demonstrates significant improvements in inference speed, reducing the computational load by retaining most of BERT's capabilities [4]. Evaluating their respective designs, these architectures consistently leverage techniques like knowledge distillation to optimize processing power [2][3].

## Evaluation Metrics and Open Problems
Evaluation of small language models remains a critical area of focus, with traditional metrics like BLEU and ROUGE struggling to capture nuanced performance characteristics. New frameworks suggest a multi-metric approach to better assess models' capabilities, particularly in out-of-distribution settings [5][9]. Open problems persist regarding generalization abilities and how well small models can adapt to a diverse array of tasks without tailored evaluation methods [9].

## Trends and Open Problems
Recent developments in small language models emphasize not only improving their inference capabilities but also addressing their limitations in reasoning and adaptability. As smaller models continue to evolve, the focus shifts towards devising better evaluation frameworks and methodologies that capture their performance across varied tasks and domains [5][7].

## References
[1] EdgeDAE: Acceleration of Diffusion Action Experts for Real-Time Physical AI with Tiny VLAs on Edge FPGA-GPU Systems. arxiv. https://arxiv.org/abs/2610.00311 (2026-09-28)
[2] A Survey on Small Language Models in the Era of Large Language Models: Architecture, Capabilities, and Trustworthiness. web. https://dl.acm.org/doi/10.1145/3711896.3736563 (2025-08-03)
[3] TinyBERT: Distilling BERT for Natural Language Understanding. hf-search. https://huggingface.co/papers/1909.10351 (2019-09-23)
[4] DistilBERT: a Distilled Version of BERT. web. https://aclanthology.org/2020.findings-emnlp.372.pdf (N/A)
[5] Evaluating Generalization and Representation Stability in Small LMs via Prompting, Fine-Tuning and Out-of-Distribution Prompts. arxiv. https://arxiv.org/html/2506.17289v1 (N/A)
[6] Are Small Language Models Ready to Compete with Large Language Models for Practical Applications?. web. https://aclanthology.org/2025.trustnlp-main.25.pdf (N/A)
[7] Small Language Models: Survey, Measurements, and Insights. arxiv. https://arxiv.org/html/2409.15790v1 (2024-09-24)
[8] RSI-Router: Evolving Subtask-Level LLM Routing and Skills for Cost-Efficient Agents. arxiv. https://arxiv.org/abs/2609.34712 (2026-09-28)
[9] Regional-TinyStories: A Small Language Model Framework for Evaluating Language Learning, Tokenizers, and Datasets. web. https://aclanthology.org/2025.findings-ijcnlp.142.pdf (N/A)
