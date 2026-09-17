"""CPU teaching example for LINEAR_SYSTEMS_GUIDE.md; no model or dataset access.

Uses small positive-definite statistics to compare direct and matrix-free solves.
This is a teaching solver, not a replacement for the project's experiment code.
"""
from __future__ import annotations

import torch


def pcg(apply, rhs, initial, diagonal, *, max_steps=100, rtol=1e-12):
    """Preconditioned CG for this example's real positive-definite operator."""
    x = initial.clone()
    residual = rhs - apply(x)
    scale = rhs.norm().clamp_min(torch.finfo(rhs.dtype).tiny)
    z = residual / diagonal
    direction = z.clone()
    rz = torch.sum(residual * z)
    for step in range(max_steps):
        if residual.norm() <= rtol * scale:
            return x, step
        transformed = apply(direction)
        denominator = torch.sum(direction * transformed)
        if denominator <= 0:
            raise RuntimeError('This teaching example requires positive curvature.')
        step_size = rz / denominator
        x = x + step_size * direction
        residual = residual - step_size * transformed
        z = residual / diagonal
        next_rz = torch.sum(residual * z)
        direction = z + (next_rz / rz) * direction
        rz = next_rz
    if residual.norm() > rtol * scale:
        raise RuntimeError('Teaching example did not converge within the budget.')
    return x, max_steps


def vec_columns(matrix):
    """Column-major vectorization; torch.reshape by itself is row-major."""
    return matrix.T.contiguous().reshape(-1)


def main():
    # Rectangular weights expose transposition mistakes hidden by square examples.
    def matrix(values):
        return torch.tensor(values, dtype=torch.float64, device='cpu')

    inputs = [matrix([[2, 0.4], [0.4, 1]]), matrix([[1, -0.2], [-0.2, 3]])]
    outputs = [matrix([[2, 0.3, 0.1], [0.3, 1, 0.2], [0.1, 0.2, 1.5]]),
               matrix([[1, 0.1, -0.2], [0.1, 2, 0.1], [-0.2, 0.1, 1.2]])]
    experts = [matrix([[1, 2, -1], [-1, 0.5, 1]]), matrix([[3, -1, 0.5], [0, 2, -2]])]
    for stat in inputs + outputs:
        assert torch.linalg.eigvalsh(stat).min() > 0

    # RegMean: solve the system with one right-hand column per output channel.
    reg_rhs = sum(a @ w for a, w in zip(inputs, experts))
    reg_direct = torch.linalg.solve(sum(inputs), reg_rhs)
    features = [torch.linalg.cholesky(a).T for a in inputs]
    targets = [z @ w for z, w in zip(features, experts)]
    reg_lstsq = torch.linalg.lstsq(torch.cat(features), torch.cat(targets)).solution
    torch.testing.assert_close(reg_direct, reg_lstsq, rtol=1e-10, atol=1e-10)

    # CM: only the operator and a matrix-shaped right-hand side are needed by CG.
    def apply(x):
        return sum(a @ x @ g for a, g in zip(inputs, outputs))

    rhs = sum(a @ w @ g for a, w, g in zip(inputs, experts, outputs))
    diagonal = sum(a.diagonal()[:, None] * g.diagonal()[None, :]
                   for a, g in zip(inputs, outputs))
    candidate, steps = pcg(apply, rhs, torch.zeros_like(experts[0]), diagonal)

    # Explicit construction is safe only because this example has six unknowns.
    dense = sum(torch.kron(g.T.contiguous(), a) for a, g in zip(inputs, outputs))
    dense_vector = torch.linalg.solve(dense, vec_columns(rhs))
    dense_candidate = dense_vector.reshape(3, 2).T.contiguous()
    torch.testing.assert_close(candidate, dense_candidate, rtol=1e-10, atol=1e-10)
    torch.testing.assert_close(apply(candidate), rhs, rtol=1e-10, atol=1e-10)

    probe = matrix([[0.2, -0.7, 1.1], [0.8, 0.3, -0.5]]).requires_grad_()
    torch.testing.assert_close(vec_columns(apply(probe)), dense @ vec_columns(probe))
    objective = sum(0.5 * torch.trace((probe - w).T @ a @ (probe - w) @ g)
                    for a, w, g in zip(inputs, experts, outputs))
    gradient, = torch.autograd.grad(objective, probe)
    torch.testing.assert_close(gradient, apply(probe) - rhs)

    def input_only(x):
        return sum(a @ x for a in inputs)

    input_diagonal = sum(a.diagonal()[:, None] for a in inputs).expand_as(reg_rhs)
    input_candidate, _ = pcg(input_only, reg_rhs, torch.zeros_like(reg_rhs), input_diagonal)
    torch.testing.assert_close(input_candidate, reg_direct, rtol=1e-10, atol=1e-10)
    print(f'PASS: CPU checks of least squares, vectorization, objective gradient and PCG ({steps} steps).')


if __name__ == '__main__':
    main()
