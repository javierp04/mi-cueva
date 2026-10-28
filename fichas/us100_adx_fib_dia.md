# FICHA · US100 ruptura de la extensión 1,382 del día con ADX(75) subiendo (M15)
Regla: Compro US100 en velas de 15 min cuando, al cierre de una vela, el ADX de 75 velas sube, rising(adx(75),5): dejo una orden de compra stop en el nivel fib_day(1,382) = mínimo de ayer + 1,382 × (máximo de ayer − mínimo de ayer), con el nivel congelado y válida 4 velas (una nueva activación la reemplaza). Salgo cuando el precio toca el stop vigente: el stop inicial a 2,5 × ATR(30) (SMA del rango verdadero) del precio de entrada, que se sustituye por el trailing de 3 × ATR(30) bajo el cierre, actualizado al cierre de cada vela. Stop: 2,5 × ATR(30). Horario: lunes a viernes 01:01–23:59 hora del servidor del bróker (hora de Nueva York + 7 h; inicio incluido, fin excluido). Riesgo: 1 % del capital inicial (100.000) por operación.
Por qué funcionaría: cuando la fuerza de la tendencia crece (ADX subiendo) y el precio supera la extensión 1,382 del rango de ayer, la ruptura suele atraer a quien llega tarde y disparar los stops de quien vendió esperando un giro; el seguimiento de tendencia también se ve como una prima por aguantar rachas de pérdidas pequeñas. (propuesta, confírmala)

## Hipótesis completa del trader (textual)
Copiada sin cambios el 2026-10-28. Es la fuente de verdad de esta ficha. El texto no dice el activo ni la temporalidad; ver supuestos de la Fase 01. El trader aclaró después (2026-10-28) que la temporalidad es M15.

