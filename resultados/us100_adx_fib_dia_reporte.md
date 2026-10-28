# Reporte fase 04 · US100 ADX(75) subiendo + extensión 1,382 del día (M30, solo compras)

Código: `codigo/us100_adx_fib_dia.py` · Operaciones: `resultados/us100_adx_fib_dia_operaciones.csv` · Curva: `resultados/us100_adx_fib_dia_equity.png` · Cifras: `us100_adx_fib_dia_resultados.json`.

## Datos
datos/us100_1m_mt5.csv (M1, Bid) con el spread por minuto de datos/US100.csv (última columna, puntos de 0,1; las dos tablas coinciden fila a fila) · US100 · 2011-01-03T01:00 a 2026-09-17T02:58 (hora del servidor) · 5.213.359 velas M1 · 180.678 velas M30.
Spread mediano 5 puntos; minutos con spread 0 o ausente: 0.
Calidad: el informe del M1 (resultados/us100_1m_mt5_calidad.md) dice NO APTA por umbral provisional (5,5 % de minutos M1 faltantes dentro del horario; límite 5 %); el de las velas M30 (resultados/us100_30m_mt5_calidad.md) dice APTA CON AVISOS (2,8 % de velas M30 faltantes, sin rellenar). Las fases 02 y 03 ya decidieron conservar el M1 para resolver el orden del stop. Se corre con ese aviso: los minutos sin ticks (sobre todo 2011 a 2014) se tratan como ausentes, sin rellenar.

Corte 70/30 por velas M30 (int(n x 0,7) = 126.474): dentro de muestra 2011-01-03T01:00 a 2022-01-05T17:00 (126.474 velas); fuera de muestra 2022-01-05T17:30 a 2026-09-17T02:30 (54.204 velas).
Activaciones del ADX en el tramo: dentro 2333, fuera 975 (incluye las que ocurren con posición abierta, que se ignoran).

## Los 4 números, FUERA de muestra y con costes (spread + swap)
| Número | Resultado | Umbral | |
|---|---|---|---|
| Factor de beneficio | 1,66 | ≥ 1,3 | ✓ |
| Operaciones | 150 | ≥ 30 | ✓ |
| Caída máxima | 5,94 % | < 20 % | ✓ |
| Factor de beneficio sin la mejor operación | 1,51 | > 1 | ✓ |

Veredicto 4/4 · APRUEBA el método.
Referencia sin swap (solo spread): factor de beneficio 1,74, sin la mejor 1,58. El swap sumó -4.008 USD en 150 operaciones (media 0,6 noches por operación).
Encaje con MI_PLAN.md: la caída de 5,94 % no supera el 6 % que el trader acepta en backtest (encaja con el plan).

## Dentro de muestra (solo referencia, no cuenta para el veredicto)
Factor de beneficio 1,63 (sin swap 1,72) · 334 operaciones · caída 10,74 % · sin la mejor 1,54 · resultado neto 89.897 USD.

## Otros datos fuera de muestra
Resultado neto 41.150 USD sobre 100.000 (bruto 45.158 y swap -4.008) · ganadoras 45,3 % · media por operación 274 USD · mejor 9.282 · peor -2.300 · caída solo con operaciones cerradas 4,61 % (la oficial usa también la pérdida flotante al cierre de cada vela M30).
Motivos de salida fuera de muestra: {'stop': 149, 'stop_gap': 1}. Duración media 0,8 días; operaciones que pasan al menos un fin de semana: 17 de 150.

## (a) Resultado por tramo
Fuera de muestra, primeros 3 años frente al resto (corte 2025-01-05):
| Tramo | Operaciones | Factor de beneficio | Sin la mejor | Resultado USD |
|---|---|---|---|---|
| Primeros 3 años OOS | 100 | 2,08 | 1,90 | 39.583 |
| Resto OOS | 50 | 1,06 | 0,70 | 1.567 |

