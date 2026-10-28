# MI PLAN DE TRADER · 2026-10-28

## Lo que quiero conseguir
«Tener una ganancia mensual variable entre 2000 - 3000 usd», sobre una cuenta de fondeo de 200.000 USD (un 1 % a 1,5 % mensual). El «para qué» no se respondió: ingreso adicional, no sustituto de un sueldo (supuesto).

## Mis límites (el Director los usa en todas mis fichas)
- Riesgo por operación: 1 % de la cuenta (2.000 USD fijos; el lotaje se calcula por la distancia al stop)
- Caída máxima de la cuenta: 12 % en fondeo (en cuenta propia aguantaría 30 %) → si la toco, apago y reviso (regla de apagado)
- Caída máxima que acepto en un backtest: 6 % (la mitad del límite de 12 % del fondeo) (supuesto)
- Tiempo al día: 2 horas, para revisar y supervisar; los robots operan solos · Horario: 24 horas (zona horaria UTC-3, Buenos Aires)
- Frecuencia: unas 6 operaciones al mes por estrategia
- Mercados: XAUUSD, US100, BTCUSD, US500, USDJPY, EURUSD, US30 (CFDs) · Plataforma: MetaTrader 5 (MT5), con robots
- Lo que no hago: dejar operaciones abiertas el fin de semana
- Fondeo: pérdida máxima total 12 % · pérdida máxima diaria 5 % · objetivo 10 % en fase 1 y 8 % en fase 2 · sin mínimo de días · sin regla de consistencia · PENDIENTE: si la caída se mide sobre el balance inicial o sobre el pico, y si el límite diario cuenta la pérdida flotante

## Qué estrategias encajan conmigo
- Automáticas (robots) en MT5, que no necesiten que yo mire la pantalla.
- Que cierren todo antes del cierre del viernes.
- Pocas operaciones al mes, con stop definido para calcular el lotaje al 1 %.
- Sobre cualquiera de mis 7 mercados, sin horario fijo.
- Con una caída de backtest de 6 % o menos.

## Qué NO encaja conmigo
- Estrategias que mantienen la posición el fin de semana.
- Estrategias discrecionales que exigen estar frente a la pantalla.
- Estrategias sin stop, porque no puedo fijar el riesgo en 2.000 USD.

## Mi riesgo principal
Con pocas operaciones al mes y 2.000 USD por operación, una racha mala pega fuerte, y varios robots en mercados parecidos (XAUUSD, US100, US500, US30) pueden perder a la vez y acercarme al límite de 12 %. Dije que en una racha sigo la estrategia sin modificarla; es una fortaleza, pero no la puedo comprobar sin historial (supuesto).

## Lo que digo frente a lo que hago
Sin historial todavía: pasa tu historial por el Auditor TIS (herramientas/auditor-tis.html) y vuelve a /objetivos.

## Mis límites en números
Fuente: ESTIMACIÓN (no hay backtest), 2026-10-28, con 40 % de acierto y ganancia media 1,5 veces la pérdida media (supuesto neutro, sin ventaja), 6 operaciones al mes, 1 % por operación, 12 meses, 10.000 simulaciones.
- Pérdidas seguidas hasta mi caída del plan (6 %): 7.
- Racha de pérdidas en 12 meses: la mitad de las veces 7 o más; 1 de cada 20 veces, 12 o más.
- Probabilidad de tocar el 6 %: 90 %. De tocar el 12 % (fondeo perdido): 37 %.
- Límite diario del 5 %: harían falta 5 pérdidas en un día; con mi frecuencia no lo toco.
Lo que me toca aguantar sin cambiar nada: una racha de 7 pérdidas seguidas. Con una estrategia con ventaja real estos números mejoran; lo mide el backtest.

## Lo que no cuadraba y cómo lo resolví
- Con 6 operaciones al mes por estrategia y 2.000 USD por operación, las rachas malas pesan: se dejó así y que el backtest decida (el trader respondió «dale»; interpretación mía, confírmala).
- La ficha fichas/xauusd_ruptura_donchian_eficiencia.md mantiene la posición el fin de semana (supuesto 14): choca con mi límite. Se corrige en la fase 03 (cerrar antes del cierre del viernes).

## Supuestos
1. El «para qué» de la meta no se respondió: ingreso adicional.
2. Caída máxima aceptada en backtest: 6 % (la mitad del límite de 12 %).
3. Estimación con 40 % de acierto y ratio 1,5, sin backtest.
4. No dije si seguiré lo mismo en rachas con dinero propio; con fondeo, sigo la estrategia.
5. Reglas de fondeo copiadas de lo que dijo el trader; quedan PENDIENTES los detalles de cómo se mide la caída.

## Revísalo
Cuando cambie tu capital, tu tiempo o tu objetivo, o cada 3 meses: /objetivos