```
ENTRADA LONG:
  Armado:
  1. [TRIGGER] rising(adx(75),5)
  Orden: STOP en fib_day(1.382), nivel congelado al armarse; vigencia 4 velas, luego se cancela. Mientras el trigger siga verdadero no se modifica; una nueva activación reemplaza nivel y vencimiento (y, con atr_ref: signal, fotografía otro ATR).
ATR          : SMA móvil del True Range
CAPITAL INICIAL: 100000 unidades monetarias de la cuenta
SIZING       : 1% de riesgo sobre capital inicial; lotaje = riesgo / distancia al SL, redondeado hacia ABAJO al paso de lote del símbolo y acotado a su lote mínimo y máximo
SALIDAS      : SL inicial 2.5 × ATR(30); trailing 3 × ATR(30) actualizado al cierre de cada barra
REENTRADA    : una activación nueva en la vela de salida puede generar otra entrada desde la siguiente vela disponible; las órdenes stop/limit deben alcanzar su nivel. No hay reentrada normal en la misma vela
MERCADO      : sesiones en hora del servidor del bróker; inicio incluido, fin excluido
               lunes a viernes: 01:01–23:59
               Los días y horarios no declarados quedan cerrados, incluidos sábados y domingos si no tienen sesiones
VELAS        : el calendario NO recorta la serie: las velas se agregan con todas las M1 del archivo, incluidas las horas cerradas, y los indicadores se calculan sobre esa serie completa, que es la misma que construye el terminal
               Sólo se forman velas con M1 disponibles: una hora incompleta conserva su marca HH:00 y no se rellenan minutos ausentes
               Vencimientos, salidas por tiempo y cualquier contador en barras recorren esa serie entera, estén sus velas dentro o fuera de sesión
               El calendario autoriza acciones por el minuto real de cada una, no por la marca de la vela que la contiene: una vela que empieza cerrada y abre a mitad no queda bloqueada entera
               execution.trading_window es otra cosa: expresa cuándo la estrategia decide operar dentro de un mercado ya abierto
EJECUCIÓN    : si una vela contiene a la vez SL y TP, se recorren sus M1 en orden; si ambos niveles caen en el mismo minuto o faltan M1, gana el SL (execution.intrabar_resolution: m1; sl_tp_same_bar: sl_first); la salida por tiempo sostiene N barras completas DESPUÉS de la barra del fill y cierra en la apertura siguiente (execution.time_exit_mode: after_full_bars); reproduce motores que recién observan el fill intrabar al comenzar la vela posterior
AL PORTAR    : Nivel de la pendiente: tras cerrar la vela de señal, calcular el nivel con los datos hasta ese cierre INCLUSIVE y congelarlo al armar la orden. Se coloca en la apertura siguiente y no se recalcula mientras vive
               Trailing: primera actualización al cierre de la vela de ENTRADA, sin exigir avance previo; la distancia usa el ATR(30) de la vela que acaba de cerrar, no el congelado al armar. Adentro de la vela rige el nivel anterior: el stop nuevo vale recién desde la apertura siguiente
               Bid/Ask: los indicadores se calculan sobre Bid. Un long entra al Ask y liquida al Bid; un short entra al Bid y liquida al Ask, que es como disparan un buy stop y un sell stop en MT5. El trailing se ancla en el cierre del lado que liquida
BRÓKER       : Colocación: la orden se pide una sola vez, en el primer tick de la vela siguiente a la señal. Si la cotización ya está en el nivel o pasada de él no hay pendiente válida que colocar: se entra a mercado en ese tick
               Fill: al nivel. Si la vela —o el mercado, al reabrir— abre ya pasada del nivel, a esa apertura, que es lo que cobra un bróker real. El SL y el TP se calculan con el precio REAL de entrada, no con el nivel: después de un fill con gap hay que recalcularlos
               Vencimiento: orden GTC, sin expiración del bróker. La orden vive 4 velas de la serie completa —las de horas cerradas también cuentan— desde la de colocación, incluida, y se borra en el primer tick de la vela siguiente. Si el bróker rechaza el borrado por mercado cerrado, reintentarlo en CADA TICK hasta que entre, no en la vela siguiente. El fill va primero: si esa vela —o el mercado, al reabrir— abre ya en el nivel o pasada de él, la orden se llena antes de poder borrarla, y el backtest también la llena
               Reemplazo: una activación nueva cancela la orden y coloca otra —el lotaje cambia con el ATR—; no es una modificación del precio. El borrado se CONFIRMA antes de colocar la nueva: si el bróker no lo confirma, la anterior sigue viva con su nivel, su vencimiento y su ATR, y la nueva no se coloca. Si el bróker rechaza la nueva por stops level, la anterior ya no está
               Mercado cerrado: colocar, reemplazar y cancelar se piden una sola vez. Si el bróker rechaza por mercado cerrado NO se reintenta ni se traslada a la reapertura: la señal se pierde, el reemplazo deja la orden anterior como estaba y la cancelación por activación inversa la deja viva hasta vencer
               Stops level: 5 puntos. La pendiente pedida a menos de esa distancia de la cotización se rechaza y no se reintenta; la entrada cuyo SL o TP queda más cerca se descarta. Se compara en puntos enteros
               Modificación del stop: el backtest da por hecho que el stop nuevo rige desde que se calcula y que un toque sólo cuenta con el mercado abierto. Hasta que la modificación se confirma, el stop VIGENTE en el bróker es el anterior, y el EA lleva las dos cosas por separado: pide el nivel una vez calculado y, si el bróker lo rechaza —mercado cerrado, stops level—, lo RECUERDA como objetivo y lo reintenta en cada tick, sin recalcularlo, sin aflojarlo con el cálculo de la vela siguiente y releyendo la posición para confirmar el stop aplicado. Si la cotización cruza el objetivo antes de la confirmación, cierra a mercado, al precio de ese tick, no al nivel: un objetivo recordado no es un stop aceptado, y sólo protege mientras el EA corre y está conectado
               Reintentos: lo que se reintenta en cada tick —el borrado de una vencida, el stop nuevo del trailing— consulta antes la tabla de sesiones del símbolo, y con la sesión cerrada no se envía. Las operaciones no cambian, porque el bróker lo iba a rechazar, y deja de recibir una solicitud por tick durante todo el cierre
```

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: director · escritor-hipotesis (manual seguido por el director)
Qué se hizo: regla revisada campo a campo. ✅ disparo rising(adx(75),5), con supuesto · ✅ orden stop de 4 velas, nivel congelado, reemplazo por activación nueva · ✅ stop inicial 2,5 × ATR(30) · ✅ trailing 3 × ATR(30) al cierre de cada vela · ✅ sizing (1 % de 100.000, lote hacia abajo) · ✅ horario lunes a viernes 01:01–23:59 · ✅ fib_day(r) = prev_day_low + r · (prev_day_high − prev_day_low), definido por el trader · ⚠️ activo y temporalidad: el texto no los dice · ⚠️ rising(x,5): no dice si es «mayor que hace 5 velas» o «5 velas seguidas subiendo».
Resultado: hipótesis completa y medible; solo compras («ENTRADA LONG»). Encaja con MI_PLAN.md en mercado (US100), plataforma y vela de 15 minutos (M15); la frecuencia se mide en la fase 04. Igual que en las otras fichas, no cierra el viernes y el plan dice que no se deja posición el fin de semana: la regla manda como está escrita.
Supuestos: (1) Activo US100: el texto trae stops level de 5 puntos y horario 01:01–23:59, que son los del símbolo US100 (confirmar). (2) Temporalidad M15: dato del trader (corrección del 2026-10-28; antes se había supuesto M30 y esa suposición era errónea). (3) rising(x,5) = el valor de la vela cerrada es mayor que el de hace 5 velas (igual no cuenta). (4) ADX(75) = ADX de Wilder con periodo 75, calculado sobre Bid. (5) Activación = la vela cuyo cierre deja rising(adx(75),5) pasando de falso a verdadero. (6) Solo compras. (7) El resto de la mecánica (ATR = SMA del rango verdadero, orden stop colocada en la apertura siguiente, reemplazo, gap, trailing con el ATR de la vela recién cerrada, entra al Ask y sale al Bid) es la misma que en las fichas de XAUUSD y US100. (8) Costes: spread por minuto y swap del símbolo US100, como en la ficha de US100 (los modela la fase 04). (9) fib_day: el día es el día del servidor (de 00:00 a 24:00, hora de Nueva York + 7 h); «ayer» es el día anterior con velas (el lunes usa el viernes); máximo y mínimo con todas las velas de ese día, incluidas las de 01:00; sobre Bid; para una vela de señal, «ayer» es el día anterior al de esa vela. El nivel queda por encima del máximo de ayer (cuesta 0,382 veces el rango de ayer) y se congela al armar la orden.
Veredicto: APRUEBA
Siguiente paso: fase 02 (AED) con datos/us100_15m_mt5.csv, solo con el primer 70 %.

