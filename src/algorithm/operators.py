"""
Operatory genetyczne: krzyżowanie i mutacje ścieżek UAV.

Crossover: Order Crossover (OX) adaptowany dla multi-UAV
Mutacje wewnątrz ścieżki: swap, insert, invert
Mutacje między ścieżkami: transfer, exchange

"""

from __future__ import annotations

import random

from src.io.data_loader import TestCase
from src.model.individual import Solution


#---------Order Crossover----------

def order_crossover(parent1 : list[int], parent2: list[int]) -> list[int]:
    """OX dla pojedynczej permutacji"""
    size = len(parent1)
    cut1, cut2 = sorted(random.sample(range(size), 2))

    #Kopiowanie segmentu z parent1

    offspring = [None] * size
    offspring[cut1:cut2] = parent1[cut1:cut2]

    #Wypelnij reszte elementami z parent2 w kolejnosci
    segment = set(offspring[cut1:cut2])
    fill = [x for x in parent2 if x not in segment]

    idx = cut2
    for gene in fill:
        if idx >= size:
            idx = 0
        while offspring[idx] is not None:
            idx +=1
            if idx >= size:
                idx = 0
        offspring[idx] = gene
        idx += 1
    
    return offspring

def crossover(parent1: Solution, parent2: Solution, test_case: TestCase) -> Solution:

    """
    Order Crossover dla wielu UAV

    1. CONCAT - połącz ścieżki w jedną permutacje
    2. OX - zastosuj Order Crossover
    3. RESTORE - podziel z powrotem do k ścieżek (split points losowego rodzica)
    """

    # concat
    full1, splits1 = [], []
    for path in parent1.paths:
        full1.extend(path)
        splits1.append(len(full1))

    full2, splits2 = [], []
    for path in parent2.paths:
        full2.extend(path)
        splits2.append(len(full2))

    # OX
    offspring_full = order_crossover(full1, full2)

    # restore splits using one parent's split points
    splits = random.choice([splits1, splits2])
    paths = []
    prev = 0
    for sp in splits:
        paths.append(offspring_full[prev:sp])
        prev = sp

    offspring = Solution(paths=paths, num_uavs=parent1.num_uavs)

    # Jeśli potomne rozwiązanie nie jest poprawne, zwróć kopię rodzica
    if not offspring.validate(test_case):
        return parent1.copy()

    return offspring

#-------Mutacje wewnątrz jednej ścieżki-------------------

def _pick_path(solution: Solution) -> tuple[int, list[int]]:
    """Wybierz losową ścieżkę drona. Zwraca (indeks, ścieżka)"""
    uav_id = random.randint(0, solution.num_uavs - 1)
    return uav_id, solution.paths[uav_id]


def swap_mutation(solution: Solution) -> Solution:
    """Zamień dwa losowe elementy w ścieżce."""
    sol = solution.copy()
    _, path = _pick_path(sol)

    if len(path) < 2:
        return sol

    pos1, pos2 = random.sample(range(len(path)), 2)
    path[pos1], path[pos2] = path[pos2], path[pos1]
    return sol


def insert_mutation(solution: Solution) -> Solution:
    """Wyjmij element i wstaw w losowe miejsce"""
    sol = solution.copy()
    _, path = _pick_path(sol)

    if len(path) < 2:
        return sol

    remove_pos = random.randint(0, len(path) - 1)
    element = path.pop(remove_pos)
    insert_pos = random.randint(0, len(path))
    path.insert(insert_pos, element)
    return sol


def invert_mutation(solution: Solution) -> Solution:
    """Odwróc losowy segment ścieżki"""
    sol = solution.copy()
    _, path = _pick_path(sol)

    if len(path) < 2:
        return sol

    cut1, cut2 = sorted(random.sample(range(len(path) + 1), 2))
    path[cut1:cut2] = list(reversed(path[cut1:cut2]))
    return sol


#--------Mutacje między ścieżkami------------------------------


def transfer_mutation(solution: Solution) -> Solution:
    """PRzenieś region z jednego drona do drugiego"""

    if solution.num_uavs < 2:
        return solution

    sol = solution.copy()

    source_id = random.randint(0, sol.num_uavs - 1)
    dest_id = random.choice([i for i in range(sol.num_uavs) if i != source_id])

    source = sol.paths[source_id]
    dest = sol.paths[dest_id]

    if len(source) < 1:
        return sol

    element = source.pop(random.randint(0, len(source) - 1))
    dest.insert(random.randint(0, len(dest)), element)

    return sol


def exchange_mutation(solution: Solution) -> Solution:
    """Zamień regiony między dwoma dronami"""
    if solution.num_uavs < 2:
        return solution

    sol = solution.copy()

    uav1 = random.randint(0, sol.num_uavs - 1)
    uav2 = random.choice([i for i in range(sol.num_uavs) if i != uav1])

    path1 = sol.paths[uav1]
    path2 = sol.paths[uav2]

    if len(path1) < 1 or len(path2) < 1:
        return sol

    pos1 = random.randint(0, len(path1) - 1)
    pos2 = random.randint(0, len(path2) - 1)
    path1[pos1], path2[pos2] = path2[pos2], path1[pos1]
    return sol


#--------Dispatcher-----------


def mutate(solution: Solution, test_case: TestCase, mutation_rate: float = 0.1) -> Solution:
    if random.random() > mutation_rate:
        return solution

    mutated = random.choices(
        [invert_mutation, swap_mutation, transfer_mutation, insert_mutation, exchange_mutation],
        weights=[0.35, 0.25, 0.20, 0.15, 0.05],
    )[0](solution)

    if not mutated.validate(test_case):
        return solution

    return mutated