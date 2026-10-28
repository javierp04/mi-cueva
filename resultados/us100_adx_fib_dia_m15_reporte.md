# Reporte fase 04 · US100 ADX(75) subiendo + extensión 1,382 del día (M15, solo compras)

Código: `codigo/us100_adx_fib_dia_m15.py` · Operaciones: `resultados/us100_adx_fib_dia_m15_operaciones.csv` · Curva: `resultados/us100_adx_fib_dia_m15_equity.png` · Cifras: `us100_adx_fib_dia_m15_resultados.json`.

## Datos
datos/us100_1m_mt5.csv (M1, Bid) con el spread por minuto de datos/US100.csv (última columna, puntos de 0,1; las dos tablas coinciden fila a fila) · US100 · 2011-01-03T01:00 a 2026-09-17T02:58 (hora del servidor) · 5.213.359 velas M1 · 357.493 velas M15.
Spread mediano 5 puntos; minutos con spread 0 o ausente: 0.
Calidad: el informe del M1 (resultados/us100_1m_mt5_calidad.md) dice NO APTA por umbral provisional (5,5 % de minutos M1 faltantes dentro del horario; límite 5 %); el de las velas M15 (resultados/us100_15m_mt5_calidad.md) dice APTA CON AVISOS (2,8 % de velas M15 faltantes, sin rellenar). Las fases 02 y 03 ya decidieron conservar el M1 para resolver el orden del stop. Se corre con ese aviso: los minutos sin ticks (sobre todo 2011 a 2014) se tratan como ausentes, sin rellenar.

Corte 70/30 por velas M15 (int(n x 0,7) = 250.245): dentro de muestra 2011-01-03T01:00 a 2022-01-05T09:30 (250.245 velas); fuera de muestra 2022-01-05T09:45 a 2026-09-17T02:45 (107.248 velas).
Activaciones del ADX en el tramo: dentro 4530, fuera 1874 (incluye las que ocurren con posición abierta, que se ignoran).

## Los 4 números, FUERA de muestra y con costes (spread + swap)
| Número | Resultado | Umbral | |
|---|---|---|---|
| Factor de beneficio | 1,59 | ≥ 1,3 | ✓ |
| Operaciones | 192 | ≥ 30 | ✓ |
| Caída máxima | 8,27 % | < 20 % | ✓ |
| Factor de beneficio sin la mejor operación | 1,52 | > 1 | ✓ |

Veredicto 4/4 · APRUEBA el método.
Referencia sin swap (solo spread): factor de beneficio 1,65, sin la mejor 1,58. El swap sumó -4.207 USD en 192 operaciones (media 0,5 noches por operación).
Encaje con MI_PLAN.md: la caída de 8,27 % SUPERA el 6 % que el trader acepta en backtest (pasa el método pero no encaja con el plan).

## Dentro de muestra (solo referencia, no cuenta para el veredicto)
Factor de beneficio 1,84 (sin swap 1,93) · 456 operaciones · caída 7,91 % · sin la mejor 1,79 · resultado neto 157.559 USD.

## Otros datos fuera de muestra
Resultado neto 42.850 USD sobre 100.000 (bruto 47.058 y swap -4.207) · ganadoras 45,3 % · media por operación 223 USD · mejor 5.108 · peor -1.043 · caída solo con operaciones cerradas 7,44 % (la oficial usa también la pérdida flotante al cierre de cada vela M15).
Motivos de salida fuera de muestra: {'stop': 192}. Duración media 0,6 días; operaciones que pasan al menos un fin de semana: 21 de 192.

## (a) Resultado por tramo
Fuera de muestra, primeros 3 años frente al resto (corte 2025-01-05):
| Tramo | Operaciones | Factor de beneficio | Sin la mejor | Resultado USD |
|---|---|---|---|---|
| Primeros 3 años OOS | 123 | 2,05 | 1,93 | 44.917 |
| Resto OOS | 69 | 0,93 | 0,84 | -2.067 |

