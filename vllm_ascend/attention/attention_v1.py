#
# Copyright (c) 2025 Huawei Technologies Co., Ltd. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# This file is a part of the vllm-ascend project.
#
import os as _r144_ovl_os, sys as _r144_ovl_sys
print(f"[R144-OVL-LOAD] R144 overlay attention_v1 LOADED pid={_r144_ovl_os.getpid()} file={__file__}", file=_r144_ovl_sys.stderr, flush=True)
# R218ID: child-side source-identity banner (stderr -- EngineCore stdout is
# dropped, only stderr reaches the serve log; probe legs proved this). The
# wrapper gates expensive legs on file+sha matching the frozen candidate.
try:
    _r218_id_stat = _r144_ovl_os.stat(__file__)
    import hashlib as _r218_id_hl
    _r218_id_sha = _r218_id_hl.sha256(open(__file__, "rb").read()).hexdigest()[:16]
    print(f"[R218ID] file={__file__} sha={_r218_id_sha} mtime={int(_r218_id_stat.st_mtime)} size={_r218_id_stat.st_size} pid={_r144_ovl_os.getpid()}", file=_r144_ovl_sys.stderr, flush=True)
except Exception as _r218_id_e:
    print(f"[R218ID] FAILED {_r218_id_e!r}", file=_r144_ovl_sys.stderr, flush=True)


# OSCAR INT2: shared helpers live in their own module (relocated from this
# file's prologue); importing them here keeps the monolith-era call sites in
# the class bodies below working without re-inlining them.
from vllm_ascend.attention.int2.helpers import (  # noqa: F401
    _R170_EDGEFENCE_MODE,
    _R170_EDGEFENCE_N,
    _R170_MID2_ON,
    _R170_ROWSLOT_ON,
    _oscar_diag_write,
    _r136_p0_dump,
    _r218_diag,
)

_r218_diag("IMPORT file=%s" % (__file__,))
# R170_ROWSLOT (default OFF): decode-graph ROW-SLOT contract. FULL decode
# graphs bake hk[row] addresses at capture; the runtime rid->slot binding
# (monotonic under R164_SLOTMAP=1) puts request k's ring at slot k != row.
# Proof R170 (r170e all-slot dump): solo_k>=1 prefill wrote slot_k (fresh,
# frozen), every replay read+slid slot0 = previous generation's final window
# => E27 foreign-token corruption. Fix: (a) at capture bake slot=row
# (torch.npu.is_current_stream_capturing in _tt_slot), (b) bind rid->slot via
# the R166 free-list allocator (_r164_bind_slots first branch), (c) before
# each pure-decode replay, _r170_rowslot_migrate copies ring content so the
# rid at row b lives at slot b (evicting live non-decoding owners out of
# row/pad/scratch slots). Requires R161_FENCE in (1,3) so the update stream's
# copies are ordered after eager prefill writes (F1) and the previous replay
# (F3). All changes gated by this single env; OFF => byte-identical legacy
# behavior.
# R170_MIDDUMP2: host-side pre-replay paged-cache dump (the in-graph
# R170_MIDDUMP hook cannot fire at replay — python never re-executes inside
# captured code; trap found 2026-09-22 when h10 produced zero records).
# R170_EDGEFENCE: host-side full device sync at the END of update_graph_params
# (before the caller launches the graph replay). Root evidence 2026-09-22: the
# outlse census on h10/h1_fix shows the FIRST pure-replay decode step reading
# seq_lens/bt-era values for a L0..L12(h1_fix)/L18(h10) layer PREFIX — exact
# empty-attention signature (lse=-9999.0, out=0.0), extent varying per leg =>
# a race (the cross-stream carrier/input fill lands MID-replay), not structure.
# R161_FENCE=3 orders update_stream AFTER the previous replay, but nothing
# orders the replay AFTER this step's fills at the capture->replay edge.
# =1: sync every step (correctness probe; perf-costly). =2: only the first 3
# update calls (the edge itself). OFF => byte-identical legacy behavior.
# R160: install warmup-fix monkeypatch. Runs in the EngineCore process (where
# attention_v1 is imported, before graph capture). Gated by R160_WFIX / R160_WDIAG
# internally (no-op if both off). Patch module sits at overlay root (on sys.path).
try:
    import r160_warmup_fix as _r160_wfix
    _r160_wfix.start()
except Exception as _r160_e:
    print(f"[R160-OVL] warmup_fix start failed: {_r160_e!r}", file=_r144_ovl_sys.stderr, flush=True)

# R161: race-edge fence matrix (diagnostic; default OFF via R161_FENCE=0).
# Locates the missing cross-stream dependency edge for B>1 INT2 graph replay.
try:
    import r161_fence as _r161_f
    print(f"[R161-OVL] fence loaded label={_r161_f.fence_label()} pid={_r144_ovl_os.getpid()} PBCARRIER={_r144_ovl_os.environ.get('R159K_PBCARRIER','?')} PBCVERIFY={_r144_ovl_os.environ.get('R161_PBCVERIFY','?')} ENPU={_r144_ovl_os.environ.get('ENPU_ENABLE','?')}", file=_r144_ovl_sys.stderr, flush=True)
except Exception as _r161_e:
    print(f"[R161-OVL] fence load failed: {_r161_e!r}", file=_r144_ovl_sys.stderr, flush=True)
    import types as _r161_t
    _r161_f = _r161_t.SimpleNamespace(on_update_enter=lambda *a, **k: None,
        on_update_exit=lambda *a, **k: None, on_replay_enter=lambda *a, **k: None,
        on_replay_done=lambda *a, **k: None, on_cu_done=lambda *a, **k: None,
        on_middle_enter=lambda *a, **k: None, fence_label=lambda: "F0-off")

# ---- R164 tier-dump atexit (default OFF via R164_TIERDUMP) ----
if _r144_ovl_os.environ.get("R164_TIERDUMP", "0") == "1":
    import atexit as _r164_atx
    def _r164_dump_tiers():
        try:
            import json as _j164
            import sys as _s164
            _m164 = _s164.modules.get("vllm_ascend.attention.attention_v1")
            _buf = None
            if _m164 is not None:
                _c164 = getattr(_m164, "AscendINT2AttentionBackendImpl", None)
                if _c164 is not None:
                    _buf = getattr(_c164, "_r164_tdbuf", None)
            if _buf is None:
                return
            _cpu = _buf.detach().to("cpu")
            _rows = {}
            for _l in range(_cpu.shape[0]):
                for _b in range(_cpu.shape[1]):
                    _v = _cpu[_l, _b]
                    if float(_v.abs().sum()) == 0.0:
                        continue
                    _rows[f"L{_l}b{_b}"] = [round(float(x), 4) for x in _v.tolist()]
            with open("/tmp/r164_tierdump.jsonl", "a") as _f164:
                _f164.write(_j164.dumps({"pid": _r144_ovl_os.getpid(), "rows": _rows}) + "\n")
        except Exception as _e164:
            try:
                with open("/tmp/r164_tierdump.jsonl", "a") as _f164e:
                    _f164e.write("dump_error " + repr(_e164) + "\n")
            except Exception:
                pass
    _r164_atx.register(_r164_dump_tiers)

# ---- R150 P0 trace helper (file-based; default OFF via R150_TRACE) ----
import os as _r150_os, json as _r150_json
# R166_REFTRACE: PFQUANT lifecycle reference trace (default OFF). Cheap host-side
# ints only — no device syncs, no allocation. One jsonl per pid; correlate with
# R164_STEPDUMP via rids. Covers: quantize calls, paged-write coverage (slot
# span), CU skip decisions, lazy-CU fires, three-tier prefill/decode boundaries.
# R203_METAFIX (default OFF): per-STEP host mirror of step-constant metadata.
# kprof r202b step_25 (composed stack, pass-2 big step): every layer re-reads
# the SAME query_start_loc device tensor to host — q_start.cpu() at
# three-tier-prefill entry + _qs201.cpu() in the R201_PFNOMASK core = 2
# full-stream-sync D2H per layer (71 x ~1.0-1.2ms host-blocked aten::to/copy_
# pairs per step + the device starvation behind them; ~160ms/step device-idle
# gap class). The tensor is built ONCE per step (init_ascent_attn_metadata
# H2D) and never mutated within the step, so all 36 layer calls read identical
# values. Mirror it once per metadata OBJECT; mismatch (length vs
# seq_lens_list) or any failure falls back to the exact base read.
# R216 (default OFF): in-vivo LSE forensics. The product's 3-tier merge consumes
# l_h (the middle op's softmaxLse OUTPUT) via exp(l_h - m) weighting. R215 proved
# the op's LSE output is racy on real data at the B=1 base path; whether the
# GROUP-M decode path (graph replay, what serving actually runs) feeds the merge
# a correct l_h has NEVER been adjudicated against an independent reference
# (SR_CMP compares graph-vs-eager arms of the SAME op — a shared defect cancels).
# These helpers capture, at the REAL consumption boundary:
#   _r216_mid  — called at the R146 convergence point right after the carrier
#                out/lse are filled (covers BOTH graph-replay and eager calls):
#                the exact op INPUTS (qrot, Kc/Vc packed INT2, bt, per-token
#                affines, askv) + OUTPUTS (out, lse) + row identity.
#   _r216_merge— called right before the tier-merge compute: the four merge
#                operands (l_pr, l_h, o_pr, o_h) as consumed.
# Offline (RAW/r216_adjudicate.py) rebuilds the middle-tier LSE in fp32 from the
# captured INT2 operands and adjudicates. Full dumps are budget-capped; a light
# per-call ledger (lse vectors + identity) runs for every GROUP-M call to expose
# intermittent corruption across a whole leg.
# R203_D2HTRACE (DIAGNOSTIC_ONLY/default OFF): count long device-to-host reads
# (Tensor.cpu/tolist/item over the threshold) with their Python call sites —
# each is a full-stream sync on the eager path (the kprof r202b gap class).
# Used to enumerate REMAINING D2H sites after the R203_METAFIX edits; never
# enabled in A/B legs. Log: /tmp/r203_d2h.log (container /tmp — docker cp).
from dataclasses import dataclass
from enum import Enum

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

import os
import logging

logger = logging.getLogger(__name__)


# default max value of sliding window size
SWA_INT_MAX = 2147483647
_ATTN_KEYS_BUFFER = None

# R144 P0: module-level dynamic-lifecycle counters (gated by R144_TT_DEBUG=1).
# Bumped by _tt_resolve_slots when the req_id slot map finishes/reuses a slot.
# R136 P0: env-gated (R136_P0_DIAG=1, default OFF) dump of the middle launch
# OPERANDS (shapes + content hashes + key scalars) at BOTH the V1 eager launch
# site (_r109_middle_candidate) and the V1 graph replay updater site
# (_r113_update_oscar_mid), keyed by (mode, layer, step). Purpose: locate the
# FIRST step/layer/FIELD where F_eager and B_graph middle operands diverge —
# BEFORE the idx-8/idx-2 token symptom. Production byte-identical when OFF.
@register_backend(AttentionBackendEnum.CUSTOM, "ASCEND")
class AscendAttentionBackend(AttentionBackend):
    accept_output_buffer: bool = True

    @staticmethod
    def get_name() -> str:
        # HACK(Ronald1995): vllm `initialize_kv_cache` method in model runner v2 make
        # attention name assertion, we just set name to FLASH_ATTN to avoid assertion error.
        # rectify this when vllm disable the assertion.
        return "CUSTOM" if not envs_vllm.VLLM_USE_V2_MODEL_RUNNER else "FLASH_ATTN"

    @staticmethod
    def get_impl_cls() -> type["AscendAttentionBackendImpl"]:
        if enable_cp():
            from vllm_ascend.attention.context_parallel.attention_cp import AscendAttentionCPImpl

            return AscendAttentionCPImpl
        return AscendAttentionBackendImpl

    @staticmethod
    def get_builder_cls() -> type["AscendAttentionMetadataBuilder"]:
        if enable_cp():
            from vllm_ascend.attention.context_parallel.attention_cp import AscendAttentionCPMetadataBuilder

            return AscendAttentionCPMetadataBuilder
        return AscendAttentionMetadataBuilder

    @staticmethod
    def get_kv_cache_shape(
        num_blocks: int,
        block_size: int,
        num_kv_heads: int,
        head_size: int,
        cache_dtype_str: str = "",
    ) -> tuple[int, ...]:
        if cache_dtype_str == "int2_per_token_head":
            head_size = head_size // 4
        return (2, num_blocks, block_size, num_kv_heads, head_size)

    @staticmethod
    def swap_blocks(
        src_kv_cache: list[torch.Tensor],
        dst_kv_cache: list[torch.Tensor],
        src_to_dst: torch.Tensor,
    ) -> None:
        src_key_cache, src_value_cache = src_kv_cache[0], src_kv_cache[1]
        dst_key_cache, dst_value_cache = dst_kv_cache[0], dst_kv_cache[1]
        src_indices = src_to_dst[:, 0]
        dst_indices = src_to_dst[:, 1]

        dst_key_cache[dst_indices] = src_key_cache[src_indices].to(dst_key_cache.device)
        dst_value_cache[dst_indices] = src_value_cache[src_indices].to(dst_key_cache.device)

    @staticmethod
    def copy_blocks(
        kv_caches: list[torch.Tensor],
        src_to_dists: torch.Tensor,
    ) -> None:
        src_indices = src_to_dists[:, 0]
        dst_indices = src_to_dists[:, 1]

        for kv_cache in kv_caches:
            key_caches = kv_cache[0]
            value_caches = kv_cache[1]
            key_caches[dst_indices] = key_caches[src_indices]
            value_caches[dst_indices] = value_caches[src_indices]

    @staticmethod
    def get_supported_kernel_block_sizes() -> list[int]:
        return [128]


# R116 quiet mode: gate THIS MODULE's debug prints (the ~25.7K-line/leg noise
# source). Module-level `print` shadow keeps the rest of the process
# untouched; allowlisted prefixes pass through. Default OFF = R115 behavior.
if os.environ.get("R116_QUIET", "0") == "1":
    _r116_builtin_print = print
    def _r116_gate_print(*args, **kwargs):
        try:
            _s = " ".join(str(a) for a in args)
        except Exception:
            _s = ""
        if _s.startswith(("PERFLEG", "PHASE_", "R116-KEY", "[R116-ERR")):
            _r116_builtin_print(*args, **kwargs)
    print = _r116_gate_print

# R114 steady-token hook: runs INSIDE EngineCore (the overlay is what the
# engine imports; the R112/R113 parent-side monkeypatch never reached the
# engine subprocess). One timestamp per decode step = layer-0 attention entry.
class AscendAttentionState(Enum):
    PrefillNoCache = 0
    PrefillCacheHit = 1
    DecodeOnly = 2
    ChunkedPrefill = 3
    SpecDecoding = 4


@dataclass
class AscendMetadata:
    """
    Per-layer attention metadata for Ascend FlashAttention backend.

    Contains attention masks, token counts, sequence lengths and KV cache
    related properties for attention computation.
    """

    # **************************** Basic Properties ************************** #
    attn_mask: torch.Tensor | None = None
    # Current state of this attention run.
    attn_state: AscendAttentionState = AscendAttentionState.ChunkedPrefill

    # Number of tokens excluding padding.
    num_actual_tokens_pcp_padded: int = 0
    num_actual_tokens: int = 0
    num_decode_tokens: int = 0
    num_prefills: int = 0
    num_decodes: int = 0

    # The sequence length per sequence. Sequence length means the computed
    # tokens + new tokens (is None if it is a decoding).
    # (batch_size,)
    # TODO(Angazenn): The following parameters are quite redundant and
    # contains similar information (such as seq_lens seq_lens_list). We
    # should simplified these parameters once attention schema in vLLM-Ascend
    # is unified.
    seq_lens: torch.Tensor = None
    seq_lens_cpu: torch.Tensor = None
    seq_lens_list: list[int] = None  # type: ignore
    actual_seq_lengths_q: list[int] = None  # type: ignore

    query_start_loc: torch.Tensor = None
    # Maximum query length in the batch (None for decoding).
    max_query_len: int | None = None

    # ********************** KV Cache Related Properties ********************* #
    # Block addresses per sequence (Seq id -> list of physical block).
    # (batch_size, max_blocks_per_seq)
    block_tables: torch.Tensor = None

    # The indices of the token slots that input tokens will be stored into.
    # E.g., if `slot_mapping` is [35, 2, 17] and the block size is 16, the
    # three tokens are stored in the 3rd slot in block 2, 2nd slot in block 0,
    # and 1st slot in block 1, respectively.
    # (num_tokens,)
    slot_mapping: torch.Tensor = None
    # pcp
    prefill: AscendMetadataForPrefill | None = None
    # dcp
    decode_meta: AscendMetadataForDecode | None = None

    causal: bool = True
    # runner_type in model_config.
    model_runner_type: str = ""
    # prefill reshape_and_cache event
    reshape_cache_event: torch.npu.Event = None

    kvcomp_metadata: KVCompMetaData | None = None

    # R144 P0: stable per-request identity (req_id strings, batch_idx->req_id)
    # plumbed from InputBatch.req_ids via AscendCommonAttentionMetadata. None
    # when R144_TT_REQID=0 (b-keyed verbatim path) or non-ascend paths.
    request_ids: list[str] | None = None

    # R144 P0.1: explicit scheduler lifecycle events (consumed by the resolver
    # instead of absence-inference). None when R144_TT_REQID=0.
    finished_req_ids: set[str] | None = None
    preempted_req_ids: set[str] | None = None
    new_req_ids: set[str] | None = None


class AscendAttentionMetadataBuilder(AttentionMetadataBuilder[AscendMetadata]):
    """
    Builder for constructing AscendMetadata from CommonAttentionMetadata.

    Handles attention mask generation and metadata preparation for
    Ascend FlashAttention backend.
    """

    # Does this backend/builder reorder the batch?
    # If not, set this to None. Otherwise set it to the query
    # length that will be pulled into the front of the batch.
    reorder_batch_threshold: int = 1

    def __init__(
        self,
        kv_cache_spec: AttentionSpec,
        layer_names: list[str],
        vllm_config: VllmConfig,
        device: torch.device,
    ):
        super().__init__(kv_cache_spec, layer_names, vllm_config, device)
        self.vllm_config = vllm_config
        self.model_config = vllm_config.model_config
        self.compilation_config = vllm_config.compilation_config
        self.device = device
        self.max_num_blocks_per_req = cdiv(
            self.model_config.max_model_len, AscendAttentionBackend.get_supported_kernel_block_sizes()[0]
        )

        self.speculative_config = vllm_config.speculative_config
        self.decode_threshold = 1
        if self.speculative_config:
            spec_token_num = self.speculative_config.num_speculative_tokens
            self.decode_threshold += spec_token_num
            assert self.decode_threshold <= 16, (
                f"decode_threshold exceeded \
                npu_fused_infer_attention_score TND layout's limit of 16, \
                got {self.decode_threshold}"
            )

        self.reorder_batch_threshold = self.decode_threshold

        scheduler_config = vllm_config.scheduler_config
        self.chunked_prefill_enabled = scheduler_config.enable_chunked_prefill
        self.attn_mask_builder = AttentionMaskBuilder(self.device)

    @classmethod
    def get_cudagraph_support(
        cls: type["AscendAttentionMetadataBuilder"],
        vllm_config: VllmConfig,
        kv_cache_spec: AttentionSpec,
    ) -> AttentionCGSupport:
        # Explicit override in case the underlying builder specialized this getter.
        # @override omitted only because of mypy limitation due to type variable.
        return AttentionCGSupport.ALWAYS

    def reorder_batch(self, input_batch, scheduler_output: "SchedulerOutput") -> bool:
        return False

    def build(
        self,
        common_prefix_len: int,
        common_attn_metadata: AscendCommonAttentionMetadata,
        fast_build: bool = False,
    ) -> AscendMetadata:
        num_reqs = common_attn_metadata.num_reqs
        num_actual_tokens = common_attn_metadata.num_actual_tokens
        query_start_loc_cpu = common_attn_metadata.query_start_loc_cpu[: num_reqs + 1]

        num_decodes, num_prefills, num_decode_tokens, num_prefill_tokens = split_decodes_and_prefills(
            common_attn_metadata, decode_threshold=self.decode_threshold
        )

        block_table = common_attn_metadata.block_table_tensor
        # Prefer _seq_lens_cpu (always available, updated during draft
        # iterations) over seq_lens_cpu (None in async spec decode mode).
        if common_attn_metadata._seq_lens_cpu is not None:
            seq_lens = common_attn_metadata._seq_lens_cpu[:num_reqs]
        elif common_attn_metadata.seq_lens_cpu is not None:
            seq_lens = common_attn_metadata.seq_lens_cpu[:num_reqs]
        else:
            seq_lens = common_attn_metadata.seq_lens[:num_reqs].to("cpu")

        slot_mapping = common_attn_metadata.slot_mapping[:num_actual_tokens]
        # this slot_mapping override doesn't work since vllm will override it again. We should fix it vllm.
        # see: https://github.com/vllm-project/vllm/blob/ce88756b967c2c5006746a424c15dd59a284ed8c/vllm/model_executor/layers/attention/cross_attention.py#L117
        if isinstance(self.kv_cache_spec, CrossAttentionSpec):
            seq_lens = common_attn_metadata.seq_lens
            slot_mapping = common_attn_metadata.slot_mapping.to(torch.int32)
        elif self.speculative_config and self.speculative_config.parallel_drafting:
            seq_lens = common_attn_metadata.seq_lens

        attn_state = common_attn_metadata.attn_state

        # Get attn_mask from singleton AttentionMaskBuilder
        attn_mask = self.attn_mask_builder.get_attention_mask(common_attn_metadata.causal, self.model_config)

        # TODO: Yet another unnecessary H2D while we already have a query_start_loc on device
        query_start_loc = query_start_loc_cpu.pin_memory().to(self.device, non_blocking=True)

        attn_metadata = AscendMetadata(
            num_actual_tokens=num_actual_tokens,
            num_decode_tokens=num_decode_tokens,
            block_tables=block_table,
            query_start_loc=query_start_loc,
            seq_lens=seq_lens,
            seq_lens_cpu=seq_lens,
            seq_lens_list=seq_lens.tolist(),
            max_query_len=common_attn_metadata.max_query_len,
            actual_seq_lengths_q=query_start_loc_cpu[1:].tolist(),
            slot_mapping=slot_mapping,
            attn_mask=attn_mask,
            attn_state=attn_state,
            num_prefills=num_prefills,
            num_decodes=num_decodes,
            causal=common_attn_metadata.causal,
            model_runner_type=self.model_config.runner_type,
            kvcomp_metadata=common_attn_metadata.kvcomp_metadata,
            request_ids=common_attn_metadata.request_ids,
            finished_req_ids=common_attn_metadata.finished_req_ids,
            preempted_req_ids=common_attn_metadata.preempted_req_ids,
            new_req_ids=common_attn_metadata.new_req_ids,
        )
        return attn_metadata

    def build_for_graph_capture(
        self,
        common_attn_metadata: AscendCommonAttentionMetadata,
        attn_state: AscendAttentionState = AscendAttentionState.DecodeOnly,
    ):
        if attn_state in (
            AscendAttentionState.DecodeOnly,
            AscendAttentionState.ChunkedPrefill,
            AscendAttentionState.SpecDecoding,
        ):
            attn_metadata = self.build(
                common_prefix_len=0,
                common_attn_metadata=common_attn_metadata,
            )
        else:
            raise NotImplementedError(
                "Currently we only support building dummy metadata for DecodeOnly and ChunkedPrefill state"
            )

        attn_metadata.attn_state = attn_state
        return attn_metadata


