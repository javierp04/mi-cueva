# Reporte fase 04 · US30 MACD(10,50,9) cruza a la baja en sesión asiática + limit en HMA(30) + 1 ATR (M30, solo compras)

Código: `codigo/us30_macd_hma_asia.py` · Operaciones: `resultados/us30_macd_hma_asia_operaciones.csv` · Curva: `resultados/us30_macd_hma_asia_equity.png` · Cifras: `resultados/us30_macd_hma_asia_resultados.json`.

> AVISO: el símbolo US30 (punto 0,01; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300) y el swap largo (−6,9 % anual) son SUPUESTOS de la ficha, tomados de US100 (supuestos 24 y 25). El spread viene de `datos/US30.csv` (supuesto 26: por confirmar de qué bróker). Si el bróker real difiere, el resultado cambia.

## Datos
`datos/us30_1m_mt5.csv` (M1, Bid; la columna `fecha` dice UTC pero es hora del servidor y se usó tal cual) con el spread por minuto de la última columna de `datos/US30.csv` (TSV, puntos de 0,01). Alineación por fecha: de 5.284.083 minutos del M1 curado, 5.284.083 tienen su minuto en US30.csv y 0 no (esos usarían la mediana, 220 puntos). US30.csv tiene 5.600.532 filas, empieza el 2009-01-02 02:00 y 316.449 filas no se usan (2009-2010 y el resto del recorte). Cierre del M1 distinto al de US30.csv en el mismo minuto: 0 casos.
US30 · 2011-01-03T00:00 a 2026-09-18T10:41 (hora del servidor) · 5.284.083 velas M1 · 185.705 velas M30 (armadas con todas las M1). Spread mediano 220 puntos (2,20 unidades), percentil 95 1.000, máximo 2.280.
Calidad: el M1 (resultados/us30_1m_mt5_calidad.md) da NO APTA por el 6,6 % de minutos faltantes (límite 5 %) y el M30 (resultados/us30_30m_mt5_calidad.md) APTA CON AVISOS (3,6 % de velas faltantes, sin rellenar). La ficha (supuesto 28) decidió usarlo igual, como en US100. Aviso: los huecos se tratan como ausentes y los resultados pueden cambiar con datos completos.

Corte 70/30 por velas M30 (int(n × 0,7) = 129.993): dentro de muestra 2011-01-03T00:00 a 2021-12-29T16:00 (129.993 velas); fuera de muestra 2021-12-29T16:30 a 2026-09-18T10:30 (55.712 velas). Cada tramo parte de 100.000.
Activaciones (cruce a la baja con sesión asiática): dentro 1043, fuera 467 (incluye las que ocurren con posición abierta, que se ignoran).

## Los 4 números, FUERA de muestra y con costes (spread + swap)
| Número | Resultado | Umbral | |
|---|---|---|---|
| Factor de beneficio | 1,43 | ≥ 1,3 | ✓ |
| Operaciones | 430 | ≥ 30 | ✓ |
| Caída máxima | 8,92 % | < 20 % | ✓ |
| Factor de beneficio sin la mejor operación | 1,38 | > 1 | ✓ |

Veredicto 4/4 · APRUEBA.
Referencia sin swap (solo spread): factor de beneficio 1,44, sin la mejor 1,39. El swap sumó -1.339 USD en 430 operaciones (media 0,1 noches por operación).
Encaje con MI_PLAN.md: la caída de 8,92 % SUPERA el 6 % que el trader acepta en backtest (el método puede pasar, pero no encaja con el plan).

## Dentro de muestra (solo referencia, no cuenta para el veredicto)
Factor de beneficio 1,27 (sin swap 1,29) · 952 operaciones · caída 11,20 % · sin la mejor 1,26 · resultado neto 103.492 USD.

