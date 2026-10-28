# FICHA · XAUUSD ruptura del máximo de 55 velas con impulso y eficiencia subiendo (M30)
Regla: Compro XAUUSD en velas de 30 min cuando, al cierre de una vela, la eficiencia de 50 velas sube (DISPARO) y, a la vez, el estocástico %K(7,3) también sube (FILTRO): dejo una orden de compra stop en el máximo de las últimas 55 velas, con el nivel congelado y válida 10 velas (una nueva activación la reemplaza). Salgo cuando el precio toca el stop vigente: el stop inicial en el mínimo de las últimas 20 velas, que se sustituye por el trailing de 3 × ATR(30) (SMA del rango verdadero) bajo el cierre, actualizado al cierre de cada vela. Stop: mínimo de las últimas 20 velas, leído en la vela de entrada. Horario: lunes a viernes 01:05–23:59 hora del servidor del bróker (hora de Nueva York + 7 h; inicio incluido, fin excluido). Riesgo: 1 % del capital inicial (100.000) por operación.
Por qué funcionaría: cuando el oro avanza en línea recta (eficiencia subiendo) y el impulso corto acelera, romper el máximo de 55 velas suele atraer a quien llega tarde y disparar los stops de quien vendió en el máximo; esa reacción lenta alarga el movimiento (ineficiencia de comportamiento; el seguimiento de tendencia en materias primas también se ve como una prima por aguantar rachas de pérdidas pequeñas). Pierde quien vende el máximo esperando un giro. (propuesta, confírmala)

> CORRECCIÓN · 2026-10-28. Esta ficha se había escrito con una versión resumida e incompleta de la hipótesis y se habían inventado cosas. El trader entregó la hipótesis completa y está copiada tal cual abajo. Se reescribieron la Regla, la Fase 01 y la Fase 03 para que coincidan con ella. La Fase 02 se midió primero con un disparo mal definido y se repitió el mismo día con la hipótesis completa (segundo bloque de la Fase 02, el que vale). La Fase 03 sigue el texto del trader al pie de la letra. No hay cierre del viernes ni ninguna otra regla fuera del texto.

## Hipótesis completa del trader (textual)
Copiada sin cambios el 2026-10-28. Es la fuente de verdad de esta ficha.

