"""Sprint 2 · Pasos 1-3: extracción de TLA, cobertura y revisión de atípicos.

Entrada: data/raw/BD_2023.xlsx y BD_2024.xlsx. Salida: CSV en data/processed/.
Uso (desde la raíz del repositorio): python src/01_preparacion.py
"""
import pandas as pd, numpy as np
from pathlib import Path
RAIZ=Path(__file__).resolve().parents[1]
UP=RAIZ/'data'/'raw'; OUT=RAIZ/'data'/'processed'
OUT.mkdir(parents=True,exist_ok=True)
VARS=['O3','PM10','PM2.5','WS','WD','RH','ET','IT','PP']
MESES=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

# ---------- PASO 1: extraer TLA y unificar ----------
frames=[]
for y in (2023,2024):
    raw=pd.read_excel(UP/f'BD_{y}.xlsx',sheet_name='Data')
    raw.columns=[c.strip().upper() for c in raw.columns]          # 'dia ' -> 'DIA'
    t=raw[raw.STATION=='TLA'].copy()
    t['fecha_hora']=pd.to_datetime(t['DATE'])
    for c in VARS: t[c]=pd.to_numeric(t[c],errors='coerce')
    # malla horaria completa del año
    malla=pd.date_range(f'{y}-01-01',f'{y}-12-31 23:00',freq='h',name='fecha_hora')
    assert t.fecha_hora.is_unique, 'hay duplicados'
    t=t.set_index('fecha_hora')[VARS].reindex(malla).reset_index()
    t['anio']=y; frames.append(t)
    print(y,'horas en malla:',len(malla),'| horas que venían en el archivo:',(raw.STATION=='TLA').sum())
d=pd.concat(frames,ignore_index=True)
d['mes']=d.fecha_hora.dt.month
d.to_csv(OUT/'tla_horario_2023_2024.csv',index=False,encoding='utf-8-sig')

# ---------- PASO 2: cobertura por mes y variable ----------
cov=(d.groupby(['anio','mes'])[VARS].count()/d.groupby(['anio','mes']).size().values[:,None]*100).round(0)
cov.to_csv(OUT/'cobertura_mensual.csv',encoding='utf-8-sig')
for y in (2023,2024):
    c=cov.loc[y].copy(); c.index=MESES
    print(f'\nCobertura % {y}'); print(c[['O3','PM10','PM2.5','WS','WD','RH','PP']].astype(int).T.to_string())

# ---------- PASO 3: revisión de atípicos (se marca, NO se elimina) ----------
flags=[]
def add(df,tipo,var,desc):
    for _,r in df.iterrows():
        flags.append(dict(fecha_hora=r.fecha_hora,variable=var,valor=r[var],tipo=tipo,detalle=desc))
for var in ['PM10','PM2.5','O3','WS']:
    s=d[var]
    # a) pico aislado: >4x la mediana de las 6 horas vecinas (3 antes, 3 después) y > percentil 99
    vec=pd.concat([s.shift(k) for k in (-3,-2,-1,1,2,3)],axis=1).median(axis=1)
    p99=s.quantile(.99)
    m=(s>4*vec)&(s>p99)&vec.notna()
    add(d[m],'pico_aislado',var,'>4x mediana de vecinas y >P99')
    # b) valores repetidos: >=8 horas consecutivas idénticas (posible sensor atorado)
    run=(s!=s.shift()).cumsum(); n=s.groupby(run).transform('size')
    m=(n>=8)&s.notna()&(s>0)
    if m.any():
        g=d[m].groupby(run[m])
        for _,gg in g: flags.append(dict(fecha_hora=gg.fecha_hora.iloc[0],variable=var,valor=gg[var].iloc[0],tipo='racha_constante',detalle=f'{len(gg)} horas iguales'))
# c) inconsistencia física: PM2.5 > PM10
m=(d['PM2.5']>d['PM10'])
add(d[m],'PM2.5>PM10','PM2.5','PM2.5 mayor que PM10 en la misma hora')
# d) fuera de rango físico
for var,lo,hi in [('RH',0,100),('WD',0,360),('O3',0,0.6),('PM10',0,1000),('PM2.5',0,1000),('WS',0,40)]:
    m=(d[var]<lo)|(d[var]>hi); add(d[m],'fuera_de_rango',var,f'fuera de [{lo},{hi}]')
F=pd.DataFrame(flags); F['anio']=F.fecha_hora.dt.year
F.to_csv(OUT/'atipicos_marcados.csv',index=False,encoding='utf-8-sig')
print('\nMarcas por tipo/variable/año:'); print(F.groupby(['tipo','variable','anio']).size().unstack(fill_value=0).to_string())

# resumen de extremos de PM por año (top 8 horas) para revisar si son eventos reales
for y in (2023,2024):
    print(f'\nTop PM10 {y}'); print(d[d.anio==y].nlargest(8,'PM10')[['fecha_hora','PM10','PM2.5','WS','PP']].to_string(index=False))
# ¿los extremos se acompañan por PM2.5 alto y persisten varias horas? (señal de evento real)
ev=d[d.PM10>=d.PM10.quantile(.999)].copy()
print('\nUmbral P99.9 PM10:',d.PM10.quantile(.999))
ev['dia']=ev.fecha_hora.dt.date
print(ev.groupby('dia').agg(horas=('PM10','size'),max_pm10=('PM10','max'),max_pm25=('PM2.5','max')).to_string())
