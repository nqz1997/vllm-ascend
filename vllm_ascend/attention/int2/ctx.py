# SPDX-License-Identifier: Apache-2.0
"""Shared facade for the INT2 backend modules.

Two explicit import surfaces, no star re-exports:
- helpers (``vllm_ascend.attention.int2.helpers``) owns the INT2 utility
  functions and diag sinks; modules import those names from helpers directly.
- this module owns the per-process shared state (the single ``_OSCAR_CFG``
  instance, one logger) and re-exports, explicitly, the upstream framework
  names the backend method bodies reference (graph-param helpers, TP helpers,
  attention metadata types, ...), so every mixin resolves the same objects
  through one audited surface.

Consumers list every name they use; ``__all__`` below documents the surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import os

import torch
import torch_npu
import vllm.envs as envs_vllm
from vllm.config import VllmConfig, get_current_vllm_config
from vllm.distributed import get_tensor_model_parallel_rank, get_tensor_model_parallel_world_size
from vllm.utils.math_utils import cdiv
from vllm.v1.attention.backend import (  # type: ignore
    AttentionBackend,
    AttentionCGSupport,
    AttentionImpl,
    AttentionLayer,
    AttentionMetadataBuilder,
    AttentionType,
)
from vllm.v1.attention.backends.registry import (  # type: ignore
    AttentionBackendEnum,
    register_backend,
)
from vllm.v1.core.sched.output import SchedulerOutput
from vllm.v1.kv_cache_interface import AttentionSpec, CrossAttentionSpec
from vllm_ascend.ascend_forward_context import _EXTRA_CTX
from vllm_ascend.attention.attention_mask import AttentionMaskBuilder
from vllm_ascend.attention.context_parallel.common_cp import AscendMetadataForDecode, AscendMetadataForPrefill
from vllm_ascend.attention.kvcomp_attn.attention_utils import (
    get_kvcomp_decode_params,
    is_enable_hamming_sparse,
    reshape_and_cache_kvcomp,
)
from vllm_ascend.attention.utils import (
    AscendCommonAttentionMetadata,
    enable_cp,
    split_decodes_and_prefills,
    using_paged_attention,
)
from vllm_ascend.compilation.acl_graph import (
    get_draft_graph_params,
    get_draft_graph_prefill_params,
    get_graph_params,
    update_draft_graph_params_workspaces,
    update_graph_params_workspaces,
)
from vllm_ascend.device.device_op import DeviceOperator
from vllm_ascend.ops.flashcomm2_oshard_manager import flashcomm2_oshard_manager
from vllm_ascend.utils import weak_ref_tensors
from vllm_ascend.worker.kvcomp_utils import KVCompMetaData

# ---- shared module state from the base attention module ----
from vllm_ascend.oscar.diag import (  # noqa: F401
    write as _odiag_w,
    open_diag as _odiag_o,
    dump_path as _odiag_p,
)
from vllm_ascend.oscar.config import get_oscar_config

from vllm.logger import logger
from vllm_ascend.attention.attention_v1 import (  # noqa: F401
    AscendAttentionBackendImpl,
    AscendAttentionState,
    AscendC8AttentionBackendImpl,
    AscendMetadata,
    SWA_INT_MAX,
)

# Semantic configuration, one instance per process (env is read once).
_OSCAR_CFG = get_oscar_config()

# Explicit registry for the cross-module gated-diagnostic globals the method
# bodies share (counters, once-probes, passive dump buffers: _R109_STATS,
# _R164_PASSBUF/PASSN, _R164_WCHKBUF/WCHKN, _R166_WV_BLOCKS, _R197_PROBE_N,
# _R218_DISC, _R218_FIRES, _R218_XAS, _R218_MIDC_N). The monolith kept them in module
# globals(); with one module per mixin they become per-module and the
# cross-module handoffs silently no-op. Modules access them through THIS dict
# (same setdefault/get semantics, explicitly shared). Gated diagnostics only;
# no numerical path reads them.
_R2XX_G = {}

__all__ = [
    "_EXTRA_CTX", "_OSCAR_CFG", "_R2XX_G", "_odiag_o", "_odiag_p", "_odiag_w",
    "AscendCommonAttentionMetadata", "AscendC8AttentionBackendImpl",
    "AscendAttentionBackendImpl", "AscendAttentionState", "AscendMetadata",
    "AscendMetadataForDecode", "AscendMetadataForPrefill",
    "AttentionBackend", "AttentionCGSupport", "AttentionImpl",
    "AttentionLayer", "AttentionMaskBuilder", "AttentionMetadataBuilder",
    "AttentionType", "AttentionBackendEnum", "CrossAttentionSpec",
    "DeviceOperator", "KVCompMetaData", "SchedulerOutput", "SWA_INT_MAX",
    "VllmConfig", "AttentionSpec", "cdiv", "dataclass", "enable_cp",
    "envs_vllm", "flashcomm2_oshard_manager", "get_current_vllm_config",
    "get_draft_graph_params", "get_draft_graph_prefill_params",
    "get_graph_params", "get_kvcomp_decode_params",
    "get_tensor_model_parallel_rank", "get_tensor_model_parallel_world_size",
    "is_enable_hamming_sparse", "logger", "register_backend",
    "reshape_and_cache_kvcomp", "split_decodes_and_prefills",
    "update_draft_graph_params_workspaces", "update_graph_params_workspaces",
    "using_paged_attention", "weak_ref_tensors", "Enum", "torch", "torch_npu",
]