## Otros datos fuera de muestra
Resultado neto 66.416 USD sobre 100.000 (bruto 67.754 y swap -1.339) · ganadoras 40,5 % · media por operación 154 USD · mejor 7.598 · peor -1.000 · caída solo con operaciones cerradas 7,96 % (la oficial usa también la pérdida flotante al cierre de cada vela M30).
Orden de salidas fuera de muestra: {'trailing': 341, 'stop_inicial': 64, '48_velas': 22, 'trailing_gap': 3}. Dentro de muestra: {'trailing': 672, 'stop_inicial': 167, '48_velas': 70, 'trailing_gap': 39, 'stop_inicial_gap': 4}. (`stop_inicial` = el stop de 2 × ATR(30) sin que el trailing lo haya subido; `trailing` = el stop subido por el trailing; `_gap` = la vela abrió ya por debajo del stop; `48_velas` = cierre forzado; `fin_segmento` = cierre técnico al terminar el tramo.) Duración media 0,44 días; operaciones que pasan un fin de semana: 5 de 430.

## (a) Resultado por tramo
Fuera de muestra, primeros 3 años frente al resto (corte 2024-12-29):
| Tramo | Operaciones | Factor de beneficio | Sin la mejor | Resultado USD |
|---|---|---|---|---|
| Primeros 3 años OOS | 278 | 1,36 | 1,29 | 35.008 |
| Resto OOS | 152 | 1,55 | 1,42 | 31.408 |

Por año (fuera de muestra; el año de entrada de la operación):
| Año | Operaciones | Factor de beneficio | Sin la mejor | FB sin swap | Resultado USD | % ganadoras |
|---|---|---|---|---|---|---|
| 2022 | 98 | 2,13 | 1,92 | 2,15 | 35.244 | 52,0 |
| 2023 | 88 | 1,14 | 0,95 | 1,15 | 4.309 | 40,9 |
| 2024 | 92 | 0,88 | 0,75 | 0,88 | -4.545 | 33,7 |
| 2025 | 92 | 1,65 | 1,48 | 1,67 | 22.681 | 34,8 |
| 2026 | 60 | 1,40 | 1,05 | 1,41 | 8.727 | 40,0 |

Años fuera de muestra que pierden: 2024.

Por año (dentro de muestra, solo referencia):
| Año | Operaciones | Factor de beneficio | Resultado USD |
|---|---|---|---|
| 2011 | 83 | 1,12 | 4.252 |
| 2012 | 80 | 1,17 | 5.079 |
| 2013 | 82 | 1,09 | 3.132 |
| 2014 | 89 | 1,28 | 8.841 |
| 2015 | 84 | 0,97 | -1.062 |
| 2016 | 90 | 1,22 | 8.548 |
| 2017 | 85 | 1,57 | 18.975 |
| 2018 | 80 | 2,05 | 26.437 |
| 2019 | 88 | 1,16 | 6.174 |
| 2020 | 90 | 1,10 | 4.563 |
| 2021 | 101 | 1,53 | 18.553 |

## (b) Entradas a mercado (caso B) frente a limit que esperó (caso A)
B = compra a mercado en la apertura siguiente a la señal porque el Ask ya está en el nivel o por debajo (la limit de compra en hma(30) + 1 ATR casi siempre queda por encima del precio). A = la orden limit queda en espera y se llena después (`A` = el Ask baja hasta el nivel; `A_apertura` = una vela abre ya por debajo del nivel y se llena a esa apertura). 'Entrada menos nivel' = precio de entrada menos nivel, en promedio (unidades de índice).
| Grupo (fuera de muestra) | Operaciones | Factor de beneficio | Resultado USD | % ganadoras | Media USD | Entrada menos nivel |
|---|---|---|---|---|---|---|
| A total (limit que esperó) | 0 | 0,00 | 0 | 0,0 | 0 | 0,00 |
|   A (fill al nivel) | 0 | 0,00 | 0 | 0,0 | 0 | 0,00 |
|   A_apertura (fill con hueco) | 0 | 0,00 | 0 | 0,0 | 0 | 0,00 |
| B (mercado) | 430 | 1,43 | 66.416 | 40,5 | 154 | -110,26 |
Dentro de muestra (referencia): A 1 operaciones, FB 0,00, -327 USD; B 951 operaciones, FB 1,27, 103.820 USD.