## Fase 02 · AED (M30, HISTÓRICO: la temporalidad era M15; no vale) · CRITERIO + DATOS
Agente / skill: director · aed (código: codigo/us100_adx_fib_dia_aed.py)
Qué se hizo: datos/US100.csv (M1, 2011-01-03 a 2026-09-17) pasado a velas M30 y solo el primer 70 % (2011-01-03 a 2022-01-05 17:00, 126.474 velas, el mismo corte de la ficha de US100); el 30 % final queda reservado para la fase 04. Sin pre-registro. Se midió el retorno, en unidades de ATR(30) de la vela de señal, a 1, 5 y 20 velas desde el fill de la orden stop en fib_day(1,382), colocada en la apertura siguiente a la señal y viva 4 velas (fill a la apertura si abre en o sobre el nivel), contra la línea base (cualquier vela) y dos controles.
Resultado: la regla (2.333 órdenes armadas, 349 llenadas, 15,0 %; 11 se descartaron por estar el nivel a menos de 5 puntos de la cotización) da +0,08 ATR a +1 vela, +0,34 a +5 y +0,69 a +20 (mediana +0,75; el 60,7 % sube). Línea base, cualquier vela: +0,01, +0,05 y +0,17 a +20 (mediana +0,37; 55,6 % sube). Control con la orden armada en cada vela, mismo nivel y sin ADX (11.953 llenadas): +0,32 a +20 (mediana +0,39; 55,7 % sube). Control con toda vela de ADX subiendo, no solo la primera: +0,24 a +20. Dos casos, como aclaró el trader: (A) el precio estaba por debajo del nivel y sube hasta él dentro de las 4 velas, es la ruptura de verdad: 129 casos, +1,04 ATR a +20 (mediana +0,77; 59,7 % sube); (B) el precio ya estaba en el nivel o más allá al armar la orden, o abre pasado del nivel: entrada a la apertura, a un precio peor que el nivel, 220 casos (63 % de las entradas), +0,48 ATR a +20 (mediana +0,74; 61,4 % sube). El ADX empezando a subir sí aporta algo sobre el nivel solo. Por año (casi todos con 25 a 41 casos, solo pistas): supera a la línea base en 8 de 11 años y al control en 9 de 11; pierden 2013 (−0,94) y 2016 (−0,47), y 2012 queda en cero. Frecuencia: unas 32 operaciones al año en este tramo, menos que las 6 al mes de MI_PLAN.md.
Supuestos: sin pre-registro; línea base = cualquier vela con el mismo ATR; activación = rising(adx(75),5) pasa de falso a verdadero, con rising = mayor que hace 5 velas; ADX de Wilder sobre Bid; ayer = día anterior con velas, día del servidor, y el nivel queda congelado con el «ayer» de la vela que armó la orden aunque las 4 velas crucen el rollover; el nivel equivale a máximo de ayer + 0,382 × rango de ayer (aclaración del trader); nivel a menos de 5 puntos de la cotización: la orden se rechaza y no se reintenta; sin costes, spread, swap ni stop (eso es de la fase 04); la media de todas las variantes incluye la subida del índice de 2011 a 2021.
Veredicto: APRUEBA (la regla supera a la línea base y a los controles con 360 casos; solo es AED sin costes: la fase 04 es el filtro real)
Siguiente paso: fase 03 (reglas) con el agente reglas, sin tocar ningún parámetro.

## Fase 02 · AED (M15, la que vale desde 2026-10-28) · CRITERIO + DATOS
Agente / skill: director · aed (código: codigo/us100_adx_fib_dia_aed_m15.py)
Qué se hizo: el trader corrigió la temporalidad: la regla es de M15, no de M30. Con los M1 se armó datos/us100_15m_mt5.csv (357.493 velas de 15 minutos, 2011-01-03 a 2026-09-17; informe en resultados/us100_15m_mt5_calidad.md: APTA CON AVISOS, faltan el 2,8 % de las velas dentro del horario, sin rellenar). AED solo con el primer 70 % de las velas (250.245 velas, 2011-01-03 a 2022-01-05 09:30); el 30 % final queda reservado para la fase 04. Mismas mediciones de la versión M30: retorno en ATR(30) de la vela de señal a 1, 5 y 20 velas desde el fill de la orden en fib_day(1,382), vigencia 4 velas (una hora), contra la línea base y dos controles.
Resultado: la regla (4.531 órdenes armadas, 486 llenadas, 10,7 %) da +0,12 ATR a +1 vela, +0,30 a +5 y +0,63 a +20 (mediana +0,47; el 58,2 % sube). Línea base, cualquier vela: +0,01, +0,04 y +0,16 a +20 (mediana +0,27; 54,3 % sube). Control con la orden armada en cada vela, mismo nivel y sin ADX (19.370 llenadas): +0,26 a +20 (mediana +0,29; 54,8 % sube). Control con toda vela de ADX subiendo: +0,25. Casos: (A) el precio sube hasta el nivel, ruptura de verdad: 210 casos, +0,66 ATR a +20 (mediana +0,47; 55,7 % sube); (B) el precio ya estaba en el nivel o más allá, entrada a la apertura: 276 casos (57 %), +0,60 a +20 (mediana +0,47; 60,1 % sube). Por año (40 a 56 casos casi todos): supera a la línea base en 9 de 11 años y al control en 7 de 11; pierden 2014 (−0,11) y 2017 (−0,29). Frecuencia: unas 44 operaciones al año en este tramo. La regla supera a la línea base y a los controles en media, mediana y proporción de casos que suben.
Supuestos: los mismos de la versión M30 (rising = mayor que hace 5 velas; ADX de Wilder sobre Bid; activación = pasa de falso a verdadero; «ayer» = día del servidor anterior con velas; nivel congelado; nivel a menos de 5 puntos: se rechaza); sin costes, spread, swap ni stop (eso es de la fase 04); la muestra incluye la subida del índice de 2011 a 2021.
Veredicto: APRUEBA (la regla supera a la línea base y a los controles con 486 casos; solo es AED sin costes: la fase 04 es el filtro real)
Siguiente paso: fase 03 en M15 (mismo pseudocódigo, velas de 15 minutos) y repetir la fase 04.

