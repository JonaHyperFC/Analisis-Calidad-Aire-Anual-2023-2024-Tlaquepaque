# Decisiones metodológicas · Sprint 2

Registro de las decisiones tomadas, para que el reporte final sea consistente.

1. **Estación:** TLA (Tlaquepaque). Se filtra del archivo que trae todas las estaciones.
2. **Datos faltantes:** no se rellenan, no se interpolan y no se modifican. Una hora sin dato queda vacía.
3. **Atípicos:** se marcan en `data/processed/atipicos_marcados.csv`, no se eliminan.
4. **Bandas de la NOM-172-SEMARNAT-2023:** las mismas del Sprint 1 (etapa 2024) para ambos años. Para 2023 es una aplicación retrospectiva.
5. **Indicadores:** O3 horario; PM10 y PM2.5 con NowCast de 12 h (factor de ajuste 0.38 y 0.50 como en el Sprint 1); promedio diario de PM con mínimo de 18 horas; O3 diario = máximo horario.
6. **Días sin información:** se conservan como "Sin información" y no se cuentan en los porcentajes.
7. **Categorías parciales:** un día con menos de 3 contaminantes tiene categoría parcial (mínimo posible). Se marca en tablas y gráficas.
8. **Precipitación 2023:** no se usa; el acumulado anual (36 mm) no es plausible y parece falla del sensor.
9. **Criterio de comparabilidad:** un mes se compara si en ambos años al menos 75 % de sus días tiene indicador válido.
   - Exigir los 3 contaminantes deja a 2024 sin ningún mes comparable, por lo que se descarta.
   - Comparación principal de concentraciones: **PM10** (10 meses comparables: feb, mar, abr, jun, jul, ago, sep, oct, nov, dic).
   - Comparación de categoría global: días con **al menos 2 contaminantes** (7 meses: feb, mar, jun, jul, ago, nov, dic), marcada como parcial.
   - PM2.5 y O3 son de apoyo: su cobertura no alcanza para comparar mes por mes.
10. **Contaminante dominante:** solo se compara con días que tienen los 3 contaminantes y en meses con al menos 10 de esos días en ambos años (ago, nov, dic). Los empates cuentan para todos los empatados.
11. **Meteorología:** correlación de Spearman diaria, descriptiva; no demuestra causalidad. La dirección del viento no se usa (no existe en 2024). La humedad solo cubre algunos meses y distintos en cada año, por lo que sus signos no son comparables entre años.