```
Armado:
  1. [filtro] rising(stochastic(7,3).k)
  2. [TRIGGER] rising(efficiency(50))
  Orden: STOP en donchian(55).upper, nivel congelado al armarse; vigencia 10 velas, luego se cancela. Mientras el trigger siga verdadero no se modifica; una nueva activación reemplaza nivel y vencimiento (y, con atr_ref: signal, fotografía otro ATR).
ATR          : SMA móvil del True Range
CAPITAL INICIAL: 100000 unidades monetarias de la cuenta
SIZING       : 1% de riesgo sobre capital inicial; lotaje = riesgo / distancia al SL, redondeado hacia ABAJO al paso de lote del símbolo y acotado a su lote mínimo y máximo
SALIDAS      : SL inicial en el swing de 20 velas; trailing 3 × ATR(30) actualizado al cierre de cada barra
REENTRADA    : una activación nueva en la vela de salida puede generar otra entrada desde la siguiente vela disponible; las órdenes stop/limit deben alcanzar su nivel. No hay reentrada normal en la misma vela
MERCADO      : sesiones en hora del servidor del bróker; inicio incluido, fin excluido
               lunes a viernes: 01:05–23:59
               Los días y horarios no declarados quedan cerrados, incluidos sábados y domingos si no tienen sesiones
VELAS        : el calendario NO recorta la serie: las velas se agregan con todas las M1 del archivo, incluidas las horas cerradas, y los indicadores se calculan sobre esa serie completa, que es la misma que construye el terminal
               Sólo se forman velas con M1 disponibles: una hora incompleta conserva su marca HH:00 y no se rellenan minutos ausentes
               Vencimientos, salidas por tiempo y cualquier contador en barras recorren esa serie entera, estén sus velas dentro o fuera de sesión
               El calendario autoriza acciones por el minuto real de cada una, no por la marca de la vela que la contiene: una vela que empieza cerrada y abre a mitad no queda bloqueada entera
               execution.trading_window es otra cosa: expresa cuándo la estrategia decide operar dentro de un mercado ya abierto
EJECUCIÓN    : si una vela contiene a la vez SL y TP, se recorren sus M1 en orden; si ambos niveles caen en el mismo minuto o faltan M1, gana el SL (execution.intrabar_resolution: m1; sl_tp_same_bar: sl_first); la salida por tiempo sostiene N barras completas DESPUÉS de la barra del fill y cierra en la apertura siguiente (execution.time_exit_mode: after_full_bars); reproduce motores que recién observan el fill intrabar al comenzar la vela posterior
AL PORTAR    : Nivel de la pendiente: tras cerrar la vela de señal, calcular el nivel con los datos hasta ese cierre INCLUSIVE y congelarlo al armar la orden. Se coloca en la apertura siguiente y no se recalcula mientras vive
               Donchian como nivel: sobre las últimas 55 velas CERRADAS, incluida la de señal y excluida la siguiente
               Stop por swing: se lee en la vela de la ENTRADA y no en la que armó la orden — es la única salida que no se congela con la pendiente. El swing de 20 velas excluye la vela en curso
               Trailing: primera actualización al cierre de la vela de ENTRADA, sin exigir avance previo; la distancia usa el ATR(30) de la vela que acaba de cerrar, no el congelado al armar. Adentro de la vela rige el nivel anterior: el stop nuevo vale recién desde la apertura siguiente
               Bid/Ask: los indicadores se calculan sobre Bid. Un long entra al Ask y liquida al Bid; un short entra al Bid y liquida al Ask, que es como disparan un buy stop y un sell stop en MT5. El trailing se ancla en el cierre del lado que liquida
BRÓKER       : Colocación: la orden se pide una sola vez, en el primer tick de la vela siguiente a la señal. Si la cotización ya está en el nivel o pasada de él no hay pendiente válida que colocar: se entra a mercado en ese tick
               Fill: al nivel. Si la vela —o el mercado, al reabrir— abre ya pasada del nivel, a esa apertura, que es lo que cobra un bróker real. El SL y el TP se calculan con el precio REAL de entrada, no con el nivel: después de un fill con gap hay que recalcularlos
               Vencimiento: orden GTC, sin expiración del bróker. La orden vive 10 velas de la serie completa —las de horas cerradas también cuentan— desde la de colocación, incluida, y se borra en el primer tick de la vela siguiente. Si el bróker rechaza el borrado por mercado cerrado, reintentarlo en CADA TICK hasta que entre, no en la vela siguiente. El fill va primero: si esa vela —o el mercado, al reabrir— abre ya en el nivel o pasada de él, la orden se llena antes de poder borrarla, y el backtest también la llena
               Reemplazo: una activación nueva cancela la orden y coloca otra —el lotaje cambia con el ATR—; no es una modificación del precio. El borrado se CONFIRMA antes de colocar la nueva: si el bróker no lo confirma, la anterior sigue viva con su nivel, su vencimiento y su ATR, y la nueva no se coloca. Si el bróker rechaza la nueva por stops level, la anterior ya no está
               Mercado cerrado: colocar, reemplazar y cancelar se piden una sola vez. Si el bróker rechaza por mercado cerrado NO se reintenta ni se traslada a la reapertura: la señal se pierde, el reemplazo deja la orden anterior como estaba y la cancelación por activación inversa la deja viva hasta vencer
               Stops level: 4 puntos. La pendiente pedida a menos de esa distancia de la cotización se rechaza y no se reintenta; la entrada cuyo SL o TP queda más cerca se descarta. Se compara en puntos enteros
               Modificación del stop: el backtest da por hecho que el stop nuevo rige desde que se calcula y que un toque sólo cuenta con el mercado abierto. Hasta que la modificación se confirma, el stop VIGENTE en el bróker es el anterior, y el EA lleva las dos cosas por separado: pide el nivel una vez calculado y, si el bróker lo rechaza —mercado cerrado, stops level—, lo RECUERDA como objetivo y lo reintenta en cada tick, sin recalcularlo, sin aflojarlo con el cálculo de la vela siguiente y releyendo la posición para confirmar el stop aplicado. Si la cotización cruza el objetivo antes de la confirmación, cierra a mercado, al precio de ese tick, no al nivel: un objetivo recordado no es un stop aceptado, y sólo protege mientras el EA corre y está conectado
               Reintentos: lo que se reintenta en cada tick —el borrado de una vencida, el stop nuevo del trailing— consulta antes la tabla de sesiones del símbolo, y con la sesión cerrada no se envía. Las operaciones no cambian, porque el bróker lo iba a rechazar, y deja de recibir una solicitud por tick durante todo el cierre
```

