"""Gubernaturas (y Jefatura CDMX) concurrentes con la elección federal, por clave INE de entidad.
Procedencia: 2027 -> Expansión/UnoTV (sep-2026, 17 estados); 2024 -> INE/CNN (8 + CDMX); 2021 -> INE (15); 2009-2018 -> ciclo sexenal,
SIN verificar contra INE por estado (la búsqueda solo confirmó parcialmente 2009/2015). Verificar antes de publicar."""
GOB = {
    2009: {4, 6, 19, 22, 24, 26},
    2012: {7, 9, 11, 14, 17, 27, 31},
    2015: {3, 4, 6, 12, 16, 19, 22, 24, 26},
    2018: {7, 9, 11, 14, 17, 21, 27, 30, 31},
    2021: {2, 3, 4, 6, 8, 12, 16, 18, 19, 22, 24, 25, 26, 29, 32},
    2024: {7, 9, 11, 14, 17, 21, 27, 30, 31},
    2027: {1, 2, 3, 4, 6, 8, 12, 16, 18, 19, 22, 23, 24, 25, 26, 29, 32},
}
