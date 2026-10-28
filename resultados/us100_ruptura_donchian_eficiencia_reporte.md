# Reporte fase 04 · US100 ruptura Donchian con eficiencia (M30, solo compras)

Código: `codigo/us100_ruptura_donchian_eficiencia.py` · Operaciones: `resultados/us100_ruptura_donchian_eficiencia_operaciones.csv` · Curva: `resultados/us100_ruptura_donchian_eficiencia_equity.png` · Cifras: `..._resultados.json`.

## Datos
datos/us100_1m_mt5.csv (M1, Bid) con el spread por minuto de datos/US100.csv (última columna, puntos de 0,1; las dos tablas coinciden fila a fila) · US100 · 2011-01-03T01:00 a 2026-09-17T02:58 (hora del servidor) · 5.213.359 velas M1 · 180.678 velas M30.
Spread mediano 5 puntos; minutos con spread 0 o ausente: 0.
Calidad: el informe del M1 (resultados/us100_1m_mt5_calidad.md) dice NO APTA por umbral provisional (5,5 % de minutos M1 faltantes dentro del horario; límite 5 %); el de las velas M30 (resultados/us100_30m_mt5_calidad.md) dice APTA CON AVISOS (2,8 % de velas M30 faltantes, sin rellenar). La fase 02 y la 03 ya decidieron conservar el M1 para resolver el orden del stop. Se corre con ese aviso: los minutos sin ticks (sobre todo 2011 a 2014) se tratan como ausentes, sin rellenar.

Corte 70/30 por velas M30 (int(n x 0,7) = 126.474): dentro de muestra 2011-01-03T01:00 a 2022-01-05T17:00 (126.474 velas); fuera de muestra 2022-01-05T17:30 a 2026-09-17T02:30 (54.204 velas).

## Los 4 números, FUERA de muestra y con costes (spread + swap)
| Número | Resultado | Umbral | |
|---|---|---|---|
| Factor de beneficio | 1,18 | ≥ 1,3 | ✕ |
| Operaciones | 610 | ≥ 30 | ✓ |
| Caída máxima | 8,58 % | < 20 % | ✓ |
| Factor de beneficio sin la mejor operación | 1,15 | > 1 | ✓ |

Veredicto 3/4 · NO APRUEBA.
Referencia sin swap (solo spread): factor de beneficio 1,22, sin la mejor 1,19. El swap sumó -5.758 USD en 610 operaciones (media 0,5 noches por operación).
Encaje con MI_PLAN.md: la caída de 8,58 % SUPERA el 6 % que el trader acepta en backtest (pasa el método pero no encaja con el plan).

## Dentro de muestra (solo referencia, no cuenta para el veredicto)
Factor de beneficio 1,22 (sin swap 1,27) · 1469 operaciones · caída 20,10 % · sin la mejor 1,20.

## Otros datos fuera de muestra
Resultado neto 27.636 USD sobre 100.000 (bruto 33.393 y swap -5.758) · ganadoras 40,2 % · media por operación 45 USD · mejor 4.054 · peor -1.698 · caída solo con operaciones cerradas 8,31 % (la oficial usa también la pérdida flotante al cierre de cada vela M30).
Motivos de salida fuera de muestra: {'stop': 604, 'stop_gap': 6}.

## (a) Resultado por tramo
Fuera de muestra, primeros 3 años frente al resto (corte 2025-01-05):
| Tramo | Operaciones | Factor de beneficio | Sin la mejor | Resultado USD |
|---|---|---|---|---|
| Primeros 3 años OOS | 386 | 1,29 | 1,24 | 28.226 |
| Resto OOS | 224 | 0,99 | 0,94 | -590 |