Por año (fuera de muestra; el año de entrada de la operación):
| Año | Operaciones | Factor de beneficio | Sin la mejor | FB sin swap | Resultado USD | % ganadoras |
|---|---|---|---|---|---|---|
| 2022 | 35 | 1,62 | 1,21 | 1,66 | 7.819 | 45,7 |
| 2023 | 45 | 1,37 | 1,14 | 1,43 | 6.988 | 40,0 |
| 2024 | 43 | 3,65 | 3,25 | 3,80 | 30.110 | 55,8 |
| 2025 | 46 | 0,53 | 0,45 | 0,57 | -10.624 | 37,0 |
| 2026 | 23 | 2,14 | 1,78 | 2,21 | 8.558 | 52,2 |

Por año (dentro de muestra, solo referencia):
| Año | Operaciones | Factor de beneficio | Resultado USD |
|---|---|---|---|
| 2011 | 38 | 1,91 | 11.932 |
| 2012 | 40 | 1,90 | 14.095 |
| 2013 | 33 | 2,00 | 13.235 |
| 2014 | 41 | 1,28 | 4.565 |
| 2015 | 43 | 1,05 | 1.026 |
| 2016 | 36 | 1,90 | 14.510 |
| 2017 | 52 | 1,44 | 11.169 |
| 2018 | 42 | 2,85 | 27.971 |
| 2019 | 46 | 1,54 | 10.556 |
| 2020 | 43 | 2,03 | 17.747 |
| 2021 | 42 | 3,02 | 30.752 |

## (b) Caso A frente a caso B
A = la orden en espera se llena (incluye `A` = el precio sube hasta el nivel y se llena en el nivel, y `A_apertura` = una orden viva se llena a la apertura de una vela que abre ya pasada del nivel); B = entrada a mercado en la apertura siguiente a la señal con el Ask ya en el nivel o más allá. 'Sobreprecio' = precio de entrada menos nivel, en promedio.
| Grupo (fuera de muestra) | Operaciones | Factor de beneficio | Resultado USD | % ganadoras | Media USD | Sobreprecio medio (pts de índice) |
|---|---|---|---|---|---|---|
| A total | 82 | 1,41 | 13.513 | 42,7 | 165 | 1,22 |
|   A (fill al nivel) | 81 | 1,36 | 11.896 | 42,0 | 147 | 0,00 |
|   A_apertura (fill con hueco) | 1 | inf | 1.617 | 100,0 | 1.617 | 99,83 |
| B (mercado) | 110 | 1,73 | 29.337 | 47,3 | 267 | 51,64 |
Dentro de muestra (referencia): A 215 operaciones, FB 1,65, 65.434 USD; B 241 operaciones, FB 2,06, 92.125 USD.

## (c) Frecuencia
Fuera de muestra: 192 operaciones en 4,70 años = 40,9 por año = 3,4 al mes (MI_PLAN.md: unas 6 al mes). Dentro de muestra: 456 operaciones.

## (d) Caída frente al plan
Caída máxima fuera de muestra 8,27 % frente al 6 % que el trader acepta en backtest: SUPERA, no encaja con el plan. Peor operación -1.043 USD (el plan arriesga 1 %; aquí 1.000 USD sobre 100.000).