## Fase 03 · Reglas (M15; el pseudocódigo no cambia de forma, solo la vela) · MOTOR
Agente / skill: reglas (manual seguido por el director)
Qué se hizo: se tomó el pseudocódigo aprobado de la ficha US100 ruptura Donchian con eficiencia (7 pasos) y se reutilizó su estructura y su mecánica, sin cambiar ningún parámetro del trader ni añadir nada. Solo se cambió lo propio de esta regla: disparo rising(adx(75),5) sin filtro, nivel fib_day(1,382), vigencia de 4 velas, stop inicial de 2,5 × ATR(30) con el ATR fotografiado en la vela de señal, trailing de 3 × ATR(30) y lote calculado con ese stop.
Resultado: pseudocódigo de 7 pasos, escrito en velas de 15 minutos (la versión anterior, de 30, queda reemplazada), con 30 supuestos decididos (abajo). Sin huecos: orden de las salidas fijo, vigencia de 4 velas contada desde la VELA DE COLOCACIÓN, los tres casos del nivel (espera, mercado, no se coloca) y qué pasa si no se cumple nada.
Supuestos: los 30 de la lista de abajo; los que más pesan son el 8 (el ATR del stop inicial y del lote sale de la vela de señal), el 9 (el nivel usa el «ayer» de la vela de señal y no cambia aunque cruce el rollover), el 5 (activación) y el 13 (el trailing solo sube).
Veredicto: APRUEBA (pseudocódigo sin huecos; las especificaciones del símbolo son datos del trader)
Siguiente paso: fase 04 con costes sobre datos/US100.csv (M1) y las velas M15 (70 % dentro de muestra, 30 % fuera), sin tocar parámetros.

> NOTA. La hipótesis no cierra posiciones el viernes: la posición sigue hasta que la toca el stop. MI_PLAN.md dice que el trader no deja operaciones abiertas el fin de semana. La regla manda tal como el trader la escribió; no se agregó ningún cierre.

### Pseudocódigo · US100 ADX(75) subiendo + extensión 1,382 del día (M15, solo compras)

