# Calidad del aire en Tlaquepaque · 2024 vs. 2023

Análisis reproducible del Índice AIRE Y SALUD (NOM-172-SEMARNAT-2023) en la estación **TLA (Tlaquepaque)**, Jalisco.
**Sprint 2:** comportamiento de 2024 y comparación con 2023.

**Equipo 4 · Pollos Asados El ING**
Integrantes: Eduardo Yoab Venegas García (líder), Jonathan Emmanuel Alcantar López y Ana Yoseline Acosta Arreola.

Sprint 1 (marzo de 2024): https://github.com/Yapower/calidad-aire-tlaquepaque-marzo-2024

## Estructura

```
data/raw/        Bases originales con todas las estaciones (BD_2023.xlsx, BD_2024.xlsx). No se modifican.
data/processed/  Resultados del procesamiento (CSV).
src/             Código: 01_preparacion.py, pipeline_aire.py y 02_comparacion.py.
figures/         Gráficas generadas.
dashboard/       Propuesta de tablero.
reports/         Reporte final en PDF.
docs/            Bitácora y decisiones metodológicas.
```

## Cómo reproducir

1. Instalar Python 3.10 o superior y las bibliotecas: `pip install -r requirements.txt`
2. Desde la raíz del repositorio, ejecutar en orden:

```
python src/01_preparacion.py     # extrae TLA, tabla de cobertura y marcas de atípicos
python src/pipeline_aire.py      # indicadores y categorías de la NOM-172 (horas, días, meses)
python src/02_comparacion.py     # gráficas 2024 vs. 2023 (figures/) y tabla mensual comparable
```

## Archivos de salida (data/processed/)

| Archivo | Contenido |
|---|---|
| `tla_horario_2023_2024.csv` | Serie horaria de TLA (17,544 horas), sin modificar datos |
| `cobertura_mensual.csv` | % de horas con dato por mes y variable |
| `atipicos_marcados.csv` | Valores marcados para revisión (no eliminados) |
| `horas_procesadas_2023_2024.csv` | Indicador y categoría horaria |
| `dias_procesados_2023_2024.csv` | Indicador, categoría y contaminante dominante por día (731 días) |
| `resumen_mensual_2023_2024.csv` | Días por categoría y cobertura por mes |
| `tabla_comparacion_mensual.csv` | Cobertura, medias y % de días Mala o peor por mes y año; marca de meses comparables |
| `correlaciones_spearman.csv` | Correlaciones diarias de contaminantes con viento, humedad y lluvia |

## Criterios principales

- No se rellenan ni interpolan datos faltantes; los atípicos se marcan, no se eliminan.
- Se usan las mismas bandas de la NOM-172 del Sprint 1 en ambos años (en 2023 es una aplicación retrospectiva).
- La categoría de un día con menos de tres contaminantes es **parcial**.
- Un mes es comparable para una variable si, en ambos años, al menos 75 % de sus días tiene indicador válido; los demás se muestran en gris.
- Detalle en `docs/decisiones_metodologicas.md`.

## Avance del Sprint 2

- [x] Extracción de TLA y unificación 2023-2024
- [x] Cobertura por mes y variable
- [x] Revisión de valores atípicos
- [x] Pipeline NOM-172 para 2023 y 2024
- [x] Comparación 2024 vs. 2023 (gráficas F1 a F6, F8)
- [x] Relación con variables meteorológicas (F7)
- [ ] Dashboard
- [ ] Reporte PDF y bitácora del líder

## Fuente de los datos

Datos históricos de la red de monitoreo de Jalisco (SEMADET): https://aire.jalisco.gob.mx/Dhistoricos
Norma: NOM-172-SEMARNAT-2023.
