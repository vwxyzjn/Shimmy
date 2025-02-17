"""Utility functions for the compatibility wrappers."""
from __future__ import annotations

import copy
from collections import OrderedDict
from typing import Any

import numpy as np
from dm_env.specs import Array, BoundedArray, DiscreteArray
from gymnasium import spaces
from gymnasium.core import ObsType


def dm_spec2gym_space(spec) -> spaces.Space[Any]:
    """Converts a dm_env spec to a gymnasium space."""
    if isinstance(spec, (OrderedDict, dict)):
        return spaces.Dict(
            {key: dm_spec2gym_space(value) for key, value in copy.copy(spec).items()}
        )
    # not possible to use isinstance due to inheritance
    elif type(spec) is BoundedArray:
        low = np.broadcast_to(spec.minimum, spec.shape)
        high = np.broadcast_to(spec.maximum, spec.shape)
        return spaces.Box(low=low, high=high, shape=spec.shape, dtype=spec.dtype)
    elif type(spec) is Array:
        if np.issubdtype(spec.dtype, np.integer):
            low = np.iinfo(spec.dtype).min
            high = np.iinfo(spec.dtype).max
        elif np.issubdtype(spec.dtype, np.inexact):
            low = float("-inf")
            high = float("inf")
        elif spec.dtype == "bool":
            low = int(0)
            high = int(1)
        else:
            raise ValueError(f"Unknown dtype {spec.dtype} for spec {spec}.")

        return spaces.Box(low=low, high=high, shape=spec.shape, dtype=spec.dtype)
    elif type(spec) is DiscreteArray:
        return spaces.Discrete(spec.num_values)
    else:
        raise NotImplementedError(
            f"Cannot convert dm_spec to gymnasium space, unknown spec: {spec}, please report."
        )


def dm_obs2gym_obs(obs) -> np.ndarray | dict[str, Any]:
    """Converts a dm_env observation to a gymnasium observation."""
    if isinstance(obs, (OrderedDict, dict)):
        return {key: dm_obs2gym_obs(value) for key, value in copy.copy(obs).items()}
    else:
        return np.asarray(obs)


def dm_control_step2gym_step(
    timestep,
) -> tuple[ObsType, float, bool, bool, dict[str, Any]]:
    """Opens up the timestep to return obs, reward, terminated, truncated, info."""
    obs = dm_obs2gym_obs(timestep.observation)
    reward = timestep.reward or 0

    # set terminated and truncated
    terminated, truncated = False, False
    if timestep.last():
        if timestep.discount == 0:
            truncated = True
        else:
            terminated = True

    info = {
        "timestep.discount": timestep.discount,
        "timestep.step_type": timestep.step_type,
    }

    return (  # pyright: ignore[reportGeneralTypeIssues]
        obs,
        reward,
        terminated,
        truncated,
        info,
    )
