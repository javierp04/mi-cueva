# Reporte fase 04 · XAUUSD ruptura Donchian con eficiencia (M30, solo compras)

Código: `codigo/xauusd_ruptura_donchian_eficiencia.py` (se ejecuta en unos 8 segundos).
Operaciones: `resultados/xauusd_ruptura_donchian_eficiencia_operaciones.csv` · Curva: `resultados/xauusd_ruptura_donchian_eficiencia_equity.svg` (ábrela en el navegador) · Cifras: `..._resultados.json`.

## Datos
datos/XAUUSD.csv · XAUUSD · M1 (precios Bid, hora del servidor = NY + 7) · 2006-01-02 00:01 a 2026-09-17 02:58 · 7.341.149 velas M1 · 249.117 velas M30. No existe informe de calidad (resultados/XAUUSD_calidad.md): se avisa.
Corte 70/30 por velas M30: dentro de muestra 2006-01-02 a 2020-05-22 10:30 (174.381 velas); fuera de muestra 2020-05-22 11:00 a 2026-09-17 (74.736 velas).

## Los 4 números, FUERA de muestra y con costes
| Número | Resultado | Umbral | |
|---|---|---|---|
| Factor de beneficio | 1,52 | ≥ 1,3 | ✓ |
| Operaciones | 756 | ≥ 30 | ✓ |
| Caída máxima | 8,57 % | < 20 % | ✓ |
| Factor de beneficio sin la mejor operación | 1,49 | > 1 | ✓ |

Veredicto 4/4 · APRUEBA el método.
AVISO con MI_PLAN.md: la caída de 8,57 % supera el 6 % que el trader acepta en backtest. Pasa el método, no encaja con el plan.

## Dentro de muestra (solo referencia, no cuenta para el veredicto)
Factor de beneficio 1,69 · 1.607 operaciones · caída 7,90 % · sin la mejor 1,67.

## Otros datos fuera de muestra
Ganancia neta 105.039 USD sobre 100.000 (riesgo de 1.000 por operación) · ganadoras 42,5 % · ganancia media por operación 139 USD · mejor +6.693 · peor −1.000 (dentro de muestra el peor fue −2.378 por un hueco de precio) · caída solo con operaciones cerradas 7,50 % (la oficial, 8,57 %, usa también la pérdida flotante al cierre de cada vela M30).
Se cierran 79 operaciones con hueco (stop_gap) sobre 2.363 en total.

## Costes y supuestos del backtest
- Costes: el spread real del CSV (columna spread, en puntos de 0,01 USD) se suma al Bid para el Ask en cada minuto: se entra al Ask y se sale al Bid. Comisión 0 y deslizamiento 0 (supuesto: la hipótesis no los pide; costes ×2 se prueban en la fase 06). Sin swap.
- Símbolo (supuesto): 100 oz por lote, paso 0,01, mínimo 0,01, máximo 100, USD; 1 punto = 0,01 USD.
- Riesgo fijo 1 % del capital inicial (1.000 USD); lote = riesgo / (distancia al stop × 100), redondeado hacia abajo.
- Cada segmento se corre por separado empezando sin posición; indicadores calculados sobre toda la serie (solo con datos pasados). Una posición abierta al final de un segmento se cierra al Bid de la última vela (no ocurrió ninguna con ese motivo).
- Equity: capital + resultado de operaciones cerradas + resultado flotante al Bid de cierre de cada vela M30; la caída máxima sale de esa curva (más estricta que solo operaciones cerradas).
- Precio del Ask dentro de un minuto = Bid + spread de ese minuto. Un stop y su toque en el mismo minuto: gana el stop. Resolución con las M1.
- Todo lo demás: los 22 supuestos del pseudocódigo de la ficha.

## Lectura honesta
- La fase 02 ya mostró que la ventaja viene de romper el máximo de 55 y seguir el movimiento, no del filtro ni del disparo. 4/4 no dice que esos dos aporten algo.
- Posiciones que cruzan el fin de semana (la hipótesis no cierra el viernes) y unas 120 operaciones al año, no las ~6 al mes del plan.
- Pocas ganadoras grandes sostienen el resultado (42 % de aciertos).
