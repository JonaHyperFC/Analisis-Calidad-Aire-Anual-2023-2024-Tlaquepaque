"""Pipeline Sprint 2 · Estación TLA · 2023-2024 · NOM-172-SEMARNAT-2023.

Reutiliza, sin cambiar su lógica, las funciones del Sprint 1 (rnd, classify, nowcast)
y las generaliza a cualquier periodo. Entrada: serie horaria de TLA generada por
paso1_3_preparacion.py. Salidas: horas, días y resumen mensual procesados.

Uso (desde la raíz del repositorio): python src/pipeline_aire.py
"""
from __future__ import annotations
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import numpy as np
import pandas as pd

# ---- Constantes del Sprint 1 (bandas de partículas: etapa 2024 de la NOM-172-SEMARNAT-2023) ----
CATS = ["Buena", "Aceptable", "Mala", "Muy mala", "Extremadamente mala"]
THRESH = {"PM10": [45, 60, 132, 213], "PM2.5": [15, 33, 79, 130], "O3": [.058, .090, .135, .175]}
FACTOR = {"PM10": .38, "PM2.5": .5}      # factor de ajuste al NowCast (como en el Sprint 1)
MIN_HORAS_PM_DIA = 18                      # cobertura mínima diaria de partículas (Sprint 1)
POLS = list(THRESH)

# ---- Funciones del Sprint 1 ----
def rnd(value, decimals=0):
    if pd.isna(value): return np.nan
    unit = Decimal('1').scaleb(-decimals)
    return float(Decimal(str(value)).quantize(unit, rounding=ROUND_HALF_UP))

def classify(value, pollutant):
    if pd.isna(value): return np.nan
    for i, limit in enumerate(THRESH[pollutant]):
        if value <= limit: return i
    return 4

def nowcast(values, factor):
    """Últimas 12 posiciones horarias, preservando el exponente de cada hueco."""
    if len(values) < 12: return np.nan
    a = list(values)[::-1]
    if sum(pd.notna(x) for x in a[:3]) < 2: return np.nan
    valid = [x for x in a if pd.notna(x)]
    high, low = max(valid), min(valid)
    w = 1 if high == 0 else max(.5, rnd(low / high, 2))
    weights = [w ** i for i, x in enumerate(a) if pd.notna(x)]
    return rnd(factor * sum(x * w ** i for i, x in enumerate(a) if pd.notna(x)) / sum(weights))

# ---- Generalización ----
def procesar_horas(h: pd.DataFrame) -> pd.DataFrame:
    """Indicador y categoría horaria sobre la serie continua (el NowCast cruza el cambio de año)."""
    h = h.sort_values('fecha_hora').reset_index(drop=True).copy()
    for pol, col in [('PM10', 'PM10'), ('PM2.5', 'PM2.5')]:
        v = h[col].tolist()
        h[pol + '_indicador_h'] = [nowcast(v[max(0, i - 11):i + 1], FACTOR[pol]) for i in range(len(v))]
    h['O3_indicador_h'] = h['O3'].map(lambda x: rnd(x, 3))
    for pol in POLS: h[pol + '_cat_h'] = h[pol + '_indicador_h'].map(lambda x, p=pol: classify(x, p))
    cc = [p + '_cat_h' for p in POLS]
    h['categoria_h_id'] = h[cc].max(axis=1)
    h['categoria_h'] = h.categoria_h_id.map(lambda x: CATS[int(x)] if pd.notna(x) else 'Sin información')
    h['n_contam_h'] = h[cc].notna().sum(axis=1)
    h['dominantes_h'] = h.apply(lambda r: ', '.join(p for p in POLS if pd.notna(r[p + '_cat_h']) and r[p + '_cat_h'] == r.categoria_h_id), axis=1)
    h['fecha'] = h.fecha_hora.dt.date
    return h