## Fase 01 · Hipótesis · CRITERIO
Agente / skill: hipotesis · escritor-hipotesis (manual seguido por el director)
Qué se hizo: CORRECCIÓN 2026-10-28: el trader entregó la hipótesis completa y se rehízo el bloque contra ese texto. Lo que dice el texto: (1) FILTRO: rising(stochastic(7,3).k). (2) DISPARO (trigger): rising(efficiency(50)). (3) Orden STOP en donchian(55).upper, nivel congelado al armarse, vigencia 10 velas; mientras el disparo siga verdadero no se modifica; una nueva activación reemplaza nivel y vencimiento y fotografía otro ATR (atr_ref: signal). (4) ATR = SMA móvil del True Range. (5) Capital inicial 100.000; riesgo 1 % sobre el capital inicial; lote = riesgo / distancia al SL, redondeado hacia abajo. (6) Stop inicial en el swing de 20 velas; trailing 3 × ATR(30) al cierre de cada vela. (7) Reentrada desde la vela siguiente a la de salida. (8) Sesión lun-vie 01:05–23:59 hora del servidor (inicio incluido, fin excluido); velas con todas las M1; entra al Ask, sale al Bid, indicadores sobre Bid.
Resultado: hipótesis completa y medible según el texto del trader; solo compras; sin filtros ni indicadores añadidos. Diferencias con la versión anterior (que estaba mal): el estocástico es FILTRO y la eficiencia es el DISPARO (antes eran dos disparos iguales); el trailing usa el ATR(30) de la vela recién cerrada (antes: ATR fotografiado fijo); el ATR fotografiado solo vale para el lote de la orden armada; el swing de 20 se lee en la vela de entrada y excluye la vela en curso; la orden vive 10 velas de la serie completa desde la de colocación incluida; si el precio ya está en el nivel o más allá se entra a mercado; si abre con gap se llena a esa apertura; no hay cierre del viernes.
Supuestos (solo lo que el texto no dice): (1) XAUUSD y velas de 30 min vienen de la ficha anterior; el texto no los repite (confirmar). (2) Solo compras: la orden stop está en el borde superior. (3) «rising(x)» = el valor de la vela cerrada es mayor que el de la vela anterior (igual no cuenta). (4) Estocástico %K(7,3) = %K crudo de 7 velas suavizado con media simple de 3. (5) Eficiencia(50) = |cierre − cierre de hace 50 velas| / suma de los |cambios de cierre| de esas 50 velas. (6) Activación = la vela cuyo cierre deja el FILTRO verdadero y el DISPARO pasa de falso a verdadero. (7) Sin datos suficientes para calcular los indicadores no hay señal. (8) Los costes (spread, comisión) los modela la fase 04.
Veredicto: APRUEBA
Siguiente paso: fase 02 repetida con la hipótesis completa (hecha, ver abajo); después fase 04.

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: director · aed (código: codigo/xauusd_ruptura_donchian_eficiencia_aed.py)
Qué se hizo: A REPETIR (2026-10-28). Esta medición NO vale para la regla corregida: usó un disparo mal definido (estocástico y eficiencia subiendo los dos como disparo) y un ATR fotografiado. Texto original conservado como histórico: «datos/XAUUSD.csv (velas de 1 min, 2006-01-02 a 2026-09-17) pasado a 30 min: 249.117 velas, 1.098 huecos de más de 1 día. Solo se usó el primer 70 % (2006 a 2020-05-22 10:30, dentro de muestra); el 30 % final queda reservado para la fase 04. Sin pre-registro: retorno, en unidades de ATR(30), a 1, 5 y 20 velas.»
Resultado: HISTÓRICO, no vale para esta regla. «(A) Tras la activación del disparo (29.676 casos) el retorno a +20 velas es +0,082 ATR, igual que en cualquier vela. (B) Tras activarse, el precio rompe el máximo de 55 dentro de las 10 velas en 8.015 casos (27 %); entrando en ese nivel el retorno es +0,27 ATR a +1 vela, +0,31 a +5 y +0,51 a +20, frente a +0,003, +0,017 y +0,082 en cualquier vela; solo el 52 % sube. (C) A +20 velas supera a la línea base en 14 de 15 años; 2015 es negativo (−0,19). (D) Toda ruptura de 55 sin el disparo (5.387 casos) da +0,24, +0,27 y +0,44 ATR.»
Supuestos: HISTÓRICO. «Sin pre-registro; las horas son las del CSV (zona horaria sin confirmar); ATR de la vela de señal; si la vela abre sobre el nivel, se entra a la apertura; sin costes ni stop.» Dato nuevo confirmado por el trader: la hora del CSV es la del servidor del bróker (Nueva York + 7 h).
Veredicto: PENDIENTE (bloque histórico: se repitió en el bloque siguiente, que es el que vale). Veredicto histórico anterior, sin validez: APRUEBA (con reserva).
Siguiente paso: ver el bloque siguiente (fase 02 repetida con la regla corregida).

## Fase 02 · AED (repetida 2026-10-28, con la hipótesis completa) · CRITERIO + DATOS
Agente / skill: director · aed (código: codigo/xauusd_ruptura_donchian_eficiencia_aed_v2.py)
Qué se hizo: mismo CSV pasado a velas M30 y solo el primer 70 % (2006-01-02 a 2020-05-22; el 30 % final queda reservado para la fase 04). Sin pre-registro. Se midió el retorno, en unidades de ATR(30) de la vela de señal, desde el fill de la orden: orden stop en el máximo de 55, colocada en la apertura siguiente a la señal, viva 10 velas, con fill a la apertura si abre en o sobre el nivel. Se comparó con la línea base (cualquier vela) y con cuatro controles.
Resultado: la regla (filtro estocástico + trigger eficiencia; 23.196 órdenes armadas, 5.819 llenadas) da +0,29 ATR a +1 vela, +0,35 a +5 y +0,51 a +20 (mediana +0,17; el 52 % de los casos sube). Línea base, cualquier vela: +0,003, +0,017 y +0,082. Controles a +20: solo filtro +0,48, solo trigger +0,52, orden en cada vela sin filtro ni trigger +0,49 (22 % llenadas). La regla supera al control de «orden en cada vela» en solo 6 de 15 años (2015 y 2012 negativos). Variante de activación (sube la combinación): +0,51, casi igual. Conclusión: la ventaja que se mide viene de romper el máximo de 55 y seguir el movimiento, no del filtro ni del trigger (aportan unos +0,03 ATR, sin efecto visible). La media (+0,51) es mucho mayor que la mediana (+0,17): la sostienen pocas ganadoras grandes.
Supuestos: línea base = cualquier vela con el mismo ATR; activación = el trigger pasa de falso a verdadero con el filtro verdadero en esa vela; sin costes, spread ni stop (eso es de la fase 04); retornos medidos sobre Bid. La muestra incluye la subida del oro de 2006 a 2020, que infla la media de todas las variantes.
Veredicto: APRUEBA (con reserva: el movimiento existe frente a la línea base, pero el filtro y el trigger de la hipótesis no se distinguen del control sin ellos)
Siguiente paso: fase 04 con el agente validador, costes y datos fuera de muestra; no tocar el filtro ni el trigger para que pase.