Por año (fuera de muestra; el año de entrada de la operación):
| Año | Operaciones | Factor de beneficio | Sin la mejor | FB sin swap | Resultado USD | % ganadoras |
|---|---|---|---|---|---|---|
| 2022 | 109 | 1,23 | 1,08 | 1,25 | 6.040 | 36,7 |
| 2023 | 143 | 1,03 | 0,95 | 1,06 | 1.315 | 42,7 |
| 2024 | 133 | 1,66 | 1,53 | 1,72 | 20.206 | 44,4 |
| 2025 | 129 | 0,99 | 0,90 | 1,05 | -220 | 41,9 |
| 2026 | 96 | 1,01 | 0,90 | 1,04 | 293 | 32,3 |

Por año (dentro de muestra, solo referencia):
| Año | Operaciones | Factor de beneficio | Resultado USD |
|---|---|---|---|
| 2011 | 124 | 1,09 | 2.905 |
| 2012 | 138 | 0,89 | -4.875 |
| 2013 | 131 | 1,03 | 1.269 |
| 2014 | 132 | 1,34 | 12.115 |
| 2015 | 129 | 1,04 | 1.301 |
| 2016 | 128 | 1,22 | 7.649 |
| 2017 | 148 | 1,21 | 8.566 |
| 2018 | 127 | 1,46 | 15.150 |
| 2019 | 137 | 1,45 | 15.073 |
| 2020 | 146 | 1,16 | 5.925 |
| 2021 | 128 | 1,70 | 22.100 |
| 2022 | 1 | inf | 28 |

## (b) Frecuencia
Fuera de muestra: 610 operaciones en 4,70 años = 129,9 por año = 10,8 al mes (MI_PLAN.md: unas 6 al mes).

## (c) Caída frente al plan
Caída máxima fuera de muestra 8,58 % frente al 6 % que el trader acepta en backtest: SUPERA, no encaja con el plan. Peor operación -1.698 USD (el riesgo del plan es 2.000 USD en la cuenta de 200.000; aquí se prueba 1.000 USD sobre 100.000, mismo 1 %).

## (d) Comprobación de cordura del motor (3 operaciones reconstruidas a mano)
Se rehace cada operación con otro camino de cálculo (velas M30 con `resample` de pandas, ATR y canal con `rolling`, y el stop barrido minuto a minuto), y se compara con lo que anotó el motor:

    Operación #1469 (OOS): entrada 2022-01-11 11:22 · salida 2022-01-11 16:05 · motivo stop
      - Stop inicial a mano: mínimo de las 20 velas M30 previas a 2022-01-11 11:00:00 = 15574.9 (motor 15574.9) -> OK
      - Minuto de entrada 2022-01-11 11:22:00: apertura 15670.8, máximo 15699.2, spread 0.4 -> Ask apertura 15671.2, Ask máximo 15699.6; precio de entrada del motor 15679.3
      - Nivel de entrada: coincide con el máximo de 55 velas a mano al cierre de 2022-01-11 10:30:00 = 15679.3 -> OK
      - Lote a mano: 1.000 / (15679.3 - 15574.9) = 9.579 -> 9.57 (motor 9.57) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente = 2022-01-11 16:05:00 a 15587.74 (motor 2022-01-11 16:05 a 15587.74) -> OK
      - Resultado a mano: bruto -876.23 + swap 0.00 (0 noches) = -876.23 (motor: bruto -876.23 + swap 0.00 (0 noches) = -876.23)
    Operación #1470 (OOS): entrada 2022-01-11 18:15 · salida 2022-01-12 17:41 · motivo stop
      - Stop inicial a mano: mínimo de las 20 velas M30 previas a 2022-01-11 18:00:00 = 15487.2 (motor 15487.2) -> OK
      - Minuto de entrada 2022-01-11 18:15:00: apertura 15716.9, máximo 15751.1, spread 0.5 -> Ask apertura 15717.4, Ask máximo 15751.6; precio de entrada del motor 15744.1
      - Nivel de entrada: coincide con el máximo de 55 velas a mano al cierre de 2022-01-11 17:30:00 = 15744.1 -> OK
      - Lote a mano: 1.000 / (15744.1 - 15487.2) = 3.893 -> 3.89 (motor 3.89) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente = 2022-01-12 17:41:00 a 15887.48 (motor 2022-01-12 17:41 a 15887.48) -> OK
      - Resultado a mano: bruto 557.75 + swap -11.65 (1 noches) = 546.10 (motor: bruto 557.75 + swap -11.65 (1 noches) = 546.10)
    Operación #1471 (OOS): entrada 2022-01-26 11:25 · salida 2022-01-26 21:44 · motivo stop
      - Stop inicial a mano: mínimo de las 20 velas M30 previas a 2022-01-26 11:00:00 = 13966.2 (motor 13966.2) -> OK
      - Minuto de entrada 2022-01-26 11:25:00: apertura 14412.8, máximo 14419.4, spread 0.8 -> Ask apertura 14413.6, Ask máximo 14420.2; precio de entrada del motor 14414.6
      - Nivel de entrada: coincide con el máximo de 55 velas a mano al cierre de 2022-01-26 10:30:00 = 14414.6 -> OK
      - Lote a mano: 1.000 / (14414.6 - 13966.2) = 2.230 -> 2.23 (motor 2.23) -> OK
      - Salida a mano: primer minuto con Bid mínimo <= stop vigente = 2022-01-26 21:44:00 a 14361.57 (motor 2022-01-26 21:44 a 14361.57) -> OK
      - Resultado a mano: bruto -118.26 + swap 0.00 (0 noches) = -118.26 (motor: bruto -118.26 + swap 0.00 (0 noches) = -118.26)