Contadores del motor (qué pasó con cada señal):
| Contador | Dentro de muestra | Fuera de muestra |
|---|---|---|
| senales | 952 | 430 |
| caso_B | 951 | 430 |
| caso_C_rechazo | 0 | 0 |
| caso_A_colocada | 1 | 0 |
| senal_perdida_mercado_cerrado | 0 | 0 |
| ordenes_vencidas | 0 | 0 |
| ordenes_canceladas_alza | 0 | 0 |
| ordenes_reemplazadas | 0 | 0 |
| descartes_stops_level | 0 | 0 |
| cancelacion_inversa_sin_mercado | 0 | 0 |

## (c) Frecuencia
Fuera de muestra: 430 operaciones en 4,72 años = 91,2 por año = 7,6 al mes (MI_PLAN.md: unas 6 al mes). Dentro de muestra: 952 operaciones.

## (d) Caída frente al plan
Caída máxima fuera de muestra 8,92 % frente al 6 % que el trader acepta en backtest: SUPERA, no encaja con el plan. Peor operación -1.000 USD (el plan arriesga 1 %: 1.000 USD sobre 100.000).

## (e) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)
Se rehace cada operación con otro camino de cálculo (velas M30 con `resample` de pandas, ATR con `rolling`, EMA con semilla SMA hecha con `ewm` de pandas, LWMA/HMA con `rolling.apply` sobre una ventana local, sesión asiática con `zoneinfo` de Python, swap con la última M1 antes de cada medianoche y el stop barrido minuto a minuto) y se compara con lo que anotó el motor:

    Operacion #952 (OOS, origen B): entrada 2022-01-03 07:30 · salida 2022-01-03 15:59 · motivo trailing · noches 0
      - Senal a mano: vela 2022-01-03 07:00:00 (hora servidor) = 2022-01-03 14:00 en Tokio (dentro de 09:00-15:00); MACD principal 33.077 < senal 34.401 y en la vela anterior 35.119 >= 34.732 -> OK
      - Nivel a mano: HMA(30) = 36487.109 + ATR(14) 31.099 = 36518.209 (motor 36518.209) -> OK; ATR(30) de la vela de senal 43.149 (motor 43.149) -> OK
      - Entrada a mercado (caso B): primer minuto de la vela siguiente (2022-01-03 07:30:00); Ask de apertura 36453.87 <= nivel 36518.209; el motor compro a 36453.87 -> OK
      - Stop inicial a mano: 36453.87 - 2 x 43.149 = 36367.571 (motor 36367.571) -> OK; lote: 1.000 / 86.299 = 11.588 -> 11.58 (motor 11.58) -> OK
      - Salida a mano (trailing = cierre - 2,5 x ATR(30) de cada vela; 48 velas = apertura de la vela F+49): 2022-01-03 15:59:00 a 36455.477, motivo trailing (motor 2022-01-03 15:59 a 36455.477, trailing) -> OK
      - Resultado a mano: bruto 18.61 + swap 0.00 (0 noches) = 18.61 (motor: bruto 18.61 + swap 0.00 (0 noches) = 18.61) -> OK
    Operacion #963 (OOS, origen B): entrada 2022-02-15 08:00 · salida 2022-02-16 09:30 · motivo 48_velas · noches 1
      - Senal a mano: vela 2022-02-15 07:30:00 (hora servidor) = 2022-02-15 14:30 en Tokio (dentro de 09:00-15:00); MACD principal -84.790 < senal -81.611 y en la vela anterior -76.998 >= -80.817 -> OK
      - Nivel a mano: HMA(30) = 34570.891 + ATR(14) 48.981 = 34619.873 (motor 34619.873) -> OK; ATR(30) de la vela de senal 102.839 (motor 102.839) -> OK
      - Entrada a mercado (caso B): primer minuto de la vela siguiente (2022-02-15 08:00:00); Ask de apertura 34484.66 <= nivel 34619.873; el motor compro a 34484.66 -> OK
      - Stop inicial a mano: 34484.66 - 2 x 102.839 = 34278.983 (motor 34278.983) -> OK; lote: 1.000 / 205.677 = 4.862 -> 4.86 (motor 4.86) -> OK
      - Salida a mano (trailing = cierre - 2,5 x ATR(30) de cada vela; 48 velas = apertura de la vela F+49): 2022-02-16 09:30:00 a 34957.120, motivo 48_velas (motor 2022-02-16 09:30 a 34957.12, 48_velas) -> OK
      - Resultado a mano: bruto 2,296.16 + swap -32.12 (1 noches) = 2,264.04 (motor: bruto 2,296.16 + swap -32.12 (1 noches) = 2,264.04) -> OK
    Operacion #953 (OOS, origen B): entrada 2022-01-18 06:00 · salida 2022-01-18 06:23 · motivo stop_inicial · noches 0
      - Senal a mano: vela 2022-01-18 05:30:00 (hora servidor) = 2022-01-18 12:30 en Tokio (dentro de 09:00-15:00); MACD principal -4.575 < senal -0.259 y en la vela anterior 6.272 >= 0.819 -> OK
      - Nivel a mano: HMA(30) = 35949.519 + ATR(14) 40.964 = 35990.483 (motor 35990.483) -> OK; ATR(30) de la vela de senal 37.452 (motor 37.452) -> OK
      - Entrada a mercado (caso B): primer minuto de la vela siguiente (2022-01-18 06:00:00); Ask de apertura 35887.50 <= nivel 35990.483; el motor compro a 35887.5 -> OK
      - Stop inicial a mano: 35887.5 - 2 x 37.452 = 35812.597 (motor 35812.597) -> OK; lote: 1.000 / 74.903 = 13.351 -> 13.35 (motor 13.35) -> OK
      - Salida a mano (trailing = cierre - 2,5 x ATR(30) de cada vela; 48 velas = apertura de la vela F+49): 2022-01-18 06:23:00 a 35812.597, motivo stop_inicial (motor 2022-01-18 06:23 a 35812.597, stop_inicial) -> OK
      - Resultado a mano: bruto -999.96 + swap 0.00 (0 noches) = -999.96 (motor: bruto -999.96 + swap 0.00 (0 noches) = -999.96) -> OK