## Fase 03 · Reglas · MOTOR
Agente / skill: reglas (manual seguido por el director)
Qué se hizo: CORRECCIÓN 2026-10-28: pseudocódigo reescrito para que refleje exactamente la hipótesis completa del trader, incluido el modelo de backtest (ejecución al Ask/Bid, colocación, vencimiento, reemplazo, stops level). Se quitó el cierre del viernes agregado antes, porque la hipótesis no lo tiene.
Resultado: pseudocódigo de 7 pasos con 22 supuestos decididos (abajo). Sin huecos: orden de salidas fijo, vigencia de 10 velas contada desde la VELA DE COLOCACIÓN, y qué pasa si no se cumple nada.
Supuestos: los 22 de la lista de abajo; los que más pesan son el 10 (el trailing solo sube), el 6 (activación) y el 13 (sin órdenes nuevas con posición abierta).
Veredicto: APRUEBA (pseudocódigo fiel a la hipótesis, con supuestos declarados)
Siguiente paso: fase 04 con costes sobre los datos del trader (70 % dentro de muestra, 30 % fuera).

> NOTA. La hipótesis no cierra posiciones el viernes: la posición sigue hasta que la toca el stop. MI_PLAN.md dice que el trader no deja operaciones abiertas el fin de semana. La regla manda tal como el trader la escribió; no se agregó ningún cierre.

### Pseudocódigo · XAUUSD ruptura Donchian con eficiencia (M30, solo compras)

