# Copyright 2020 The Flax Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common utils used in Flax examples."""

import jax
from jax import lax
import jax.numpy as jnp
import numpy as onp


def shard(xs):
  local_device_count = jax.local_device_count()
  return jax.tree_map(
      lambda x: x.reshape((local_device_count, -1) + x.shape[1:]), xs)


def shard_prng_key(prng_key):
  # PRNG keys can used at train time to drive stochastic modules
  # e.g. DropOut. We would like a different PRNG key for each local
  # device so that we end up with different random numbers on each one,
  # hence we split our PRNG key and put the resulting keys into the batch
  return jax.random.split(prng_key, num=jax.local_device_count())


def onehot(labels, num_classes, on_value=1.0, off_value=0.0):
  x = (labels[..., None] == jnp.arange(num_classes)[None])
  x = lax.select(x, jnp.full(x.shape, on_value), jnp.full(x.shape, off_value))
  return x.astype(jnp.float32)


def pmean(tree, axis_name='batch'):
  num_devices = lax.psum(1., axis_name)
  return jax.tree_map(lambda x: lax.psum(x, axis_name) / num_devices, tree)


def psum(tree, axis_name='batch'):
  return jax.tree_map(lambda x: lax.psum(x, axis_name), tree)


def stack_forest(forest):
  stack_args = lambda *args: onp.stack(args)
  return jax.tree_multimap(stack_args, *forest)


def get_metrics(device_metrics):
  device_metrics = jax.tree_map(lambda x: x[0], device_metrics)
  metrics_np = jax.device_get(device_metrics)
  return stack_forest(metrics_np)