Por año (fuera de muestra; el año de entrada de la operación):
| Año | Operaciones | Factor de beneficio | Sin la mejor | FB sin swap | Resultado USD | % ganadoras |
|---|---|---|---|---|---|---|
| 2022 | 25 | 1,89 | 1,38 | 1,93 | 9.202 | 48,0 |
| 2023 | 41 | 2,76 | 2,25 | 2,87 | 22.607 | 56,1 |
| 2024 | 34 | 1,58 | 1,26 | 1,67 | 7.774 | 47,1 |
| 2025 | 30 | 1,43 | 0,73 | 1,52 | 5.740 | 33,3 |
| 2026 | 20 | 0,66 | 0,42 | 0,70 | -4.172 | 35,0 |

Por año (dentro de muestra, solo referencia):
| Año | Operaciones | Factor de beneficio | Resultado USD |
|---|---|---|---|
| 2011 | 26 | 1,68 | 5.736 |
| 2012 | 30 | 1,09 | 1.497 |
| 2013 | 24 | 1,44 | 5.399 |
| 2014 | 26 | 1,13 | 1.468 |
| 2015 | 26 | 1,06 | 771 |
| 2016 | 39 | 1,23 | 4.429 |
| 2017 | 35 | 1,70 | 10.717 |
| 2018 | 28 | 4,38 | 25.868 |
| 2019 | 40 | 1,47 | 7.902 |
| 2020 | 32 | 2,50 | 17.099 |
| 2021 | 28 | 1,72 | 9.012 |

## (b) Caso A frente a caso B
A = la orden en espera se llena (incluye `A` = el precio sube hasta el nivel y se llena en el nivel, y `A_apertura` = una orden viva se llena a la apertura de una vela que abre ya pasada del nivel); B = entrada a mercado en la apertura siguiente a la señal con el Ask ya en el nivel o más allá. 'Sobreprecio' = precio de entrada menos nivel, en promedio.
| Grupo (fuera de muestra) | Operaciones | Factor de beneficio | Resultado USD | % ganadoras | Media USD | Sobreprecio medio (pts de índice) |
|---|---|---|---|---|---|---|
| A total | 64 | 2,20 | 27.217 | 51,6 | 425 | 0,00 |
|   A (fill al nivel) | 64 | 2,20 | 27.217 | 51,6 | 425 | 0,00 |
|   A_apertura (fill con hueco) | 0 | 0,00 | 0 | 0,0 | 0 | 0,00 |
| B (mercado) | 86 | 1,35 | 13.933 | 40,7 | 162 | 82,64 |
Dentro de muestra (referencia): A 133 operaciones, FB 2,02, 58.511 USD; B 201 operaciones, FB 1,36, 31.386 USD.

## (c) Frecuencia
Fuera de muestra: 150 operaciones en 4,70 años = 31,9 por año = 2,7 al mes (MI_PLAN.md: unas 6 al mes). Dentro de muestra: 334 operaciones.

## (d) Caída frente al plan
Caída máxima fuera de muestra 5,94 % frente al 6 % que el trader acepta en backtest: dentro del plan. Peor operación -2.300 USD (el plan arriesga 1 %; aquí 1.000 USD sobre 100.000).