```
DATOS: XAUUSD, velas de 30 minutos, solo compras. Horas = las del servidor del bróker
  (hora de Nueva York + 7 h, confirmado por el trader); las del CSV son esas mismas.
  Precios: los indicadores se calculan sobre Bid. COMPRA se hace al Ask; SALGO se hace al Bid.
  Velas: se arman con TODAS las M1 del archivo (también las de horas cerradas) y los
  indicadores usan esa serie completa. Solo existen velas con M1; no se rellenan minutos.
  MERCADO ABIERTO en un minuto = lunes a viernes, de 01:05 (incluido) a 23:59 (excluido).
  Cada acción (colocar, borrar, tocar un stop) vale según el minuto real en que ocurre.
  Capital inicial = 100.000. RIESGO = 1 % del capital inicial = 1.000.
  Una sola operación a la vez. Al empezar: sin operación, sin ORDEN VIVA, sin SEÑAL.

  Definiciones (al cierre de cada vela, sobre Bid):
    ATR = media simple de los últimos 30 rangos verdaderos (rango verdadero = el mayor entre
          máximo-mínimo, |máximo-cierre anterior| y |mínimo-cierre anterior|).
    K = media simple de 3 de K_CRUDO; K_CRUDO = 100 x (cierre - mínimo de las 7 últimas velas) /
        (máximo de las 7 últimas - mínimo de las 7 últimas). Si ese rango es 0, repito el K_CRUDO anterior.
    EF = |cierre - cierre de hace 50 velas| / suma de los |cambios de cierre vela a vela| de esas 50 velas.
        Si la suma es 0, EF = 0.
    FILTRO = K de esta vela > K de la vela anterior.
    DISPARO = EF de esta vela > EF de la vela anterior.
    ACTIVACIÓN = FILTRO verdadero y DISPARO verdadero ahora y DISPARO falso en la vela anterior.
    Sin las velas suficientes para calcular algo, FILTRO, DISPARO y ACTIVACIÓN son falsos.

CADA VELA NUEVA (la llamo VELA ACTUAL), en este orden:

  1. Al empezar la VELA ACTUAL (haya o no mercado abierto):
       SI hay una ORDEN VIVA: VIDA = VIDA + 1.

  2. En el PRIMER TICK de la VELA ACTUAL:
       a. SI estoy fuera y hay una ORDEN VIVA y el Ask está en NIVEL o por encima:
            COMPRA al Ask de ese tick (si abrió con gap, a esa apertura). Ve al paso 4.
       b. SI hay una ORDEN VIVA con VIDA >= 11 (ya vivió sus 10 velas):
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
                * SI el Ask ya está en NIVEL_SEÑAL o por encima: COMPRA al Ask de ese
                  tick (a mercado). Ve al paso 4.
                * SI NO, SI NIVEL_SEÑAL - Ask < 4 puntos enteros: el bróker rechaza la
                  orden y no se reintenta; no queda ORDEN VIVA (la anterior ya no está).
                * SI NO: coloco una ORDEN VIVA de COMPRA STOP con NIVEL = NIVEL_SEÑAL,
                  ATR_ORDEN = ATR_SEÑAL y VIDA = 1. La VELA ACTUAL es la VELA DE COLOCACIÓN.
            Borro la SEÑAL (se usa una sola vez).

  3. Durante la VELA ACTUAL, recorriendo sus M1 en orden, con mercado abierto:
       SI estoy fuera y hay una ORDEN VIVA con VIDA <= 10 y el Ask alcanza NIVEL:
         COMPRA en NIVEL. Ve al paso 4.

  4. Tras cualquier COMPRA (en el paso 2 o en el 3):
       PRECIO_ENTRADA = el precio real de la compra. La ORDEN VIVA desaparece.
       STOP_SWING = el mínimo más bajo de las 20 velas cerradas anteriores a la VELA ACTUAL
                    (la vela en curso no cuenta). Se lee ahora, en la vela de entrada.
       DISTANCIA = PRECIO_ENTRADA - STOP_SWING (con el precio real, no con NIVEL).
       SI DISTANCIA < 4 puntos enteros: la entrada se descarta (no hay operación). Ve al paso 6.
       LOTE = RIESGO / DISTANCIA, redondeado hacia ABAJO al paso de lote del símbolo y
              acotado entre su lote mínimo y máximo.
       STOP_VIGENTE = STOP_SWING. Ve al paso 5.

  5. MIENTRAS esté dentro, en cada vela nueva, en este orden:
       a. En cada minuto con mercado abierto (también el de la compra y los siguientes de
          la vela de entrada): SI la vela abrió con el Bid por debajo de STOP_VIGENTE,
          SALGO a esa apertura. SI NO, SI el Bid toca STOP_VIGENTE, SALGO en STOP_VIGENTE.
          Si la compra y el toque caen en el mismo minuto, gana el stop. Tras SALGO ve al paso 6.
       b. Al cierre de la VELA ACTUAL, si sigo dentro (también al cierre de la vela de
          entrada, sin exigir avance previo):
            TRAILING = cierre (Bid) de la VELA ACTUAL - 3 x ATR(30) de esa misma vela.
            SI TRAILING > STOP_VIGENTE: STOP_VIGENTE = TRAILING.
            El stop nuevo vale desde la apertura de la vela siguiente; dentro de la vela
            rige el anterior.

  6. Al cerrar la VELA ACTUAL, calculo los indicadores (siempre, haya o no operación) y:
       SI estoy fuera (sin operación) y hay ACTIVACIÓN:
         NIVEL_SEÑAL = el máximo más alto de las últimas 55 velas cerradas
                       (incluida la VELA ACTUAL; la siguiente no cuenta). Queda congelado.
         ATR_SEÑAL = ATR(30) al cierre de la VELA ACTUAL (la fotografía; solo sirve
                     para el ATR_ORDEN de la orden armada).
         SEÑAL = lista para pedirse en el primer tick de la vela siguiente.
         (Una salida en esta misma vela no impide la ACTIVACIÓN: puede haber reentrada
         desde la vela siguiente. En esta misma vela no hay otra entrada.)
       SI NO (no hay ACTIVACIÓN, o estoy dentro): no hay SEÑAL nueva. Mientras el DISPARO
         siga verdadero, la ORDEN VIVA no cambia: NIVEL, VIDA y ATR_ORDEN siguen igual.

  7. SI no se cumplió nada de lo anterior → no hago nada. FIN de la vela.
     Si la orden agota sus 10 velas sin llenarse, se borra (paso 2b) y no se opera hasta la
     próxima ACTIVACIÓN. Una posición abierta sigue abierta hasta que el stop la cierre.
```

Lo que viene del texto del trader y se aplicó tal cual (no son supuestos): ATR = SMA del rango verdadero; nivel Donchian congelado; vigencia de 10 velas de la serie completa desde la de colocación incluida y borrado en el primer tick de la vela siguiente (el fill va primero); entrada a mercado si el precio ya está en el nivel o más allá; fill con gap a la apertura y distancia/lote con el precio real; stop por swing de 20 leído en la vela de entrada y excluyendo la vela en curso; trailing con el ATR(30) de la vela recién cerrada, sin exigir avance previo; entra al Ask y sale al Bid; reemplazo con borrado confirmado antes de colocar (si la nueva se rechaza por stops level, la anterior ya no está); con mercado cerrado se pide una sola vez y no se reintenta (la señal se pierde; el reemplazo deja la anterior); stops level 4 puntos enteros, sin reintento; reentrada desde la vela siguiente a la de salida; capital 100.000 y 1 % de riesgo con el lote redondeado hacia abajo. En real, el EA recuerda el stop del trailing si el bróker lo rechaza y lo reintenta en cada tick (solo con sesión abierta); el backtest da por hecho que el stop nuevo rige desde la apertura siguiente y que un toque solo cuenta con el mercado abierto.

