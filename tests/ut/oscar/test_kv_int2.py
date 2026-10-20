# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the INT2 KV cache quantization method (scheme registration
and class surgery)."""
from unittest import mock

import pytest
import torch

from vllm_ascend.quantization.methods.kv_int2 import (
    AscendINT2KVCacheAttentionMethod,
    _int2_kv_scale_weight_loader,
)
from vllm_ascend.quantization.methods.registry import get_scheme_class


class _FakeLayer:
    def __init__(self, with_impl=False):
        if with_impl:
            self.impl = type("Impl", (), {})()
        self.kv_cache_torch_dtype = None
        self.k_cache_scale = None
        self.v_cache_scale = None


class TestSchemeRegistration:
    def test_registered_under_int2_per_token_head(self):
        cls = get_scheme_class("INT2_PER_TOKEN_HEAD", "attention")
        assert cls is AscendINT2KVCacheAttentionMethod


class TestCreateWeights:
    def _method(self):
        with mock.patch("vllm_ascend.quantization.methods.kv_int2."
                        "get_current_vllm_config") as cfg:
            cfg.return_value = type("C", (), {"kv_transfer_config": None})()
            m = AscendINT2KVCacheAttentionMethod({"type": "int2"}, "prefix")
        return m

    def test_sets_packed_dtype_and_scales(self):
        m = self._method()
        layer = _FakeLayer()
        m.create_weights(layer)
        assert layer.kv_cache_torch_dtype == torch.uint8
        assert layer.k_cache_scale.numel() == 1
        assert layer.v_cache_scale.numel() == 1
        assert not layer.k_cache_scale.requires_grad

    def test_class_surgery_rebinds_impl(self):
        m = self._method()
        layer = _FakeLayer(with_impl=True)
        fake_backend = type("FakeINT2Backend", (), {})()
        import sys
        import types
        mod = types.ModuleType("vllm_ascend.attention.attention_int2")
        mod.AscendINT2AttentionBackendImpl = fake_backend.__class__
        with mock.patch.dict(sys.modules,
                             {"vllm_ascend.attention.attention_int2": mod}):
            m.create_weights(layer)
        assert layer.impl.__class__ is fake_backend.__class__

    def test_apply_fails_closed(self):
        m = self._method()
        layer = _FakeLayer()
        m.create_weights(layer)
        with pytest.raises(RuntimeError, match="should not be called"):
            m.apply(layer, None, None, None, None, None, None, None, None)


class TestScaleWeightLoader:
    def test_scalar_fill(self):
        p = torch.nn.Parameter(torch.ones(1))
        _int2_kv_scale_weight_loader(p, torch.tensor([2.0]))
        assert p.data.item() == 2.0

    def test_tp_shard_per_head(self):
        # loaded [total_kv_heads, head_size] -> shard for this rank
        with mock.patch("vllm_ascend.quantization.methods.kv_int2."
                        "get_tensor_model_parallel_rank", return_value=1), \
             mock.patch("vllm_ascend.quantization.methods.kv_int2."
                        "get_tensor_model_parallel_world_size", return_value=2):
            p = torch.nn.Parameter(torch.zeros(2, 4))
            loaded = torch.arange(16, dtype=torch.float32).reshape(4, 4) * 1.0
            _int2_kv_scale_weight_loader(p, loaded)
            # rank 1 of 4 heads -> rows 2:4
            assert torch.equal(p.data, loaded[2:4])
