# Calidad de datos · datos/us30_30m_mt5.csv

Veredicto: **APTA CON AVISOS** para backtest

- Origen: datos/crudos/us30_30m_mt5.csv · temporalidad 30m · zona original UTC
- Desde 2011-01-03 00:00 hasta 2026-09-18 10:30 UTC · 15.7 años
- Velas: 185705 en el crudo → 185705 curadas (0.0% eliminadas)
- Horario aprendido de los datos: 24 de 24 horas con sesión (hora de Nueva York)
- Velas faltantes dentro del horario: 6893 (3.6%)
- Días sin sesión (festivos o cierres, normal: no cuentan como hueco): 32
- Volumen: 1% en cero

## Avisos
- 2110 saltos fuera de lo normal: revísalos en el gráfico (pueden ser reales).
- 6893 velas faltantes dentro del horario del activo (3.6%). No se rellenaron.

## Saltos para revisar (primeros 10)
- 2011-01-18 00:00 UTC
- 2011-01-18 02:00 UTC
- 2011-01-24 00:00 UTC
- 2011-01-24 01:00 UTC
- 2011-01-31 01:00 UTC
- 2011-02-07 01:00 UTC
- 2011-02-21 00:00 UTC
- 2011-02-21 01:00 UTC
- 2011-02-22 00:00 UTC
- 2011-02-22 02:00 UTC

## Velas faltantes (primeras 10)
- 2011-01-04 00:30
- 2011-01-05 00:30
- 2011-01-06 00:30
- 2011-01-07 00:30
- 2011-01-07 23:00
- 2011-01-07 23:30
- 2011-01-11 00:30
- 2011-01-12 00:30
- 2011-01-13 00:30
- 2011-01-14 00:30

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