Supuestos del pseudocódigo (todos decididos; solo lo que el texto no dice):
1. XAUUSD y velas de 30 min vienen de la ficha anterior; el texto no los repite (confirmar).
2. Solo compras: la orden stop está en el borde superior del canal.
3. «rising(x)» = el valor de la vela cerrada es mayor que el de la vela anterior; igual no cuenta.
4. Estocástico %K(7,3) = %K crudo de 7 velas (incluida la actual) suavizado con media simple de 3; si el rango es 0 se repite el %K crudo anterior.
5. Eficiencia(50) = avance neto de 50 velas / camino total (suma de cambios absolutos de cierre); si el camino es 0, EF = 0.
6. Activación = FILTRO verdadero y DISPARO pasando de falso a verdadero en la misma vela; el FILTRO no se vigila por separado.
7. Donchian(55).upper = el mayor de los máximos (Bid) de las 55 velas cerradas, incluida la de señal. Swing de 20 = el menor de los mínimos (Bid) de las 20 velas cerradas anteriores a la de entrada.
8. Los indicadores necesitan sus velas completas; antes de eso no hay señal.
9. Los costes (spread, comisión, deslizamiento) los modela la fase 04; el toque del NIVEL se mide con el Ask (Bid + spread de esa fase).
10. Stop vigente = el mayor entre el swing de 20 y el trailing; el trailing solo sube (el stop nunca se afloja). El texto no dice «solo sube».
11. Si una vela posterior abre con el Bid por debajo del stop, se sale a esa apertura (hueco); si no, en el nivel del stop. El texto lo da para entradas, no para salidas.
12. Si la compra y el toque del stop caen en la misma vela, se recorren las M1 desde el minuto de la compra; en el mismo minuto gana el stop (mismo criterio que SL y TP).
13. Con posición abierta no se arman órdenes nuevas; las activaciones de ese tiempo se ignoran, pero los indicadores se calculan igual para saber si el DISPARO estaba falso en la vela anterior.
14. El lote lo da el texto: lotaje = riesgo / distancia al SL, con el precio real de entrada, redondeado hacia abajo (paso 4). El ATR fotografiado (atr_ref: signal) se guarda con la orden armada y no entra en esa cuenta ni en el trailing, que usa el ATR de la vela recién cerrada.
15. Sin objetivo de ganancia ni salida por tiempo: salen solo el stop swing y el trailing.
16. Sin límite de operaciones por día; la posición puede pasar de un día a otro y de una semana a otra (ver NOTA).
17. Si al reemplazar, la vela de colocación abre en el NIVEL de la orden vieja o más allá, la vieja se llena primero (paso 2a), como en el caso del vencimiento.
18. En el backtest, un borrado o un reemplazo con mercado abierto se confirma siempre; solo falla por mercado cerrado.
19. «Punto» = el punto del símbolo en el CSV; las comparaciones de 4 puntos se hacen con enteros.
20. Si la entrada se descarta por stops level (paso 4), la orden queda consumida y no hay operación.
21. Si faltan datos (huecos), las velas se cuentan tal como están en el CSV, sin rellenar.
22. Los indicadores se calculan siempre, también con posición abierta y con mercado cerrado.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador · validador-4de4 (código: codigo/xauusd_ruptura_donchian_eficiencia.py; operaciones, curva y reporte en resultados/xauusd_ruptura_donchian_eficiencia_*)
Qué se hizo: backtest del pseudocódigo de la fase 03 tal cual, con datos/XAUUSD.csv (M1 Bid, 2006-01-02 a 2026-09-17, 7,34 M velas pasadas a 249.117 velas M30), resolución con las M1, entrada al Ask (Bid + spread del CSV) y salida al Bid. Dentro de muestra 2006-01-02 a 2020-05-22 10:30; fuera de muestra 2020-05-22 11:00 a 2026-09-17.
Resultado: FUERA de muestra: factor de beneficio 1,52 (≥ 1,3 ✓) · 756 operaciones (≥ 30 ✓) · caída máxima 8,57 % (< 20 % ✓) · factor de beneficio sin la mejor operación 1,49 (> 1 ✓) → 4/4. Referencia dentro de muestra: 1,69 · 1.607 operaciones · caída 7,90 % · 1,67. AVISO: la caída de 8,57 % supera el 6 % de MI_PLAN.md (pasa el método, no encaja con el plan); además mantiene posiciones el fin de semana y opera ~120 veces al año (el plan dice ~6 al mes). Sin informe de calidad de datos.
Supuestos: spread real del CSV como único coste (comisión 0, deslizamiento 0, sin swap; costes ×2 van en la fase 06); XAUUSD 100 oz por lote, paso 0,01, mín 0,01, máx 100, punto 0,01 USD; riesgo 1.000 USD fijo (1 % de 100.000); caída medida con pérdida flotante al cierre de cada vela M30; cada segmento corre por separado; más los 22 supuestos de la fase 03.
Veredicto: APRUEBA (4/4 fuera de muestra, con aviso: la caída supera la que acepta el plan)
Contraste independiente (2026-10-28): el trader corrió la misma regla en el Probador de estrategias de MT5 y dijo que el resultado es «prácticamente igual» (sin cifras guardadas aquí). Se da por buena la implementación del backtest.
Siguiente paso: fase 05 (meseta de parámetros); la caída de 8,57 % frente al 6 % del plan sigue abierta, y la ventaja viene de la ruptura y no del filtro ni del disparo.

