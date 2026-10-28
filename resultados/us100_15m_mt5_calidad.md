# Calidad de datos · datos/us100_15m_mt5.csv

Veredicto: **APTA CON AVISOS** para backtest

- Origen: datos/crudos/us100_15m_mt5.csv · temporalidad 15m · zona original UTC
- Desde 2011-01-03 01:00 hasta 2026-09-17 02:45 UTC · 15.7 años
- Velas: 357493 en el crudo → 357493 curadas (0.0% eliminadas)
- Horario aprendido de los datos: 23 de 24 horas con sesión (hora de Nueva York)
- Velas faltantes dentro del horario: 10274 (2.8%)
- Días sin sesión (festivos o cierres, normal: no cuentan como hueco): 36
- Volumen: 2% en cero

## Avisos
- 3771 saltos fuera de lo normal: revísalos en el gráfico (pueden ser reales).
- 10274 velas faltantes dentro del horario del activo (2.8%). No se rellenaron.

## Saltos para revisar (primeros 10)
- 2011-01-03 16:30 UTC
- 2011-01-18 16:30 UTC
- 2011-01-28 18:30 UTC
- 2011-02-03 17:00 UTC
- 2011-02-10 17:00 UTC
- 2011-02-22 16:30 UTC
- 2011-02-22 16:45 UTC
- 2011-03-02 01:00 UTC
- 2011-03-07 17:30 UTC
- 2011-03-09 16:30 UTC

## Velas faltantes (primeras 10)
- 2011-01-03 23:15
- 2011-01-03 23:30
- 2011-01-03 23:45
- 2011-01-04 00:00
- 2011-01-04 23:15
- 2011-01-04 23:30
- 2011-01-04 23:45
- 2011-01-05 00:00
- 2011-01-05 23:15
- 2011-01-05 23:30

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
