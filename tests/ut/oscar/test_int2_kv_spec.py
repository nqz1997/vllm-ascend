# SPDX-License-Identifier: Apache-2.0
"""Behavioral tests for the INT2 KV-cache accounting adapters.

Two independent accountings must agree with what the backend actually
allocates:

* paged payload: four 2-bit values per byte plus four bf16 scale/offset
  lanes per token-head cell, published through ``state_content_bytes``;
* high-precision ring: the BF16 three-tier window lives outside the paged
  spec but inside the same free-memory budget, so it is reserved before
  the engine turns the budget into blocks.
"""
from types import SimpleNamespace

import torch
from vllm.v1.kv_cache_interface import FullAttentionSpec

from vllm_ascend.worker.v1.model_runner import NPUModelRunner
from vllm_ascend.worker.v2.attn_utils import _pack_int2_full_attention_spec
from vllm_ascend.worker.worker import NPUWorker


def _full_spec(head_size=128, head_size_v=128):
    return FullAttentionSpec(
        block_size=128,
        num_kv_heads=8,
        head_size=head_size,
        head_size_v=head_size_v,
        dtype=torch.uint8,
    )


def _runner(cache_dtype="int2_per_token_head"):
    return SimpleNamespace(
        vllm_config=SimpleNamespace(
            cache_config=SimpleNamespace(cache_dtype=cache_dtype),
            model_config=SimpleNamespace(dtype=torch.bfloat16),
        )
    )


def _worker(max_num_seqs=32):
    hf = SimpleNamespace(
        num_hidden_layers=36,
        num_key_value_heads=8,
        num_attention_heads=32,
        hidden_size=4096,
    )
    return SimpleNamespace(
        model_config=SimpleNamespace(hf_text_config=hf, dtype=torch.bfloat16),
        vllm_config=SimpleNamespace(
            scheduler_config=SimpleNamespace(max_num_seqs=max_num_seqs)
        ),
    )


class TestPackedInt2Spec:
    def test_packs_to_the_physical_page(self):
        spec = _full_spec()
        out = NPUModelRunner._maybe_pack_int2_spec(_runner(), spec)
        assert out is not spec
        # K/V payload: 2 * (128 // 4) = 64 B; four bf16 lanes = 8 B.
        assert out.state_content_bytes == 72
        assert out.page_size_bytes == 73728

    def test_other_cache_dtypes_keep_the_dense_spec(self):
        spec = _full_spec()
        assert NPUModelRunner._maybe_pack_int2_spec(_runner("bfloat16"), spec) is spec

    def test_indivisible_head_size_fails_closed(self):
        spec = _full_spec(head_size=98, head_size_v=98)
        assert NPUModelRunner._maybe_pack_int2_spec(_runner(), spec) is spec

    def test_v2_spec_builder_uses_the_same_packing(self):
        spec = _full_spec()
        cfg = _runner().vllm_config
        out = _pack_int2_full_attention_spec(spec, cfg)
        assert out.state_content_bytes == 72
        assert out.page_size_bytes == 73728


class TestHighPrecisionRingReservation:
    def test_matches_the_slotstate_layout(self, monkeypatch):
        monkeypatch.setenv("R109_TT_MAX_SEQS", "32")
        monkeypatch.delenv("R205_HPFIT", raising=False)
        monkeypatch.delenv("R199_PRREAD", raising=False)
        # 36 layers * K/V * 33 rows * 1028 hp tokens * 8 heads * 128 dim * bf16
        assert NPUWorker._oscar_int2_hp_ring_bytes(_worker()) == 5_002_297_344

    def test_prread_drops_the_four_token_margin(self, monkeypatch):
        monkeypatch.setenv("R109_TT_MAX_SEQS", "32")
        monkeypatch.delenv("R205_HPFIT", raising=False)
        monkeypatch.setenv("R199_PRREAD", "1")
        assert (
            NPUWorker._oscar_int2_hp_ring_bytes(_worker())
            == 36 * 2 * 33 * 1024 * 8 * 128 * 2
        )

    def test_hpfit_caps_the_env_cap(self, monkeypatch):
        monkeypatch.setenv("R109_TT_MAX_SEQS", "96")
        monkeypatch.setenv("R205_HPFIT", "1")
        monkeypatch.setenv("R205_HPFIT_MARGIN", "8")
        monkeypatch.delenv("R199_PRREAD", raising=False)
        # min(env=96, max_num_seqs + margin = 40)
        assert (
            NPUWorker._oscar_int2_hp_ring_bytes(_worker())
            == 36 * 2 * 40 * 1028 * 8 * 128 * 2
        )