## Fase 05 · Optimización · MOTOR
Agente / skill: director · optimizar (código: codigo/xauusd_ruptura_donchian_eficiencia_optimizar.py y _optimizar_informe.py; datos en resultados/xauusd_ruptura_donchian_eficiencia_meseta.csv, mapa en resultados/xauusd_ruptura_donchian_eficiencia_meseta.png y .svg; curva de la fase 04 en _equity.png; código de los gráficos en codigo/xauusd_ruptura_donchian_eficiencia_graficos.py)
Qué se hizo: rejilla de 4 parámetros que la regla ya tenía, 5 valores cada uno, 625 combinaciones (el trader pidió más ejes y más valores que los 2 ejes de la skill; se pasó del tope de 81 por su pedido): canal Donchian 41-48-55-62-69, multiplicador del trailing 2,4-2,7-3,0-3,3-3,6, swing del stop inicial 14-17-20-23-26 y vigencia de la orden 6-8-10-12-14. Solo dentro de muestra (2006-01-02 a 2020-05-22 10:30), con el mismo motor y costes de la fase 04; la combinación actual reproduce la fase 04 (1.607 operaciones, factor de beneficio 1,69). El fuera de muestra no se miró.
Resultado: MESETA. En toda la rejilla el factor de beneficio va de 1,44 a 1,71 (mediana 1,61), con al menos 1.254 operaciones por combinación y 100 % de las combinaciones con factor ≥ 1,3. Los 8 vecinos inmediatos (un paso en un eje) cumplen: factor mínimo 1,64, 1.515 operaciones o más. Los 80 vecinos del cubo completo (con diagonales) también: factor mínimo 1,57. El punto más débil es el canal corto (41 velas: 1,55). Mejores casillas, solo informativas y no elegidas: 1,71 (swing 14).
Supuestos: vecinos inmediatos = un paso en un solo eje (8); umbral del Reto (factor ≥ 1,3, ≥ 30 operaciones, ≥ 70 % del factor actual); no se variaron el estocástico ni la eficiencia (la fase 02 mostró que casi no aportan); el mapa tiene 6 paneles (pares de ejes con los otros dos en su valor actual), en PNG y en SVG; la caída máxima dentro de muestra de la rejilla va de 3,4 % a 11,4 % (mediana 6,3 %; 265 de las 625 combinaciones quedan bajo el 6 % del plan, la actual no: 7,9 %).
Veredicto: APRUEBA (meseta; se quedan los parámetros de la fase 04, que siguen 4/4 fuera de muestra, sin volver a correrlos)
Siguiente paso: fase 06, robustez: costes ×2, Monte Carlo y los peores años. Sigue abierta la caída frente al 6 % del plan.

## Fase 06 · Robustez · MOTOR
Agente / skill: director · robustez (código: codigo/xauusd_ruptura_donchian_eficiencia_robustez.py, semilla 42; gráficas en resultados/xauusd_ruptura_donchian_eficiencia_robustez.png; números en _robustez.json)
Qué se hizo: la regla y los parámetros de la fase 04 y 05, sin cambiar nada. Cuatro pruebas sobre el tramo fuera de muestra (2020-05-22 a 2026-09-17, 756 operaciones, que reproduce la fase 04) y, para los años, sobre todo el periodo.
Resultado: (a) costes ×2 ✓: factor de beneficio 1,49 (mínimo 1,1), caída 9,54 %. (b) Monte Carlo del orden ✓: 1.000 barajas, caída máxima mediana 7,0 %, percentil 95 de 11,6 % (máximo 30 %), la peor 19,6 %. (c) Remuestreo con reemplazo ✓: factor de beneficio con percentil 5 de 1,28 (mínimo 1), mediana 1,53, percentil 95 de 1,77. (d) Años malos ✓: 19 de 21 años ganan; los dos que pierden son 2018 (−168 USD) y 2021 (−1.048 USD), casi en cero; sin el mejor año (2008) el factor de beneficio es 1,59. Veredicto de robustez 4/4.
Supuestos: umbrales provisionales del Reto (a: factor ≥ 1,1; b: caída p95 < 30 %; c: factor p5 > 1; d: mitad de los años ganadores y factor sin el mejor año > 1), METODO.md no trae otros. Costes ×2 = el spread del CSV multiplicado por 2 (spread medio 10,3 puntos, unos 0,10 USD por onza); en la fase 04 era el único coste, así que no hay comisión ni deslizamiento que duplicar. Monte Carlo y remuestreo sobre el resultado de cada operación (1 % de riesgo sobre el capital inicial, sin reinvertir), con la caída medida con operaciones cerradas. Años por fecha de entrada; 2026 es un año parcial; el tramo dentro de muestra y el de fuera se corrieron por separado desde 100.000.
Veredicto: APRUEBA (4/4). Aviso: un spread ×2 de unos 0,20 USD es un castigo suave para el oro; un bróker con comisión y deslizamiento reales puede costar más. Aprobar la fase 06 no valida la estrategia: faltan tamaño y riesgo (07) y puesta en marcha (08).
Siguiente paso: fases 07 y 08, que todavía no tienen agente ni skill; se construyen durante el Reto. La caída de 8,57 % sigue por encima del 6 % de MI_PLAN.md y es lo primero a resolver en la fase 07.