def procesar_dias(h: pd.DataFrame) -> pd.DataFrame:
    rec = []
    for fecha, g in h.groupby('fecha'):
        r = {'fecha': str(fecha)}
        for pol in ('PM10', 'PM2.5'):
            r[pol + '_horas_validas'] = int(g[pol].count())
            r[pol + '_media_d'] = rnd(g[pol].mean()) if g[pol].count() >= MIN_HORAS_PM_DIA else np.nan
        r['O3_horas_validas'] = int(g['O3'].count())
        r['O3_max_h'] = rnd(g['O3'].max(), 3) if g['O3'].count() else np.nan
        r['PM10_indicador_d'] = r['PM10_media_d']; r['PM2.5_indicador_d'] = r['PM2.5_media_d']; r['O3_indicador_d'] = r['O3_max_h']
        for pol in POLS: r[pol + '_cat_d'] = classify(r[pol + '_indicador_d'], pol)
        valid = [r[p + '_cat_d'] for p in POLS if pd.notna(r[p + '_cat_d'])]
        r['categoria_d_id'] = max(valid) if valid else np.nan
        r['categoria_d'] = CATS[int(max(valid))] if valid else 'Sin información'
        r['dominantes_d'] = ', '.join(p for p in POLS if pd.notna(r[p + '_cat_d']) and r[p + '_cat_d'] == r['categoria_d_id'])
        r['n_contam_d'] = len(valid)
        r['cobertura_3_contaminantes'] = len(valid) == 3
        # variables meteorológicas diarias (para el paso de relaciones; no intervienen en la NOM)
        r['WS_media_d'] = g['WS'].mean() if g['WS'].count() >= 18 else np.nan
        r['PP_suma_d'] = g['PP'].sum() if g['PP'].count() >= 18 else np.nan
        r['RH_media_d'] = g['RH'].mean() if g['RH'].count() >= 18 else np.nan
        rec.append(r)
    d = pd.DataFrame(rec)
    d['fecha'] = pd.to_datetime(d.fecha); d['anio'] = d.fecha.dt.year; d['mes'] = d.fecha.dt.month
    return d

def resumen_mensual(d: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for (y, m), g in d.groupby(['anio', 'mes']):
        r = {'anio': y, 'mes': m, 'dias_mes': len(g), 'dias_con_categoria': int((g.categoria_d != 'Sin información').sum()),
             'dias_3_contaminantes': int(g.cobertura_3_contaminantes.sum())}
        for c in CATS + ['Sin información']: r['dias_' + c] = int((g.categoria_d == c).sum())
        for p in POLS: r['dias_dom_' + p] = int(g.dominantes_d.str.split(', ').map(lambda it, p=p: p in it).sum())
        for p, c in [('PM10', 'PM10_media_d'), ('PM2.5', 'PM2.5_media_d')]: r[p + '_media_mensual'] = g[c].mean()
        r['O3_max_mensual_ppm'] = g['O3_max_h'].max(); r['O3_media_max_diarios'] = g['O3_max_h'].mean()
        filas.append(r)
    return pd.DataFrame(filas)

def run(src: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    h = procesar_horas(pd.read_csv(src, parse_dates=['fecha_hora']))
    d = procesar_dias(h); m = resumen_mensual(d)
    h.to_csv(out / 'horas_procesadas_2023_2024.csv', index=False, encoding='utf-8-sig')
    d.to_csv(out / 'dias_procesados_2023_2024.csv', index=False, encoding='utf-8-sig')
    m.to_csv(out / 'resumen_mensual_2023_2024.csv', index=False, encoding='utf-8-sig')
    return h, d, m

if __name__ == '__main__':
    raiz = Path(__file__).resolve().parents[1]
    origen = Path(sys.argv[1]) if len(sys.argv) > 1 else raiz / 'data' / 'processed' / 'tla_horario_2023_2024.csv'
    destino = Path(sys.argv[2]) if len(sys.argv) > 2 else raiz / 'data' / 'processed'
    run(origen, destino)