## (e) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)
Se rehace cada operación con otro camino de cálculo (velas M15 con `resample` de pandas, ATR con `rolling`, ADX con `ewm` de pandas, nivel desde el máximo y mínimo diario de las M1, swap con la última M1 antes de cada medianoche y el stop barrido minuto a minuto), y se compara con lo que anotó el motor:

    Operación #457 (OOS, origen B): entrada 2022-01-31 17:15 · salida 2022-02-01 10:01 · motivo stop · noches 1
      - Señal a mano: activación del ADX(75) en la vela 2022-01-31 17:00:00; ayer = 2022-01-28 (máx 14454.6, mín 13842.8) -> nivel = mín + 1,382 x rango = 14688.308 (motor 14688.308) -> OK
      - ATR(30) en la vela de señal a mano 43.683 (motor 43.683) -> OK
      - Entrada a mercado: primer minuto de la vela 2022-01-31 17:15:00 (2022-01-31 17:15:00) tiene Ask de apertura 14702.6 >= nivel 14688.308; el motor compró a 14702.6 -> OK
      - Stop inicial a mano: 14702.6 - 2,5 x 43.683 = 14593.392 (motor 14593.392) -> OK; lote a mano: 1.000 / 109.208 = 9.157 -> 9.15 (motor 9.15) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = 2022-02-01 10:01:00 a 14902.800 (motor 2022-02-01 10:01 a 14902.8) -> OK
      - Resultado a mano: bruto 1,831.83 + swap -25.72 (1 noches) = 1,806.11 (motor: bruto 1,831.83 + swap -25.72 (1 noches) = 1,806.11) -> OK
    Operación #456 (OOS, origen A): entrada 2022-01-12 16:02 · salida 2022-01-12 16:41 · motivo stop · noches 0
      - Señal a mano: activación del ADX(75) en la vela 2022-01-12 15:45:00; ayer = 2022-01-11 (máx 15848.8, mín 15487.2) -> nivel = mín + 1,382 x rango = 15986.931 (motor 15986.931) -> OK
      - ATR(30) en la vela de señal a mano 29.027 (motor 29.027) -> OK
      - Entrada con orden en espera: ningún minuto abierto antes de 2022-01-12 16:02:00 alcanza el nivel (Ask máximo < 15986.931): True; en 2022-01-12 16:02:00 el Ask máximo es 15987.7 (Ask apertura 15979.7); precio del motor 15986.931 -> OK
      - Stop inicial a mano: 15986.931 - 2,5 x 29.027 = 15914.364 (motor 15914.365) -> OK; lote a mano: 1.000 / 72.567 = 13.780 -> 13.78 (motor 13.78) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = 2022-01-12 16:41:00 a 15914.364 (motor 2022-01-12 16:41 a 15914.365) -> OK
      - Resultado a mano: bruto -999.97 + swap 0.00 (0 noches) = -999.97 (motor: bruto -999.97 + swap 0.00 (0 noches) = -999.97) -> OK
    Operación #573 (OOS, origen B): entrada 2024-11-29 19:30 · salida 2024-12-03 12:34 · motivo stop · noches 2
      - Señal a mano: activación del ADX(75) en la vela 2024-11-29 19:15:00; ayer = 2024-11-28 (máx 20844.4, mín 20746.6) -> nivel = mín + 1,382 x rango = 20881.760 (motor 20881.76) -> OK
      - ATR(30) en la vela de señal a mano 26.573 (motor 26.573) -> OK
      - Entrada a mercado: primer minuto de la vela 2024-11-29 19:30:00 (2024-11-29 19:30:00) tiene Ask de apertura 20926.1 >= nivel 20881.760; el motor compró a 20926.1 -> OK
      - Stop inicial a mano: 20926.1 - 2,5 x 26.573 = 20859.667 (motor 20859.667) -> OK; lote a mano: 1.000 / 66.433 = 15.053 -> 15.05 (motor 15.05) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = 2024-12-03 12:34:00 a 21150.620 (motor 2024-12-03 12:34 a 21150.62) -> OK
      - Resultado a mano: bruto 3,379.03 + swap -119.78 (2 noches) = 3,259.24 (motor: bruto 3,379.03 + swap -119.78 (2 noches) = 3,259.24) -> OK

## Costes y supuestos del backtest
- Spread real del CSV por minuto (Ask = Bid + spread × 0,1): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (la ficha). Aviso de la ficha (supuesto 30): el spread es de RoboForex medido de 2017-12 a 2026; antes es un perfil fabricado, y puede ser optimista.
- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M15 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor (la noche del viernes cuenta una vez), sin día triple. Se suma al resultado de cada operación y entra en el factor de beneficio y en la caída.
- Símbolo: punto 0,1; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 5 puntos; horario 01:01–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.
- ADX de Wilder clásico (semilla = media simple de los 75 primeros valores de TR/+DM/-DM y de los 75 primeros DX) sobre las velas M15 Bid completas; rising = mayor que hace 5 velas. Decisión de implementación: la ficha no fija la semilla; solo afecta a las primeras ~600 velas.
- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (motivo `fin_segmento`).
- Una compra consume la señal pendiente (si una orden vieja se llena en el primer tick, la señal nueva no se coloca nunca más tarde). El motor hermano dejaba la señal viva en ese caso; aquí se limpia.
- Equity: capital + resultado de operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M15; la caída máxima sale de esa curva.
- Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1.
- Todo lo demás: los 30 supuestos del pseudocódigo de la ficha.
