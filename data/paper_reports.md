# Research Report: attention

**Generated**: 2026-05-10 22:10:29
**Total Papers**: 15
**High-Relevance Papers**: 7
**Enrichment**: Introduction / methodology / conclusion + recent related arXiv ids from export HTML

---

## Executive Summary

This report analyzes papers retrieved for the query **"attention"**. 
Among 15 papers, 7 achieved high relevance scores (≥8). 
The following sections provide detailed analysis based on upstream rankings, 
paper abstracts, and arXiv export enrichment (introduction, **methodology**, conclusion, and recent citations).
This report **centers on methods and contributions** per paper and for the field.

---

## ⭐ High-Relevance Papers (Top Picks)

> **[Cubit: Token Mixer with Kernel Ridge Regression](https://arxiv.org/abs/2605.06501v1)**
> Relevance: 10.0/10 | Authors: Chuanyang Zheng, Jiankai Sun, Yihang Gao...
>
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): Since its introduction in 2017, the Transformer has become one of the most widely adopted architectures in modern deep learning. Despite extensive efforts to improve positional encoding, attention mechanisms, and feed-forward networks, the core token-mixing mechanism in Transformers remains attention. In this work, we show that the attention module in Transformers can be interpreted as performing Nadaraya-Watson regression, where it computes similarities between tokens and aggregates the corresp...
>
> **Introduction (excerpt)**: Recurrent Neural Networks (RNNs), introduced in the 1980s Hopfield (1982); Jordan (1986); Elman (1991); Graves (2012), process sequences by recurrently updating hidden states across tokens, incurring linear computational complexity with respect to sequence length. In 2017, the Transformer architectu...
> **Conclusion (excerpt)**: In this work, we propose Cubit, a novel architecture based on Kernel Ridge Regression that replaces the Nadaraya-Watson estimator underlying Transformers. We conduct extensive evaluations across diverse datasets, sequence lengths, and model scales. Cubit consistently outperforms the Transformer, wit...
> **Recent related arXiv ids** (last 2 years): [2405.21060](https://arxiv.org/abs/2405.21060), [2406.06563](https://arxiv.org/abs/2406.06563), [2409.04431](https://arxiv.org/abs/2409.04431), [2409.19606](https://arxiv.org/abs/2409.19606), [2412.06464](https://arxiv.org/abs/2412.06464)

> **[Long Context Pre-Training with Lighthouse Attention](https://arxiv.org/abs/2605.06554v1)**
> Relevance: 10.0/10 | Authors: Bowen Peng, Subho Ghosh, Jeffrey Quesnelle
>
> **Methods & Methodology**: Architecture, data, optimizer.

A 530530M-parameter Llama-3-style decoder (dmodel=1024d_{\text{model}}{=}1024, 3030 layers, H=8H{=}8, head dim 128128, FFN 15361536, byte-level tokenizer). Layers {0,1,28,29}\{0,1,28,29\} retain dense SDPA — PyTorch 2.11.02.11.0+cu128
’s torch.nn.attention.sdpa_kernel...
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): Training causal transformers at extreme sequence lengths is bottlenecked by the quadratic time and memory of scaled dot-product attention (SDPA). In this work, we propose Lighthouse Attention, a training-only symmetrical selection-based hierarchical attention algorithm that wraps around ordinary SDPA and can be easily removed towards the end of the training. Our hierarchical selection is also gradient-free, which exempts us from dealing with a complicated and potentially inefficient backward pas...
>
> **Introduction (excerpt)**: The frontier of language modeling has moved toward contexts of 128K, 1M, and longer, pushed by agentic multi-step reasoning, long-document understanding, and interleaved multimodal inputs [25, 1, 11, 22, 27, 8, 23]. Training at these scales is the dominant hardware bottleneck: scaled dot-product att...
> **Conclusion (excerpt)**: We introduce Lighthouse Attention, a selection-based hierarchical attention for long-context pretraining that pools Q,K,VQ,K,V symmetrically across a multi-resolution pyramid and places
selection outside the attention kernel, reducing the attention step to stock FlashAttention on a dense sub-sequenc...
> **Recent related arXiv ids** (last 2 years): [2407.02490](https://arxiv.org/abs/2407.02490), [2407.14057](https://arxiv.org/abs/2407.14057), [2407.21783](https://arxiv.org/abs/2407.21783), [2412.15115](https://arxiv.org/abs/2412.15115), [2412.19437](https://arxiv.org/abs/2412.19437)

> **[FreeSpec: Training-Free Long Video Generation via Singular-Spectrum Reconstruction](https://arxiv.org/abs/2605.06509v1)**
> Relevance: 8.6471/10 | Authors: Fangda Chen, Shanshan Zhao, Longrong Yang...
>
> **Methods & Methodology**: Datasets.

Following recent training-free long video generation methods [24, 25, 31], we evaluate our method on long text-to-video generation using 100 enhanced prompts from VBench-Long [16].

Compared Methods.

We compare FreeSpec with representative training-free long video generation baselines.
D...
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): Video diffusion models perform well in short-video synthesis, but their training-free extension to long videos often suffers from content drift, temporal inconsistency, and over-smoothed dynamics. Existing methods improve temporal consistency by combining a global branch with a local branch, but they often further decompose appearance consistency and temporal dynamics within each branch using predefined criteria. This assignment is unreliable when appearance and action progression are tightly co...
>
> **Introduction (excerpt)**: Video diffusion models [3, 38, 8, 39, 19, 12, 36, 5, 30] have achieved remarkable progress in short-video generation, producing realistic appearances, coherent motion, and strong text alignment over dozens of frames. However, directly training long-video diffusion models remains prohibitively expens...
> **Conclusion (excerpt)**: In this paper, we presented FreeSpec, a training-free spectral reconstruction framework for long-video generation. We showed that enlarged self-attention windows cause spectral concentration, where feature energy is dominated by a few low-rank singular directions. This preserves coarse structure but...
> **Recent related arXiv ids** (last 2 years): [2405.04233](https://arxiv.org/abs/2405.04233), [2410.13720](https://arxiv.org/abs/2410.13720), [2412.03603](https://arxiv.org/abs/2412.03603), [2501.00103](https://arxiv.org/abs/2501.00103), [2503.20314](https://arxiv.org/abs/2503.20314)

> **[Resource-Efficient CSI Prediction: A Gated Fusion and Factorized Projection Approach](https://arxiv.org/abs/2605.06578v1)**
> Relevance: 8.620700000000001/10 | Authors: Mohammad Hussain, Maedeh Adibag, Dilara Gurer...
>
> **Methods & Methodology**: Prediction accuracy is evaluated using sample-weighted NMSE (dB) as the primary
metric, with per-frame MSE tracked at each future step k=1,…,NLk=1,\ldots,N_{L}.
Training minimizes a weighted MSE loss with decaying weights wk=k−1/2w_{k}=k^{-1/2}.
A 200-sample gap between training and validation segme...
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): Accurate Channel State Information (CSI) prediction is essential for dynamic multiple-input multiple-output (MIMO) systems but remains computationally demanding. This letter proposes a resource-efficient predictor that combines a gated recurrent unit (GRU) encoder with Luong attention, a bottleneck gated fusion module, and a Dimension-wise Separable Linear Head (DSLH). The gated fusion module integrates local recurrent features with global attention context, while the DSLH reduces the cost of th...
>
> **Introduction (excerpt)**: The performance of MIMO systems relies heavily on accurate CSI. In dynamic wireless environments, the channel varies rapidly, causing CSI to “age” between acquisition and use, leading to severe performance degradation. To mitigate this, deep learning (DL) predictors have been widely adopted to forec...
> **Conclusion (excerpt)**: This letter presented a resource-efficient CSI predictor based on a GRU backbone, gated attention fusion, and a Dimension-wise Separable Linear Head (DSLH). Under 3GPP TR 38.901 channel simulations, the proposed model achieved an average NMSE of −13.84-13.84 dB while reducing parameters by 26% and i...

> **[Scene-Adaptive Continual Learning for CSI-based Human Activity Recognition with Mixture of Experts](https://arxiv.org/abs/2605.06447v1)**
> Relevance: 8.620700000000001/10 | Authors: Wenhan Zheng, Yuyi Mao, Ivan Wang-Hei Ho
>
> **Methods & Methodology**: Dataset:
We utilize the CSI data from the multi-modal MM-Fi dataset, which is extracted from WiFi signal collected by a TP-Link N750 router in four environments via the Atheros CSI Tool. It features K=27K=27 human activities across four environments, including two living rooms (𝒟1,𝒟2\mathcal{D}_{1},...
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): Channel state information (CSI)-based human activity recognition (HAR) is vulnerable to performance degradation under domain shifts across varying physical environments. Continual learning (CL) offers a principled way to learn new domains sequentially while preserving past knowledge, but existing CL solutions for CSI-based HAR scale poorly with accumulating domains, rely on a large replay buffer, or incur linearly growing inference cost. In this letter, we propose Scene-Adaptive Mixture of Exper...
>
> **Introduction (excerpt)**: Channel state information (CSI) is a fine-grained physical layer measurement within wireless communication networks that grants a unique opportunity with privacy-preserving human activity recognition (HAR) [9]. The high sensitivity of CSI to the propagation environment, characterized by multipath fa...
> **Conclusion (excerpt)**: In this letter, we propose the SAMoE-C framework for robust cross-domain CSI-based HAR. By integrating an MoE architecture and a novel training protocol, our method successfully preserves knowledge from previously seen environments while adapting to new ones, achieving high domain discrimination and...
> **Recent related arXiv ids** (last 2 years): [2605.06447](https://arxiv.org/abs/2605.06447)

> **[Towards Emotion Consistency Analysis of Large Language Models in Emotional Conversational Contexts](https://arxiv.org/abs/2605.06476v1)**
> Relevance: 8.2599/10 | Authors: Sneha Oram, Ojaswita Bhushan, Pushpak Bhattacharyya
>
> **Methods & Methodology**: We present our overall methodology of the ECP framework in Figure 2
. Following experiments, we perform a human evaluation to examine the responses given by the LLMs.
Three labels are used for response evaluation: ‘agree’, ‘disagree’, and ‘neutral’, to record the LLMs’ position to the query prompts....
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): In this work, we conduct an analysis to examine the consistency of Large Language Models (LLMs) with respect to their own generated responses in an emotionally-driven conversational context. Specifically, the text generated by LLM is framed as a query to the same model, and its responses are subsequently assessed. This is performed with three queries across two dimensions of extreme and moderate emotions. The three queries are, in particular, false claim queries that contain inherently wrong ass...
>
> **Introduction (excerpt)**: Systems such as ChatGPT can generate empathetic responses and have been increasingly adopted to support the mental well-being of users Welivita and Pu (2024); Zhao et al.
(2023); Qian et al.
(2023).
Previous research has investigated multiple strategies to improve empathy in Large Language Models (L...
> **Conclusion (excerpt)**: Focusing on the implications of employing LLMs for empathetic text generation, we present an analysis of their consistency across two dimensions of extreme and moderate emotion versions. The evaluation is conducted based on the proportion of disagreement stance and attention scores.
Our findings ind...
> **Recent related arXiv ids** (last 2 years): [2406.10960](https://arxiv.org/abs/2406.10960), [2501.08102](https://arxiv.org/abs/2501.08102), [2605.06476](https://arxiv.org/abs/2605.06476)

> **[The Structural Origin of Attention Sink: Variance Discrepancy, Super Neurons, and Dimension Disparity](https://arxiv.org/abs/2605.06611v1)**
> Relevance: 8.0856/10 | Authors: Siquan Li, Kaiqi Jiang, Jiacheng Sun...
>
> **Methods & Methodology**: To ensure reproducibility, we provide the detailed configurations used for the pre-training experiments....
>
> **Contributions (Key Claims)**: N/A
>
> **Abstract** (supporting): Despite the prevalence of the attention sink phenomenon in Large Language Models (LLMs), where initial tokens disproportionately monopolize attention scores, its structural origins remain elusive. This work provides a \textit{mechanistic explanation} for this phenomenon. First, we trace its root to the value aggregation process inherent in self-attention, which induces a systematic variance discrepancy. We further demonstrate that this discrepancy is drastically amplified by the activation of su...
>
> **Introduction (excerpt)**: Attention sinks are a recurring feature of decoder-only transformers: across layers and inputs, a small set of tokens, most notably the initial token, can receive disproportionately large attention despite limited semantic relevance (Vig and Belinkov, 2019; Clark et al.
, 2019; Bondarenko et al.
, 2...
> **Recent related arXiv ids** (last 2 years): [2406.18139](https://arxiv.org/abs/2406.18139), [2407.01601](https://arxiv.org/abs/2407.01601), [2409.04431](https://arxiv.org/abs/2409.04431), [2410.01131](https://arxiv.org/abs/2410.01131), [2410.10781](https://arxiv.org/abs/2410.10781)

---

## Detailed Analysis by Category

### Medium Relevance Papers
- **Transformers Efficiently Perform In-Context Logistic Regression via Normalized Gradient Descent** (ID: 2605.06609v1, Score: 0)
- **MedHorizon: Towards Long-context Medical Video Understanding in the Wild** (ID: 2605.06537v1, Score: 0)
  - We present MedHorizon
, an in-the-wild benchmark for long-context medical video understanding. Representative general-domain, medical-domain, and retrieval-style MLLMs perform poorly, with the best mo...
- **FedFrozen: Two-Stage Federated Optimization via Attention Kernel Freezing** (ID: 2605.06446v1, Score: 0)
  - In this paper, we introduced 
FedFrozen
, a two-stage federated optimization framework designed to mitigate client drift in attention-based models. Theoretically, we established that the full-model wa...
- **DINORANKCLIP: DINOv3 Distillation and Injection for Vision-Language Pretraining with High-Order Ranking Consistency** (ID: 2605.06592v1, Score: 0)
  - Scope.

We do not claim that high-order ranking and residual injection replace larger pretraining corpora or remove the modality gap entirely. We claim that, given a fixed contrastive recipe and a fix...

### Lower Relevance Papers
- When and Why SignSGD Outperforms SGD: A Theoretical Study Based on $\ell_1$-norm Lower Bounds (ID: 2605.06615v1, Score: 1.3)
- OA-WAM: Object-Addressable World Action Model for Robust Robot Manipulation (ID: 2605.06481v1, Score: 1.3)
- From Review to Design: Ethical Multimodal Driver Monitoring Systems for Risk Mitigation, Incident Response, and Accountability in Automated Vehicles (ID: 2605.06439v1, Score: 1.3)
- Scalable GPU Construction of 3D Voronoi and Power Diagrams (ID: 2605.06408v1, Score: 1.3)

---

## Comparison Table

| Rank | Paper | Relevance | Key Methods | Main Contribution | Recent related ids |
|------|-------|-----------|-------------|-------------------|--------------------|
| 1 | Cubit: Token Mixer with Kernel Ridge Reg... | 0/10 |  |  | 2405.21060, 2406.06563, 2409.04431 |
| 2 | Long Context Pre-Training with Lighthous... | 0/10 |  |  | 2407.02490, 2407.14057, 2407.21783 |
| 3 | FreeSpec: Training-Free Long Video Gener... | 0/10 |  |  | 2405.04233, 2410.13720, 2412.03603 |
| 4 | Resource-Efficient CSI Prediction: A Gat... | 0/10 |  |  |  |
| 5 | Scene-Adaptive Continual Learning for CS... | 0/10 |  |  | 2605.06447 |
| 6 | Towards Emotion Consistency Analysis of ... | 0/10 |  |  | 2406.10960, 2501.08102, 2605.06476 |
| 7 | The Structural Origin of Attention Sink:... | 0/10 |  |  | 2406.18139, 2407.01601, 2409.04431 |
| 8 | Transformers Efficiently Perform In-Cont... | 0/10 |  |  |  |
| 9 | MedHorizon: Towards Long-context Medical... | 0/10 |  |  | 2406.16852, 2406.19280, 2408.01800 |
| 10 | FedFrozen: Two-Stage Federated Optimizat... | 0/10 |  |  | 2408.09101 |
| 11 | DINORANKCLIP: DINOv3 Distillation and In... | 0/10 |  |  |  |
| 12 | When and Why SignSGD Outperforms SGD: A ... | 0/10 |  |  |  |
| 13 | OA-WAM: Object-Addressable World Action ... | 0/10 |  |  |  |
| 14 | From Review to Design: Ethical Multimoda... | 0/10 |  |  |  |
| 15 | Scalable GPU Construction of 3D Voronoi ... | 0/10 |  |  |  |