## Costes y supuestos del backtest
- Spread real del CSV por minuto (Ask = Bid + spread × 0,1): se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (la ficha). Aviso de la ficha (supuesto 30): el spread es de RoboForex medido de 2017-12 a 2026; antes es un perfil fabricado, y puede ser optimista (10 a 15 % más barato que OANDA hoy).
- Swap largo −6,9 % anual, base 365, sobre el nocional (cierre Bid de la última vela M30 antes de la medianoche × lote × 1), una vez por cada noche de lunes a viernes al pasar las 00:00 del servidor (la noche del viernes cuenta una vez), sin día triple. Se suma al resultado de cada operación y entra en el factor de beneficio y en la caída. Se cobra en la curva de equity en el momento en que pasa la medianoche.
- Símbolo: punto 0,1; 1 lote = 1 USD por unidad de índice; lote 0,01 a 300; stops level 5 puntos; horario 01:01–23:59 L–V; riesgo 1 % de 100.000 (1.000 USD); lote redondeado hacia abajo.
- Cada tramo se corre por separado empezando sin posición; los indicadores se calculan sobre toda la serie (solo con datos pasados). Una posición abierta al final de un tramo se cierra al Bid de la última vela (motivo `fin_segmento`).
- Equity: capital + resultado de operaciones cerradas + swap cobrado + resultado flotante al Bid de cierre de cada vela M30; la caída máxima sale de esa curva.
- Un stop y su toque en el mismo minuto: gana el stop. Resolución intrabar con M1.
- Todo lo demás: los 30 supuestos del pseudocódigo de la ficha.

## Lectura honesta
- Falla el factor de beneficio (1,18 frente a 1,3), también sin swap (1,22): el swap empeora el resultado pero no es la causa.
- Un tramo sostiene el resultado: primeros 3 años fuera de muestra FB 1,29 con 386 operaciones; el resto, FB 0,99 con 224. Por año, el mejor (2024) pesa mucho más que los demás.
- Frecuencia 10,8 al mes frente a las ~6 del plan; la caída 8,58 % supera el 6 % del plan; la posición puede pasar el fin de semana (la hipótesis no cierra el viernes).
- Coherente con la fase 02: la ventaja sobre la línea base era pequeña y el filtro y el disparo no aportaban sobre un control sin ellos.
