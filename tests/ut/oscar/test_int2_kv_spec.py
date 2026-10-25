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
import types
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
    w = SimpleNamespace(
        model_config=SimpleNamespace(hf_text_config=hf, dtype=torch.bfloat16),
        vllm_config=SimpleNamespace(
            scheduler_config=SimpleNamespace(max_num_seqs=max_num_seqs)
        ),
    )
    # R218 wave-4: the fail-safe fallback dispatches back into
    # _oscar_int2_hp_ring_bytes_conservative on self; give the fake the real
    # bound method so the exception path is exercised end-to-end.
    w._oscar_int2_hp_ring_bytes_conservative = types.MethodType(
        NPUWorker._oscar_int2_hp_ring_bytes_conservative, w)
    return w


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

    # ---- R218 wave-4 T4: fail-safe exception path ----
    # The reservation must never silently return 0 (the old fail-open): the
    # packed INT2 pool would consume the whole budget and the BF16 ring would
    # then OOM at startup. Exact-path failures fall back to a conservative
    # UPPER bound; underivable geometry fails closed with RuntimeError.

    def test_exact_failure_falls_back_to_upper_bound(self, monkeypatch):
        import vllm_ascend.oscar.config as _ocfg

        def _boom():
            raise RuntimeError("oscar config introspection broken")

        monkeypatch.setattr(_ocfg, "get_oscar_config", _boom)
        monkeypatch.setenv("R109_TT_MAX_SEQS", "32")
        monkeypatch.delenv("R205_HPFIT", raising=False)
        monkeypatch.setenv("R199_PRREAD", "1")   # exact path would drop +4
        # Conservative bound keeps the +4 margin even under PRREAD.
        got = NPUWorker._oscar_int2_hp_ring_bytes(_worker())
        assert got == 36 * 2 * 33 * 1028 * 8 * 128 * 2
        # and it never under-reserves vs the (unreachable) exact value
        assert got >= 36 * 2 * 33 * 1024 * 8 * 128 * 2

    def test_fallback_ignores_the_hpfit_shrink(self, monkeypatch):
        import vllm_ascend.oscar.config as _ocfg

        monkeypatch.setattr(
            _ocfg, "get_oscar_config", lambda: (_ for _ in ()).throw(
                RuntimeError("boom"))
        )
        monkeypatch.setenv("R109_TT_MAX_SEQS", "96")
        monkeypatch.setenv("R205_HPFIT", "1")
        monkeypatch.setenv("R205_HPFIT_MARGIN", "8")
        monkeypatch.delenv("R199_PRREAD", raising=False)
        # HPFIT caps ms to 40 on the exact path; the bound keeps ms=96
        # (>= max_num_seqs + 1 = 33) so it can only over-reserve.
        assert (
            NPUWorker._oscar_int2_hp_ring_bytes(_worker())
            == 36 * 2 * 96 * 1028 * 8 * 128 * 2
        )

    def test_fallback_reads_the_window_envs(self, monkeypatch):
        import vllm_ascend.oscar.config as _ocfg

        monkeypatch.setattr(
            _ocfg, "get_oscar_config", lambda: (_ for _ in ()).throw(
                RuntimeError("boom"))
        )
        monkeypatch.setenv("R109_TT_MAX_SEQS", "32")
        monkeypatch.setenv("R109_TT_PREFIX", "256")
        monkeypatch.delenv("R205_HPFIT", raising=False)
        monkeypatch.delenv("R199_PRREAD", raising=False)
        assert (
            NPUWorker._oscar_int2_hp_ring_bytes(_worker())
            == 36 * 2 * 33 * (256 + 896 + 4) * 8 * 128 * 2
        )

    def test_underivable_geometry_fails_closed(self, monkeypatch):
        import pytest

        monkeypatch.setenv("R109_TT_MAX_SEQS", "32")
        broken = SimpleNamespace(
            model_config=SimpleNamespace(hf_text_config=None,
                                         dtype=torch.bfloat16),
            vllm_config=SimpleNamespace(
                scheduler_config=SimpleNamespace(max_num_seqs=32)
            ),
        )
        broken._oscar_int2_hp_ring_bytes_conservative = types.MethodType(
            NPUWorker._oscar_int2_hp_ring_bytes_conservative, broken)
        with pytest.raises(RuntimeError, match="fail-closed"):
            NPUWorker._oscar_int2_hp_ring_bytes(broken)
