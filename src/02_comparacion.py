"""Sprint 2 · Paso 6: comparación 2024 vs. 2023 (gráficas y tabla mensual).

Entrada: data/processed/dias_procesados_2023_2024.csv y horas_procesadas_2023_2024.csv
Salida:  figures/*.png y data/processed/tabla_comparacion_mensual.csv
Uso (desde la raíz del repositorio): python src/02_comparacion.py

Criterios: un mes es comparable para una variable si, en ambos años, al menos el 75 % de sus
días tiene indicador válido. Los meses que no cumplen se muestran en gris, no se ocultan.
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

RAIZ = Path(__file__).resolve().parents[1]
PROC, FIG = RAIZ / 'data' / 'processed', RAIZ / 'figures'; FIG.mkdir(exist_ok=True)
CATS = ["Buena", "Aceptable", "Mala", "Muy mala", "Extremadamente mala"]
COL = ["#54aa66", "#f1c74b", "#ef9448", "#d65d57", "#9170aa"]; GRIS = "#d3d7db"
MES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
C23, C24 = '#6c8ea4', '#d9822b'
UMBRAL = 75
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'axes.titlesize': 10})

d = pd.read_csv(PROC / 'dias_procesados_2023_2024.csv', parse_dates=['fecha'])
h = pd.read_csv(PROC / 'horas_procesadas_2023_2024.csv', parse_dates=['fecha_hora'])
h['anio'] = h.fecha_hora.dt.year; h['mes'] = h.fecha_hora.dt.month; h['hora'] = h.fecha_hora.dt.hour
d['pm10_ok'] = d.PM10_media_d.notna(); d['pm25_ok'] = d['PM2.5_media_d'].notna(); d['o3_ok'] = d.O3_max_h.notna()
d['ge2'] = d.n_contam_d >= 2

# ---------- tabla mensual ----------
g = d.groupby(['anio', 'mes'])
T = pd.DataFrame({
    'dias': g.size(), 'cov_PM10': g.pm10_ok.mean() * 100, 'cov_PM25': g.pm25_ok.mean() * 100, 'cov_O3': g.o3_ok.mean() * 100,
    'cov_2contam': g.ge2.mean() * 100,
    'PM10_media': g.PM10_media_d.mean(), 'PM10_mediana': g.PM10_media_d.median(),
    'PM25_media': g['PM2.5_media_d'].mean(), 'O3_media_max_diario': g.O3_max_h.mean(),
}).reset_index()
T['pct_PM10_mala_o_peor'] = d[d.pm10_ok].groupby(['anio', 'mes']).PM10_cat_d.apply(lambda s: (s >= 2).mean() * 100).reindex(
    pd.MultiIndex.from_frame(T[['anio', 'mes']])).values
T['pct_global_mala_o_peor'] = d[d.ge2].groupby(['anio', 'mes']).categoria_d_id.apply(lambda s: (s >= 2).mean() * 100).reindex(
    pd.MultiIndex.from_frame(T[['anio', 'mes']])).values
def comparable(col):
    p = T.pivot(index='mes', columns='anio', values=col); return [m for m in p.index if (p.loc[m] >= UMBRAL).all()]
M_PM10, M_CAT = comparable('cov_PM10'), comparable('cov_2contam')
T['comparable_PM10'] = T.mes.isin(M_PM10); T['comparable_categoria_global'] = T.mes.isin(M_CAT)
T.round(2).to_csv(PROC / 'tabla_comparacion_mensual.csv', index=False, encoding='utf-8-sig')
print('Meses comparables PM10:', [MES[m-1] for m in M_PM10]); print('Meses comparables categoría (>=2 contam.):', [MES[m-1] for m in M_CAT])

def guardar(fig, nombre): fig.savefig(FIG / nombre, dpi=170, bbox_inches='tight'); plt.close(fig)

# ---------- F1: cobertura ----------
fig, axs = plt.subplots(1, 2, figsize=(12, 3.3), sharey=True)
filas = [('cov_PM10', 'PM₁₀'), ('cov_PM25', 'PM₂.₅'), ('cov_O3', 'O₃'), ('cov_2contam', '≥ 2 contaminantes')]
for ax, y in zip(axs, (2023, 2024)):
    z = np.array([[T[(T.anio == y) & (T.mes == m)][c].iloc[0] for m in range(1, 13)] for c, _ in filas])
    ax.imshow(z, cmap='Blues', vmin=0, vmax=100, aspect='auto')
    for i in range(4):
        for j in range(12):
            ok = z[i, j] >= UMBRAL
            ax.text(j, i, f'{z[i, j]:.0f}', ha='center', va='center', fontsize=8, color='white' if z[i, j] > 55 else '#333', fontweight='bold' if ok else 'normal')
            if ok: ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False, ec='#1b3a4b', lw=1.4))
    ax.set_xticks(range(12), MES); ax.set_yticks(range(4), [n for _, n in filas]); ax.set_title(str(y))
fig.suptitle('¿Qué tan comparable es cada variable? % de días con indicador válido (recuadro = ≥ 75 %)', fontweight='bold', y=1.04)
guardar(fig, 'F1_cobertura.png')

# ---------- F2: mapa de calor mes × año ----------
fig, axs = plt.subplots(2, 1, figsize=(11, 4.6))
for ax, (col, cov, titulo, cmap, fmt) in zip(axs, [
        ('PM10_media', 'cov_PM10', 'PM₁₀: media mensual de promedios diarios (µg/m³)', 'YlOrRd', '{:.0f}'),
        ('pct_PM10_mala_o_peor', 'cov_PM10', 'PM₁₀: % de días en categoría Mala o peor', 'YlOrRd', '{:.0f}')]):
    z = np.array([[T[(T.anio == y) & (T.mes == m)][col].iloc[0] if T[(T.anio == y) & (T.mes == m)][cov].iloc[0] >= UMBRAL else np.nan
                   for m in range(1, 13)] for y in (2023, 2024)])
    vmax = np.nanmax(z); cm = plt.get_cmap(cmap).copy(); cm.set_bad(GRIS)
    ax.imshow(np.ma.masked_invalid(z), cmap=cm, vmin=0, vmax=vmax, aspect='auto')
    for i in range(2):
        for j in range(12):
            ax.text(j, i, 'sin datos\nsuficientes' if np.isnan(z[i, j]) else fmt.format(z[i, j]), ha='center', va='center',
                    fontsize=6.5 if np.isnan(z[i, j]) else 9, color='#666' if np.isnan(z[i, j]) else ('white' if z[i, j] > vmax * .62 else '#222'))
    ax.set_xticks(range(12), MES); ax.set_yticks([0, 1], ['2023', '2024']); ax.set_title(titulo, loc='left')
    for s in ax.spines.values(): s.set_visible(False)
fig.tight_layout(); guardar(fig, 'F2_mapa_calor_mensual_PM10.png')

# ---------- F3: distribución de categorías ----------
def dist(df, col):
    return {y: [(df[(df.anio == y)][col] == k).sum() for k in range(5)] for y in (2023, 2024)}
fig = plt.figure(figsize=(12, 7.2)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.35], hspace=.5, wspace=.4)
for pos, (titulo, df, col, sub) in enumerate([
        ('PM₁₀ solamente · meses comparables', d[d.pm10_ok & d.mes.isin(M_PM10)], 'PM10_cat_d', ', '.join(MES[m-1] for m in M_PM10)),
        ('Categoría global (parcial) · meses con ≥ 2 contaminantes', d[d.ge2 & d.mes.isin(M_CAT)], 'categoria_d_id', ', '.join(MES[m-1] for m in M_CAT))]):
    ax = fig.add_subplot(gs[0, pos]); D = dist(df, col)
    etiquetas = []
    for r, y in enumerate((2023, 2024)):
        n = sum(D[y]); izq = 0; etiquetas.append(f'{y}\n(n={n} días)')
        for k in range(5):
            w = D[y][k] / n * 100 if n else 0
            ax.barh(r, w, left=izq, color=COL[k], ec='white')
            if w >= 6: ax.text(izq + w / 2, r, f'{w:.0f}%', ha='center', va='center', fontsize=8.5, fontweight='bold')
            izq += w
    ax.set_yticks([0, 1], etiquetas); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel('% de días'); ax.set_title(titulo + f'\n({sub})', fontsize=9, loc='left')
ax = fig.add_subplot(gs[1, :]); w = .38
for y, off in ((2023, -w / 2), (2024, w / 2)):
    for m in range(1, 13):
        s = d[(d.anio == y) & (d.mes == m) & d.pm10_ok].PM10_cat_d; ok = T[(T.anio == y) & (T.mes == m)].cov_PM10.iloc[0] >= UMBRAL
        if not ok or len(s) == 0: ax.bar(m + off, 100, w, color=GRIS, hatch='//', ec='white'); continue
        base = 0
        for k in range(5):
            p = (s == k).mean() * 100; ax.bar(m + off, p, w, bottom=base, color=COL[k], ec='white', lw=.5); base += p
    for m in range(1, 13): ax.text(m + off, -5, str(y)[2:], ha='center', fontsize=6.5, color=C23 if y == 2023 else C24)
ax.set_xticks(range(1, 13), MES); ax.tick_params(axis='x', pad=12); ax.set_ylabel('% de días con PM₁₀ válido'); ax.set_ylim(0, 100)
ax.set_title('Categoría diaria según PM₁₀ por mes (barra izquierda 2023, derecha 2024; gris = cobertura < 75 %)', loc='left')
fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(COL[:4], CATS[:4])] + [Patch(facecolor=GRIS, hatch='//', ec='white', label='Sin datos suficientes')],
           loc='lower center', ncol=5, frameon=False, bbox_to_anchor=(.5, -.03))
guardar(fig, 'F3_distribucion_categorias.png')

# ---------- F4: concentraciones PM10 por mes ----------
fig, ax = plt.subplots(figsize=(12, 4.6))
for y, off, c in ((2023, -.2, C23), (2024, .2, C24)):
    data, pos = [], []
    for m in range(1, 13):
        if T[(T.anio == y) & (T.mes == m)].cov_PM10.iloc[0] >= UMBRAL: data.append(d[(d.anio == y) & (d.mes == m)].PM10_media_d.dropna().values); pos.append(m + off)
    bp = ax.boxplot(data, positions=pos, widths=.32, patch_artist=True, showfliers=True, flierprops=dict(marker='.', ms=3, alpha=.5, mfc=c, mec=c),
                    medianprops=dict(color='#222', lw=1.5), boxprops=dict(lw=.8), whiskerprops=dict(lw=.8))
    for b in bp['boxes']: b.set_facecolor(c); b.set_alpha(.75)
for m in range(1, 13):
    if m not in M_PM10:
        for y, off in ((2023, -.2), (2024, .2)):
            if T[(T.anio == y) & (T.mes == m)].cov_PM10.iloc[0] < UMBRAL: ax.text(m + off, 3, f'{str(y)[2:]}:\ncob.\n<75%', ha='center', fontsize=5.8, color='#777')
for v, t in ((45, 'Buena ≤45'), (60, 'Aceptable ≤60')): ax.axhline(v, color='#888', ls='--', lw=.8); ax.text(.42, v + 1, t, fontsize=7, va='bottom', ha='left', color='#555')
ax.set_xticks(range(1, 13), MES); ax.set_xlim(.4, 12.7); ax.set_ylabel('PM₁₀, promedio diario (µg/m³)')
ax.set_title('¿Cambiaron las concentraciones de PM₁₀? Distribución diaria por mes', loc='left')
ax.legend(handles=[Patch(color=C23, label='2023'), Patch(color=C24, label='2024')], frameon=False, loc='upper right', bbox_to_anchor=(1, .93))
guardar(fig, 'F4_boxplot_PM10_mensual.png')

# ---------- F5: serie diaria y episodios ----------
fig, axs = plt.subplots(2, 1, figsize=(12, 6.2), sharey=True)
top = {}
for ax, y, c in zip(axs, (2023, 2024), (C23, C24)):
    s = d[d.anio == y].set_index('fecha').PM10_media_d
    ax.axvspan(pd.Timestamp(f'{y}-01-01'), pd.Timestamp(f'{y}-01-01'), color=GRIS)
    for f in s.index[s.isna()]: ax.axvspan(f, f + pd.Timedelta(days=1), color=GRIS, lw=0, alpha=.9)
    ax.plot(s.index, s.values, color=c, lw=1); ax.fill_between(s.index, 0, s.values, color=c, alpha=.25)
    ax.axhline(60, color='#888', ls='--', lw=.8); ax.axhline(132, color='#d65d57', ls='--', lw=.8)
    top[y] = s.nlargest(3)
    for (f, v), off in zip(top[y].items(), [(0, 14), (-34, 8), (34, 8)]):
        ax.annotate(f'{f:%d-%b}\n{v:.0f}', (f, v), xytext=off, textcoords='offset points', ha='center', fontsize=7.5, arrowprops=dict(arrowstyle='-', lw=.5))
    ax.set_title(f'{y}', loc='right'); ax.set_ylabel('PM₁₀ diario (µg/m³)'); ax.set_ylim(0, 240)
axs[1].text(.995, .93, 'Gris = día sin PM₁₀ diario válido · línea gris: 60 (límite Aceptable) · roja: 132 (límite Mala)', transform=axs[1].transAxes, ha='right', fontsize=7.5, color='#555')
fig.suptitle('¿Hubo periodos o episodios atípicos? PM₁₀ promedio diario, con los 3 días más altos de cada año', fontweight='bold', y=1.0)
fig.tight_layout(); guardar(fig, 'F5_serie_diaria_episodios.png')

# ---------- F6: contaminante dominante (solo días con los 3 contaminantes) ----------
d3 = d[d.n_contam_d == 3]; cnt = d3.groupby(['anio', 'mes']).size().unstack(0).fillna(0)
M_DOM = [m for m in cnt.index if (cnt.loc[m] >= 10).all()]
dd = d3[d3.mes.isin(M_DOM)]
fig, ax = plt.subplots(figsize=(7.5, 3.6)); pols = ['PM10', 'PM2.5', 'O3']; names = ['PM₁₀', 'PM₂.₅', 'O₃']; colp = ['#d87039', '#8048a2', '#2c7893']
res = {}
for y, off in ((2023, -.2), (2024, .2)):
    s = dd[dd.anio == y]; n = len(s); vals = [s.dominantes_d.str.split(', ').map(lambda it, p=p: p in it).sum() for p in pols]; res[y] = (n, vals)
    b = ax.bar(np.arange(3) + off, [v / n * 100 for v in vals], .38, color=C23 if y == 2023 else C24, label=f'{y} (n={n} días)')
    for xi, v in zip(np.arange(3) + off, vals): ax.text(xi, v / n * 100 + 1.5, f'{v}', ha='center', fontsize=8)
ax.set_xticks(range(3), names); ax.set_ylabel('% de días en que fue responsable'); ax.set_ylim(0, 105); ax.legend(frameon=False)
ax.set_title(f'¿Qué contaminante pesa más? Solo días con los 3 contaminantes\n(meses: {", ".join(MES[m-1] for m in M_DOM)}; los empates cuentan para ambos)', loc='left', fontsize=9)
guardar(fig, 'F6_contaminante_dominante.png')

# ---------- F7: relaciones con variables meteorológicas ----------
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.4), gridspec_kw={'width_ratios': [1, 1.15]})
ax = axs[0]
for y, c in ((2023, C23), (2024, C24)):
    s = d[(d.anio == y)].dropna(subset=['PM10_media_d', 'WS_media_d']); ax.scatter(s.WS_media_d, s.PM10_media_d, s=9, alpha=.45, color=c, label=f'{y} (n={len(s)})')
ax.set_xlabel('Velocidad del viento, promedio diario (m/s)'); ax.set_ylabel('PM₁₀ diario (µg/m³)'); ax.legend(frameon=False); ax.set_title('PM₁₀ vs. viento', loc='left')
ax = axs[1]
vars_ = [('WS_media_d', 'Viento (m/s)'), ('RH_media_d', 'Humedad (%)'), ('PP_suma_d', 'Lluvia (mm)')]
cols = [(p, y) for p in ('PM10_media_d', 'PM2.5_media_d', 'O3_max_h') for y in (2023, 2024)]
R = np.full((3, 6), np.nan); N = np.zeros((3, 6), int)
for j, (p, y) in enumerate(cols):
    for i, (v, _) in enumerate(vars_):
        if v == 'PP_suma_d' and y == 2023: continue            # lluvia 2023 no confiable
        s = d[d.anio == y][[p, v]].dropna(); N[i, j] = len(s)
        if len(s) >= 30 and s[v].nunique() > 1: R[i, j] = s.corr(method='spearman').iloc[0, 1]
cm = plt.get_cmap('RdBu_r').copy(); cm.set_bad(GRIS)
ax.imshow(np.ma.masked_invalid(R), cmap=cm, vmin=-.8, vmax=.8, aspect='auto')
for i in range(3):
    for j in range(6):
        ax.text(j, i, ('excluida\n(sensor no\nconfiable)' if (i == 2 and cols[j][1] == 2023) else 'n<30 o\nno usable') if np.isnan(R[i, j]) else f'{R[i, j]:+.2f}\n(n={N[i, j]})', ha='center', va='center', fontsize=7.2 if not np.isnan(R[i, j]) else 6.3, color='#222' if np.isnan(R[i, j]) or abs(R[i, j]) < .5 else 'white')
ax.set_xticks(range(6), [f'{n}\n{y}' for n in ('PM₁₀', 'PM₂.₅', 'O₃') for y in (2023, 2024)]); ax.set_yticks(range(3), [n for _, n in vars_])
ax.set_title('Correlación de Spearman (diaria) · gris = sin base suficiente', loc='left')
for s in ax.spines.values(): s.set_visible(False)
fig.tight_layout(); guardar(fig, 'F7_relaciones_meteorologia.png')
RHO = pd.DataFrame(R, index=[n for _, n in vars_], columns=[f'{p}_{y}' for p, y in cols]); RHO.round(3).to_csv(PROC / 'correlaciones_spearman.csv', encoding='utf-8-sig')

# ---------- F8: horas relevantes (ciclo diario) ----------
M_O3 = comparable('cov_O3')
fig, axs = plt.subplots(1, 2, figsize=(12, 3.8))
for y, c in ((2023, C23), (2024, C24)):
    s = h[(h.anio == y) & h.mes.isin(M_PM10)].groupby('hora').PM10.agg(['median', lambda x: x.quantile(.25), lambda x: x.quantile(.75)])
    axs[0].plot(s.index, s['median'], color=c, lw=2, label=str(y)); axs[0].fill_between(s.index, s.iloc[:, 1], s.iloc[:, 2], color=c, alpha=.15)
    s = h[(h.anio == y) & h.mes.isin(M_O3)].groupby('hora').O3.mean() * 1000; axs[1].plot(s.index, s.values, color=c, lw=2, label=str(y))
axs[0].set_title(f'PM₁₀ por hora del día (mediana y rango intercuartil)\nmeses comparables: {", ".join(MES[m-1] for m in M_PM10)}', loc='left', fontsize=9)
axs[1].set_title(f'O₃ por hora del día (promedio, ppb)\nmeses con ≥75 % de días en ambos años: {", ".join(MES[m-1] for m in M_O3)}', loc='left', fontsize=9)
axs[1].axhline(58, color='#888', ls='--', lw=.8); axs[1].text(0, 59.5, 'límite Buena (58 ppb)', fontsize=7.5, color='#555')
for a, yl in zip(axs, ('PM₁₀ (µg/m³)', 'O₃ (ppb)')): a.set_xlabel('Hora local del archivo'); a.set_ylabel(yl); a.set_xticks(range(0, 24, 3)); a.legend(frameon=False)
fig.tight_layout(); guardar(fig, 'F8_ciclo_horario.png')

# ---------- cifras clave para el reporte ----------
print('\n== PM10, meses comparables ==')
a = T[T.mes.isin(M_PM10)].pivot(index='mes', columns='anio', values=['PM10_media', 'pct_PM10_mala_o_peor']).round(1); a.index = [MES[m-1] for m in a.index]; print(a.to_string())
tot = d[d.mes.isin(M_PM10) & d.pm10_ok].groupby('anio').PM10_media_d.agg(['mean', 'median', 'count']).round(1); print(tot.to_string())
print('Top días PM10:', {y: [(f'{f:%Y-%m-%d}', round(v)) for f, v in top[y].items()] for y in top})
print('Dominancia (3 contam.):', res, 'meses', [MES[m-1] for m in M_DOM])
print('\nSpearman:'); print(RHO.round(2).to_string())
print('\nDist PM10 (meses comp):', {y: dist(d[d.pm10_ok & d.mes.isin(M_PM10)], 'PM10_cat_d')[y] for y in (2023, 2024)})
print('Dist global (>=2, meses comp):', dist(d[d.ge2 & d.mes.isin(M_CAT)], 'categoria_d_id'))