## Código · MetaTrader 5 · herramienta
Agente / skill: programador
Qué se hizo: traducción del pseudocódigo de la fase 03 a MQL5 (2026-10-28): un Asesor Experto que opera y un indicador que solo dibuja entradas, salidas, stop vigente y nivel de la orden. Parámetros con los números y nombres de la ficha.
Resultado: robots/xauusd_ruptura_donchian_eficiencia_mt5_estrategia.mq5 + robots/xauusd_ruptura_donchian_eficiencia_mt5_indicador.mq5
Supuestos: de plataforma, numerados (versión 2, 2026-10-28). (P1) La orden es una BUY STOP real, GTC: se pide una sola vez en el primer tick de la vela siguiente a la señal, se llena en el nivel (o en la apertura si hay gap) y el robot la borra al vencer sus 10 velas; el reemplazo borra y confirma antes de colocar la nueva; la señal con mercado cerrado se pierde. (P2) El stop swing se lee en la vela de la ENTRADA y el lote sale de él; una orden pendiente no puede cambiar de lote, así que en cada vela nueva la orden se repone (se borra y se pide otra con el mismo nivel y la misma vida) con el swing y el lote de esa vela, como hace el motor del trader (su reporte muestra la misma orden repuesta cada 30 minutos con el stop y el lote cambiando, por ejemplo 0,52, 0,54, 0,57, 0,63, 0,66, 0,93 y 1,12 hasta llenarse). El nivel y la vigencia siguen congelados hasta una activación nueva. (P3) La hora de la regla es la del servidor del bróker (NY+7): desfase_horas = 0. (P4) Si se reinicia el robot, la orden pendiente sigue en el bróker y se recupera su vida por la hora en que se colocó. (P5) Los costes los pone el bróker; la comisión del símbolo hay que revisarla. (P6) El indicador usa velas de 30 min con Ask = precio + spread de la vela; si en una misma vela se llena la orden y se toca el stop, gana el stop. (P7) Sin cierre del viernes, igual que la ficha. (La versión 1 usaba una orden virtual a mercado y entraba peor que el nivel.)
Contraste con el motor del trader (2026-10-28, informes informe-1.htm y informe-2.htm, Expert xauusd-efficiency-stoch-donchian, OANDA, M30, con spread y swap): sus 756 operaciones desde 2020-05-22 coinciden con las de Python en 748 entradas, y las primeras tienen el mismo precio y el mismo lote (1.715,90 y 1,12 lotes). Con swap incluido (−8.663 USD) da factor de beneficio 1,50, 1,46 sin la mejor operación y caída de 7,56 % con operaciones cerradas; Python da 1,52, 1,49 y 7,50 %. Es decir, el backtest de Python reproduce el motor del trader. Por tramos: 2020-05 a 2023-08 factor 1,15 en Python y 1,12 en OANDA; 2023-08 a 2026-09 factor 1,98 y 1,97. La mayor parte del resultado fuera de muestra viene del último tramo.
Versión 2 en el Probador (OANDA, XAUUSD_PROD, M30, 2020-05-22 a 2026-09-17, M1 OHLC): 756 operaciones, factor de beneficio 1,51 con swap (1,56 sin swap; 1,47 sin la mejor operación), caída de equidad 8,09 %, beneficio neto 98.652, swap −8.512. Contra el motor del trader: 756 de 756 entradas a la misma hora y al mismo precio, 100 % de las salidas a la misma hora, factor 1,51 contra 1,50 y neto 98.652 contra 99.774. Contra Python: 748 de 756 entradas coinciden (99,2 % al mismo precio), 98,8 % de las salidas. El lote coincidía solo en el 79 % porque esa versión 2 fijaba el lote al colocar la orden; la versión 3 repone la orden en cada vela (P2) y falta probarla.
Coincide con Python: sí (y con el motor del trader).
Versión 3 en el Probador (OANDA, XAUUSD_PROD, M30, 2020-05-22 a 2026-09-17, M1 OHLC): 756 operaciones, factor de beneficio 1,50 con swap, caída de equidad 8,98 %, beneficio neto 99.866, swap −8.663. Contra el motor del trader: 756 de 756 entradas coincidentes, el 99,7 % con el mismo lote, factor 1,50 contra 1,50, neto 99.866 contra 99.774 y el mismo swap (−8.663). Contra Python: 748 de 756 entradas, el 99,1 % con el mismo lote.
Coincide con Python: sí (y con el motor del trader).
Veredicto: COMPILA (versión 3 compilada y probada; reproduce el motor del trader)
Siguiente paso: probar en cuenta demo antes de cualquier uso real; las fases 07 y 08 siguen pendientes.