```
DATOS: US100, velas de 15 minutos (M15), solo compras. Horas = las del servidor del bróker
  (hora de Nueva York + 7 h). Horario operable de US100 (dato del trader): lunes a viernes
  01:01–23:59, inicio incluido, fin excluido.
  Precios: los indicadores se calculan sobre Bid. COMPRA se hace al Ask; SALGO se hace al Bid.
  Ask = Bid + spread de la vela (la columna spread del CSV, en puntos de 0,1 unidades).
  PUNTO = 0,1 unidades de índice. STOPS_LEVEL = 5 puntos = 0,5 unidades (dato del bróker).
  Velas: se arman con TODAS las M1 del archivo (también las de horas cerradas, como las de
  01:00) y los indicadores usan esa serie completa. Solo existen velas con M1; no se rellenan minutos.
  MERCADO ABIERTO en un minuto = lunes a viernes, de 01:01 (incluido) a 23:59 (excluido).
  Cada acción (colocar, borrar, tocar un stop) vale según el minuto real en que ocurre.
  Capital inicial = 100.000 USD (cuenta en USD, apalancamiento 1:100). RIESGO = 1 % del capital
  inicial = 1.000.
  VALOR_UNIDAD = 1 USD por lote por cada unidad de índice (dato del trader). Paso de lote 0,01,
  mínimo 0,01, máximo 300.
  COSTES (modelo; el cálculo y la prueba son de la fase 04):
    - Spread: el de la última columna del CSV en cada vela, en puntos de 0,1. Si falta, 5 puntos
      (la mediana). Es el único coste de entrada y salida (Ask = Bid + spread).
    - Comisión = 0. Deslizamiento = 0.
    - Swap (solo compras, aplica el largo): -6,9 % anual, base 365 días, sobre el valor nocional
      (precio x lote x contract_size 1). Se cobra una vez por cada noche de lunes a viernes, al pasar
      el rollover de las 00:00 hora del servidor, con coeficiente 1 (sin día triple).
  Una sola operación a la vez. Al empezar: sin operación, sin ORDEN VIVA, sin SEÑAL.

  Definiciones (al cierre de cada vela, sobre Bid):
    ATR = media simple de los últimos 30 rangos verdaderos (rango verdadero = el mayor entre
          máximo-mínimo, |máximo-cierre anterior| y |mínimo-cierre anterior|).
    ADX = ADX de Wilder de periodo 75.
    DISPARO = el ADX de esta vela es mayor que el ADX de hace 5 velas (igual no cuenta).
    ACTIVACIÓN = DISPARO verdadero ahora y DISPARO falso en la vela anterior.
    Sin las velas suficientes para calcular algo, DISPARO y ACTIVACIÓN son falsos.
    DÍA = día del servidor (de 00:00 a 24:00). AYER = el día anterior al DÍA de la vela de señal
          que tenga velas (el lunes usa el viernes; si hay festivo, el último día con velas).
    MAX_AYER y MIN_AYER = el mayor máximo y el menor mínimo (Bid) de TODAS las velas de AYER,
          incluidas las de 01:00.

CADA VELA NUEVA (la llamo VELA ACTUAL), en este orden:

  1. Al empezar la VELA ACTUAL (haya o no mercado abierto):
       SI hay una ORDEN VIVA: VIDA = VIDA + 1.

  2. En el PRIMER TICK de la VELA ACTUAL:
       a. SI estoy fuera y hay una ORDEN VIVA y el Ask está en NIVEL o por encima:
            COMPRA al Ask de ese tick (si abrió con gap, a esa apertura). Ve al paso 4.
       b. SI hay una ORDEN VIVA con VIDA >= 5 (ya vivió sus 4 velas):
            pido borrarla. SI el mercado está cerrado, se reintenta en cada tick con mercado
            abierto (sin enviar nada con la sesión cerrada); en el primer tick con mercado
            abierto se hace antes el punto a (la orden se llena si abre en NIVEL o más allá)
            y, si no se llenó, se borra. Orden borrada: ya no hay ORDEN VIVA.
            Sigo con el punto c si hay SEÑAL; si no, ve al paso 3.
       c. SI hay una SEÑAL (la dejó la vela anterior) y estoy fuera:
            - SI el mercado está cerrado en ese minuto: la SEÑAL se pierde, no se
              reintenta. La ORDEN VIVA anterior, si la había, queda como estaba.
            - SI NO: SI hay una ORDEN VIVA, la cancelo y espero a que el borrado se confirme
              (si no se confirma, la anterior sigue con su NIVEL, su VIDA y su ATR_ORDEN, y la
              nueva no se coloca). Luego:
                * Caso B: SI el Ask ya está en NIVEL_SEÑAL o por encima: COMPRA al Ask de ese
                  tick (a mercado, a un precio igual o peor que el nivel). Ve al paso 4.
                * Caso C: SI NO, SI NIVEL_SEÑAL - Ask < 5 puntos enteros (0,5 unidades): el
                  bróker rechaza la orden y no se reintenta; no queda ORDEN VIVA (la anterior
                  ya no está).
                * Caso A: SI NO, coloco una ORDEN VIVA de COMPRA STOP con NIVEL = NIVEL_SEÑAL,
                  ATR_ORDEN = ATR_SEÑAL y VIDA = 1. La VELA ACTUAL es la VELA DE COLOCACIÓN.
            Borro la SEÑAL (se usa una sola vez).

  3. Durante la VELA ACTUAL, recorriendo sus M1 en orden, con mercado abierto:
       SI estoy fuera y hay una ORDEN VIVA con VIDA <= 4 y el Ask alcanza NIVEL:
         COMPRA en NIVEL. Ve al paso 4.

  4. Tras cualquier COMPRA (en el paso 2 o en el 3):
       PRECIO_ENTRADA = el precio real de la compra. La ORDEN VIVA desaparece.
       ATR_STOP = ATR_ORDEN de la orden (si la compra fue a mercado en el paso 2c, el ATR_SEÑAL
                  de la SEÑAL que la originó). Es el ATR fotografiado en la vela de señal.
       DISTANCIA = 2,5 x ATR_STOP, en unidades de índice.
       SL_INICIAL = PRECIO_ENTRADA - DISTANCIA (con el precio real, no con NIVEL).
       SI DISTANCIA < 5 puntos enteros (0,5 unidades): la entrada se descarta (no hay operación).
         Ve al paso 6.
       LOTE = RIESGO / (DISTANCIA x VALOR_UNIDAD), redondeado hacia ABAJO al paso de lote del
              símbolo (0,01) y acotado entre su lote mínimo (0,01) y máximo (300).
       STOP_VIGENTE = SL_INICIAL. Ve al paso 5.

  5. MIENTRAS esté dentro, en cada vela nueva, en este orden:
       a. En cada minuto con mercado abierto (también el de la compra y los siguientes de
          la vela de entrada): SI la vela abrió con el Bid por debajo de STOP_VIGENTE,
          SALGO a esa apertura. SI NO, SI el Bid toca STOP_VIGENTE, SALGO en STOP_VIGENTE.
          Si la compra y el toque caen en el mismo minuto, gana el stop. Tras SALGO ve al paso 6.
       b. Al cierre de la VELA ACTUAL, si sigo dentro (también al cierre de la vela de
          entrada, sin exigir avance previo):
            TRAILING = cierre (Bid) de la VELA ACTUAL - 3 x ATR(30) de esa misma vela
                       (no el ATR_STOP fotografiado).
            SI TRAILING > STOP_VIGENTE: STOP_VIGENTE = TRAILING.
            El stop nuevo vale desde la apertura de la vela siguiente; dentro de la vela
            rige el anterior.

  6. Al cerrar la VELA ACTUAL, calculo los indicadores (siempre, haya o no operación) y:
       SI estoy fuera (sin operación) y hay ACTIVACIÓN:
         AYER = el día anterior con velas al DÍA de la VELA ACTUAL.
         NIVEL_SEÑAL = MAX_AYER + 0,382 x (MAX_AYER - MIN_AYER)
                       (igual a MIN_AYER + 1,382 x (MAX_AYER - MIN_AYER)). Se calcula ahora y
                       queda congelado, aunque las 4 velas de vigencia crucen el rollover.
         ATR_SEÑAL = ATR(30) al cierre de la VELA ACTUAL (la fotografía; fija el stop inicial
                     y el lote).
         SEÑAL = lista para pedirse en el primer tick de la vela siguiente.
         (Una salida en esta misma vela no impide la ACTIVACIÓN: puede haber reentrada
         desde la vela siguiente. En esta misma vela no hay otra entrada.)
       SI NO (no hay ACTIVACIÓN, o estoy dentro): no hay SEÑAL nueva. Mientras no haya otra
         ACTIVACIÓN, la ORDEN VIVA no cambia: NIVEL, VIDA y ATR_ORDEN siguen igual.

  7. SI no se cumplió nada de lo anterior → no hago nada. FIN de la vela.
     Si la orden agota sus 4 velas sin llenarse, se borra (paso 2b) y no se opera hasta la
     próxima ACTIVACIÓN. Una posición abierta sigue abierta hasta que el stop la cierre.
```