## (f) Comprobación de que el motor no mira el futuro
Se recalcularon todos los indicadores usando SOLO las velas hasta la 15.000ª del tramo fuera de muestra (se descartan las posteriores) y se corrió el motor con ellos: MACD principal y señal, ATR(14), ATR(30), HMA, nivel, CRUCE_BAJA, CRUCE_ALZA, ASIA y ACTIVACIÓN coinciden con los de la serie completa (todos iguales), y las 121 operaciones cerradas en ese tramo son idénticas (sí). Además, por construcción: el nivel y el ATR de la señal se calculan con datos hasta el cierre de la vela de señal inclusive y la orden se coloca en el primer tick de la vela siguiente; el trailing se calcula al cierre y vale desde la apertura siguiente; el cierre forzado usa la apertura de la vela F+49.

## Costes y supuestos del backtest
- Spread real del CSV por minuto (Ask = Bid + spread × 0,01): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (ficha). Aviso: el spread de `US30.csv` es de otro origen que el M1 y puede ser optimista o pesimista; en minutos de baja liquidez llega a 22 unidades.
- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M30 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor, sin día triple. Entra en el factor de beneficio y en la caída.
- Símbolo (supuesto): punto 0,01; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 150 puntos (1,5 unidades); horario 01:00–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.
- Indicadores sobre Bid, definiciones del trader: EMA con semilla SMA y alpha 2/(n+1); MACD(10,50,9); HMA(30) = LWMA(2·LWMA(15) − LWMA(30), 5); ATR = SMA del rango verdadero con la primera barra H − L. Sesión asiática: hora de apertura de la vela, servidor = Nueva York + 7 h (con el cambio de hora de EE. UU.), pasada a Asia/Tokyo, en [09:00, 15:00).
- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (`fin_segmento`).
- Una compra consume la señal pendiente. Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1. Equity: capital + operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M30.
- Todo lo demás: los 28 supuestos del pseudocódigo de la ficha. El cierre a las 48 velas cuenta velas de la serie completa, también las de horas cerradas.