## (e) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)
Se rehace cada operación con otro camino de cálculo (velas M30 con `resample` de pandas, ATR con `rolling`, ADX con `ewm` de pandas, nivel desde el máximo y mínimo diario de las M1, swap con la última M1 antes de cada medianoche y el stop barrido minuto a minuto), y se compara con lo que anotó el motor:

    Operación #334 (OOS, origen B): entrada 2022-01-31 19:00 · salida 2022-02-01 16:42 · motivo stop · noches 1
      - Señal a mano: activación del ADX(75) en la vela 2022-01-31 18:30:00; ayer = 2022-01-28 (máx 14454.6, mín 13842.8) -> nivel = mín + 1,382 x rango = 14688.308 (motor 14688.308) -> OK
      - ATR(30) en la vela de señal a mano 52.367 (motor 52.367) -> OK
      - Entrada a mercado: primer minuto de la vela 2022-01-31 19:00:00 (2022-01-31 19:00:00) tiene Ask de apertura 14790.8 >= nivel 14688.308; el motor compró a 14790.8 -> OK
      - Stop inicial a mano: 14790.8 - 2,5 x 52.367 = 14659.883 (motor 14659.883) -> OK; lote a mano: 1.000 / 130.917 = 7.638 -> 7.63 (motor 7.63) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = 2022-02-01 16:42:00 a 14860.870 (motor 2022-02-01 16:42 a 14860.87) -> OK
      - Resultado a mano: bruto 534.63 + swap -21.45 (1 noches) = 513.18 (motor: bruto 534.63 + swap -21.45 (1 noches) = 513.18) -> OK
    Operación #337 (OOS, origen A): entrada 2022-03-18 18:06 · salida 2022-03-21 16:53 · motivo stop · noches 1
      - Señal a mano: activación del ADX(75) en la vela 2022-03-18 16:30:00; ayer = 2022-03-17 (máx 14136.0, mín 13821.2) -> nivel = mín + 1,382 x rango = 14256.254 (motor 14256.254) -> OK
      - ATR(30) en la vela de señal a mano 34.013 (motor 34.013) -> OK
      - Entrada con orden en espera: ningún minuto abierto antes de 2022-03-18 18:06:00 alcanza el nivel (Ask máximo < 14256.254): True; en 2022-03-18 18:06:00 el Ask máximo es 14257.9 (Ask apertura 14243.2); precio del motor 14256.254 -> OK
      - Stop inicial a mano: 14256.254 - 2,5 x 34.013 = 14171.221 (motor 14171.22) -> OK; lote a mano: 1.000 / 85.033 = 11.760 -> 11.76 (motor 11.76) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = 2022-03-21 16:53:00 a 14331.970 (motor 2022-03-21 16:53 a 14331.97) -> OK
      - Resultado a mano: bruto 890.42 + swap -32.06 (1 noches) = 858.36 (motor: bruto 890.42 + swap -32.06 (1 noches) = 858.36) -> OK
    Operación #340 (OOS, origen B): entrada 2022-05-26 18:00 · salida 2022-05-30 15:40 · motivo stop · noches 2
      - Señal a mano: activación del ADX(75) en la vela 2022-05-26 17:30:00; ayer = 2022-05-25 (máx 12027.2, mín 11669.3) -> nivel = mín + 1,382 x rango = 12163.918 (motor 12163.918) -> OK
      - ATR(30) en la vela de señal a mano 51.833 (motor 51.833) -> OK
      - Entrada a mercado: primer minuto de la vela 2022-05-26 18:00:00 (2022-05-26 18:00:00) tiene Ask de apertura 12192.4 >= nivel 12163.918; el motor compró a 12192.4 -> OK
      - Stop inicial a mano: 12192.4 - 2,5 x 51.833 = 12062.817 (motor 12062.817) -> OK; lote a mano: 1.000 / 129.583 = 7.717 -> 7.71 (motor 7.71) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente (trailing = cierre - 3 x ATR(30) de cada vela) = 2022-05-30 15:40:00 a 12784.300 (motor 2022-05-30 15:40 a 12784.3) -> OK
      - Resultado a mano: bruto 4,563.55 + swap -36.35 (2 noches) = 4,527.20 (motor: bruto 4,563.55 + swap -36.35 (2 noches) = 4,527.20) -> OK

## Costes y supuestos del backtest
- Spread real del CSV por minuto (Ask = Bid + spread × 0,1): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (la ficha). Aviso de la ficha (supuesto 30): el spread es de RoboForex medido de 2017-12 a 2026; antes es un perfil fabricado, y puede ser optimista.
- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M30 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor (la noche del viernes cuenta una vez), sin día triple. Se suma al resultado de cada operación y entra en el factor de beneficio y en la caída.
- Símbolo: punto 0,1; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 5 puntos; horario 01:01–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.
- ADX de Wilder clásico (semilla = media simple de los 75 primeros valores de TR/+DM/-DM y de los 75 primeros DX) sobre las velas M30 Bid completas; rising = mayor que hace 5 velas. Decisión de implementación: la ficha no fija la semilla; solo afecta a las primeras ~600 velas.
- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (motivo `fin_segmento`).
- Una compra consume la señal pendiente (si una orden vieja se llena en el primer tick, la señal nueva no se coloca nunca más tarde). El motor hermano dejaba la señal viva en ese caso; aquí se limpia.
- Equity: capital + resultado de operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M30; la caída máxima sale de esa curva.
- Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1.
- Todo lo demás: los 30 supuestos del pseudocódigo de la ficha.