Lo que viene del texto del trader y se aplicó tal cual (no son supuestos): disparo rising(adx(75),5) con activación; nivel fib_day(1,382) calculado al cierre de la vela de señal, congelado y colocado en la apertura siguiente; vigencia de 4 velas de la serie completa desde la de colocación incluida y borrado en el primer tick de la vela siguiente (el fill va primero); activación nueva reemplaza nivel y vencimiento, con borrado confirmado antes de colocar; entrada a mercado si el precio ya está en el nivel o más allá; fill con gap a la apertura, SL y lote con el precio real; ATR = SMA del rango verdadero; stop inicial 2,5 × ATR(30); trailing 3 × ATR(30) de la vela recién cerrada, desde la vela de entrada; sizing de 1 % sobre 100.000 con lote hacia abajo y acotado; entra al Ask y sale al Bid; con mercado cerrado se pide una sola vez y no se reintenta; stops level 5 puntos sin reintento; horario de lunes a viernes; reentrada desde la vela siguiente a la de salida; sin TP ni salida por tiempo.

Supuestos del pseudocódigo (todos decididos; solo lo que el texto no dice):
1. US100 y velas de 15 min (M15, dato del trader): supuestos de la Fase 01; solo compras («ENTRADA LONG»).
2. rising(x,5) = el valor de la vela cerrada es mayor que el de hace 5 velas; igual no cuenta.
3. ADX de Wilder de periodo 75 sobre Bid; necesita sus velas completas, antes de eso no hay señal.
4. No hay filtro de estocástico ni de eficiencia: el trader no los puso, así que la activación es solo el disparo.
5. Activación = DISPARO pasando de falso a verdadero al cierre de la vela; con posición abierta no se arman órdenes nuevas (las activaciones de ese tiempo se ignoran), pero los indicadores se calculan igual para saber si DISPARO estaba falso en la vela anterior.
6. Los indicadores se calculan siempre, también con posición abierta y con mercado cerrado.
7. Solo hay una posición a la vez; una activación con la orden viva y sin posición la reemplaza (nivel, vencimiento y ATR).
8. El texto dice que el reemplazo «fotografía otro ATR» y que «el lotaje cambia con el ATR». Decido, por ser lo más fiel: el ATR(30) de la vela de señal se guarda con la orden (ATR_ORDEN) y de él salen el stop inicial (2,5 × ATR_ORDEN, medido desde el precio real de entrada) y el lote (riesgo / distancia al stop). El trailing sí usa el ATR(30) de la vela recién cerrada, nunca el fotografiado.
9. fib_day: el día es el día del servidor (00:00 a 24:00, Nueva York + 7 h); «ayer» es el día anterior con velas al día de la vela de señal (el lunes usa el viernes); máximo y mínimo sobre Bid con todas las velas de ese día, incluidas las de 01:00. El nivel se calcula al cierre de la vela de señal con ese «ayer» y queda congelado aunque las 4 velas de vigencia crucen el rollover.
10. Nivel = máximo de ayer + 0,382 × rango de ayer (aclaración del trader, igual a mínimo de ayer + 1,382 × rango).
11. Caso A: si el precio está por debajo del nivel (a 5 puntos o más), la orden espera y entra al nivel si el Ask lo alcanza dentro de las 4 velas. Caso B: si el Ask ya está en el nivel o más allá, o la vela abre pasada, se compra a mercado en la apertura siguiente, a un precio igual o peor que el nivel. Caso C: si el nivel queda a menos de 5 puntos (0,5 unidades) por encima de la cotización, la orden se rechaza y no se reintenta. Se comprueba en ese orden (B, C, A).
12. Si la orden agota sus 4 velas, se borra y no se opera hasta la próxima activación; si la vela de colocación o la de reemplazo abre en el nivel o más allá, la orden vieja se llena primero (paso 2a).
13. Stop vigente = el mayor entre el SL inicial y el trailing; el trailing solo sube (el stop nunca se afloja). El texto no dice «solo sube».
14. Si una vela posterior abre con el Bid por debajo del stop, se sale a esa apertura (hueco); si no, en el nivel del stop. El texto lo da para entradas, no para salidas.
15. Si la compra y el toque del stop caen en el mismo minuto, gana el stop; si la compra y el stop caen en la misma vela se recorren las M1 desde el minuto de la compra.
16. Si tras un fill con gap el SL calculado con el precio real queda a menos de 5 puntos del Bid, la entrada se descarta (stops level); la orden queda consumida. Con DISTANCIA = 2,5 × ATR esto solo pasa con un ATR muy pequeño.
17. Sin objetivo de ganancia ni salida por tiempo: salen solo el SL inicial y el trailing.
18. Sin límite de operaciones por día; la posición puede pasar de un día a otro y de una semana a otra (ver NOTA). Sin cierre del viernes.
19. En el backtest, un borrado o un reemplazo con mercado abierto se confirma siempre; solo falla por mercado cerrado.
20. En real, el EA recuerda el stop del trailing si el bróker lo rechaza y lo reintenta en cada tick con sesión abierta; el backtest da por hecho que el stop nuevo rige desde la apertura siguiente y que un toque solo cuenta con el mercado abierto.
21. «Punto» = 0,1 unidades; las comparaciones del stops level (5 puntos) se hacen con enteros.
22. Si faltan datos (huecos), las velas se cuentan tal como están en el CSV, sin rellenar; las 4 velas de vigencia y el «hace 5 velas» se cuentan sobre esa serie.
23. Si no hay un día anterior con velas (inicio del archivo), no hay «ayer» y no hay activación.
24. Símbolo (dato del trader): punto 0,1; contract_size 1; 1 lote gana o pierde 1 USD por cada unidad de índice; paso de lote 0,01, mínimo 0,01, máximo 300; cuenta en USD, apalancamiento 1:100.
25. Stops level (dato del bróker): 5 puntos = 0,5 unidades. La hipótesis textual dice 4 porque se escribió para el oro; para US100 se usa 5.
26. Horario operable (dato del símbolo): lunes a viernes 01:01–23:59 hora del servidor, inicio incluido, fin excluido. La hipótesis textual dice 01:05 (copiada del oro); para US100 se usa 01:01. Hora del servidor = Nueva York + 7 h.
27. La columna spread del CSV está en puntos de 0,1 unidades; el Ask de una vela = Bid + spread × 0,1. Si falta, 5 puntos. Comisión 0, deslizamiento 0; el toque del NIVEL se mide con el Ask.
28. Swap (dato del trader): largo -6,9 % anual, base 365 días, una vez por cada noche de lunes a viernes al pasar el rollover de las 00:00 del servidor, coeficiente 1; la noche del viernes al sábado cuenta como una; nocional con el cierre Bid de la última vela antes del rollover.
29. AVISO de datos (dato del trader): los precios mezclan fuentes (2011-2014 Admirals, 2015-2026 Dukascopy, rueda asiática 2015-2018 OANDA); el CSV tiene barras fuera de la tabla operable (como las de 01:00) que cuentan para velas e indicadores pero no para operar.
30. AVISO de spread (dato del trader): la columna de spread es de RoboForex medida de 2017-12 a 2026; antes es un perfil fabricado y puede ser optimista. La fase 04 y la 06 deben leer sus costes con esta reserva.