class AscendAttentionBackendImpl(AttentionImpl):
    # R113: class-level defaults so lazily-created instances (the __new__ path in
    # _forward_int2, class-surgery rebinds) also expose the attributes the graph
    # path queries at init (first hit: 'sliding_window' during EAGER=0 init).
    sliding_window = None
    alibi_slopes = None
    logits_soft_cap = None
    def __init__(
        self,
        num_heads: int,
        head_size: int,
        scale: float,
        num_kv_heads: int,
        alibi_slopes: list[float] | None,
        sliding_window: int | None,
        kv_cache_dtype: str,
        logits_soft_cap: float | None,
        attn_type: str,
        kv_sharing_target_layer_name: str | None,
        sinks: torch.Tensor = None,
        **kwargs,
    ) -> None:
        self.vllm_config = get_current_vllm_config()
        self.num_heads = num_heads
        self.head_size = head_size
        self.scale = float(scale)
        self.num_kv_heads = num_heads if num_kv_heads is None else num_kv_heads
        self.hidden_size = self.num_heads * self.head_size
        self.kv_cache_dtype = kv_cache_dtype
        self.sliding_window = sliding_window
        if alibi_slopes is not None:
            alibi_slopes = torch.tensor(alibi_slopes, dtype=torch.float32, device="npu")
        self.alibi_slopes = alibi_slopes
        self.attn_type = attn_type

        assert self.num_heads % self.num_kv_heads == 0
        self.num_queries_per_kv = self.num_heads // self.num_kv_heads
        self.key_cache = None
        self.value_cache = None
        self.is_kv_producer = (
            self.vllm_config.kv_transfer_config is not None and self.vllm_config.kv_transfer_config.is_kv_producer
        )
        self.enable_c8_quant = self.vllm_config.quant_config is not None and getattr(
            self.vllm_config.quant_config, "enable_c8_quant", False
        )
        self.sinks = sinks
        self.layerIndex = 0
        self.enable_hamming_sparse = is_enable_hamming_sparse()

    @staticmethod
    def update_graph_params(
        update_stream,
        forward_context,
        num_tokens,
        vllm_config,
        speculative_config=None,
        num_dcp_pcp_tokens=None,
        draft_attn_metadatas=None,
    ):
        # R156 HOSTPROF: host wall of the per-step attn-param update loop
        # (the 36-layer staging/CU loop). File-based, env-gated, default OFF.
        import os as _os156, time as _t156
        _hp156 = _os156.environ.get("R156_HOSTPROF", "0") == "1"
        _t156_t0 = _t156.perf_counter() if _hp156 else 0.0
        if _os156.environ.get("R159K_BDIAG", "0") == "1":
            try:
                with open("/tmp/r159k_bdiag.log", "a") as _bf:
                    _bf.write(f"[R159K_UGP] update_graph_params called nt={num_tokens} pid={_os156.getpid()}\n")
            except Exception:
                pass
        globals().setdefault('_R156_H2_STEP', {})["done"] = False
        try:
            return AscendAttentionBackendImpl._update_graph_params_r156(
                update_stream, forward_context, num_tokens, vllm_config,
                speculative_config, num_dcp_pcp_tokens, draft_attn_metadatas)
        finally:
            global _R170_EDGEFENCE_N
            if _R170_EDGEFENCE_MODE:
                # R170 edge fence (see flag comment at module top). Placed in
                # the wrapper finally so EVERY return path of the pre-replay
                # updater is covered; the replay the caller launches next is
                # then ordered behind ALL enqueued writes on ANY stream.
                if _R170_EDGEFENCE_MODE == 1 or _R170_EDGEFENCE_N < 3:
                    torch.npu.synchronize()
                _R170_EDGEFENCE_N += 1
            elif _os156.environ.get("R218_EDGEEV", "0") == "1":
                # R218 cheap edge ordering (default OFF, additive): give the
                # caller's stream -- the one that is about to launch THIS step's
                # captured replay -- a device-side dependency on the step's
                # metadata fills, without a host sync.  The fills and the shared
                # per-bucket event are recorded on update_stream by
                # _r164_update_meta (_ev.record(update_stream), keyed by
                # num_tokens), so waiting on that event here IS the missing
                # capture->replay edge (header note, lines 38-47), at device cost
                # only.  R170_EDGEFENCE=1 (torch.npu.synchronize) is the host-cost
                # probe of the same hypothesis; this is the shippable shape.
                try:
                    _regEE = getattr(globals().get(
                        "AscendINT2AttentionBackendImpl"), "_r164_events", None)
                    _evEE = _regEE.get(int(num_tokens)) if _regEE else None
                    if _evEE is not None:
                        torch.npu.current_stream().wait_event(_evEE)
                except Exception:
                    pass
            if _hp156:
                _dt = (_t156.perf_counter() - _t156_t0) * 1e3
                try:
                    with open(_os156.environ.get("R156_HOSTPROF_OUT",
                                             "/tmp/r156_hostprof.jsonl"), "a") as _f156:
                        _f156.write('{"ev": "update_loop", "ms": %.3f, "ntok": %d}\n'
                                    % (_dt, int(num_tokens)))
                except Exception:
                    pass

    @classmethod
    def _update_graph_params_r156(
            cls, update_stream, forward_context, num_tokens, vllm_config,
            speculative_config, num_dcp_pcp_tokens, draft_attn_metadatas):
        # R161 fence: make update_stream wait for cross-stream producers (prev
        # replay for F3, default stream for F1) before overwriting carriers.
        _r161_f.on_update_enter(update_stream, forward_context)
        if _R170_ROWSLOT_ON:
            # R170_ROWSLOT: after the fence edges (update_stream now ordered
            # after eager prefill writers + previous replay), migrate ring
            # content to decode-ROW slots before this step's graph replay.
            # update_graph_params is hardcoded to the BASE impl, so resolve
            # the INT2-subclass migrator when cls lacks it (fail-closed).
            # R171_PREMIG (default OFF): this POST-replay placement races the
            # just-launched replay's baked row-slot ring reads/slides with the
            # migrate's copy-engine writes (r171a: cross-solo drift WORSENED
            # 0.107->0.188 L1, 0.126->0.272 L2 + end-of-leg device hang in the
            # OUTLSE full sync — copy-engine vs in-flight AIC on the same
            # addresses). With PREMIG the driver migrates at the PRE-replay
            # point on the CURRENT (=replay) stream — FIFO-ordered after the
            # previous replay + eager prefill writes, before this launch — so
            # this post-replay copy is DISABLED (running both would re-create
            # the race from the other side).
            if _r144_ovl_os.environ.get("R171_PREMIG", "0") == "1":
                _mig170 = None
                if _r144_ovl_os.environ.get("R191_AUDIT", "0") == "1" and not globals().get('_R191_PREMIG', False):
                    globals()['_R191_PREMIG'] = True
                    try:
                        _oscar_diag_write("r191_audit.log", 
                            f"[PREMIG_RUNTIME] pid={_r144_ovl_os.getpid()} post-replay migrate disabled (PRE-replay wrapper owns migration)\n")
                    except Exception:
                        pass
            else:
                _mig170 = getattr(cls, "_r170_rowslot_migrate", None)
                if _mig170 is None:
                    _sub170 = globals().get(
                        "AscendINT2AttentionBackendImpl")
                    _mig170 = (_sub170._r170_rowslot_migrate
                               if _sub170 is not None else None)
                if _mig170 is None:
                    raise AttributeError(
                        "_r170_rowslot_migrate not defined on %r or the "
                        "INT2 impl" % (cls,))
                try:
                    _mig170(update_stream, forward_context, num_tokens)
                except RuntimeError:
                    raise
                except Exception as _e170u:
                    raise RuntimeError(
                        "[R170-ROWSLOT] migrate failed: %r (fail-closed)"
                        % (_e170u,)) from _e170u
        if using_paged_attention(num_tokens, vllm_config):
            # Paged Attention update logic
            if _EXTRA_CTX.is_draft_model:
                if _EXTRA_CTX.is_draft_model_prefill:
                    graph_params = get_draft_graph_prefill_params()
                else:
                    graph_params = get_draft_graph_params()
            else:
                graph_params = get_graph_params()
            with torch.npu.stream(update_stream):
                for key, param, handle, event in zip(
                    forward_context.attn_metadata,
                    graph_params.attn_params[num_tokens],
                    graph_params.handles[num_tokens],
                    graph_params.events[num_tokens],
                ):
                    (
                        query,
                        key_cache,
                        value_cache,
                        num_kv_heads,
                        num_heads,
                        scale,
                        block_table,
                        seq_lens,
                        output,
                    ) = param
                    seq_lens = forward_context.attn_metadata[key].seq_lens
                    # R170_MIDDUMP2 v2 REMOVED (was here): this
                    # using_paged_attention branch never runs on
                    # OSCAR legs (see h13/h15 postmortem — zero
                    # records). v3 lives after the _r164_update_meta
                    # call in the _r164_on branch below.

                    workspace = torch_npu._npu_paged_attention_get_workspace(
                        query=query,
                        key_cache=key_cache,
                        value_cache=value_cache,
                        num_kv_heads=num_kv_heads,
                        num_heads=num_heads,
                        scale_value=scale,
                        block_table=block_table,
                        context_lens=seq_lens,
                        out=output,
                    )
                    torch.npu.graph_task_update_begin(update_stream, handle)
                    torch_npu._npu_paged_attention(
                        query=query,
                        key_cache=key_cache,
                        value_cache=value_cache,
                        num_kv_heads=num_kv_heads,
                        num_heads=num_heads,
                        scale_value=scale,
                        block_table=block_table,
                        context_lens=seq_lens,
                        out=output,
                        workspace=workspace,
                    )
                    torch.npu.graph_task_update_end(update_stream)
                    event.record(update_stream)
        elif _EXTRA_CTX.sinks:
            # FIA update logic
            if _EXTRA_CTX.is_draft_model:
                graph_params = get_draft_graph_params()
                attn_metadata = draft_attn_metadatas
                attn_keys = list(attn_metadata[0].keys())
            else:
                graph_params = get_graph_params()
                attn_metadata = forward_context.attn_metadata
                attn_keys = list(attn_metadata.keys())
            # For Qwen3-next, since the kv_cache_config has already categorized
            # linear_attn and self_attn, the attn_metadata is first arranged with
            # self_attn followed by linear_attn. Therefore, using zip directly
            # filters out the update operations for linear_attn.
            # TODO: We use a new variable `attn_keys` to ensure the loop count is
            # correct after get by `zip` because of the new structure of the attn_metadata
            # when running with the merged full eagle-graph. Should check it with Qwen3-next.
            num_layers = len(attn_keys)
            if num_layers == 0:
                return
            if _EXTRA_CTX.is_draft_model:
                attn_keys = attn_keys * (len(graph_params.attn_params[num_tokens]) // num_layers)
            attn_count = 0
            # R156-H3: fused all-layer staging (one kernel launch replaces the
            # ~800-enqueue per-layer loop). Runs BEFORE the per-layer loop;
            # the updater per layer then only CUEAGER-checks + records events.
            if (os.environ.get("R156_H3", "0") == "1"
                    and graph_params.attn_params.get(num_tokens)
                    and len(graph_params.attn_params[num_tokens]) > 0
                    and isinstance(graph_params.attn_params[num_tokens][0][0], str)
                    and graph_params.attn_params[num_tokens][0][0] == "OSCAR_MID_R113"):
                _p0h3 = graph_params.attn_params[num_tokens][0]
                _implH3 = _p0h3[21]
                _mdH3 = None
                for _kH3 in forward_context.attn_metadata:
                    _mdH3 = forward_context.attn_metadata[_kH3]
                    break
                _okH3 = False
                if _mdH3 is not None:
                    _okH3 = _implH3._r156_h3_stage_all(
                        update_stream, forward_context,
                        graph_params.attn_params[num_tokens], num_tokens)
                if _okH3:
                    type(_implH3)._r156_h3_stamp = {
                        "k": (num_tokens, int(_mdH3.seq_lens_list[0]),
                              int(_p0h3[17]))}
                else:
                    type(_implH3)._r156_h3_stamp = None
            with torch.npu.stream(update_stream):
                for key, param, handle, event in zip(
                    attn_keys,
                    graph_params.attn_params[num_tokens],
                    graph_params.handles[num_tokens],
                    graph_params.events[num_tokens],
                ):
                    (
                        query,
                        key_cache,
                        value,
                        block_tables,
                        attn_mask,
                        block_size,
                        seq_lens,
                        num_kv_heads,
                        num_heads,
                        scale,
                        sliding_window,
                        sinks,
                        attn_output,
                        softmax_lse,
                    ) = param

                    if _EXTRA_CTX.is_draft_model:
                        draft_step = attn_count // num_layers
                        seq_lens = attn_metadata[draft_step][key].seq_lens_list
                        actual_seq_lengths_q = attn_metadata[draft_step][key].actual_seq_lengths_q
                        attn_count = attn_count + 1
                    else:
                        seq_lens = attn_metadata[key].seq_lens_list
                        actual_seq_lengths_q = attn_metadata[key].actual_seq_lengths_q

                    torch.npu.graph_task_update_begin(update_stream, handle)
                    torch_npu.npu_fused_infer_attention_score_v2.out(
                        query=query,
                        key=key_cache,
                        value=value,
                        block_table=block_tables,
                        atten_mask=attn_mask,
                        input_layout="TND",
                        block_size=block_size,
                        actual_seq_qlen=actual_seq_lengths_q,
                        actual_seq_kvlen=seq_lens,
                        num_key_value_heads=num_kv_heads,
                        num_query_heads=num_heads,
                        sparse_mode=4 if sliding_window is not None else 3,
                        pre_tokens=sliding_window if sliding_window is not None else SWA_INT_MAX,
                        next_tokens=0,
                        softmax_scale=scale,
                        learnable_sink=sinks,
                        workspace=graph_params.workspaces.get(num_tokens),
                        out=[attn_output, softmax_lse],
                    )
                    torch.npu.graph_task_update_end(update_stream)
                    event.record(update_stream)
        else:
            # FIA update logic
            if _EXTRA_CTX.is_draft_model:
                if _EXTRA_CTX.is_draft_model_prefill:
                    graph_params = get_draft_graph_prefill_params()
                else:
                    graph_params = get_draft_graph_params()
                attn_metadata = draft_attn_metadatas
                attn_keys = list(attn_metadata[0].keys())
            else:
                graph_params = get_graph_params()
                attn_metadata = forward_context.attn_metadata
                attn_keys = list(attn_metadata.keys())
                # In some speculative methods (such as DFlash), the order of attn_keys in the Target model
                # will be disrupted instead of increasing by layer index, so need regular expressions to
                # reorder the attn_keys and stor the results in _ATTN_KEYS_BUFFER.
                attn_keys_length = len(graph_params.attn_params[num_tokens])
                global _ATTN_KEYS_BUFFER
                if _ATTN_KEYS_BUFFER is None:
                    import regex as re

                    def extract_layer_index(key: str) -> int:
                        match = re.search(r"(\d+)", key)
                        return int(match.group(1)) if match else 0

                    attn_keys_tmp = attn_keys[:attn_keys_length]
                    attn_keys_tmp.sort(key=extract_layer_index)
                    _ATTN_KEYS_BUFFER = attn_keys_tmp
                attn_keys[:attn_keys_length] = _ATTN_KEYS_BUFFER
            # For Qwen3-next, since the kv_cache_config has already categorized
            # linear_attn and self_attn, the attn_metadata is first arranged with
            # self_attn followed by linear_attn. Therefore, using zip directly
            # filters out the update operations for linear_attn.
            # TODO: We use a new variable `attn_keys` to ensure the loop count is
            # correct after get by `zip` because of the new structure of the attn_metadata
            # when running with the merged full eagle-graph. Should check it with Qwen3-next.
            num_layers = len(attn_keys)
            if num_layers == 0:
                return
            if _EXTRA_CTX.is_draft_model:
                attn_keys = attn_keys * (len(graph_params.attn_params[num_tokens]) // num_layers)
            # R159K_B2FIX: INT2 three-tier middle capture appends num_layers × B
            # entries (the for-b loop at line 7499→7845 calls _r113_middle_graph
            # once per b per layer, each appending one ExternalEvent at line 7363).
            # But attn_keys has only num_layers entries, so the zip(attn_keys,
            # params, ...) below truncates to num_layers — leaving
            # (B-1)*num_layers ExternalEvents with NO event.record(update_stream).
            # The graph's baked event.wait(graph_stream) nodes (line 7363) then
            # block FOREVER on the first unrecorded event → first replay hangs at
            # acl_graph.py:277. B=1 is exempt (num_layers×1==num_layers); BF16 is
            # exempt (FIA appends one entry/layer, no for-b loop). Derive each
            # entry's layer key from the baked _lid (param[24], the stable
            # name-parsed layer ordinal from _oscar_layer_ord) so ALL events get
            # recorded. Default OFF; no effect when len(params)==num_layers.
            if (os.environ.get("R159K_B2FIX", "0") == "1"
                    and not _EXTRA_CTX.is_draft_model):
                _np_mid = len(graph_params.attn_params[num_tokens])
                if _np_mid > num_layers:
                    _bf_keys = []
                    for _p in graph_params.attn_params[num_tokens]:
                        if (isinstance(_p, (tuple, list)) and len(_p) > 24
                                and isinstance(_p[24], int)
                                and 0 <= _p[24] < num_layers):
                            _bf_keys.append(attn_keys[_p[24]])
                        else:
                            _bf_keys.append(attn_keys[0])
                    attn_keys = _bf_keys
                    if os.environ.get("R191_AUDIT", "0") == "1" and not globals().get('_R191_B2FIX', False):
                        globals()['_R191_B2FIX'] = True
                        try:
                            _oscar_diag_write("r191_audit.log", 
                                f"[B2FIX_RUNTIME] pid={os.getpid()} n_params={_np_mid} n_layers={num_layers} keys_derived={len(_bf_keys)}\n")
                        except Exception:
                            pass
            attn_count = 0
            if os.environ.get("R159K_BDIAG", "0") == "1":
                globals().setdefault('_R159K_LOOP_N', 0)
                globals()['_R159K_LOOP_N'] += 1
                if globals()['_R159K_LOOP_N'] <= 3:
                    _npa = len(graph_params.attn_params.get(num_tokens, []))
                    _nkeys = len(attn_keys)
                    _pm0 = graph_params.attn_params[num_tokens][0][0] if _npa and len(graph_params.attn_params[num_tokens][0]) > 0 else 'EMPTY'
                    try:
                        with open("/tmp/r159k_bdiag.log", "a") as _bf:
                            _bf.write(f"[R159K_LOOP] call#{globals()['_R159K_LOOP_N']} nt={num_tokens} n_params={_npa} n_keys={_nkeys} b2fix={os.environ.get('R159K_B2FIX','?')} param0={_pm0}\n")
                    except Exception:
                        pass
            # R156-H3: fused all-layer staging (one kernel launch replaces the
            # ~800-enqueue per-layer loop). Runs BEFORE the per-layer loop;
            # the updater per layer then only CUEAGER-checks + records events.
            if (os.environ.get("R156_H3", "0") == "1"
                    and graph_params.attn_params.get(num_tokens)
                    and len(graph_params.attn_params[num_tokens]) > 0
                    and isinstance(graph_params.attn_params[num_tokens][0][0], str)
                    and graph_params.attn_params[num_tokens][0][0] == "OSCAR_MID_R113"):
                _p0h3 = graph_params.attn_params[num_tokens][0]
                _implH3 = _p0h3[21]
                _mdH3 = None
                for _kH3 in forward_context.attn_metadata:
                    _mdH3 = forward_context.attn_metadata[_kH3]
                    break
                _okH3 = False
                if _mdH3 is not None:
                    _okH3 = _implH3._r156_h3_stage_all(
                        update_stream, forward_context,
                        graph_params.attn_params[num_tokens], num_tokens)
                if _okH3:
                    type(_implH3)._r156_h3_stamp = {
                        "k": (num_tokens, int(_mdH3.seq_lens_list[0]),
                              int(_p0h3[17]))}
                else:
                    type(_implH3)._r156_h3_stamp = None
            # R164 BATCHED_STAGE: refresh the layer-invariant device metadata
            # ONCE per step (bt-mirror + askv + asq) and record the SINGLE
            # shared E_inputs_ready. Per-layer updater entries become no-ops
            # (staging lives in the graph); fills 36*B -> ~36 in-graph groups.
            _r164_on = (os.environ.get("R164_BATCHED_STAGE", "0") == "1"
                        and graph_params.attn_params.get(num_tokens)
                        and len(graph_params.attn_params[num_tokens]) > 0
                        and graph_params.attn_params[num_tokens][0][0] == "OSCAR_MID_R164")
            if _r164_on:
                _p0r = graph_params.attn_params[num_tokens][0]
                _mdR = None
                for _kR in forward_context.attn_metadata:
                    _mdR = forward_context.attn_metadata[_kR]
                    break
                if _mdR is None:
                    raise RuntimeError("[R164] no attn_metadata at replay (fail-closed)")
                # R218_UPFILL (default OFF): publish the per-step metadata on
                # the CALLER's current stream -- the same stream the replay is
                # launched on (the ownership rule _r170_mdfill's "cur" mode
                # already uses) -- instead of the side update_stream. Then
                #   prev-replay -> fills -> this replay
                # is stream-FIFO BY CONSTRUCTION: no fence events, and the
                # fills' device source (md.block_tables, refreshed by the
                # runner on this same stream) is read in enqueue order.
                # Replaces the R218_UPSYNC host syncs: =1 heals ragged rebind
                # but CORRUPTS uniform admission/split steps (b254/b255/b256:
                # ctx2048 rows 17-19 @token4, ctx8192 row0 @33 under BOTH
                # gate variants -- "sync when slots change" is not a valid
                # predicate, admission reorders rows prefill-first so
                # positional slots always change).
                _upsR218 = update_stream
                if os.environ.get("R218_UPFILL", "0") == "1":
                    _upsR218 = torch.npu.current_stream()
                _p0r[21]._r164_update_meta(
                    _upsR218, _mdR, _p0r[21], int(_p0r[17]),
                    int(_p0r[18]), int(_p0r[19]), num_tokens)
                if _R170_MID2_ON:
                    # R170_MIDDUMP2 v3 (default OFF): host-side pre-replay
                    # paged-cache fingerprint in the LIVE branch (h13/h15
                    # postmortem: v2 sat in the never-taken paged branch;
                    # v1 sat in the R164 no-op'd per-layer updater). Dump the
                    # first-3 layer entries' key_cache pages for row-0's mid
                    # blocks, first 2 pure-decode steps per rid. ident3K
                    # fixture => identical ksum across solos; a walking ksum
                    # = write-side defect B (H1'); clean pages + corrupt out
                    # = read/carrier (H2'). Every failure path writes an
                    # err-record — probes must never be silently void.
                    def _mid2_log3(_rec):
                        with open("/tmp/r170_middump2.jsonl", "a") as _f3:
                            _f3.write(_rec + "\n")
                    try:
                        _apL = graph_params.attn_params[num_tokens]
                        # R170b fix: `0 or 1` == 1 — the `or 1` idiom mapped
                        # pure-decode (num_prefills==0) to 1, skipping EXACTLY
                        # the steps we dump (zero records, silent; h17/h18
                        # void probes). Keep default-1 (missing attr => skip),
                        # drop the `or`.
                        _npf3 = int(getattr(_mdR, "num_prefills", 1))
                        if _npf3 != 0:
                            _apL = ()  # mixed/prefill step — pure decodes only
                        _rids3 = getattr(_mdR, "request_ids", None) or ["?"]
                        _rid3 = str(_rids3[0])
                        _mid2_seen = globals().setdefault(
                            '_R170_MID3_SEEN', {})
                        for _li3 in range(min(3, len(_apL))):
                            _pL3 = _apL[_li3]
                            _impl3 = _pL3[21] if len(_pL3) > 21 else None
                            if _impl3 is None:
                                continue
                            _cnt3 = _mid2_seen.get((_rid3, _li3), 0)
                            if _cnt3 >= 2:
                                continue
                            _mid2_seen[(_rid3, _li3)] = _cnt3 + 1
                            try:
                                _blk_lo3 = int(_p0r[18]) // int(
                                    _impl3.vllm_config.cache_config.block_size)
                                _sl3 = getattr(_mdR, "seq_lens_list", None)
                                _slv3 = int(_sl3[0]) if _sl3 else -1
                                _bt3 = _mdR.block_tables
                                _row3 = _bt3[0, _blk_lo3:_blk_lo3 + 24]
                                _row3l = [int(x) for x in _row3.tolist()]
                                _kc3 = getattr(_impl3, "key_cache", None)
                                if _kc3 is None:
                                    _mid2_log3('{"rid": "%s", "lidx": %d, '
                                               '"dec": %d, "err": "no kc"}'
                                               % (_rid3, _li3, _cnt3))
                                    continue
                                _pg3 = _kc3[_row3l[0]]
                                _ksum3 = float(_pg3.float().abs().sum().item())
                                _kfp3 = (_pg3.view(torch.int16)
                                         .reshape(-1)[:16]
                                         .to(torch.int32).tolist())
                                # R170c ring dump (defect-B read-side fork,
                                # H2' confirmed 13:50Z): pages bit-identical
                                # across solos, so the walking state is NOT
                                # the key pages. The per-slot hp K/V rings
                                # (_tt_hp_k/_v[_lid], [max_seqs, max_hp, H,
                                # D] bf16) are persistent, written by the
                                # prefill seed + slide, READ at decode — the
                                # top candidate. rg = [Kall, Vall, Kt64, Vt64]
                                # abs-sums for THIS rid's slot at this layer;
                                # identical across solos => rings clean too.
                                _rg3 = None
                                try:
                                    _smap3 = getattr(type(_impl3),
                                                     "_r164_slotmap",
                                                     None) or {}
                                    _slot3 = _smap3.get(_rid3)
                                    _rk3 = (getattr(_impl3, "_tt_hp_k",
                                                    None) or {}).get(_li3)
                                    _rv3 = (getattr(_impl3, "_tt_hp_v",
                                                    None) or {}).get(_li3)
                                    if (_slot3 is not None
                                            and _rk3 is not None
                                            and _rv3 is not None):
                                        _n3 = int(_rk3.shape[1])
                                        _s3 = int(_slot3)
                                        _rg3 = [
                                            round(float(_rk3[_s3, :_n3].float().abs().sum().item()), 3),
                                            round(float(_rv3[_s3, :_n3].float().abs().sum().item()), 3),
                                            round(float(_rk3[_s3, max(0, _n3 - 64):_n3].float().abs().sum().item()), 3),
                                            round(float(_rv3[_s3, max(0, _n3 - 64):_n3].float().abs().sum().item()), 3)]
                                except Exception:
                                    _rg3 = None
                                _mid2_log3(
                                    '{"rid": "%s", "lidx": %d, "dec": %d, '
                                    '"sl": %d, "blk_lo": %d, "bt0": %s, '
                                    '"ksum": %.1f, "kfp": %s, "rg": %s, '
                                    '"oid": %d}'
                                    % (_rid3, _li3, _cnt3, _slv3, _blk_lo3,
                                       str(_row3l[:12]), _ksum3, _kfp3,
                                       str(_rg3), id(_impl3) % 100000))
                            except Exception as _e3i:
                                _mid2_log3('{"rid": "%s", "lidx": %d, '
                                           '"dec": %d, "err": "%s"}'
                                           % (_rid3, _li3, _cnt3,
                                              repr(_e3i)[:120].replace(
                                                  '"', "'")))
                    except Exception as _e3:
                        try:
                            _mid2_log3('{"err_outer": "%s"}'
                                       % repr(_e3)[:140].replace('"', "'"))
                        except Exception:
                            pass
            with torch.npu.stream(update_stream):
                for key, param, handle, event in zip(
                    attn_keys,
                    graph_params.attn_params[num_tokens],
                    graph_params.handles[num_tokens],
                    graph_params.events[num_tokens],
                ):
                    # R113: OSCAR marker params (three-tier middle task-group
                    # nodes) get their dedicated updater; never hit the FIA
                    # positional unpack below.
                    if len(param) > 0 and isinstance(param[0], str) and param[0].startswith("OSCAR_"):
                        if param[0] == "OSCAR_MID_R113":
                            _h2st = globals().get('_R156_H2_STEP', {})
                            if (os.environ.get("R156_H4", "0") == "1"
                                    and not _h2st.get("done")):
                                _h2st["done"] = bool(
                                    AscendAttentionBackendImpl._r156_h4_fused_update(
                                        update_stream, forward_context,
                                        graph_params.attn_params[num_tokens],
                                        graph_params.handles[num_tokens],
                                        graph_params.events[num_tokens],
                                        num_tokens))
                                if _h2st["done"]:
                                    continue
                            if (os.environ.get("R156_H2", "0") == "1"
                                    and not _h2st.get("done")):
                                _h2st["done"] = bool(
                                    AscendAttentionBackendImpl._r156_h2_fused_update(
                                        update_stream, forward_context,
                                        graph_params.attn_params[num_tokens],
                                        graph_params.handles[num_tokens],
                                        graph_params.events[num_tokens],
                                        num_tokens))
                                if _h2st["done"]:
                                    continue
                                # fused declined: per-layer path continues
                            # R156 HP2: total per-layer updater wall (the
                            # subblock timers inside sum to only ~0.74ms/step;
                            # this locates the remaining host mass)
                            import time as _t156c, os as _os156c
                            _hp2c = _os156c.environ.get("R156_HOSTPROF", "0") == "2"
                            _tA2 = _t156c.perf_counter() if _hp2c else 0.0
                            AscendAttentionBackendImpl._r113_update_oscar_mid(
                                update_stream, key, param, handle, event, forward_context)
                            if _hp2c:
                                _acc2 = globals().setdefault(
                                    '_R156_HP2C', {"n": 0, "tot": 0.0, "mx": 0.0})
                                _d2 = _t156c.perf_counter() - _tA2
                                _acc2["tot"] += _d2
                                _acc2["mx"] = max(_acc2["mx"], _d2)
                                _acc2["n"] += 1
                                if _acc2["n"] % 36 == 0 and (_acc2["n"] // 36) % 20 == 0:
                                    import json as _js2
                                    with open("/tmp/r156_hp2c.jsonl", "a") as _f2:
                                        _f2.write(_js2.dumps(
                                            {"n": _acc2["n"],
                                             "sum_ms": round(_acc2["tot"] * 1e3, 3),
                                             "max_ms": round(_acc2["mx"] * 1e3, 3)}) + "\n")
                                    _acc2["tot"] = 0.0; _acc2["mx"] = 0.0
                            continue
                        if param[0] == "OSCAR_MID_R113_BATCHED":
                            # R161 P1-A: ONE batched middle updater per layer
                            # (param[17]=Bcap; param[21]=impl). len(params)
                            # == num_layers -> zip is clean (no B2FIX needed).
                            type(param[21])._r113_update_oscar_mid_batched(
                                update_stream, key, param, handle, event, forward_context)
                            continue
                        if param[0] == "OSCAR_MID_R163_V1CAP":
                            # R163 V1CAP: content-only update (no task_update).
                            type(param[21])._r113_update_oscar_mid_v1cap(
                                update_stream, key, param, handle, event, forward_context)
                            continue
                        if param[0] == "OSCAR_MID_R164":
                            # R164: staging is IN-GRAPH; the per-step metadata
                            # refresh + shared E_inputs_ready record happened
                            # ONCE above. Per-layer: only the one-step-lag paged
                            # flush (same semantics as all prior paths).
                            if not _r164_on:
                                raise RuntimeError(
                                    "[R164] metadata refresh missed before marker "
                                    f"{param[0]} (fail-closed)")
                            if os.environ.get("R155_T_NOFLUSH", "0") != "1":
                                param[21]._r113_flush_stage(update_stream, param[23])
                            continue
                        if param[0] == "OSCAR_SR_R155":
                            # R155 F3: re-issue the S/R FIA per replay (static
                            # shapes) inside the task-update region — the
                            # N-path mechanism; a stale captured aclnn task
                            # costs ~1.16ms/replay (D1 leg).
                            (_m, q_sr, k_sr, v_sr, n_pr_sr, nh_sr, nkv_sr,
                             sc_sr, out_sr, lse_sr, ws_sr) = param
                            torch.npu.graph_task_update_begin(update_stream, handle)
                            torch_npu.npu_fused_infer_attention_score_v2.out(
                                query=q_sr, key=k_sr, value=v_sr,
                                input_layout="BNSD",
                                actual_seq_qlen=[1], actual_seq_kvlen=[n_pr_sr],
                                num_query_heads=nh_sr, num_key_value_heads=nkv_sr,
                                softmax_scale=sc_sr, sparse_mode=0,
                                return_softmax_lse=True, workspace=ws_sr,
                                out=[out_sr, lse_sr])
                            torch.npu.graph_task_update_end(update_stream)
                            event.record(update_stream)
                            continue
                        raise RuntimeError(f"[R113-GA] unknown OSCAR marker {param[0]} (fail-closed)")
                    (
                        query,
                        key_cache,
                        value,
                        block_tables,
                        attn_mask,
                        block_size,
                        seq_lens,
                        query_start_loc,
                        num_kv_heads,
                        num_heads,
                        scale,
                        attn_output,
                        softmax_lse,
                        sparse_mode,
                        pre_tokens,
                        next_tokens,
                        c8_k_aq_scale,
                        c8_k_aq_offset,
                        c8_v_aq_scale,
                        c8_v_aq_offset,
                    ) = param

                    if _EXTRA_CTX.is_draft_model:
                        draft_step = attn_count // num_layers
                        seq_lens = attn_metadata[draft_step][key].seq_lens_list
                        actual_seq_lengths_q = attn_metadata[draft_step][key].actual_seq_lengths_q
                        block_tables = attn_metadata[draft_step][key].block_tables
                        attn_count = attn_count + 1
                        if not attn_metadata[draft_step][key].causal:
                            sparse_mode = 0
                    else:
                        seq_lens = attn_metadata[key].seq_lens_list
                        actual_seq_lengths_q = attn_metadata[key].actual_seq_lengths_q
                        # NOTE:
                        # For models with sliding-window attention on the FIA full-graph replay path,
                        # rebinding `block_tables` to the latest metadata tensor causes corrupted /
                        # repeated outputs in our repro on Ascend NPU.
                        #
                        # Keep the captured block_tables tensor on this affected path.
                        # Non-SWA models preserve the original behavior and continue to refresh
                        # block_tables from attn_metadata.
                        if not hasattr(vllm_config.model_config.hf_text_config, "sliding_window"):
                            block_tables = attn_metadata[key].block_tables

                    torch.npu.graph_task_update_begin(update_stream, handle)
                    input_layout = "TND"
                    extra_args = {}
                    if c8_k_aq_scale is not None:
                        extra_args = {
                            "key_antiquant_scale": c8_k_aq_scale,
                            "value_antiquant_scale": c8_v_aq_scale,
                            "key_antiquant_mode": 0,
                            "value_antiquant_mode": 0,
                            "inner_precise": 1,
                        }
                        input_layout = "BNSD"
                        sparse_mode = 0
                    torch_npu.npu_fused_infer_attention_score.out(
                        query=query,
                        key=key_cache,
                        value=value,
                        block_table=block_tables,
                        atten_mask=attn_mask,
                        input_layout=input_layout,
                        block_size=block_size,
                        actual_seq_lengths=actual_seq_lengths_q,
                        actual_seq_lengths_kv=seq_lens,
                        num_key_value_heads=num_kv_heads,
                        num_heads=num_heads,
                        scale=scale,
                        sparse_mode=sparse_mode,
                        pre_tokens=pre_tokens,
                        next_tokens=next_tokens,
                        **extra_args,
                        workspace=graph_params.workspaces.get(num_tokens),
                        out=[attn_output, softmax_lse],
                    )
                    torch.npu.graph_task_update_end(update_stream)

                    event.record(update_stream)
                # R161 F2/F5: after ALL per-(layer,b) carrier fills are enqueued
                # on update_stream, record the coarse fill-complete edge so the
                # replay stream can wait it (single fence, no per-(layer,b) host
                # sync). No-op when R161_FENCE not in {2,5}.
                _r161_f.on_update_exit(update_stream)
    @classmethod
    def _r156_h4_fused_update(cls, update_stream, forward_context, params,
                              handles, events, num_tokens):
        """R156-H4 (R156_H4=1; needs the runner buffer consolidation + H4
        pools): ONE flat staging sequence for ALL layers — ~15 launches per
        STEP (vs ~430 per-layer; the per-launch device wall is ~80us). Far
        below the H2 saturation point. B=1; returns False -> per-layer."""
        import os as _os
        import torch as _t
        p0 = params[0]
        if p0[17] != 0:
            return False
        impl = p0[21]
        md = None
        for _k in forward_context.attn_metadata:
            md = forward_context.attn_metadata[_k]
            break
        if md is None:
            return False
        sl = int(md.seq_lens_list[0])
        (marker, q, k, v, bt, ks_c, ko_c, vs_c, vo_c, out_h, lse_h, mask,
         nq, scale, nkv, layout, block_size, b, mid_start, rcnt, S_pad,
         _impl, _nt, layer_idx, _lid0) = p0
        mid_len = sl - rcnt - mid_start
        if mid_len <= 0:
            return False
        _shr = getattr(type(impl), "_r156_h4_share", None)
        if _shr is None or _shr.get("L") != len(params):
            return False
        L = len(params)
        P = _shr["pools"]
        nb_now = (mid_len + block_size - 1) // block_size
        blk_lo = mid_start // block_size
        bt_live = md.block_tables
        if bt_live.dtype != _t.int32 or bt_live.stride(1) != 1:
            return False
        bt_gather = bt_live[0, blk_lo:blk_lo + nb_now]
        # --- merged SOURCE views (runtime-detected, order-independent) -----
        _det = getattr(type(impl), "_r156_h4_src", None)
        if _det is None or _det.get("L") != L or _det.get("sig") != tuple(
                params[i][21].key_cache.data_ptr() for i in range(0, L, 7)):
            kcs = [params[i][21].key_cache for i in range(L)]
            vcs = [params[i][21].value_cache for i in range(L)]
            page_elems = kcs[0].numel()
            base_k = min(t.data_ptr() for t in kcs)
            base_v = min(t.data_ptr() for t in vcs)
            span_k = max(t.data_ptr() for t in kcs) - base_k
            ok = all((t.data_ptr() - base_k) % page_elems == 0 for t in kcs) and \
                all((t.data_ptr() - base_v) % page_elems == 0 for t in vcs)
            if not ok:
                type(impl)._r156_h4_src = None
                return False
            st_k = kcs[0]
            n_pages_total = (max(t.data_ptr() for t in kcs) - base_k) // page_elems + 1
            flat_k = _t.as_strided(kcs[0], (n_pages_total,) + tuple(kcs[0].shape[1:]),
                                   tuple(kcs[0].stride()), storage_offset=0)
            n_pages_v = (max(t.data_ptr() for t in vcs) - base_v) // page_elems + 1
            flat_v = _t.as_strided(vcs[0], (n_pages_v,) + tuple(vcs[0].shape[1:]),
                                   tuple(vcs[0].stride()), storage_offset=0)
            off_k = _t.tensor([(t.data_ptr() - base_k) // page_elems for t in kcs],
                              dtype=_t.int64, device=bt_live.device)
            off_v = _t.tensor([(t.data_ptr() - base_v) // page_elems for t in vcs],
                              dtype=_t.int64, device=bt_live.device)
            type(impl)._r156_h4_src = {
                "L": L, "flat_k": flat_k, "flat_v": flat_v,
                "off_k": off_k.view(L, 1), "off_v": off_v.view(L, 1),
                "sig": tuple(params[i][21].key_cache.data_ptr() for i in range(0, L, 7)),
                "kc0": kcs[0]}
            _det = type(impl)._r156_h4_src
        flat_k, flat_v = _det["flat_k"], _det["flat_v"]
        off_k, off_v = _det["off_k"], _det["off_v"]
        # --- global scale mega ------------------------------------------------
        _gd = globals().get('_R156_H4_SCALE', {})
        gmeg = None
        for _e in _gd.values():
            gmeg = _e["t"]
            break
        if gmeg is None or gmeg.shape[0] != L:
            return False
        # CU-boundary step or CUEAGER off: defer to per-layer path
        if _os.environ.get("R155_CUEAGER", "0") == "1":
            t0_f = sl - rcnt
            if t0_f >= 0 and (t0_f % 64) == 0 and (t0_f + 64) > (sl - 1 - 0):
                pass  # rare boundary; still fine (CU handled per-layer below only if fired)
        S_now = nb_now * block_size
        ar = _t.arange(L, device=bt_live.device, dtype=_t.int64).view(L, 1)
        with _t.npu.stream(update_stream):
            idx_k = (off_k + bt_gather.view(1, nb_now)).view(L * nb_now)
            idx_v = (off_v + bt_gather.view(1, nb_now)).view(L * nb_now)
            gk = flat_k.index_select(0, idx_k)     # [L*nb, bs, nkv, pk]
            gv = flat_v.index_select(0, idx_v)
            car_k = P["k"].view(L, nb_now, block_size, nkv, -1)
            car_k.copy_(gk.view(L, nb_now, block_size, nkv, -1).permute(0, 1, 3, 2, 4))
            car_v = P["v"].view(L, nb_now, block_size, nkv, -1)
            car_v.copy_(gv.view(L, nb_now, block_size, nkv, -1).permute(0, 1, 3, 2, 4))
            sc = gmeg[:, :, bt_gather]             # [L,4,nb,bs,nkv]
            scv = sc.view(L, 4, S_now, nkv).permute(0, 1, 3, 2)
            car_sc = P["sc"]                        # [L,4,nkv,s_pad]
            car_sc[:, :, :, :mid_len].copy_(scv[:, :, :, :mid_len])
            ks_v = car_sc[:, 0, :, :mid_len]
            ko_v = car_sc[:, 1, :, :mid_len]
            vs_v = car_sc[:, 2, :, :mid_len]
            vo_v = car_sc[:, 3, :, :mid_len]
            _t.neg(scv[:, 1, :, :mid_len], out=ko_v)
            ko_v.mul_(ks_v)
            _t.neg(scv[:, 3, :, :mid_len], out=vo_v)
            vo_v.mul_(vs_v)
            P["bt"].copy_(_t.arange(P["bt"].shape[2], dtype=_t.int32,
                                    device=bt_live.device).view(1, 1, -1))
            _cp0 = getattr(type(impl), "_r113_cpool", {})
            _c0 = _cp0.get(params[0][24])
            if _c0 is None:
                return False
            _c0["askv_dev"].fill_(mid_len)
            _c0["asq_dev"].fill_(1)
        for i in range(L):
            events[i].record(update_stream)
        return True

    @classmethod
    def _r156_h2_fused_update(cls, update_stream, forward_context, params,
                              handles, events, num_tokens):
        """R156-H2 (R156_H2=1, requires H1 family): ONE flat pass over all
        OSCAR_MID_R113 params. Removes the per-layer function call, 25-tuple
        unpack, env reads and dict lookups (measured ~0.66ms/layer of python
        floor at the 38ms H1x point). Byte-identical device ops to the H1
        path (E-class). B=1 only; returns False to fall back per-layer."""
        import os as _os
        import torch as _t
        p0 = params[0]
        if p0[17] != 0:
            return False
        impl = p0[21]
        md = None
        for _k in forward_context.attn_metadata:
            md = forward_context.attn_metadata[_k]
            break
        if md is None:
            return False
        try:
            sl = int(md.seq_lens_list[0])
        except Exception:
            return False
        (marker, q, k, v, bt, ks_c, ko_c, vs_c, vo_c, out_h, lse_h, mask,
         nq, scale, nkv, layout, block_size, b, mid_start, rcnt, S_pad,
         _impl, _nt, layer_idx, _lid0) = p0
        mid_len = sl - rcnt - mid_start
        # shared per-step constants (identical across the 36 layers)
        nb_now = (mid_len + block_size - 1) // block_size
        blk_lo = mid_start // block_size
        bt_live = md.block_tables
        if bt_live.dtype != _t.int32 or bt_live.stride(1) != 1:
            return False
        bt_gather = bt_live[0, blk_lo:blk_lo + nb_now]
        kc = impl.key_cache
        vc = impl.value_cache
        mega = getattr(impl, "_r156_scale_mega", None)
        cu_on = _os.environ.get("R155_CUEAGER", "0") == "1"
        # per-layer tuple: (k_car, v_car, ks, ko, vs, vo, bt_pool, cpool_c)
        layers = []
        _cp = getattr(type(impl), "_r113_cpool", {})
        for _p in params:
            if _p[17] != 0:
                return False
            _c = _cp.get(_p[24])
            if _c is None:
                return False
            layers.append((_p[2], _p[3], _p[4],
                           _c["askv_dev"], _c["asq_dev"], _p[21]))
        ident = getattr(cls, "_r156_btident2", None)
        ik = (int(bt.shape[1]), bt.dtype, bt.device)
        if ident is None or ident[0] != ik:
            type(impl)._r156_btident2 = (
                ik, _t.arange(bt.shape[1], dtype=bt.dtype,
                              device=bt.device).view(1, -1))
            ident = type(impl)._r156_btident2
        _ident = ident[1]
        S_now = nb_now * block_size
        with _t.npu.stream(update_stream):
            if mid_len <= 0:
                # neutralize path: fall back to the per-layer updater
                return False
            for i, (_k, _v, _bt, _askv, _asq, _impl) in enumerate(layers):
                if cu_on:
                    try:
                        _impl._r155_cu_ring_row(md, params[i][24], 0,
                                                mid_start, rcnt, sl)
                    except Exception as _e_cu:
                        raise RuntimeError(f"[R155-CUEAGER] ring-row CU failed: {_e_cu}")
                _bt.copy_(_ident)
                _k[:nb_now].copy_(kc[bt_gather].permute(0, 2, 1, 3))
                _v[:nb_now].copy_(vc[bt_gather].permute(0, 2, 1, 3))
                if mega is not None:
                    _sc4 = mega[:, bt_gather].view(4, S_now, nkv)
                    ks_c_i = _cp[params[i][24]]
                    _c = ks_c_i
                    _c["ks"][0, :, :mid_len] = _sc4[0, :mid_len].t()
                    _t.neg(_sc4[1, :mid_len].t(), out=_c["ko"][0, :, :mid_len])
                    _c["ko"][0, :, :mid_len].mul_(_c["ks"][0, :, :mid_len])
                    _c["vs"][0, :, :mid_len] = _sc4[2, :mid_len].t()
                    _t.neg(_sc4[3, :mid_len].t(), out=_c["vo"][0, :, :mid_len])
                    _c["vo"][0, :, :mid_len].mul_(_c["vs"][0, :, :mid_len])
                _askv.fill_(mid_len)
                _asq.fill_(1)
                if _os.environ.get("R168_MIDIN", "0") == "1":
                    # R168 P0-A: per-layer carrier input checksums (B8-vs-B1
                    # input-side equality decides kernel-numeric vs staging bug)
                    try:
                        _mn = globals().setdefault('_R168_MIDIN_N', [0])
                        # R218: cap was hard-coded 4000, which the capture warmup
                        # alone exhausts -> the dump never reached a real request.
                        if _mn[0] < int(_os.environ.get("R168_MIDIN_MAX", "4000")):
                            _mn[0] += 1
                            import json as _jm168
                            _c168 = _cp[params[i][24]]
                            with open("/tmp/r168_midin.jsonl", "a") as _fm168:
                                _fm168.write(_jm168.dumps({
                                    "n": _mn[0], "lid": int(params[i][24]),
                                    "ml": int(mid_len),
                                    "rids": [str(x) for x in (getattr(md, "request_ids", None) or [])][:8],
                                    "k": [round(float(x), 4) for x in _k[:nb_now].float().sum(dim=(1, 2))],
                                    "v": [round(float(x), 4) for x in _v[:nb_now].float().sum(dim=(1, 2))],
                                    "ks": round(float(_c168["ks"][0, :, :mid_len].float().sum()), 4),
                                    "ko": round(float(_c168["ko"][0, :, :mid_len].float().sum()), 4),
                                    "vs": round(float(_c168["vs"][0, :, :mid_len].float().sum()), 4),
                                    "vo": round(float(_c168["vo"][0, :, :mid_len].float().sum()), 4),
                                }) + "\n")
                    except Exception:
                        pass
                if not _os.environ.get("R155_T_NOFLUSH", "0") == "1":
                    _impl._r113_flush_stage(update_stream, params[i][23])
                events[i].record(update_stream)
        return True

    @staticmethod
    def _r113_update_oscar_mid(update_stream, key, param, handle, event, forward_context):
        """Replay-time updater for OSCAR_MID_R113 params (runs per layer per step).

        1. Eagerly refill the layer's STATIC middle carriers on the update
           stream: block gather from the LIVE paged caches + live block table
           (indexed torch ops are legal here — eager), tight-pitch scale
           staging over the true span. Carriers' padding tail keeps stale
           bytes; the op only attends [0, askv).
        2. Re-issue the frozen middle launch with the CURRENT askv inside the
           task-group update region, fail-closed on status.
        3. Record the ExternalEvent that unblocks the graph's attention task.
        4. Flush the PREVIOUS replay's staged paged-KV write (see
           _r113_flush_stage).
        """
        (marker, q, k, v, bt, ks, ko, vs, vo, out_h, lse_h, mask,
         nq, scale, nkv, layout, block_size, b, mid_start, rcnt, S_pad,
         impl, num_tokens, layer_idx, _lid) = param
        import os as _os, time as _t156b
        # R159K_PBCARRIER: match the per-(layer,b) carrier key from capture.
        _ukey = (_lid, b) if _os.environ.get("R159K_PBCARRIER", "0") == "1" else _lid
        if not hasattr(type(impl), '_r159k_bdiag_seen'):
            type(impl)._r159k_bdiag_seen = True
            import sys as _sys
            print(f"[R159K_BDIAG-ENV] BDIAG={_os.environ.get('R159K_BDIAG','?')} PBCARRIER={_os.environ.get('R159K_PBCARRIER','?')} B2FIX={_os.environ.get('R159K_B2FIX','?')} first_call_lid={_lid} b={b}", file=_sys.stderr, flush=True)
        _hp4t0 = _t156b.perf_counter() if _os.environ.get("R156_HOSTPROF", "0") == "2" else 0.0
        _mkp = getattr(type(impl), '_r163_markers', None)
        if _mkp is None:
            _mkp = type(impl)._r163_markers = set()
        if "OSCAR_MID_R113" not in _mkp:
            _mkp.add("OSCAR_MID_R113")
            open("/tmp/r163_markers.log","a").write(f"ACTIVE marker=OSCAR_MID_R113 PER-B lid={_lid}\n")
        md = forward_context.attn_metadata[key]
        sl = int(md.seq_lens_list[b])
        # R159K_SLFIX: the graph-capture warmup (cudagraph_num_of_warmups=1, per
        # capture-size [1,2,4,8,16]) increments b=0's seq_len one extra time (the
        # size-1 capture uses b=0). vllm does not reset this → b=0's sl is +1 vs
        # b=1.. for the whole run → the three-tier reads one extra "future" token
        # (the token being generated, K/V not yet in cache) → B>1 correctness
        # divergence (B4 2/4, B8 0/8). BF16 is immune (batched FIA uses one
        # seq_len). Workaround: use the min sl across the batch (all requests
        # share the same decode step → the min is the correct value; the inflated
        # b=0 is the outlier). Default OFF.
        if _os.environ.get("R159K_SLFIX", "0") == "1":
            try:
                _allsl = [int(x) for x in md.seq_lens_list]
                if len(_allsl) > 1:
                    sl = min(_allsl)
            except Exception:
                pass
        mid_len = sl - rcnt - mid_start
        # R159K_BDIAG: first-step per-(layer,b) seq_len + block-table dump to
        # isolate the request-0 off-by-one (B>1 three-tier correctness divergence).
        if _os.environ.get("R159K_BDIAG", "0") == "1":
            _bdg = globals().setdefault('_R159K_BDIAG', {"n": 0})
            _bdg["n"] += 1
            if _bdg["n"] <= 200:
                try:
                    _bt_live = md.block_tables
                    _nb = max(1, (mid_len + block_size - 1) // block_size) if mid_len > 0 else 0
                    _blo = mid_start // block_size
                    _bt_row = _bt_live[b, _blo:_blo + _nb].tolist() if hasattr(_bt_live, 'tolist') else str(_bt_live[b])
                    with open("/tmp/r159k_bdiag.log", "a") as _bf:
                        _bf.write(f"[R159K_BDIAG] lid={_lid} b={b} sl={sl} mid_len={mid_len} nb_now={_nb} blk_lo={_blo} bt={_bt_row[:8]}\n")
                    # R160: dump impl three-tier state per (lid,b) to find b0/b1 vs b2/b3 diff
                    if _bdg["n"] <= 8 and b <= 3:
                        try:
                            _rc = dict(getattr(impl, "_tt_rcnt", {}))
                            _pf = dict(getattr(impl, "_tt_pref", {}))
                            _rs = dict(getattr(impl, "_tt_rcnt_seen", {}))
                            _hp = getattr(impl, "_tt_hp_k", {})
                            _hpb = _hp.get(_lid) if isinstance(_hp, dict) else None
                            _hph = float(_hpb[b, :, 0, 0].abs().sum().item()) if _hpb is not None else None
                            # gathered K/V carrier content (per-b) — does b0/b1 differ from b2/b3?
                            _ksum = float(k[:max(1,_nb), :, :, :].abs().sum().item()) if k is not None and hasattr(k, "abs") else None
                            _vsum = float(v[:max(1,_nb), :, :, :].abs().sum().item()) if v is not None and hasattr(v, "abs") else None
                            with open("/tmp/r159k_bdiag.log", "a") as _bf:
                                _bf.write(f"[R160-IMPL] lid={_lid} b={b} rcnt={_rc} pref={_pf} seen={_rs} hp_abs_sum[b]={_hph} k_abs_sum={_ksum} v_abs_sum={_vsum} k_shape={tuple(k.shape) if k is not None and hasattr(k,'shape') else None}\n")
                        except Exception as _e:
                            with open("/tmp/r159k_bdiag.log", "a") as _bf:
                                _bf.write(f"[R160-IMPL] err lid={_lid} b={b}: {repr(_e)[:120]}\n")
                except Exception as _e:
                    with open("/tmp/r159k_bdiag.log", "a") as _bf:
                        _bf.write(f"[R159K_BDIAG] err lid={_lid} b={b}: {repr(_e)[:120]}\n")
        globals().setdefault('_R156_HP4', {"n": 0, "pro": 0.0, "fil": 0.0, "epi": 0.0})
        # R159K_HPCOPY: the capture-warmup shifts b=0's ring-update HP buffer one
        # step ahead (the warmup ran the ring update once for b=0). For identical
        # prompts, b=1's K/V == b=0's K/V → copy b=1's HP buffer row to b=0's on
        # the first replay to align. HACK (identical-prompt only); validates the
        # off-by-one hypothesis. Default OFF.
        if _os.environ.get("R159K_HPCOPY", "0") == "1" and b in (0, 1):
            try:
                _hpc = globals().setdefault('_R159K_HPCOPY_DONE', set())
                _hpckey = (_lid, b)
                if _hpckey not in _hpc:
                    _hpc.add(_hpckey)
                    _hpk = getattr(impl, '_tt_hp_k', None) or {}
                    _hpv = getattr(impl, '_tt_hp_v', None) or {}
                    if _lid in _hpk and _lid in _hpv and _hpk[_lid].shape[0] > 2:
                        with torch.npu.stream(update_stream):
                            _hpk[_lid][b].copy_(_hpk[_lid][2])
                            _hpv[_lid][b].copy_(_hpv[_lid][2])
                        with open("/tmp/r159k_bdiag.log", "a") as _bf:
                            _bf.write(f"[R159K_HPCOPY] copied b=2->b={b} lid={_lid}\n")
            except Exception as _e:
                try:
                    with open("/tmp/r159k_bdiag.log", "a") as _bf:
                        _bf.write(f"[R159K_HPCOPY] err lid={_lid} b={b}: {repr(_e)[:120]}\n")
                except Exception:
                    pass
        _r156diag_on = _os.environ.get("R156_DIAG", "0") == "1"
        # R156 DIAG: prove the 49ms path executes the middle tier for real
        # (mid_len>0, 36 calls/step, packed INT2 carriers non-zero, V1 launch).
        # File-based, env-gated R156_DIAG=1; NEVER enabled in perf legs.
        if _r156diag_on:
            _dg = globals().setdefault('_R156_DIAG', {"n": 0, "step": -1, "mid0": -1})
            _dg["n"] += 1
            if _dg["n"] % 36 == 1:
                _dg["step"] += 1
            _dump = (_dg["step"] % 50 == 0 and _dg["n"] % 36 == 1)
            if _dump:
                _bt_live = md.block_tables
                _nb = max(1, (mid_len + block_size - 1) // block_size) if mid_len > 0 else 0
                try:
                    import hashlib as _hl156
                    _kc_d = impl.key_cache
                    _pg = (_bt_live[b, mid_start // block_size: mid_start // block_size + _nb]
                           if _nb else _bt_live[b, :1])
                    _src_nonzero = int(torch.count_nonzero(_kc_d[_pg]).item())
                    _car_nonzero = -1
                    _cp_d = getattr(type(impl), '_r113_cpool', {}).get(_ukey)
                    if _cp_d is not None and _nb:
                        _car_nonzero = int(torch.count_nonzero(_cp_d["k"][:_nb]).item())
                    with open(_os.environ.get("R156_DIAG_OUT", "/tmp/r156_diag.jsonl"), "a") as _f156:
                        _f156.write('{"step": %d, "lid": %d, "sl": %d, "mid_len": %d, '
                                    '"calls_so_far": %d, "src_nz": %d, "car_nz": %d, '
                                    '"srl": %d, "cu_fire": %d}\n' % (
                                        _dg["step"], _lid, sl, mid_len, _dg["n"],
                                        _src_nonzero, _car_nonzero,
                                        getattr(type(impl), '_r156_diag_srl', [0])[0],
                                        getattr(type(impl), '_r156_diag_cu', [0])[0]))
                except Exception as _e156:
                    with open(_os.environ.get("R156_DIAG_OUT", "/tmp/r156_diag.jsonl"), "a") as _f156:
                        _f156.write('{"diag_err": "%s"}\n' % repr(_e156)[:200])
        _v1 = _os.environ.get("R133_GRAPH_V1", "0") == "1"
        # R137 P0.3: short-prompt case (plen1, sl<=pref+rcnt -> mid_len<=0).
        # There is no INT2 middle to attend. The captured middle launch cannot
        # be un-baked from the graph, so NEUTRALIZE it: set askv_dev=0 (kernel
        # attends 0 middle tokens -> o_h=0, l_h=-inf) and SKIP carrier staging
        # (no blocks to gather — "do not call the empty middle INT2 op" for the
        # re-issue path). The merge in full_graph_int2_threetier_middle then
        # sees w_h=exp(-inf)=0 -> middle contributes nothing -> output ==
        # the BF16 prefix/recent path (math-equal to eager, which skips middle
        # via the mid_len<=0 guard in _r109_middle_candidate). The S+R tier
        # already covers the full sequence when mid_len<=0.
        if mid_len <= 0:
            _cp_e = getattr(type(impl), '_r113_cpool', None)
            if _cp_e is not None and _ukey in _cp_e:
                _c_e = _cp_e[_ukey]
                with torch.npu.stream(update_stream):
                    if _v1:
                        _c_e["askv_dev"].fill_(0)
                        _c_e["asq_dev"].fill_(1)
            event.record(update_stream)
            impl._r113_flush_stage(update_stream, layer_idx)
            return
        if mid_len > S_pad:
            raise RuntimeError(
                f"[R113-GA] replay span invalid: sl={sl} mid_len={mid_len} "
                f"(pref={mid_start} rcnt={rcnt} S_pad={S_pad}) — fail-closed")
        mod = getattr(type(impl), '_r112_mod', None)
        _cp = getattr(type(impl), '_r113_cpool', None)
        if mod is None or _cp is None or _ukey not in _cp:
            raise RuntimeError("[R113-GA] carriers/module missing at replay update (fail-closed)")
        _c = _cp[_ukey]
        askv = [mid_len]
        nb_now = (mid_len + block_size - 1) // block_size
        blk_lo = mid_start // block_size
        _t_nostage = _os.environ.get("R155_T_NOSTAGE", "0") == "1"
        # R156-H3: if the batched fused staging already ran for this step
        # (stamp = (num_tokens, sl)), skip the per-layer staging AND the
        # askv/asq fills (the kernel wrote carriers + bt identity + fills).
        _h3_skip = False
        if getattr(type(impl), "_r156_h3_on", False):
            _st = getattr(type(impl), "_r156_h3_stamp", None)
            if _st is not None and _st.get("k") == (num_tokens, sl, b):
                _h3_skip = True
        # R157 GSTAGE updater (R157_GSTAGE=1, default OFF): minimal per-layer
        # work — K/V staging is captured IN the graph; only the bt-mirror
        # refresh (1/step), the CUEAGER ring-row check, the every-64-step
        # scale refresh (H5 semantics, E-class vs C3) and the askv/asq fills
        # remain on the update_stream.
        if (_os.environ.get("R157_GSTAGE", "0") == "1"
                and _v1 and mid_len > 0 and b == 0
                and os.environ.get("R155_T_NOSTAGE", "0") != "1"
                and not _h3_skip):
            _evd_g = getattr(AscendINT2AttentionBackendImpl, "_r156_h1f", None)
            if _evd_g is None:
                _evd_g = AscendINT2AttentionBackendImpl._r156_h1f = {}
            _fk_g = (id(impl), str(k.device))
            _fp_g = _evd_g.get(_fk_g)
            if _fp_g is None:
                _fp_g = _evd_g[_fk_g] = {"n": 0}
            _fp_g["n"] += 1
            if _fp_g["n"] > 3:
                with torch.npu.stream(update_stream):
                    _ms_g = globals().setdefault('_R157_GS_STAMP', {})
                    if _ms_g.get('sl') != int(sl):
                        _ms_g['sl'] = int(sl)
                        _gs_pool = getattr(type(impl), '_r157_gstage_idx', None)
                        if _gs_pool:
                            _idx_g = _gs_pool.get((str(k.device), int(_c["nb_max"])))
                            if _idx_g is not None:
                                _blk_lo_g = mid_start // block_size
                                _idx_g.copy_(md.block_tables[
                                    0, _blk_lo_g:_blk_lo_g + _idx_g.shape[0]])
                    if os.environ.get("R155_CUEAGER", "0") == "1":
                        t0_g = int(sl) - int(rcnt)
                        if t0_g >= 0 and (t0_g % 64) == 0:
                            impl._r155_cu_ring_row(md, _lid, 0, mid_start, rcnt, sl)
                    if (_fp_g["n"] % 64) == 4:
                        mega_g = getattr(impl, "_r156_scale_mega", None)
                        if mega_g is not None:
                            nb_now_g = (mid_len + block_size - 1) // block_size
                            blk_lo_g = mid_start // block_size
                            bt_gather_g = md.block_tables[
                                0, blk_lo_g:blk_lo_g + nb_now_g]
                            S_now_g = nb_now_g * block_size
                            _sc4_g = mega_g[:, bt_gather_g].view(4, S_now_g, nkv)
                            _c["ks"][0, :, :mid_len] = _sc4_g[0, :mid_len].t()
                            torch.neg(_sc4_g[1, :mid_len].t(),
                                      out=_c["ko"][0, :, :mid_len])
                            _c["ko"][0, :, :mid_len].mul_(_c["ks"][0, :, :mid_len])
                            _c["vs"][0, :, :mid_len] = _sc4_g[2, :mid_len].t()
                            torch.neg(_sc4_g[3, :mid_len].t(),
                                      out=_c["vo"][0, :, :mid_len])
                            _c["vo"][0, :, :mid_len].mul_(_c["vs"][0, :, :mid_len])
                    _c["askv_dev"].fill_(mid_len)
                    _c["asq_dev"].fill_(1)
                event.record(update_stream)
                return
        # R156-H1F FAST PATH (default OFF; R156_H1F=1): the minimal per-layer
        # staging for the canonical steady state (B=1, V1, mid_len>0, H1
        # family). Keeps per-layer pacing (H2 batching REJECTED: burst fills
        # the launch queue) while skipping ~40 lines of checks/lookups.
        if (_os.environ.get("R156_H1F", "0") == "1"
                and _v1 and mid_len > 0 and b == 0
                and os.environ.get("R155_T_NOSTAGE", "0") != "1"
                and getattr(impl, "_r156_scale_mega", None) is not None
                and not _h3_skip):
            _evd_f = getattr(AscendINT2AttentionBackendImpl, "_r156_h1f", None)
            if _evd_f is None:
                _evd_f = AscendINT2AttentionBackendImpl._r156_h1f = {}
            _fk = (id(impl), str(k.device))
            _fp = _evd_f.get(_fk)
            if _fp is None:
                _fp = _evd_f[_fk] = {"n": 0}
            _fp["n"] += 1
            if _fp["n"] > 3:  # steady state only (skip warmup steps)
                _btid_f = getattr(type(impl), "_r156_btident_f", None)
                _ik_f = (int(bt.shape[1]), bt.dtype, bt.device)
                if _btid_f is None or _btid_f[0] != _ik_f:
                    type(impl)._r156_btident_f = (
                        _ik_f, torch.arange(bt.shape[1], dtype=bt.dtype,
                                            device=bt.device).view(1, -1))
                    _btid_f = type(impl)._r156_btident_f
                nb_now_f = (mid_len + block_size - 1) // block_size
                blk_lo_f = mid_start // block_size
                bt_live_f = md.block_tables
                bt_gather_f = bt_live_f[0, blk_lo_f:blk_lo_f + nb_now_f]
                mega_f = impl._r156_scale_mega
                S_now_f = nb_now_f * block_size
                kc_f = impl.key_cache
                vc_f = impl.value_cache
                _h5 = os.environ.get("R156_H5", "0") == "1"
                _nosc = (_h5 and (_fp["n"] % 64) != 4)  # refresh on n%64==4
                _nobt = _h5 and os.environ.get("R156_NOBT", "0") == "1"
                with torch.npu.stream(update_stream):
                    _kv_gather_k = kc_f[bt_gather_f].permute(0, 2, 1, 3)
                    _kv_gather_v = vc_f[bt_gather_f].permute(0, 2, 1, 3)
                    if _nosc:
                        _sc4_f = mega_f[:, bt_gather_f].view(4, S_now_f, nkv)
                    if os.environ.get("R155_CUEAGER", "0") == "1":
                        t0_f = int(sl) - int(rcnt)
                        if t0_f >= 0 and (t0_f % 64) == 0:
                            impl._r155_cu_ring_row(md, _lid, 0, mid_start, rcnt, sl)
                    if not _nobt:
                        bt.copy_(_btid_f[1])
                    k[:nb_now_f].copy_(_kv_gather_k)
                    v[:nb_now_f].copy_(_kv_gather_v)
                    if _nosc:
                        _c["ks"][0, :, :mid_len] = _sc4_f[0, :mid_len].t()
                        torch.neg(_sc4_f[1, :mid_len].t(),
                                  out=_c["ko"][0, :, :mid_len])
                        _c["ko"][0, :, :mid_len].mul_(_c["ks"][0, :, :mid_len])
                        _c["vs"][0, :, :mid_len] = _sc4_f[2, :mid_len].t()
                        torch.neg(_sc4_f[3, :mid_len].t(),
                                  out=_c["vo"][0, :, :mid_len])
                        _c["vo"][0, :, :mid_len].mul_(_c["vs"][0, :, :mid_len])
                    _c["askv_dev"].fill_(mid_len)
                    _c["asq_dev"].fill_(1)
                event.record(update_stream)
                return
        # R156 HOSTPROF=2: per-subblock host-time split of the staging loop
        import time as _t156b
        _hp2 = _os.environ.get("R156_HOSTPROF", "0") == "2"
        _acc = globals().setdefault('_R156_HP2', {"n": 0, "cu": 0.0, "bt": 0.0,
                                                  "kv": 0.0, "sc": 0.0, "fl": 0.0,
                                                  "ev": 0.0, "oth": 0.0, "t0": 0.0})
        _acc["t0"] = _t156b.perf_counter()
        with torch.npu.stream(update_stream):
          if _os.environ.get("R155_CUEAGER", "0") == "1":
            # R155 A2-lite: EAGER cache-update of the ring-prefix row (the
            # next-to-evict token) on the update_stream, ordered BEFORE the
            # staging gathers below. Same CU kernel, same input bytes (the
            # ring stores key_rot/value_rot verbatim) => E-class; the row
            # lands in the paged cache >=1 step before the middle reads it.
            _tA = _t156b.perf_counter()
            try:
                impl._r155_cu_ring_row(md, _lid, b, mid_start, rcnt, sl)
            except Exception as _e_cu:
                raise RuntimeError(f"[R155-CUEAGER] ring-row CU failed: {_e_cu}")
            _acc["cu"] += _t156b.perf_counter() - _tA
            # R161 F4: record E_cu after the ring-row CacheUpdate (update_stream).
            _r161_f.on_cu_done(update_stream)
          if not _t_nostage and not _h3_skip:
            # R161 F4: wait E_cu so the CU paged write is visible before gather.
            _r161_f.on_middle_enter(update_stream)
            _tA = _t156b.perf_counter()
            # R119 fix#5 (THE KEY — idx-8 root): the capture-time launch mutates
            # the shared bt pool tensor in place, leaving it non-identity; the
            # launch contract (R110 D6a) requires the IDENTITY arange — rewrite
            # bt to identity every replay so the captured launch addresses the
            # compacted carriers [0..n). Without this, graph re-reads a polluted
            # bt -> eager-vs-graph argmax flip at low-margin tokens (idx-8).
            # R156-H1: the identity arange is CONSTANT per bt width — cache it
            # type-level (kills one arange kernel per layer per step; the copy
            # bytes are identical => E-class).
            _h1 = _os.environ.get("R156_H1", "0") == "1"
            if _h1:
                _btid = getattr(type(impl), '_r156_btident', None)
                if _btid is None:
                    _btid = type(impl)._r156_btident = {}
                _ik = (int(bt.shape[1]), bt.dtype, bt.device)
                _ident = _btid.get(_ik)
                if _ident is None:
                    _ident = _btid[_ik] = torch.arange(
                        bt.shape[1], dtype=bt.dtype, device=bt.device).view(1, -1)
                bt.copy_(_ident)
            else:
                bt.copy_(torch.arange(bt.shape[1], dtype=bt.dtype,
                                      device=bt.device).view(1, -1))
            bt_live = md.block_tables
            bt_gather = bt_live[b, blk_lo:blk_lo + nb_now]
            _acc["bt"] += _t156b.perf_counter() - _tA
            _tA = _t156b.perf_counter()
            kc = impl.key_cache
            vc = impl.value_cache
            # gather + layout to the op carrier ([nb, nkv, bs, packed] int8)
            if _h1:
                _c["k"][:nb_now].copy_(kc[bt_gather].permute(0, 2, 1, 3))
                _c["v"][:nb_now].copy_(vc[bt_gather].permute(0, 2, 1, 3))
            else:
                _c["k"][:nb_now] = kc[bt_gather].permute(0, 2, 1, 3).contiguous().view(torch.int8)
                _c["v"][:nb_now] = vc[bt_gather].permute(0, 2, 1, 3).contiguous().view(torch.int8)
            # R170_MIDDUMP (default OFF): per-solo FIRST decode steps, dump the
            # gathered mid-tier PAGE content (kc/vc rows via bt_gather) for
            # cross-solo comparison. Identical prompts => identical ksum/vsum/
            # kfp across solos; a differing solo localizes the first stale
            # tensor to the paged-cache PAGES (write-side race) vs the shared
            # carriers (read/refresh side). Async-safe per R159K_BDIAG: syncs
            # only update_stream before .item().
            try:
                import os as _os170md
                if _os170md.environ.get("R170_MIDDUMP", "0") == "1" and b == 0:
                    _lids170 = [int(x) for x in _os170md.environ.get(
                        "R170_MIDDUMP_LIDS", "0,1,2").split(",") if x.strip()]
                    if _lid in _lids170 and int(getattr(md, "num_prefills", 1) or 1) == 0:
                        _rid170 = str((getattr(md, "request_ids", None) or ["?"])[0])
                        _seen170 = globals().setdefault('_R170_MID_SEEN', {})
                        _cnt170 = _seen170.get(_rid170, 0)
                        if _cnt170 < 2:
                            _seen170[_rid170] = _cnt170 + 1
                            import torch as _t170md
                            _t170md.npu.current_stream().synchronize()
                            _ksum170 = float(_c["k"][:nb_now].abs().sum().item())
                            _vsum170 = float(_c["v"][:nb_now].abs().sum().item())
                            _kfp170 = _c["k"][:nb_now].view(-1)[:16].to(torch.int32).tolist()
                            _btg170 = bt_gather.tolist() if hasattr(bt_gather, "tolist") else str(bt_gather)
                            _btrow170 = md.block_tables[b].tolist() if hasattr(md.block_tables, "tolist") else None
                            with open("/tmp/r170_middump.jsonl", "a") as _fm170:
                                _fm170.write(
                                    '{"rid": "%s", "lid": %d, "b": %d, "dec": %d, "sl": %s, '
                                    '"mid_start": %s, "mid_len": %s, "nb_now": %s, "blk_lo": %s, '
                                    '"ksum": %.1f, "vsum": %.1f, "kfp": %s, "btg": %s, "btrow0": %s}\n'
                                    % (_rid170, int(_lid), int(b), _cnt170, sl, mid_start,
                                       mid_len, nb_now, blk_lo, _ksum170, _vsum170,
                                       _kfp170, _btg170, str(_btrow170[:8]) if _btrow170 else None))
            except Exception:
                pass
            # R161 ALLYSYNC: serialize the per-(layer,b) carrier fill on update_stream
            # for ALL layers (vs BDIAG which only syncs layer0 b0-3). Diagnostic: if this
            # fixes b1/b2/b3, the race is the within-step fill-vs-read on the shared
            # per-layer carrier. Default OFF (intrusive; not the final fix).
            if _os.environ.get("R161_ALLYSYNC", "0") == "1":
                torch.npu.current_stream().synchronize()
            # R160: dump gathered K/V carrier content + bt_gather per b (after fill) to
            # test if b0/b1's paged-cache content differs from b2/b3 (identical prompts → should match).
            if _os.environ.get("R159K_BDIAG", "0") == "1":
                _bdg2 = globals().setdefault('_R160_KVDUMP', {"n": 0})
                _bdg2["n"] += 1
                # R160 P0 FIRST_DIVERGENCE dump (async-safe): the updater runs
                # inside `with torch.npu.stream(update_stream)`, so .item() on
                # tensors created/overwritten here syncs ONLY the update_stream
                # (not a global torch.npu.synchronize() — that deadlocks replay).
                # Gated to first 8 (layer,b) entries of lid==0 only.
                if _bdg2["n"] <= 8 and b <= 3 and _lid == 0:
                    try:
                        import torch as _tnv
                        _ust = _tnv.npu.current_stream()  # == update_stream here
                        if _os.environ.get("R161_NOUSYNC", "0") != "1":
                            _ust.synchronize()
                        _ksum = float(_c["k"][:nb_now].abs().sum().item())
                        _vsum = float(_c["v"][:nb_now].abs().sum().item())
                        _kfp = _c["k"][:nb_now].view(-1)[:16].to(torch.int32).tolist()
                        _btg = bt_gather.tolist() if hasattr(bt_gather, "tolist") else str(bt_gather)
                        # q_rot (param[1]) per-b fingerprint — catches position/RoPE divergence
                        _qfp = q.view(-1)[:8].to(torch.float32).tolist() if q is not None and hasattr(q, "view") else None
                        _qsum = float(q.abs().sum().item()) if q is not None and hasattr(q, "abs") else None
                        # HP recent-window slice (the S+R tier source) per-b
                        _hp = getattr(impl, '_tt_hp_k', {}) or {}
                        _hpb = _hp.get(_lid) if isinstance(_hp, dict) else None
                        _hprec = None; _hpfp = None
                        if _hpb is not None:
                            _slc = _hpb[b, mid_start:mid_start + rcnt]
                            _hprec = float(_slc.abs().sum().item())
                            _hpfp = _slc.view(-1)[:8].to(torch.float32).tolist()
                        # CPU metadata (async-safe, already host)
                        _btrow = md.block_tables[b].tolist() if hasattr(md.block_tables, "tolist") else None
                        _smap = None
                        try:
                            _smap = md.slot_mapping.tolist() if md.slot_mapping is not None else None
                        except Exception:
                            pass
                        # carrier SOURCE verification (is the middle block written?)
                        _kc = impl.key_cache
                        _kcg = _kc[bt_gather]
                        _kcabs = float(_kcg.float().abs().sum().item())
                        _kcdt = str(_kc.dtype)
                        # read PREVIOUS step's graph-level merged/o_pr/o_h sums
                        _gd = globals().get('_r160_gdump', {})
                        _gdm = _gd.get(_lid)
                        _gdm_v = _gdm[:10].to(torch.float32).cpu().tolist() if _gdm is not None else None
                        with open("/tmp/r159k_bdiag.log", "a") as _bf:
                            _bf.write(f"[R160-KV] lid={_lid} b={b} sl={sl} mid_len={mid_len} nb_now={nb_now} blk_lo={blk_lo} bt_gather={_btg} bt_row={_btrow[:8] if _btrow else None} slot_map={_smap[:8] if _smap else None}\n")
                            _bf.write(f"[R160-KV]   q_abs_sum={_qsum} q_fp={_qfp} k_abs_sum={_ksum} v_abs_sum={_vsum} k_fp={_kfp} hp_rec_abs_sum={_hprec} hp_rec_fp={_hpfp}\n")
                            _bf.write(f"[R160-KV]   kc_src_abs_sum={_kcabs} kc_dtype={_kcdt} kc_shape={tuple(_kc.shape)} kcg_shape={tuple(_kcg.shape)} PREV_gdump[lid={_lid}]={_gdm_v}\n")
                    except Exception as _e:
                        with open("/tmp/r159k_bdiag.log", "a") as _bf:
                            _bf.write(f"[R160-KV] err lid={_lid} b={b}: {repr(_e)[:160]}\n")
                # R160 P0 graph-dump READBACK (async-safe): the compiled merge fn
                # wrote per-b per-field stats to _r160_dbg_buf during the PREVIOUS
                # replay (default stream). Sync ONLY the readback (default) stream,
                # copy the layer-0 slice to host, log. NO global torch.npu.synchronize.
                # Fires at (lid==0, b==0) — the first updater call of each step — so
                # step N's read sees step N-1's replay dump. _R160_GREAD counter
                # bounds it to the first few steps.
                if _lid == 0 and b == 0:
                    _rd = globals().setdefault('_R160_GREAD', {"n": 0})
                    _rd["n"] += 1
                    if 2 <= _rd["n"] <= 5:  # steps 1..4's replay data
                        try:
                            import torch as _tnr
                            _rds = _tnr.npu.default_stream()
                            if _os.environ.get("R161_NODREAD", "0") != "1":
                                _rds.synchronize()
                            _buf = globals().get('_r160_dbg_buf', None)
                            if _buf is not None:
                                _sl = _buf[0, :4, :6, :21].to(torch.float32).cpu().tolist()
                                _flds = ["q_rot", "o_pr", "l_pr", "o_h", "l_h", "merged"]
                                with open("/tmp/r159k_bdiag.log", "a") as _bf:
                                    _bf.write(f"[R160-GDREAD] step_prev={_rd['n']-1} lid=0\n")
                                    for _bi in range(4):
                                        for _fi in range(6):
                                            _s = _sl[_bi][_fi]
                                            _bf.write(f"[R160-GDREAD] b={_bi} {_flds[_fi]} sum={_s[0]:.4f} abs={_s[1]:.4f} sumsq={_s[2]:.4f} min={_s[3]:.4f} max={_s[4]:.4f} fp={[_s[5+i] for i in range(8)]}\n")
                        except Exception as _e:
                            with open("/tmp/r159k_bdiag.log", "a") as _bf:
                                _bf.write(f"[R160-GDREAD] err: {repr(_e)[:160]}\n")
            _acc["kv"] += _t156b.perf_counter() - _tA
            # scale/offset staging over the true span (tight pitch, R110 D6b)
            _tA = _t156b.perf_counter()
            S_now = nb_now * block_size
            if not (getattr(impl, "_r156_scale_mega", None) is not None and _h1):
                ksb = impl.k_scale_cache[bt_gather].reshape(S_now, nkv)
                kzb = impl.k_zero_cache[bt_gather].reshape(S_now, nkv)
                vsb = impl.v_scale_cache[bt_gather].reshape(S_now, nkv)
                vzb = impl.v_zero_cache[bt_gather].reshape(S_now, nkv)
            _mega = getattr(impl, "_r156_scale_mega", None)
            if _mega is not None and _h1:
                # R156-H1c: single gather over the mega cache [4, nb, bs, nkv]
                # replaces 4 index launches; same bytes => E-class.
                _sc4 = _mega[:, bt_gather]                     # 1 launch
                _sc4f = _sc4.view(4, nb_now * block_size, nkv)
                _c["ks"][0, :, :mid_len] = _sc4f[0, :mid_len].t()
                torch.neg(_sc4f[1, :mid_len].t(), out=_c["ko"][0, :, :mid_len])
                _c["ko"][0, :, :mid_len].mul_(_c["ks"][0, :, :mid_len])
                _c["vs"][0, :, :mid_len] = _sc4f[2, :mid_len].t()
                torch.neg(_sc4f[3, :mid_len].t(), out=_c["vo"][0, :, :mid_len])
                _c["vo"][0, :, :mid_len].mul_(_c["vs"][0, :, :mid_len])
            elif _h1:
                # R156-H1: fold neg into an alpha=-1 mul.out writing the
                # carrier slice directly. (-x)*y and alpha-form -(x*y) differ
                # only by an exact sign flip => bit-identical bf16 (E-class).
                _c["ks"][0, :, :mid_len] = ksb[:mid_len].t()
                torch.neg(kzb[:mid_len].t(), out=_c["ko"][0, :, :mid_len])
                _c["ko"][0, :, :mid_len].mul_(_c["ks"][0, :, :mid_len])
                _c["vs"][0, :, :mid_len] = vsb[:mid_len].t()
                torch.neg(vzb[:mid_len].t(), out=_c["vo"][0, :, :mid_len])
                _c["vo"][0, :, :mid_len].mul_(_c["vs"][0, :, :mid_len])
            else:
                _c["ks"][0, :, :mid_len] = ksb[:mid_len].t().bfloat16()
                _c["ko"][0, :, :mid_len] = (-kzb[:mid_len].t() * _c["ks"][0, :, :mid_len]).bfloat16()
                _c["vs"][0, :, :mid_len] = vsb[:mid_len].t().bfloat16()
                _c["vo"][0, :, :mid_len] = (-vzb[:mid_len].t() * _c["vs"][0, :, :mid_len]).bfloat16()
            _acc["sc"] += _t156b.perf_counter() - _tA
          if _v1 and not _h3_skip:
            # R135 V1: fill the STABLE-ADDRESS device carriers in-place. The
            # captured graph launch re-executes on replay reading them LIVE
            # (R134 P0/P1/P2 proven N=36, 3 fresh procs: g.replay() reads
            # askv_dev live, NO task_update, NO re-issue, NO re-capture).
            # asq_dev = actualSeqQ = 1 (decode, constant).
            # R156-H1b: with the shared per-b scalar pair, fill ONCE per step
            # (first layer writes; stamp = (b, sl) — sl increments per step).
            _h1b = bool(globals().get('_R156_H1B_ACTIVE'))
            if _h1b:
                _st1 = globals().setdefault('_R156_H1B_STAMP', {})
                _sk1 = (int(b), int(sl))
                if _st1.get('v') != _sk1:
                    _st1['v'] = _sk1
                    _c["askv_dev"].fill_(int(mid_len))
                    _c["asq_dev"].fill_(1)
            else:
                _tf0 = _t156b.perf_counter()
                _c["askv_dev"].fill_(int(mid_len))
                _c["asq_dev"].fill_(1)
                globals()['_R156_HP4']["fil"] += _t156b.perf_counter() - _tf0
          if not _t_nostage:
            _r136_p0_dump("graph", layer_idx,
                        globals().setdefault('_R117_MID_N', [0])[0],
                        {"mid_start": int(mid_start), "mid_len": int(mid_len),
                         "nb_now": int(nb_now), "block_size": int(block_size),
                         "S_pad": int(S_pad), "askv": int(mid_len)},
                        {"q": q, "k": _c["k"][:nb_now], "v": _c["v"][:nb_now],
                         "bt": bt, "ks": _c["ks"][0, :, :mid_len],
                         "ko": _c["ko"][0, :, :mid_len],
                         "vs": _c["vs"][0, :, :mid_len],
                         "vo": _c["vo"][0, :, :mid_len]})
            globals()['_R117_MID_N'][0] += 1
        if not _v1:
            # R185 OPERAND SNAPSHOT (env R185_OPDUMP): capture the EXACT device tensors entering
            # launch_lse_fast at the LSE input-consumption point, for standalone MSD_ON replay.
            # Sync the compute stream first (carrier fills via graph_task_update; full sync guarantees
            # no cross-stream stale read). Read-only; single-shot (first middle-tier call = crash call).
            import os as _os185
            if _os185.environ.get("R185_OPDUMP") == "1" and not getattr(type(self), "_r185_dumped", False):
                type(self)._r185_dumped = True
                torch.npu.synchronize()
                _od185 = _os185.environ.get("R185_OPDUMP_DIR", "/tmp/r185")
                _os185.makedirs(_od185, exist_ok=True)
                _snap = {
                    "q": q.detach().cpu().clone(), "k": k.detach().cpu().clone(),
                    "v": v.detach().cpu().clone(), "bt": bt.detach().cpu().clone(),
                    "ks": ks.detach().cpu().clone(), "ko": ko.detach().cpu().clone(),
                    "vs": vs.detach().cpu().clone(), "vo": vo.detach().cpu().clone(),
                    "out_h": out_h.detach().cpu().clone(), "lse_h": lse_h.detach().cpu().clone(),
                    "askv": list(int(x) for x in askv), "nq": int(nq), "scale": float(scale),
                    "nkv": int(nkv), "layout": layout, "block_size": int(block_size),
                    "layer_idx": int(layer_idx), "b": int(b), "sl": int(sl),
                    "mid_len": int(mid_len), "nb_now": int(nb_now),
                    "q_shape": list(q.shape), "q_stride": list(q.stride()),
                    "k_shape": list(k.shape), "k_stride": list(k.stride()),
                    "bt_shape": list(bt.shape), "bt_stride": list(bt.stride()),
                    "ks_shape": list(ks.shape), "ks_stride": list(ks.stride()),
                }
                _p185 = f"{_od185}/r185_opdump_l{layer_idx}_b{b}_sl{sl}.pt"
                torch.save(_snap, _p185)
                print(f"[R185-OPDUMP] l={layer_idx} b={b} sl={sl} mid_len={mid_len} nb_now={nb_now} "
                      f"askv={list(int(x) for x in askv)} bt_min={int(bt.min())} bt_max={int(bt.max())} "
                      f"ks_absmax={float(ks.abs().max())} ko_absmax={float(ko.abs().max())} "
                      f"-> {_p185}", flush=True)
            torch.npu.graph_task_update_begin(update_stream, handle)
            fr = mod.launch_lse_fast(
                q, k, v, bt, ks, ko, vs, vo, out_h, lse_h,
                nq, scale, nkv, layout, block_size,
                1, 1, askv, mask, 0, 0, 0, True)
            torch.npu.graph_task_update_end(update_stream)
            if not (int(fr[0]) == 0 and int(fr[2]) == 0):
                raise RuntimeError(f"[R113-GA] replay update launch NOT ok: {tuple(int(x) for x in fr)}")
        # V1: no launch here — the captured launch_lse_v1_own re-executes on
        # graph replay; the event below makes the graph stream wait for the
        # update_stream carrier + askv fills.
        _tA = _t156b.perf_counter()
        globals()['_R156_HP4']["epi"] += _tA - _hp4t0 - (
            _acc["cu"] + _acc["bt"] + _acc["kv"] + _acc["sc"]
            + _acc["fl"] + _acc["ev"]) / 36.0
        event.record(update_stream)
        _acc["ev"] += _t156b.perf_counter() - _tA
        _tA = _t156b.perf_counter()
        if _os.environ.get("R155_T_NOFLUSH", "0") != "1":
            impl._r113_flush_stage(update_stream, layer_idx)
        _acc["fl"] += _t156b.perf_counter() - _tA
        _hp4 = globals()['_R156_HP4']
        _hp4["n"] += 1
        if _hp4["n"] % 36 == 0 and (_hp4["n"] // 36) % 20 == 0:
            import json as _js4
            with open("/tmp/r156_hp4.jsonl", "a") as _f4:
                _f4.write(_js4.dumps({k: round(v * 1e3, 3) for k, v in _hp4.items()
                                      if k != "n"} | {"n": _hp4["n"]}) + "\n")
            for _k4 in ("pro", "fil", "epi"):
                _hp4[_k4] = 0.0
        if _hp2:
            _acc["oth"] += (_t156b.perf_counter() - _acc["t0"]) - (
                _acc["cu"] + _acc["bt"] + _acc["kv"] + _acc["sc"]
                + _acc["fl"] + _acc["ev"])
            _acc["n"] += 1
            if _acc["n"] % 36 == 0 and (_acc["n"] // 36) % 20 == 0:
                try:
                    import json as _js156
                    with open(_os.environ.get("R156_HOSTPROF_OUT",
                                             "/tmp/r156_hp2.jsonl"), "a") as _f156b:
                        _f156b.write(_js156.dumps({k: (round(v, 3) if isinstance(v, float)
                                                       else v) for k, v in _acc.items()}
                                                  ) + "\n")
                    for _k2 in ("cu", "bt", "kv", "sc", "fl", "ev", "oth"):
                        _acc[_k2] = 0.0
                except Exception:
                    pass
        # R117 P0-B diag (env-gated, default OFF): per-replay per-layer hashes of
        # the middle SOURCE blocks (live paged cache), the REFILLED carriers, and
        # the HP ring — the first-wrong-tensor ladder for the step-8 divergence.
        if os.environ.get("R117_MID_DIAG", "0") == "1":
            try:
                import hashlib as _hl, json as _js
                torch.npu.synchronize()
                def _h(t):
                    return _hl.sha256(t.contiguous().view(torch.uint8).cpu().numpy().tobytes()).hexdigest()[:12]
                _hk, _hv = impl._tt_hp_bufs(_lid, _c["k"].device, torch.bfloat16)
                _rec = {"mode": "graph", "layer": int(layer_idx),
                        "cnt": globals().setdefault('_R117_MID_N', [0])[0],
                        "sl": int(sl), "mid": [int(mid_start), int(sl - rcnt)],
                        "askv": int(mid_len), "nb_now": int(nb_now),
                        "bt": bt_gather.cpu().tolist(),
                        "src_k": _h(kc[bt_gather]), "src_v": _h(vc[bt_gather]),
                        "q": _h(q),
                        "slotmap": _h(md.slot_mapping.view(torch.uint8)) if md.slot_mapping is not None else "none",
                        "oh": _h(out_h), "lh": _h(lse_h),
                        "curblk_k": _h(kc[bt_live[b, (sl - 1) // block_size]:(bt_live[b, (sl - 1) // block_size]) + 1]),
                        "curblk_v": _h(vc[bt_live[b, (sl - 1) // block_size]:(bt_live[b, (sl - 1) // block_size]) + 1]),
                        "src_ks": _h(impl.k_scale_cache[bt_gather]),
                        "car_k": _h(_c["k"][:nb_now]), "car_v": _h(_c["v"][:nb_now]),
                        "car_ks": _h(_c["ks"][0, :, :mid_len]), "car_ko": _h(_c["ko"][0, :, :mid_len]),
                        "car_vs": _h(_c["vs"][0, :, :mid_len]), "car_vo": _h(_c["vo"][0, :, :mid_len]),
                        "ring_k": _h(_hk[b]), "ring_v": _h(_hv[b]),
                        "rk_pre": _h(_hk[b, :128]), "rk_r0": _h(_hk[b, 128:320]),
                        "rk_r1": _h(_hk[b, 320:512]), "rk_r2": _h(_hk[b, 512:624]),
                        "rk_tail": _h(_hk[b, 624:640]), "rv_tail": _h(_hv[b, 624:640]),
                        "rk_slots": "|".join(_h(_hk[b, s:s+1]) for s in range(624, 640)),
                        "rv_slots": "|".join(_h(_hv[b, s:s+1]) for s in range(624, 640))}
                globals()['_R117_MID_N'][0] += 1
                _p = os.environ.get("R117_MID_DIAG_OUT", "/tmp/r117_mid_diag.jsonl")
                if os.environ.get("R118_RAW", "0") == "1" and _rec["cnt"] <= 12:
                    _rec["raw_tail_k"] = _hk[b, 639].float().tolist()
                    _rec["raw_tail_v"] = _hv[b, 639].float().tolist()
                    _rec["raw_q0"] = q[0, 0, :8].float().tolist() if q.dim() == 3 else q[0, :8].float().tolist()
                with open(_p, "a") as _f:
                    _f.write(_js.dumps(_rec) + "\n")
            except Exception as _e:
                print(f"[R117-MID-DIAG] graph diag failed: {_e}", flush=True)
        # R118 graph-mode ladder dump (default OFF): hash the trace carriers
        # AFTER this replay so graph rows align with the R117_MID_DIAG ladder
        # (cnt N == updater call N == replay N; carriers hold what the replay
        # actually consumed).
        if os.environ.get("R118_TRACE", "0") == "1":
            try:
                import r118_trace as _rt118g
            except ImportError:
                _rt118g = None
            if _rt118g is not None:
                _gn = globals().setdefault('_R118_G_N', [0])
                _rt118g.dump_row("graph", _gn[0],
                                 {"L": int(layer_idx), "sl": int(sl),
                                  "mid": [int(mid_start), int(sl - rcnt)],
                                  "askv": int(mid_len)})
                _gn[0] += 1

    def process_weights_after_loading(self, act_dtype: torch.dtype):
        super().process_weights_after_loading(act_dtype)
        if flashcomm2_oshard_manager.flashcomm2_oshard_enable():
            flashcomm2_oshard_manager.post_process_after_loading()

    def full_graph_fia(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
        layer=None,
    ) -> torch.Tensor:
        passed_key = key
        key, value, block_size, block_table, actual_seq_lengths_kv = self._get_fia_params(key, value, attn_metadata)
        if self.enable_hamming_sparse and attn_metadata.attn_state != AscendAttentionState.DecodeOnly:
            reshape_and_cache_kvcomp(attn_metadata.kvcomp_metadata, self.layerIndex, passed_key)
        elif self.enable_hamming_sparse:
            block_table, actual_seq_lengths_kv = get_kvcomp_decode_params(
                self.layerIndex, attn_metadata.kvcomp_metadata, query, passed_key, block_table, actual_seq_lengths_kv
            )

        num_tokens = attn_metadata.actual_seq_lengths_q[-1]
        if _EXTRA_CTX.is_draft_model:
            if _EXTRA_CTX.is_draft_model_prefill:
                graph_params = get_draft_graph_prefill_params()
            else:
                graph_params = get_draft_graph_params()
        else:
            graph_params = get_graph_params()
        actual_seq_lengths_q = attn_metadata.actual_seq_lengths_q
        # Prepare tensors for attention output
        # TODO: Refactor this to step-level instead of layer-level

        # Get workspace from cache or calculate it if not present.
        workspace = graph_params.workspaces.get(num_tokens)
        softmax_lse = torch.empty(1, dtype=query.dtype, device=query.device)
        input_layout = "TND"
        attn_mask = attn_metadata.attn_mask
        sparse_mode = 4 if self.sliding_window else 3 if attn_metadata.causal else 0
        pre_tokens = self.sliding_window or SWA_INT_MAX
        next_tokens = 0 if self.sliding_window else SWA_INT_MAX

        extra_args = {}
        if self.enable_c8_quant and layer is not None:
            extra_args = {
                "key_antiquant_scale": layer._c8_k_aq_scale_nz_bnsd,
                "value_antiquant_scale": layer._c8_v_aq_scale_nz_bnsd,
                "key_antiquant_mode": 0,
                "value_antiquant_mode": 0,
                "inner_precise": 1,
            }

            # change key/value shape
            _, block_size, _, _ = self.key_cache.shape  # type: ignore
            key = self._nz_5d_view(self.key_cache, block_size)
            value = self._nz_5d_view(self.value_cache, block_size)

            # TODO: change layerout from BNSD to TND.
            input_layout = "BNSD"
            query = query.unsqueeze(2)
            output = output.unsqueeze(2)
            attn_mask = None
            sparse_mode = 0
        if workspace is None:
            workspace = torch_npu._npu_fused_infer_attention_score_get_max_workspace(
                query=query,
                key=key,
                value=value,
                atten_mask=attn_mask,
                block_table=block_table,
                input_layout=input_layout,
                block_size=block_size,
                actual_seq_lengths=actual_seq_lengths_q,
                actual_seq_lengths_kv=actual_seq_lengths_kv,
                num_key_value_heads=self.num_kv_heads,
                num_heads=self.num_heads,
                sparse_mode=sparse_mode,
                pre_tokens=pre_tokens,
                next_tokens=next_tokens,
                scale=self.scale,
                **extra_args,
            )
            if _EXTRA_CTX.is_draft_model:
                update_draft_graph_params_workspaces(num_tokens, workspace)
            else:
                update_graph_params_workspaces(num_tokens, workspace)

        # Handle graph capturing mode
        stream = torch_npu.npu.current_stream()

        event = torch.npu.ExternalEvent()
        event.wait(stream)
        event.reset(stream)
        graph_params.events[num_tokens].append(event)
        attn_params = (
            weak_ref_tensors(query),
            weak_ref_tensors(key),
            weak_ref_tensors(value),
            weak_ref_tensors(block_table),
            weak_ref_tensors(attn_mask) if attn_mask is not None else None,
            block_size,
            actual_seq_lengths_kv,
            actual_seq_lengths_q,
            self.num_kv_heads,
            self.num_heads,
            self.scale,
            weak_ref_tensors(output),
            weak_ref_tensors(softmax_lse),
            sparse_mode,
            pre_tokens,
            next_tokens,
        )
        if self.enable_c8_quant and layer is not None:
            attn_params = attn_params + (
                weak_ref_tensors(layer._c8_k_aq_scale_nz_bnsd),
                None,
                weak_ref_tensors(layer._c8_v_aq_scale_nz_bnsd),
                None,
            )  # type: ignore
        else:
            attn_params = attn_params + (None, None, None, None)  # type: ignore
        graph_params.attn_params[num_tokens].append(attn_params)

        if os.environ.get("R155_T_NOFIA", "0") == "1":
            # R155 causal toggle (measurement ONLY): skip the in-graph FIA in
            # the NATIVE BF16 path — measures N's in-graph FIA cost directly
            # (output zeroed; sha breaks by design).
            with torch.no_grad():
                output.fill_(0)
            return output.view(num_tokens, self.num_heads, self.head_size)
        torch.npu.graph_task_group_begin(stream)
        torch_npu.npu_fused_infer_attention_score.out(
            query=query,
            key=key,
            value=value,
            atten_mask=attn_mask,
            block_table=block_table,
            input_layout=input_layout,
            block_size=block_size,
            actual_seq_lengths=actual_seq_lengths_q,
            actual_seq_lengths_kv=actual_seq_lengths_kv,
            num_key_value_heads=self.num_kv_heads,
            num_heads=self.num_heads,
            scale=self.scale,
            sparse_mode=sparse_mode,
            pre_tokens=pre_tokens,
            next_tokens=next_tokens,
            workspace=workspace,
            out=[output, softmax_lse],
            **extra_args,
        )

        output = output.view(num_tokens, self.num_heads, self.head_size)

        handle = torch.npu.graph_task_group_end(stream)
        graph_params.handles[num_tokens].append(handle)
        return output, num_tokens

    def full_graph_fia_v2(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
    ) -> torch.Tensor:
        key, value, block_size, block_table, actual_seq_lengths_kv = self._get_fia_params(key, value, attn_metadata)
        actual_seq_lengths_kv = attn_metadata.seq_lens
        num_tokens = attn_metadata.actual_seq_lengths_q[-1]
        if _EXTRA_CTX.is_draft_model:
            graph_params = get_draft_graph_params()
        else:
            graph_params = get_graph_params()

        actual_seq_lengths_q = attn_metadata.actual_seq_lengths_q
        workspace = graph_params.workspaces.get(num_tokens)
        softmax_lse = torch.empty(1, dtype=query.dtype, device=query.device)
        if workspace is None:
            workspace = torch_npu._npu_fused_infer_attention_score_v2_get_max_workspace(
                query=query,
                key=key,
                value=value,
                atten_mask=attn_metadata.attn_mask,
                block_table=block_table,
                input_layout="TND",
                block_size=block_size,
                actual_seq_qlen=actual_seq_lengths_q,
                actual_seq_kvlen=actual_seq_lengths_kv,
                num_key_value_heads=self.num_kv_heads,
                softmax_scale=self.scale,
                num_query_heads=self.num_heads,
                sparse_mode=4 if self.sliding_window is not None else 3,
                pre_tokens=self.sliding_window if self.sliding_window is not None else SWA_INT_MAX,
                next_tokens=0,
                learnable_sink=self.sinks,
            )

            if _EXTRA_CTX.is_draft_model:
                update_draft_graph_params_workspaces(num_tokens, workspace)
            else:
                update_graph_params_workspaces(num_tokens, workspace)

        # Handle graph capturing mode
        stream = torch_npu.npu.current_stream()

        event = torch.npu.ExternalEvent()
        event.wait(stream)
        event.reset(stream)
        graph_params.events[num_tokens].append(event)
        graph_params.attn_params[num_tokens].append(
            (
                weak_ref_tensors(query),
                weak_ref_tensors(key),
                weak_ref_tensors(value),
                weak_ref_tensors(block_table),
                weak_ref_tensors(attn_metadata.attn_mask),
                block_size,
                actual_seq_lengths_kv,
                self.num_kv_heads,
                self.num_heads,
                self.scale,
                self.sliding_window,
                self.sinks,
                weak_ref_tensors(output),
                weak_ref_tensors(softmax_lse),
            )
        )
        torch.npu.graph_task_group_begin(stream)
        torch_npu.npu_fused_infer_attention_score_v2.out(
            query=query,
            key=key,
            value=value,
            atten_mask=attn_metadata.attn_mask,
            block_table=block_table,
            input_layout="TND",
            block_size=block_size,
            actual_seq_qlen=actual_seq_lengths_q,
            actual_seq_kvlen=actual_seq_lengths_kv,
            num_key_value_heads=self.num_kv_heads,
            num_query_heads=self.num_heads,
            sparse_mode=4 if self.sliding_window is not None else 3,
            pre_tokens=self.sliding_window if self.sliding_window is not None else SWA_INT_MAX,
            next_tokens=0,
            softmax_scale=self.scale,
            learnable_sink=self.sinks,
            workspace=workspace,
            out=[output, softmax_lse],
        )
        handle = torch.npu.graph_task_group_end(stream)
        graph_params.handles[num_tokens].append(handle)
        return output, num_tokens

    def full_graph_pa(
        self,
        query: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor | None = None,
    ):
        graph_params = get_graph_params()
        num_tokens = query.shape[0]
        if _EXTRA_CTX.capturing:
            if os.environ.get("R155_T_NOFIA", "0") == "1":
                # R155 causal toggle (measurement ONLY): skip the in-graph PA
                # (native BF16 decode attention) — measures its graph cost.
                with torch.no_grad():
                    output.fill_(0)
                return output
            # Get workspace from cache or calculate it if not present.
            workspace = graph_params.workspaces.get(num_tokens)
            if workspace is None:
                workspace = torch_npu._npu_paged_attention_get_workspace(
                    query=query,
                    key_cache=self.key_cache,
                    value_cache=self.value_cache,
                    num_kv_heads=self.num_kv_heads,
                    num_heads=self.num_heads,
                    scale_value=self.scale,
                    block_table=attn_metadata.block_tables,
                    context_lens=attn_metadata.seq_lens,
                    out=output,
                )
                update_graph_params_workspaces(num_tokens, workspace)

            # Handle graph capturing mode
            stream = torch_npu.npu.current_stream()

            event = torch.npu.ExternalEvent()
            event.wait(stream)
            event.reset(stream)
            graph_params.events[num_tokens].append(event)
            graph_params.attn_params[num_tokens].append(
                (
                    weak_ref_tensors(query),
                    weak_ref_tensors(self.key_cache),
                    weak_ref_tensors(self.value_cache),
                    self.num_kv_heads,
                    self.num_heads,
                    self.scale,
                    attn_metadata.block_tables,
                    attn_metadata.seq_lens,
                    weak_ref_tensors(output),
                )
            )

            torch.npu.graph_task_group_begin(stream)
            torch_npu._npu_paged_attention(
                query=query,
                key_cache=self.key_cache,
                value_cache=self.value_cache,
                num_kv_heads=self.num_kv_heads,
                num_heads=self.num_heads,
                scale_value=self.scale,
                block_table=attn_metadata.block_tables,
                context_lens=attn_metadata.seq_lens,
                out=output,
                workspace=workspace,
            )
            handle = torch.npu.graph_task_group_end(stream)
            graph_params.handles[num_tokens].append(handle)
            return output

    def _get_fia_params(self, key: torch.Tensor, value: torch.Tensor, attn_metadata: AscendMetadata, kv_cache=None):
        # PrefillNoCache doesn't need key_cache, but other modes do
        # Only initialize/require cache for modes that actually use it
        if attn_metadata.attn_state != AscendAttentionState.PrefillNoCache:
            # Initialize cache from kv_cache if not already set (for DecodeOnly mode)
            if self.key_cache is None and kv_cache is not None:
                if (
                    isinstance(kv_cache, torch.Tensor)
                    and kv_cache.dim() > 0
                    and kv_cache.shape[0] == 2
                    or isinstance(kv_cache, (list, tuple))
                    and len(kv_cache) >= 2
                ):
                    self.key_cache, self.value_cache = kv_cache[0], kv_cache[1]

            if self.key_cache is None:
                raise RuntimeError(
                    f"key_cache is None in _get_fia_params for mode {attn_metadata.attn_state}. kv_cache={kv_cache}"
                )

        if attn_metadata.attn_state == AscendAttentionState.PrefillNoCache:
            block_size = 128
            block_table = None
            actual_seq_lengths_kv = attn_metadata.actual_seq_lengths_q
            if self.attn_type == AttentionType.ENCODER_DECODER:
                actual_seq_lengths_kv = torch.cumsum(attn_metadata.seq_lens, dim=0).tolist()
        elif attn_metadata.attn_state == AscendAttentionState.PrefillCacheHit:
            batch_size = attn_metadata.seq_lens.shape[0]
            block_table = attn_metadata.block_tables[:batch_size, :]
            num_block, block_size, _, _ = self.key_cache.shape  # type: ignore
            key = self.key_cache.view(  # type: ignore
                num_block, block_size, -1
            )
            value = self.value_cache.view(  # type: ignore
                num_block, block_size, -1
            )
            actual_seq_lengths_kv = attn_metadata.seq_lens_list
        elif attn_metadata.attn_state == AscendAttentionState.DecodeOnly:
            num_block, block_size, _, _ = self.key_cache.shape  # type: ignore
            key = self.key_cache.view(  # type: ignore
                num_block, block_size, -1
            )
            value = self.value_cache.view(  # type: ignore
                num_block, block_size, -1
            )
            block_table = attn_metadata.block_tables
            actual_seq_lengths_kv = attn_metadata.seq_lens_list
        # chunked prefill.
        else:
            num_block, block_size, _, _ = self.key_cache.shape  # type: ignore
            key = self.key_cache.view(  # type: ignore
                num_block, block_size, -1
            )
            value = self.value_cache.view(  # type: ignore
                num_block, block_size, -1
            )
            block_table = attn_metadata.block_tables
            actual_seq_lengths_kv = attn_metadata.seq_lens_list
        return key, value, block_size, block_table, actual_seq_lengths_kv

    def forward_fused_infer_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
        kv_cache=None,
    ):
        # we inherit ForwardContext in model runner v2, when enable model
        # runner v2, there is not capturing attribute in forward_context,
        # just use getattr to avoid attribute error.
        if _EXTRA_CTX.capturing:
            if self.sinks is not None:
                attn_output, num_tokens = self.full_graph_fia_v2(query, key, value, attn_metadata, output)
                output[:num_tokens] = attn_output[:num_tokens]
                return output
            else:
                attn_output, num_tokens = self.full_graph_fia(query, key, value, attn_metadata, output)
                output[:num_tokens] = attn_output[:num_tokens]
                return output
        passed_key = key
        key, value, block_size, block_table, actual_seq_lengths_kv = self._get_fia_params(
            key, value, attn_metadata, kv_cache
        )
        if self.enable_hamming_sparse and attn_metadata.attn_state != AscendAttentionState.DecodeOnly:
            reshape_and_cache_kvcomp(attn_metadata.kvcomp_metadata, self.layerIndex, passed_key)
        elif self.enable_hamming_sparse:
            block_table, actual_seq_lengths_kv = get_kvcomp_decode_params(
                self.layerIndex, attn_metadata.kvcomp_metadata, query, passed_key, block_table, actual_seq_lengths_kv
            )
        num_tokens = attn_metadata.actual_seq_lengths_q[-1]
        query = query[:num_tokens]
        if (
            attn_metadata.attn_state == AscendAttentionState.PrefillNoCache
            and self.attn_type != AttentionType.ENCODER_DECODER
        ):
            key = key[:num_tokens]
            value = value[:num_tokens]
        # Get workspace from cache or calculate it if not present.
        if self.sinks is not None:
            actual_seq_qlen = attn_metadata.actual_seq_lengths_q
            if attn_metadata.attn_state == AscendAttentionState.DecodeOnly:
                actual_seq_qlen = torch.tensor([1] * len(attn_metadata.seq_lens_list), dtype=torch.int32).cumsum(dim=0)
            if self.sliding_window is not None:
                sparse_mode = 4
            else:
                sparse_mode = 3
            attn_output, _ = torch_npu.npu_fused_infer_attention_score_v2(
                query,
                key,
                value,
                num_query_heads=self.num_heads,
                num_key_value_heads=self.num_kv_heads,
                input_layout="TND",
                pre_tokens=self.sliding_window if self.sliding_window is not None else SWA_INT_MAX,
                next_tokens=0,
                atten_mask=attn_metadata.attn_mask,
                sparse_mode=sparse_mode,
                softmax_scale=self.scale,
                block_table=block_table,
                block_size=block_size,
                actual_seq_qlen=actual_seq_qlen,
                actual_seq_kvlen=actual_seq_lengths_kv,
                learnable_sink=self.sinks,
            )
        else:
            if not attn_metadata.causal:
                attn_output, _ = torch_npu.npu_fused_infer_attention_score(
                    query=query,
                    key=key,
                    value=value,
                    block_table=block_table,
                    input_layout="TND",
                    block_size=block_size,
                    actual_seq_lengths=attn_metadata.actual_seq_lengths_q,
                    actual_seq_lengths_kv=actual_seq_lengths_kv,
                    num_key_value_heads=self.num_kv_heads,
                    num_heads=self.num_heads,
                    scale=self.scale,
                    sparse_mode=0,
                )
            elif self.sliding_window is not None:
                attn_output, _ = torch_npu.npu_fused_infer_attention_score(
                    query=query,
                    key=key,
                    value=value,
                    atten_mask=attn_metadata.attn_mask,
                    block_table=block_table,
                    input_layout="TND",
                    block_size=block_size,
                    actual_seq_lengths=attn_metadata.actual_seq_lengths_q,
                    actual_seq_lengths_kv=actual_seq_lengths_kv,
                    num_key_value_heads=self.num_kv_heads,
                    num_heads=self.num_heads,
                    scale=self.scale,
                    pre_tokens=self.sliding_window,
                    next_tokens=0,
                    sparse_mode=4,
                )
            else:
                attn_output, _ = torch_npu.npu_fused_infer_attention_score(
                    query=query,
                    key=key,
                    value=value,
                    atten_mask=attn_metadata.attn_mask,
                    block_table=block_table,
                    input_layout="TND",
                    block_size=block_size,
                    actual_seq_lengths=attn_metadata.actual_seq_lengths_q,
                    actual_seq_lengths_kv=actual_seq_lengths_kv,
                    num_key_value_heads=self.num_kv_heads,
                    num_heads=self.num_heads,
                    scale=self.scale,
                    sparse_mode=3,
                )

            attn_output = attn_output.view(num_tokens, self.num_heads, self.head_size)
        output[:num_tokens] = attn_output[:num_tokens]
        return output

    def forward_paged_attention(
        self,
        query: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if _EXTRA_CTX.capturing:
            return self.full_graph_pa(query, attn_metadata, output)
        torch_npu._npu_paged_attention(
            query=query,
            key_cache=self.key_cache,
            value_cache=self.value_cache,
            num_kv_heads=self.num_kv_heads,
            num_heads=self.num_heads,
            scale_value=self.scale,
            block_table=attn_metadata.block_tables,
            context_lens=attn_metadata.seq_lens,
            out=output,
        )
        return output

    def _forward_encoder_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_metadata: AscendMetadata,
        _: torch.Tensor,
    ) -> torch.Tensor:
        # use default sparse_mode 0 in normal scenario, which means no mask works on it
        return torch_npu.npu_fusion_attention(
            query=query,
            key=key,
            value=value,
            head_num=self.num_heads,
            input_layout="TND",
            scale=self.scale,
            actual_seq_qlen=attn_metadata.actual_seq_lengths_q,
            actual_seq_kvlen=attn_metadata.actual_seq_lengths_q,
        )[0]

    def do_kv_cache_update(
        self,
        layer: torch.nn.Module,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: list[torch.Tensor],
        slot_mapping: torch.Tensor,
    ) -> None:
        if self.attn_type in (AttentionType.ENCODER_ONLY):
            return

        if self.key_cache is None:
            self.key_cache, self.value_cache = kv_cache[0], kv_cache[1]

        DeviceOperator.reshape_and_cache(
            key=key,
            value=value,
            key_cache=self.key_cache,
            value_cache=self.value_cache,
            slot_mapping=slot_mapping,
        )

    def reshape_and_cache(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: tuple[torch.Tensor],
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
    ):
        if len(kv_cache) > 1:
            if self.is_kv_producer:
                attn_metadata.reshape_cache_event = torch.npu.Event()
            if self.key_cache is None:
                self.key_cache, self.value_cache = kv_cache[0], kv_cache[1]
            slots = attn_metadata.slot_mapping
            encoder_decoder = self.attn_type == AttentionType.ENCODER_DECODER
            DeviceOperator.reshape_and_cache(
                key=key[: attn_metadata.num_actual_tokens] if not encoder_decoder else key,
                value=value[: attn_metadata.num_actual_tokens] if not encoder_decoder else value,
                key_cache=self.key_cache,
                value_cache=self.value_cache,
                # quick fix to make sure slots is int32 for cross attention case.
                # see: https://github.com/vllm-project/vllm/blob/ce88756b967c2c5006746a424c15dd59a284ed8c/vllm/model_executor/layers/attention/cross_attention.py#L117
                slot_mapping=slots[: attn_metadata.num_actual_tokens] if not encoder_decoder else slots.to(torch.int32),
            )
            if self.is_kv_producer:
                attn_metadata.reshape_cache_event.record()
        return query, key, value, output

    def forward_impl(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: tuple[torch.Tensor],
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
    ):
        num_tokens = query.shape[0]
        if (
            attn_metadata.attn_state == AscendAttentionState.DecodeOnly
            and using_paged_attention(num_tokens, self.vllm_config)
            and self.sliding_window is None
        ):
            output = self.forward_paged_attention(query, attn_metadata, output)
        else:
            output = self.forward_fused_infer_attention(query, key, value, attn_metadata, output, kv_cache)

        return output

    def forward(
        self,
        layer: AttentionLayer,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: tuple[torch.Tensor],
        attn_metadata: AscendMetadata,
        output: torch.Tensor | None = None,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Forward pass with Ascend attention.
        Args:
            query: shape = [num_tokens, num_heads, head_size]
            key: shape = [num_tokens, num_kv_heads, head_size]
            value: shape = [num_tokens, num_kv_heads, head_size]
            kv_cache: shape =
                [2, num_blocks, block_size, num_kv_heads, head_size]
            attn_metadata: Metadata for attention.
        Returns:
            shape = [num_tokens, num_heads * head_size]
        """
        assert output is not None, "Output tensor must be provided."

        # R144 DIAG: outer-forward file probe (first 3 calls only)
        _r144of_n = globals().setdefault('_R144_OUT_FWD_N', [0])
        if _r144of_n[0] < 3:
            _r144of_n[0] += 1
            try:
                with open("/tmp/r144_out_fwd_probe.log", "a") as _pf:
                    _pf.write(f"[R144-OUT-FWD] call#{_r144of_n[0]} pid={os.getpid()} "
                              f"num_tok={query.shape[0]}\n")
            except Exception:
                pass

        # INT2 KV cache dispatch: if cache is uint8 (packed INT2), use INT2 forward
        if kv_cache is not None and len(kv_cache) >= 2:
            k_cache = kv_cache[0]
            if not getattr(type(self), "_r190_dtype_logged", False):
                type(self)._r190_dtype_logged = True
                _oscar_diag_write("r190_probe.log", f"[R190-DTYPE] k_cache.dtype={k_cache.dtype} kv_cache_len={len(kv_cache)}\n")
            if isinstance(k_cache, torch.Tensor) and k_cache.dtype == torch.uint8:
                # R189 PROBE: run a small MSD_ON LSE before this layer's attention to check cube state
                if os.environ.get("R189_PROBE") == "1":
                    _oscar_diag_write("r190_probe.log", "[R189-ENTRY] forward INT2 path entered\n")
                if os.environ.get("R189_PROBE") == "1" and not getattr(type(self), "_r189_done", False):
                    type(self)._r189_done = True
                    try:
                        if not hasattr(type(self), "_r189_mod"):
                            import torch.utils.cpp_extension as _ce189
                            _R152=os.environ.get("R152_LAUNCHER_DIR", "")
                            _TN=os.path.dirname(torch_npu.__file__)
                            _INC=[os.path.join(_TN,"include"),os.path.join(_TN,"include","third_party","op-plugin"),"/usr/local/Ascend/cann-9.0.0/aarch64-linux/include","/usr/local/Ascend/cann-9.0.0/include"]
                            _VENDOR=os.environ.get("R183_COMPOSITE_OPP", "")
                            _INC.append(_VENDOR+"/op_api/include")
                            _LD=["-L/usr/local/Ascend/cann-9.0.0/lib64","-lascendcl","-lopapi","-L"+os.path.join(_TN,"lib"),"-ltorch_npu","-L"+_VENDOR+"/op_api/lib","-lcust_opapi","-Wl,-rpath,/usr/local/Ascend/cann-9.0.0/lib64","-Wl,-rpath,"+_VENDOR+"/op_api/lib"]
                            os.environ['TORCH_EXTENSIONS_DIR']=f"/tmp/r189_{os.getpid()}"
                            os.makedirs(os.environ['TORCH_EXTENSIONS_DIR'],exist_ok=True)
                            type(self)._r189_mod=_ce189.load(name="r189",sources=[_R152+"/int2_op_launch_lse_fast_r152.cpp"],extra_include_paths=_INC,extra_ldflags=_LD,build_directory=os.environ['TORCH_EXTENSIONS_DIR'],verbose=False)
                        _dev=query.device
                        _D,_nq,_nkv,_bs=128,32,8,128
                        _q=(torch.randn(1,_nq,1,_D,device=_dev)*0.5).bfloat16()
                        _k=torch.randint(0,256,(4,_nkv,_bs,_D//4),device=_dev,dtype=torch.uint8).view(torch.int8)
                        _v=torch.randint(0,256,(4,_nkv,_bs,_D//4),device=_dev,dtype=torch.uint8).view(torch.int8)
                        _bt=torch.arange(4,dtype=torch.int32,device=_dev).unsqueeze(0)
                        _ks=(torch.rand(1,_nkv,4*_bs,device=_dev)*0.05+0.001).bfloat16()
                        _ko=(torch.randn(1,_nkv,4*_bs,device=_dev)*0.02).bfloat16()
                        _vs=(torch.rand(1,_nkv,4*_bs,device=_dev)*0.05+0.001).bfloat16()
                        _vo=(torch.randn(1,_nkv,4*_bs,device=_dev)*0.02).bfloat16()
                        _o=torch.zeros(1,_nq,1,_D,dtype=torch.bfloat16,device=_dev)
                        _l=torch.zeros(1,_nq,1,dtype=torch.float32,device=_dev)
                        _oscar_diag_write("r190_probe.log", "[R189-PROBE] BEFORE-LSE-call\n")
                        _r=type(self)._r189_mod.launch_lse_fast(_q,_k,_v,_bt,_ks,_ko,_vs,_vo,_o,_l,_nq,1.0/(_D**0.5),_nkv,"BNSD",_bs,1,1,[4*_bs],torch.zeros(0,dtype=torch.bfloat16,device=_dev),0,0,0,True)
                        torch.npu.synchronize()
                        _oscar_diag_write("r190_probe.log", f"[R189-PROBE-L0-BEFORE-ATTN] rc={int(_r[0])} finite={torch.isfinite(_o).all().item()}\n")
                    except Exception as _e:
                        _oscar_diag_write("r190_probe.log", f"[R189-PROBE-L0-BEFORE-ATTN] CRASH: {str(_e)[:80]}\n")
                # Dispatch to INT2 forward method
                return self._forward_int2(
                    layer, query, key, value, kv_cache, attn_metadata, output
                )

        if self.enable_hamming_sparse:
            self.layerIndex = int(layer.layer_name.split(".")[2])

        if output_scale is not None or output_block_scale is not None:
            raise NotImplementedError("fused output quantization is not yet supported for AscendAttentionBackendImpl")

        assert layer._k_scale_float == 1.0 and layer._v_scale_float == 1.0
        num_tokens = query.shape[0]
        if attn_metadata is None:
            return output.fill_(0)

        # Initialize key_cache and value_cache from kv_cache if not already set.
        # This is needed for DecodeOnly mode where key/value are None but we still
        # need access to the cache for attention computation.
        if self.key_cache is None and kv_cache is not None:
            if (
                isinstance(kv_cache, torch.Tensor)
                and kv_cache.dim() > 0
                and kv_cache.shape[0] == 2
                or isinstance(kv_cache, (list, tuple))
                and len(kv_cache) >= 2
            ):
                self.key_cache, self.value_cache = kv_cache[0], kv_cache[1]

        output_padded = None
        if key is not None and value is not None:
            output_padded = output
            query, key, value, output_padded = self.reshape_and_cache(
                query, key, value, kv_cache, attn_metadata, output
            )
        # pooling model branch
        if attn_metadata.model_runner_type == "pooling" and not attn_metadata.causal:
            attn_output = self._forward_encoder_attention(query, key, value, attn_metadata, output)
            output[:num_tokens] = attn_output[:num_tokens]
            return output
        if output_padded is not None:
            attn_output = self.forward_impl(query, key, value, kv_cache, attn_metadata, output_padded)
        else:
            attn_output = self.forward_impl(query, key, value, kv_cache, attn_metadata, output)
        output[:num_tokens] = attn_output[:num_tokens]
        return output

    def _forward_int2(
        self,
        layer: "AttentionLayer",
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: tuple[torch.Tensor],
        attn_metadata: "AscendMetadata",
        output: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass with INT2 KV cache (packed uint8).

        This method handles INT2 KV cache when the cache dtype is uint8.
        It quantizes K/V to INT2 before writing to cache, and dequantizes
        before attention computation.
        """
        from vllm_ascend.attention.attention_int2 import AscendINT2AttentionBackendImpl

        # Lazy initialization of INT2 backend instance
        if not hasattr(self, "_int2_backend"):
            self._int2_backend = AscendINT2AttentionBackendImpl.__new__(
                AscendINT2AttentionBackendImpl
            )
            # Copy necessary attributes from self
            self._int2_backend.num_heads = self.num_heads
            self._int2_backend.head_size = self.head_size
            self._int2_backend.scale = self.scale
            self._int2_backend.num_kv_heads = self.num_kv_heads
            self._int2_backend.vllm_config = self.vllm_config
            self._int2_backend.device = query.device  # Use query device instead of self.device
            self._int2_backend.kv_cache_dtype = self.kv_cache_dtype
            # R113: also copy the standard attrs queried on the graph init path
            # (class-level defaults exist as backstop; copy real values when present).
            for _a in ("sliding_window", "alibi_slopes", "attn_type",
                       "logits_soft_cap", "hidden_size", "num_heads", "head_size"):
                if getattr(self, _a, None) is not None:
                    setattr(self._int2_backend, _a, getattr(self, _a))
            self._int2_backend.key_cache = None
            self._int2_backend.value_cache = None
            # Set KV transfer attributes
            self._int2_backend.is_kv_producer = getattr(self, 'is_kv_producer', False)
            self._int2_backend.is_kv_consumer = getattr(self, 'is_kv_consumer', False)
            # Populate Oscar rotation matrices (this __new__ bypassed __init__).
            self._int2_backend._oscar_R_k = None
            self._int2_backend._oscar_R_v = None
            self._int2_backend._oscar_rot_loaded = False
            self._int2_backend._load_oscar_rotations()

        # Delegate to INT2 backend's forward method
        return self._int2_backend.forward(
            layer, query, key, value, kv_cache, attn_metadata, output
        )


class AscendC8AttentionBackendImpl(AscendAttentionBackendImpl):
    """Attention backend implementation for INT8 KV cache (C8/QuaRot) models.

    This subclass handles static per-channel INT8 KV cache quantization.
    It is activated via class surgery in AscendC8KVCacheAttentionMethod.create_weights
    (vllm_ascend/quantization/methods/kv_c8.py)
    so that C8 attention layers automatically use this forward path.
    """

    def forward(
        self,
        layer: AttentionLayer,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: tuple[torch.Tensor],
        attn_metadata: AscendMetadata,
        output: torch.Tensor | None = None,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
    ) -> torch.Tensor:
        assert output is not None, "Output tensor must be provided."

        if output_scale is not None or output_block_scale is not None:
            raise NotImplementedError("fused output quantization is not yet supported for AscendC8AttentionBackendImpl")

        num_tokens = query.shape[0]
        if attn_metadata is None:
            return output.fill_(0)

        self._prepare_c8_scales(layer, query.device)
        float_key, float_value = None, None
        if self.vllm_config.kv_transfer_config is None:
            if key is not None and value is not None:
                if attn_metadata.attn_state != AscendAttentionState.DecodeOnly:
                    float_key, float_value = key, value
                key, value = self._quantize_kv_to_int8(key, value, layer, attn_metadata.num_actual_tokens)
                query, key, value, _ = self._reshape_and_cache(query, key, value, kv_cache, attn_metadata, output)
            # pooling model branch
            if attn_metadata.model_runner_type == "pooling":
                attn_output = self._forward_encoder_attention(query, key, value, attn_metadata, output)
                output[:num_tokens] = attn_output[:num_tokens]
                return output
            if attn_metadata.attn_state == AscendAttentionState.DecodeOnly:
                if _EXTRA_CTX.capturing:
                    attn_output, num_tokens = self.full_graph_fia(query, key, value, attn_metadata, output, layer)
                    output[:num_tokens] = attn_output[:num_tokens]
                    return output
                return self._forward_c8_decode(query, attn_metadata, output, layer)
            elif attn_metadata.attn_state == AscendAttentionState.ChunkedPrefill:
                return self._forward_c8_chunked_prefill(query, float_key, float_value, attn_metadata, output, layer)
            else:
                return self._forward_c8_fused_infer_attention(
                    query,
                    float_key if float_key is not None else key,
                    float_value if float_value is not None else value,
                    attn_metadata,
                    output,
                    layer,
                )
        else:
            if attn_metadata.attn_state != AscendAttentionState.DecodeOnly and self.is_kv_producer:
                output_padded = None
                if key is not None and value is not None:
                    output_padded = output
                    query, key, value, output_padded = self.reshape_and_cache(
                        query, key, value, kv_cache, attn_metadata, output
                    )
                # pooling model branch
                if attn_metadata.model_runner_type == "pooling":
                    attn_output = self._forward_encoder_attention(query, key, value, attn_metadata, output)
                    output[:num_tokens] = attn_output[:num_tokens]
                    return output
                if output_padded is not None:
                    attn_output = self.forward_impl(query, key, value, kv_cache, attn_metadata, output_padded)
                else:
                    attn_output = self.forward_impl(query, key, value, kv_cache, attn_metadata, output)
                output[:num_tokens] = attn_output[:num_tokens]
                return output
            elif not self.is_kv_producer:
                if key is not None and value is not None:
                    key, value = self._quantize_kv_to_int8(key, value, layer, attn_metadata.num_actual_tokens)
                    query, key, value, _ = self._reshape_and_cache(query, key, value, kv_cache, attn_metadata, output)
                # pooling model branch
                if attn_metadata.model_runner_type == "pooling":
                    attn_output = self._forward_encoder_attention(query, key, value, attn_metadata, output)
                    output[:num_tokens] = attn_output[:num_tokens]
                    return output
                if _EXTRA_CTX.capturing:
                    attn_output, num_tokens = self.full_graph_fia(query, key, value, attn_metadata, output, layer)
                    output[:num_tokens] = attn_output[:num_tokens]
                    return output
                elif attn_metadata.attn_state == AscendAttentionState.DecodeOnly:
                    return self._forward_c8_decode(query, attn_metadata, output, layer)

    def _nz_5d_view(self, cache: torch.Tensor, block_size: int) -> torch.Tensor:
        """View a KV cache tensor in NZ 5D layout: (num_blocks, num_kv_heads, head_size//nz, block_size, nz)."""
        NZ_FMT_LAST_DIM = 32
        return cache.view(-1, self.num_kv_heads, self.head_size // NZ_FMT_LAST_DIM, block_size, NZ_FMT_LAST_DIM)

    def _prepare_c8_scales(self, layer: AttentionLayer, device: torch.device) -> None:
        """Shard per-channel C8 scales/offsets to this TP rank and pre-compute
        BF16 BNSD antiquant tensors for FIA V1 decode fast path.
        """
        if hasattr(layer, "_c8_scales_prepared"):
            return

        def _shard_and_reshape(raw: torch.Tensor) -> torch.Tensor:
            if raw.numel() == 1:
                return raw.to(device=device)
            expected = self.num_kv_heads * self.head_size
            if raw.numel() != expected:
                total_kv_heads = raw.numel() // self.head_size
                tp_rank = get_tensor_model_parallel_rank()
                tp_size = get_tensor_model_parallel_world_size()
                kv_head_start = tp_rank * total_kv_heads // tp_size
                raw = raw.view(total_kv_heads, self.head_size)[
                    kv_head_start : kv_head_start + self.num_kv_heads
                ].contiguous()
            return raw.view(1, self.num_kv_heads, self.head_size).to(device=device)

        layer._c8_k_scale = _shard_and_reshape(layer.k_cache_scale.data)
        layer._c8_k_offset = _shard_and_reshape(layer.k_cache_offset.data)
        layer._c8_v_scale = _shard_and_reshape(layer.v_cache_scale.data)
        layer._c8_v_offset = _shard_and_reshape(layer.v_cache_offset.data)

        layer._c8_k_inv_scale = 1.0 / layer._c8_k_scale
        layer._c8_v_inv_scale = 1.0 / layer._c8_v_scale

        nz_bnsd = (self.num_kv_heads, 1, self.head_size)
        layer._c8_k_aq_scale_nz_bnsd = layer._c8_k_scale.view(nz_bnsd).contiguous()
        layer._c8_v_aq_scale_nz_bnsd = layer._c8_v_scale.view(nz_bnsd).contiguous()

        layer._c8_scales_prepared = True

    def _dequant_paged_kv_to_dense(
        self,
        key: torch.Tensor,
        value: torch.Tensor,
        block_table: torch.Tensor,
        seq_lens: list,
        target_dtype: torch.dtype,
        layer,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Gather paged INT8 KV blocks and dequantize."""
        batch_size = block_table.shape[0]
        max_blocks_per_seq = block_table.shape[1]

        # NZ 5D view: (num_blocks, num_kv_heads, head_size//nz, block_size, nz)
        block_size = self.key_cache.shape[1]  # type: ignore[attr-defined]
        max_tokens_padded = max_blocks_per_seq * block_size

        flat_ids = block_table.reshape(-1)
        key_nz = self._nz_5d_view(key, block_size)
        value_nz = self._nz_5d_view(value, block_size)

        # Gather: (batch*max_blocks, H, D//nz, S, nz)
        gathered_k = key_nz[flat_ids]
        gathered_v = value_nz[flat_ids]
        # NZ→ND conversion: permute (S, H, D//nz, nz) → reshape (S, H, D)
        gathered_k = (
            gathered_k.permute(0, 3, 1, 2, 4)
            .contiguous()
            .view(batch_size, max_tokens_padded, self.num_kv_heads, self.head_size)
        )
        gathered_v = (
            gathered_v.permute(0, 3, 1, 2, 4)
            .contiguous()
            .view(batch_size, max_tokens_padded, self.num_kv_heads, self.head_size)
        )

        seq_lens_t = torch.tensor(seq_lens, dtype=torch.long, device=key.device)
        positions = torch.arange(max_tokens_padded, dtype=torch.long, device=key.device)
        valid_mask = (positions.unsqueeze(0) < seq_lens_t.unsqueeze(1)).view(-1)

        dense_k = gathered_k.view(-1, self.num_kv_heads, self.head_size)[valid_mask]
        dense_v = gathered_v.view(-1, self.num_kv_heads, self.head_size)[valid_mask]

        # Scale-only dequant for NZ (symmetric)
        dense_k = dense_k.to(target_dtype) * layer._c8_k_scale
        dense_v = dense_v.to(target_dtype) * layer._c8_v_scale
        return dense_k, dense_v

    def _quantize_kv_to_int8(
        self,
        key: torch.Tensor,
        value: torch.Tensor,
        layer: AttentionLayer,
        num_actual_tokens: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Quantize K/V from float to INT8 using static per-channel C8 scales."""
        actual_key = key[:num_actual_tokens]
        actual_value = value[:num_actual_tokens]

        k_int8 = torch.clamp(
            torch.round(actual_key * layer._c8_k_inv_scale + layer._c8_k_offset),
            -128,
            127,
        ).to(torch.int8)
        v_int8 = torch.clamp(
            torch.round(actual_value * layer._c8_v_inv_scale + layer._c8_v_offset),
            -128,
            127,
        ).to(torch.int8)
        return k_int8, v_int8

    def _forward_c8_decode(
        self,
        query: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
        layer: AttentionLayer,
    ) -> torch.Tensor:
        """C8 decode via FIA V1 BNSD with native paged INT8 KV + perchannel antiquant."""
        num_block, block_size, _, _ = self.key_cache.shape  # type: ignore[attr-defined]
        assert block_size % 32 == 0, f"C8 INT8 KV cache requires block_size to be a multiple of 32, got {block_size}"
        batch_size = len(attn_metadata.seq_lens_list)

        key = self._nz_5d_view(self.key_cache, block_size)
        value = self._nz_5d_view(self.value_cache, block_size)

        attn_output, _ = torch_npu.npu_fused_infer_attention_score(
            query[:batch_size].unsqueeze(2),
            key,
            value,
            key_antiquant_scale=layer._c8_k_aq_scale_nz_bnsd,
            value_antiquant_scale=layer._c8_v_aq_scale_nz_bnsd,
            block_table=attn_metadata.block_tables,
            actual_seq_lengths_kv=attn_metadata.seq_lens_list,
            num_heads=self.num_heads,
            num_key_value_heads=self.num_kv_heads,
            input_layout="BNSD",
            scale=self.scale,
            block_size=block_size,
            antiquant_mode=0,
            key_antiquant_mode=0,
            value_antiquant_mode=0,
            inner_precise=1,
            sparse_mode=0,
        )
        attn_output = attn_output.squeeze(2)
        output[:batch_size] = attn_output
        return output

    def _forward_c8_chunked_prefill(
        self,
        query: torch.Tensor,
        float_key: torch.Tensor | None,
        float_value: torch.Tensor | None,
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
        layer: AttentionLayer,
    ) -> torch.Tensor:
        """C8 ChunkedPrefill: decode via FIA V1 BNSD paged INT8 (zero gather),
        prefill via FIA V1 TND with float KV (new) or gather+dequant (continuing).
        """
        num_decode_tokens = attn_metadata.num_decode_tokens
        num_decodes = attn_metadata.num_decodes
        actual_seq_qlen = attn_metadata.actual_seq_lengths_q
        num_tokens = int(actual_seq_qlen[-1])  # type: ignore[index]

        if num_decode_tokens > 0:
            num_block, block_size, _, _ = self.key_cache.shape  # type: ignore[attr-defined]
            assert block_size % 32 == 0, (
                f"C8 INT8 KV cache requires block_size to be a multiple of 32, got {block_size}"
            )
            kv_k = self._nz_5d_view(self.key_cache, block_size)
            kv_v = self._nz_5d_view(self.value_cache, block_size)

            attn_out, _ = torch_npu.npu_fused_infer_attention_score(
                query[:num_decode_tokens].unsqueeze(2),
                kv_k,
                kv_v,
                key_antiquant_scale=layer._c8_k_aq_scale_nz_bnsd,
                value_antiquant_scale=layer._c8_v_aq_scale_nz_bnsd,
                block_table=attn_metadata.block_tables[:num_decodes],
                actual_seq_lengths_kv=attn_metadata.seq_lens_list[:num_decodes],
                num_heads=self.num_heads,
                num_key_value_heads=self.num_kv_heads,
                input_layout="BNSD",
                scale=self.scale,
                block_size=block_size,
                antiquant_mode=0,
                key_antiquant_mode=0,
                value_antiquant_mode=0,
                inner_precise=1,
                sparse_mode=0,
            )
            output[:num_decode_tokens] = attn_out.squeeze(2)

        if attn_metadata.num_prefills > 0:
            prefill_q = query[num_decode_tokens:num_tokens]

            prefill_seq_qlen = [
                actual_seq_qlen[i] - num_decode_tokens for i in range(num_decodes, len(actual_seq_qlen))
            ]

            all_new_prefill = True
            for i in range(num_decodes, len(attn_metadata.seq_lens_list)):
                q_start = actual_seq_qlen[i - 1] if i > 0 else 0
                qlen_i = actual_seq_qlen[i] - q_start
                if attn_metadata.seq_lens_list[i] > qlen_i:
                    all_new_prefill = False
                    break

            if all_new_prefill and float_key is not None and float_value is not None:
                prefill_k = float_key[num_decode_tokens:num_tokens]
                prefill_v = float_value[num_decode_tokens:num_tokens]
                prefill_seq_kvlen = prefill_seq_qlen
            else:
                num_block, blk_size, _, _ = self.key_cache.shape  # type: ignore[attr-defined]
                paged_k = self._nz_5d_view(self.key_cache, blk_size)
                paged_v = self._nz_5d_view(self.value_cache, blk_size)

                prefill_bt = attn_metadata.block_tables[num_decodes:]
                prefill_sl = attn_metadata.seq_lens_list[num_decodes:]
                prefill_k, prefill_v = self._dequant_paged_kv_to_dense(
                    paged_k, paged_v, prefill_bt, prefill_sl, query.dtype, layer
                )
                prefill_seq_kvlen = torch.tensor(prefill_sl, dtype=torch.int32).cumsum(dim=0)

            # block_table is None for prefill; FIA ignores block_size in this case.
            # Use cache block_size for consistency rather than a magic number.
            cache_block_size = self.key_cache.shape[1]  # type: ignore[attr-defined]
            attn_out, _ = torch_npu.npu_fused_infer_attention_score(
                query=prefill_q,
                key=prefill_k,
                value=prefill_v,
                atten_mask=attn_metadata.attn_mask,
                block_table=None,
                input_layout="TND",
                block_size=cache_block_size,
                actual_seq_lengths=prefill_seq_qlen,
                actual_seq_lengths_kv=prefill_seq_kvlen,
                num_key_value_heads=self.num_kv_heads,
                num_heads=self.num_heads,
                scale=self.scale,
                sparse_mode=3,
            )
            n_prefill = num_tokens - num_decode_tokens
            attn_out = attn_out.view(n_prefill, self.num_heads, self.head_size)
            output[num_decode_tokens:num_tokens] = attn_out[:n_prefill]

        return output

    def _forward_c8_fused_infer_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
        layer: AttentionLayer,
    ):
        """C8 FIA V1 TND for prefill states (PrefillNoCache uses float KV directly,
        PrefillCacheHit gathers + dequants paged INT8 KV).
        """
        key, value, block_size, block_table, actual_seq_lengths_kv = self._get_fia_params(key, value, attn_metadata)

        actual_seq_qlen = attn_metadata.actual_seq_lengths_q
        num_tokens = int(actual_seq_qlen[-1])  # type: ignore[index]
        query = query[:num_tokens]

        if (
            attn_metadata.attn_state == AscendAttentionState.PrefillNoCache
            and self.attn_type != AttentionType.ENCODER_DECODER
        ):
            key = key[:num_tokens]
            value = value[:num_tokens]

        if key.dtype == torch.int8:
            if block_table is not None:
                seq_lens = (
                    actual_seq_lengths_kv if isinstance(actual_seq_lengths_kv, list) else actual_seq_lengths_kv.tolist()
                )
                key, value = self._dequant_paged_kv_to_dense(key, value, block_table, seq_lens, query.dtype, layer)
                block_table = None
                # block_table is None after dequant; FIA ignores block_size.
                # Use cache block_size for consistency rather than a magic number.
                block_size = self.key_cache.shape[1]  # type: ignore[attr-defined]
                actual_seq_lengths_kv = torch.tensor(seq_lens, dtype=torch.int32).cumsum(dim=0)
            else:
                key = (key.to(query.dtype) - layer._c8_k_offset) * layer._c8_k_scale
                value = (value.to(query.dtype) - layer._c8_v_offset) * layer._c8_v_scale

        attn_output, _ = torch_npu.npu_fused_infer_attention_score(
            query=query,
            key=key,
            value=value,
            atten_mask=attn_metadata.attn_mask,
            block_table=block_table,
            input_layout="TND",
            block_size=block_size,
            actual_seq_lengths=actual_seq_qlen,
            actual_seq_lengths_kv=actual_seq_lengths_kv,
            num_key_value_heads=self.num_kv_heads,
            num_heads=self.num_heads,
            scale=self.scale,
            sparse_mode=3,
        )
        attn_output = attn_output.view(num_tokens, self.num_heads, self.head_size)
        output[:num_tokens] = attn_output
        return output

    def _reshape_and_cache(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: tuple[torch.Tensor],
        attn_metadata: AscendMetadata,
        output: torch.Tensor,
    ):
        if len(kv_cache) > 1:
            if self.is_kv_producer:
                attn_metadata.reshape_cache_event = torch.npu.Event()
            if self.key_cache is None:
                self.key_cache, self.value_cache = kv_cache[0], kv_cache[1]
            slots = attn_metadata.slot_mapping

            encoder_decoder = self.attn_type == AttentionType.ENCODER_DECODER

            # NZ write path: 5D view + npu_scatter_pa_kv_cache
            block_size = self.vllm_config.cache_config.block_size
            k_cache_layer = self._nz_5d_view(self.key_cache, block_size)
            v_cache_layer = self._nz_5d_view(self.value_cache, block_size)

            torch_npu.npu_scatter_pa_kv_cache(
                key=key[: attn_metadata.num_actual_tokens] if not encoder_decoder else key,
                value=value[: attn_metadata.num_actual_tokens] if not encoder_decoder else value,
                key_cache=k_cache_layer,
                value_cache=v_cache_layer,
                slot_mapping=slots[: attn_metadata.num_actual_tokens] if not encoder_decoder else slots,
            )

            if self.is_kv_producer:
                attn_metadata.reshape_cache_event.record()
        return query, key, value, output




