"""
Funkcje celu dla optymalizacji ścieżek UAV.

f1: Czas zakończenia misji (max czas ze wszystkich dronów)
f2: Znormalizowany współczynnik nieodkrytego obszaru
    f2 = 1 - ∫V(t)dt / (V_total * T_cut)
"""

from __future__ import annotations

from dataclasses import dataclass

from src.io.data_loader import TestCase
from src.model.individual import Solution


# Harmonogram lotu


@dataclass
class ScheduleEntry:
    """Pojedynczy punkt w harmonogramie lotu drona"""

    region: int
    arrival_time: float
    departure_time: float
    victims: int



def build_schedule(path: list[int], test_case: TestCase) -> list[ScheduleEntry]:
    """Zbuduj harmonogram lotu dla danego drona"""

    schedule = []
    current_time = 0.0

    for i, region in enumerate(path):
        if i == 0:
            arrival = test_case.get_reach_time(region)
        else:
            arrival = current_time + test_case.get_flight_time(path[i-1], region)
        
        departure = arrival + test_case.get_scan_time(region)
        victims = test_case.get_population(region)

        schedule.append(ScheduleEntry(region, arrival, departure, victims))
        current_time = departure
    
    return schedule

def build_all_schedules(solution: Solution, test_case: TestCase) -> list[list[ScheduleEntry]]:
    """Zbuduj harmonogramy dla wszystkich dronów"""

    return [build_schedule(path, test_case) for path in solution.paths]


def compute_f1(schedules: list[list[ScheduleEntry]]) -> float:
    """f1 = max departure time ze wszystkich dronów (najwolniejszy dron wyznacza czas zakonczenia misji)"""

    max_time = 0.0

    if schedules:
        for schedule in schedules:
            max_time = max(max_time, schedule[-1].departure_time)
    
    return max_time

def compute_f2(schedules: list[list[ScheduleEntry]], total_victims) -> float:
    """
    f2 = 1 - ∫₀ᵀᶜᵘᵗ V(t)dt / (V_total * T_cut)

    gdzie:
    V(t) = skumulowana liczba odkrytych poszkodowanych w chwili t
    T_cut = czas zakonczenia operacji najszybszego drona
    V_total = łączna liczba poszkodowanych na całym terenie akcji

    """
    
    completion_times = [s[-1].departure_time for s in schedules if s]

    t_cut = min(completion_times)

    # teoretyczny przypadek kiedy wszystkie ofiary zostaly znalezione od razu
    if t_cut <= 0:        
        return 1.0
    
    #nikt nie zostal odnaleziony
    if total_victims <= 0:
        return 0.0
    

    #zdarzenia odkrycia do T_cut (w tym momencie uznajemy ze ofiary zostaja odnalezione po zeskanowaniu = departure)
    events = sorted(
        (entry.departure_time, entry.victims)
        for schedule in schedules
        for entry in schedule
        if entry.victims > 0 and entry.departure_time <= t_cut
    )

    if not events:
        return 1.0

    # Całka pole pod funkcją V(t)
    integral = 0.0
    cumulative = 0
    prev_time = 0.0

    for event_time, victims in events:
        integral += cumulative * (event_time - prev_time)
        cumulative += victims
        prev_time = event_time

    #Ostatni prostokąt
    integral += cumulative * (t_cut - prev_time)

    f2  = 1.0 - integral / (total_victims * t_cut)
    return f2


# ----Ewaluacja rozwiazania----------------


def evaluate(solution: Solution, test_case: TestCase) -> tuple[float, float]:
    """
    Stworz harmonogramy i oblicz funkcje celu

    Wynik zapisywany w solution.f1 i solution.f2

    """

    schedules = build_all_schedules(solution, test_case)

    f1 = compute_f1(schedules)
    f2 = compute_f2(schedules, test_case.total_population)

    solution.f1 = f1
    solution.f2 = f2


    return f1, f2
    