## Fase 04 · Backtest (M30, HISTÓRICO: la temporalidad era M15; no vale) · MOTOR
Agente / skill: validador · validador-4de4 (código: codigo/us100_adx_fib_dia.py, derivado del motor de la ficha hermana de US100; reporte: resultados/us100_adx_fib_dia_reporte.md)
Qué se hizo: backtest con datos/us100_1m_mt5.csv (M1, 5.213.359 velas, 2011-01-03 a 2026-09-17) y el spread por minuto de datos/US100.csv; 180.678 velas M30. Corte 70/30 por velas: dentro de muestra hasta 2022-01-05 17:00, fuera de muestra 2022-01-05 17:30 a 2026-09-17 (54.204 velas). Costes: spread real del CSV (Ask = Bid + spread × 0,1), comisión 0, deslizamiento 0 y swap largo −6,9 % anual (base 365, sobre el nocional, una vez por noche de lunes a viernes a las 00:00 del servidor) incluido en cada operación, en el factor de beneficio y en la caída. Pseudocódigo tal cual, sin tocar parámetros. Cordura: 3 operaciones fuera de muestra (dos del caso B, una del caso A; las tres cruzan 1 a 2 noches) reconstruidas a mano por otro camino (resample de pandas, ADX con ewm, nivel desde las M1, swap con la última M1 antes de cada medianoche) coinciden con el motor en nivel, ATR, entrada, stop, lote, salida y swap.
Resultado: fuera de muestra y con costes, factor de beneficio 1,66 (✓, mínimo 1,3) · 150 operaciones (✓, mínimo 30) · caída máxima 5,94 % (✓, máximo 20 %) · factor de beneficio sin la mejor operación 1,51 (✓, mayor que 1) → 4/4. Sin swap el factor sería 1,74 (el swap resta 4.008 USD de 45.158 brutos). Dentro de muestra (solo referencia): FB 1,63, 334 operaciones, caída 10,74 %. Alertas: (1) un tramo sostiene el resultado: primeros 3 años fuera de muestra FB 2,08 (100 operaciones, +39.583 USD); el resto (2025-01 a 2026-09) FB 1,06 (50 operaciones, +1.567 USD) y sin la mejor 0,70; 2026 pierde (FB 0,66, −4.172 USD) y 2023 aporta 22.607 de 41.150 USD. (2) Caso A (ruptura, fill al nivel): 64 operaciones, FB 2,20; caso B (a mercado con el precio ya pasado, en promedio 82,6 puntos de índice sobre el nivel): 86 operaciones, FB 1,35; el B pesa 57 % de las entradas y es el más cercano al umbral. (3) Frecuencia 31,9 operaciones al año = 2,7 al mes (el plan dice unas 6). (4) Caída 5,94 % contra el 6 % del plan: encaja por muy poco. (5) 17 de 150 operaciones pasan un fin de semana (el plan dice que no se deja posición abierta); la regla no cierra el viernes.
Supuestos: datos con aviso (M1 NO APTA por 5,5 % de minutos faltantes, usado igual para resolver el orden del stop sin rellenar; M30 APTA CON AVISOS, 2,8 % de velas faltantes); spread de RoboForex medido de 2017-12 a 2026, antes es un perfil fabricado y puede ser optimista (supuesto 30); ADX de Wilder clásico con semilla en media simple de los primeros 75 valores (la ficha no fija la semilla; solo afecta al arranque); una compra consume la señal pendiente; precio del nocional del swap = cierre Bid de la última vela M30 antes de las 00:00; cada tramo se corre por separado desde 100.000, con la posición abierta al final cerrada al Bid de la última vela.
Veredicto: APRUEBA (4/4; con la reserva de que el resultado fuera de muestra viene de 2022 a 2024 y de que 2025-2026 apenas empatan)
Siguiente paso: fase 05 (skill optimizar: meseta de parámetros, no pico), sin bajar ninguno de los 4 números.

