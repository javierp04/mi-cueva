# Calidad de datos · datos/us100_1m_mt5.csv

Veredicto: **NO APTA** para backtest

- Origen: datos/crudos/us100_1m_mt5.csv · temporalidad 1m · zona original UTC
- Desde 2011-01-03 01:00 hasta 2026-09-17 02:58 UTC · 15.7 años
- Velas: 5213359 en el crudo → 5213359 curadas (0.0% eliminadas)
- Horario aprendido de los datos: 23 de 24 horas con sesión (hora de Nueva York)
- Velas faltantes dentro del horario: 297529 (5.5%)
- Días sin sesión (festivos o cierres, normal: no cuentan como hueco): 36
- Volumen: 2% en cero

## Avisos
- 53004 saltos fuera de lo normal: revísalos en el gráfico (pueden ser reales).
- 297529 velas faltantes dentro del horario del activo (5.5%). No se rellenaron.

## Saltos para revisar (primeros 10)
- 2011-01-03 10:37 UTC
- 2011-01-03 16:31 UTC
- 2011-01-05 10:35 UTC
- 2011-01-05 10:42 UTC
- 2011-01-05 15:15 UTC
- 2011-01-07 15:31 UTC
- 2011-01-07 16:31 UTC
- 2011-01-10 01:00 UTC
- 2011-01-10 16:33 UTC
- 2011-01-10 16:40 UTC

## Velas faltantes (primeras 10)
- 2011-01-03 02:39
- 2011-01-03 02:40
- 2011-01-03 02:46
- 2011-01-03 02:47
- 2011-01-03 02:48
- 2011-01-03 02:51
- 2011-01-03 02:52
- 2011-01-03 02:53
- 2011-01-03 02:54
- 2011-01-03 03:04

## Días sin sesión (primeros 10)
- 2011-04-22
- 2011-12-25
- 2011-12-26
- 2012-01-01
- 2012-01-02
- 2012-04-29
- 2012-12-25
- 2013-01-01
- 2013-03-29
- 2013-06-30

Umbrales provisionales del Reto: NO APTA si se eliminó más del 5 %, faltan más del 5 % de las velas dentro del horario del activo,
hay menos de 1 año o menos de 100 velas. Datos gratuitos: buenos para investigar, no iguales a datos de pago.
