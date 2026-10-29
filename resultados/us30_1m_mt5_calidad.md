# Calidad de datos · datos/us30_1m_mt5.csv

Veredicto: **NO APTA** para backtest

- Origen: datos/crudos/us30_1m_mt5.csv · temporalidad 1m · zona original UTC
- Desde 2011-01-03 00:00 hasta 2026-09-18 10:41 UTC · 15.7 años
- Velas: 5284083 en el crudo → 5284083 curadas (0.0% eliminadas)
- Horario aprendido de los datos: 24 de 24 horas con sesión (hora de Nueva York)
- Velas faltantes dentro del horario: 361815 (6.6%)
- Días sin sesión (festivos o cierres, normal: no cuentan como hueco): 32
- Volumen: 1% en cero

## Avisos
- 61344 saltos fuera de lo normal: revísalos en el gráfico (pueden ser reales).
- 361815 velas faltantes dentro del horario del activo (6.6%). No se rellenaron.

## Saltos para revisar (primeros 10)
- 2011-01-03 01:00 UTC
- 2011-01-04 00:00 UTC
- 2011-01-04 00:04 UTC
- 2011-01-05 00:00 UTC
- 2011-01-05 00:01 UTC
- 2011-01-05 03:34 UTC
- 2011-01-05 10:42 UTC
- 2011-01-05 15:15 UTC
- 2011-01-06 00:00 UTC
- 2011-01-06 00:04 UTC

## Velas faltantes (primeras 10)
- 2011-01-03 02:01
- 2011-01-03 02:03
- 2011-01-03 02:04
- 2011-01-03 02:06
- 2011-01-03 02:07
- 2011-01-03 02:08
- 2011-01-03 02:09
- 2011-01-03 02:12
- 2011-01-03 02:22
- 2011-01-03 02:25

## Días sin sesión (primeros 10)
- 2011-04-22
- 2011-12-25
- 2012-01-01
- 2013-03-29
- 2013-12-22
- 2014-04-18
- 2015-12-25
- 2016-01-01
- 2016-03-25
- 2016-12-25

Umbrales provisionales del Reto: NO APTA si se eliminó más del 5 %, faltan más del 5 % de las velas dentro del horario del activo,
hay menos de 1 año o menos de 100 velas. Datos gratuitos: buenos para investigar, no iguales a datos de pago.