## Fase 04 · Backtest (M15, la que vale desde 2026-10-28) · MOTOR
Agente / skill: validador (validador-4de4) · código: codigo/us100_adx_fib_dia_m15.py · reporte: resultados/us100_adx_fib_dia_m15_reporte.md
Qué se hizo: backtest con datos/us100_1m_mt5.csv (M1, resuelve el orden dentro de cada vela) y el spread por minuto de datos/US100.csv, velas M15 de datos/us100_15m_mt5.csv (APTA CON AVISOS). Corte 70/30 por velas: dentro de muestra 2011-01-03 a 2022-01-05 (250.245 velas); fuera de muestra 2022-01-05 a 2026-09-17 (107.248 velas). Capital 100.000, riesgo 1 % por operación, spread, swap largo −6,9 % anual, sin comisión. Mismo motor y mismos costes que la versión M30; solo cambió la vela. Se rehicieron 3 operaciones a mano por otro camino y coincidieron.
Resultado: fuera de muestra y con costes: factor de beneficio 1,59 (≥ 1,3 ✓) · 192 operaciones (≥ 30 ✓) · caída máxima 8,27 % (< 20 % ✓) · factor de beneficio sin la mejor operación 1,52 (> 1 ✓). Veredicto 4/4. Resultado neto +42.850 USD (bruto 47.058 y swap −4.207), 45,3 % ganadoras. Dentro de muestra (solo referencia): factor de beneficio 1,84, 456 operaciones, caída 7,91 %. Por tramo: los primeros 3 años fuera de muestra dan factor de beneficio 2,05 (123 operaciones, +44.917 USD) y el resto da 0,93 (69 operaciones, −2.067 USD). Por año: 2022 1,62 · 2023 1,37 · 2024 3,65 · 2025 0,53 · 2026 2,14. Caso A (ruptura, 82 operaciones) factor de beneficio 1,41; caso B (a mercado, 110 operaciones) 1,73. Frecuencia: 40,9 operaciones al año = 3,4 al mes (el plan dice unas 6). 21 de 192 operaciones pasan un fin de semana.
Supuestos: los 30 de la Fase 03; datos con aviso (precios de varias fuentes; spread de RoboForex medido de 2017-12 a 2026, antes un perfil fabricado, posible optimismo); la regla no cierra el viernes; sin optimizar nada.
Veredicto: APRUEBA (4/4). Reservas: el resultado depende de 2022 a 2024 (2024 aporta 30.110 USD) y 2025 pierde; la caída de 8,27 % supera el 6 % que el plan acepta en backtest; la frecuencia (3,4 al mes) es menor que la del plan (6).
Siguiente paso: fase 05 (optimización, meseta de parámetros) con skill optimizar, solo dentro de muestra.
