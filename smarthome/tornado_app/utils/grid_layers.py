"""
Utilitaires pour gérer la grille en couches (layered grid system).
Permet le chevauchement de pièces, capteurs et équipements.
"""


def is_legacy_grid(grid):
    """Vérifie si la grille est au format legacy (tableau 2D d'entiers)."""
    if not grid or not isinstance(grid, list):
        return False
    if not grid[0] or not isinstance(grid[0], list):
        return False
    # Legacy: premier élément est un entier
    return isinstance(grid[0][0], int)


def migrate_grid_to_layers(grid):
    """
    Migre une grille legacy vers le format en couches.

    Args:
        grid: Grille au format legacy [[int, int, ...], ...]

    Returns:
        Grille au format couches [[{base, sensors, equipments}, ...], ...]
    """
    if not is_legacy_grid(grid):
        return grid  # Déjà au bon format

    layered_grid = []
    for row in grid:
        layered_row = []
        for cell_value in row:
            layered_row.append({"base": cell_value, "sensors": [], "equipments": []})
        layered_grid.append(layered_row)

    return layered_grid


def get_cell_base(grid, row, col):
    """Obtenir la valeur de base d'une cellule (pièce/mur/vide)."""
    if is_legacy_grid(grid):
        return grid[row][col]
    return grid[row][col].get("base", 0)


def set_cell_base(grid, row, col, value):
    """Définir la valeur de base d'une cellule."""
    if is_legacy_grid(grid):
        grid[row][col] = value
    else:
        grid[row][col]["base"] = value


def add_sensor_to_cell(grid, row, col, sensor_id):
    """Ajouter un capteur à une cellule."""
    if is_legacy_grid(grid):
        grid = migrate_grid_to_layers(grid)

    if sensor_id not in grid[row][col]["sensors"]:
        grid[row][col]["sensors"].append(sensor_id)

    return grid


def remove_sensor_from_cell(grid, row, col, sensor_id):
    """Retirer un capteur d'une cellule."""
    if is_legacy_grid(grid):
        return grid

    if sensor_id in grid[row][col]["sensors"]:
        grid[row][col]["sensors"].remove(sensor_id)

    return grid


def add_equipment_to_cell(grid, row, col, equipment_id):
    """Ajouter un équipement à une cellule."""
    if is_legacy_grid(grid):
        grid = migrate_grid_to_layers(grid)

    if equipment_id not in grid[row][col]["equipments"]:
        grid[row][col]["equipments"].append(equipment_id)

    return grid


def remove_equipment_from_cell(grid, row, col, equipment_id):
    """Retirer un équipement d'une cellule."""
    if is_legacy_grid(grid):
        return grid

    if equipment_id in grid[row][col]["equipments"]:
        grid[row][col]["equipments"].remove(equipment_id)

    return grid


def get_sensor_coverage(grid, sensor_id):
    """
    Obtenir toutes les cellules couvertes par un capteur.

    Returns:
        List[tuple]: Liste de (row, col) couverts par le capteur
    """
    if is_legacy_grid(grid):
        return []

    coverage = []
    for row_idx, row in enumerate(grid):
        for col_idx, cell in enumerate(row):
            if sensor_id in cell.get("sensors", []):
                coverage.append((row_idx, col_idx))

    return coverage


def clear_sensor_from_grid(grid, sensor_id):
    """Retirer complètement un capteur de toute la grille."""
    if is_legacy_grid(grid):
        return grid

    for row in grid:
        for cell in row:
            if sensor_id in cell.get("sensors", []):
                cell["sensors"].remove(sensor_id)

    return grid


def clear_equipment_from_grid(grid, equipment_id):
    """Retirer complètement un équipement de toute la grille."""
    if is_legacy_grid(grid):
        return grid

    for row in grid:
        for cell in row:
            if equipment_id in cell.get("equipments", []):
                cell["equipments"].remove(equipment_id)

    return grid


def paint_sensor_area(grid, sensor_id, cells):
    """
    Peindre une zone pour un capteur (étendre sa portée).

    Args:
        grid: La grille
        sensor_id: ID du capteur
        cells: Liste de tuples (row, col) à peindre
    """
    if is_legacy_grid(grid):
        grid = migrate_grid_to_layers(grid)

    for row, col in cells:
        add_sensor_to_cell(grid, row, col, sensor_id)

    return grid


def get_cell_info(grid, row, col):
    """
    Obtenir toutes les informations d'une cellule.

    Returns:
        dict: {
            "base": int,
            "sensors": List[int],
            "equipments": List[int]
        }
    """
    if is_legacy_grid(grid):
        return {"base": grid[row][col], "sensors": [], "equipments": []}

    return grid[row][col]


def simplify_grid_for_export(grid):
    """
    Simplifie la grille pour l'export (retire les listes vides).
    """
    if is_legacy_grid(grid):
        return grid

    simplified = []
    for row in grid:
        simplified_row = []
        for cell in row:
            # Ne garder que les données non vides
            simple_cell = {"base": cell.get("base", 0)}

            if cell.get("sensors"):
                simple_cell["sensors"] = cell["sensors"]
            if cell.get("equipments"):
                simple_cell["equipments"] = cell["equipments"]

            simplified_row.append(simple_cell)
        simplified.append(simplified_row)

    return simplified
