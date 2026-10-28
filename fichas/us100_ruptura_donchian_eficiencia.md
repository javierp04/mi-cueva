# FICHA · US100 ruptura del máximo de 55 velas con impulso y eficiencia subiendo (M30)
Regla: Compro US100 en velas de 30 min cuando, al cierre de una vela, la eficiencia de 50 velas sube (DISPARO) y, a la vez, el estocástico %K(7,3) también sube (FILTRO): dejo una orden de compra stop en el máximo de las últimas 55 velas, con el nivel congelado y válida 10 velas (una nueva activación la reemplaza). Salgo cuando el precio toca el stop vigente: el stop inicial en el mínimo de las últimas 20 velas, que se sustituye por el trailing de 3 × ATR(30) (SMA del rango verdadero) bajo el cierre, actualizado al cierre de cada vela. Stop: mínimo de las últimas 20 velas, leído en la vela de entrada. Horario: lunes a viernes 01:05–23:59 hora del servidor del bróker (hora de Nueva York + 7 h; inicio incluido, fin excluido). Riesgo: 1 % del capital inicial (100.000) por operación.
Por qué funcionaría: es la misma hipótesis de xauusd_ruptura_donchian_eficiencia llevada a otro activo sin cambiar nada (huella): cuando el precio avanza en línea recta y el impulso corto acelera, romper el máximo de 55 velas atrae a quien llega tarde y dispara los stops de quien vendió en el máximo. Pierde quien vende el máximo esperando un giro. (propuesta, confírmala)

## Hipótesis completa del trader (textual)
Es la hipótesis de xauusd_ruptura_donchian_eficiencia, copiada sin cambios el 2026-10-28; solo cambia el activo (US100). El trader indicó US100 y que el CSV ya está en datos/.

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
Agente / skill: director · escritor-hipotesis (manual seguido por el director)
Qué se hizo: se tomó la hipótesis completa del trader tal cual y se aplicó a US100 (M30), sin tocar ningún parámetro: filtro = estocástico %K(7,3) subiendo, disparo = eficiencia(50) subiendo, orden stop en el máximo de 55 velas con el nivel congelado y 10 velas de vida, stop inicial en el mínimo de 20 velas, trailing 3 × ATR(30), riesgo 1 % del capital inicial (100.000).
Resultado: hipótesis completa y medible; solo compras; sin filtros ni indicadores añadidos. Encaja con MI_PLAN.md: US100 está en la lista de mercados, vela de 30 minutos, operada por robot en MT5. La frecuencia (el plan dice unas 6 operaciones al mes por estrategia) se mide en la fase 04. Igual que en la ficha del oro, la hipótesis no cierra el viernes y el plan dice que no se deja posición el fin de semana: la regla manda como está escrita.
Supuestos: (1) Mismos parámetros y mismas definiciones de indicadores que la ficha de XAUUSD (huella: no se ajusta nada para este activo). (2) US100 y M30 vienen del trader. (3) Horario lunes a viernes 01:05–23:59 en hora del servidor del bróker, igual que en el oro (el CSV de US100 empieza a las 01:00; zona horaria sin confirmar). (4) Datos: datos/US100.csv, velas de 1 minuto del 2011-01-03 al 2026-09-17, mismas columnas que el de XAUUSD (la última es el spread). (5) Valor del punto, paso de lote y spread de US100 en el bróker: por confirmar en la fase 03/04 (supuesto provisional: 1 punto de índice = 1 USD por lote). (6) Costes y swap los modela la fase 04.
Veredicto: APRUEBA
Siguiente paso: fase 02 (AED) con datos/US100.csv, solo con el primer 70 %.

## Fase 02 · AED · CRITERIO + DATOS
Agente / skill: director · aed (código: codigo/us100_ruptura_donchian_eficiencia_aed.py)
Qué se hizo: datos/US100.csv (M1, 2011-01-03 a 2026-09-17) pasado a velas M30 y solo el primer 70 % (2011-01-03 a 2022-01-05 17:00, 126.474 velas); el 30 % final queda reservado para la fase 04. Sin pre-registro: retorno en unidades de ATR(30), a 1, 5 y 20 velas desde el fill de la orden (nivel congelado, colocada en la apertura siguiente, viva 10 velas, fill a la apertura si hay gap), contra la línea base (cualquier vela) y tres controles.
Resultado: la regla (16.832 órdenes armadas, 5.305 llenadas) da +0,12 ATR a +1 vela, +0,14 a +5 y +0,29 a +20 (mediana +0,31; el 54,0 % sube). Línea base, cualquier vela: +0,01, +0,05 y +0,17 a +20 (mediana +0,37; el 55,6 % sube). Es decir, la media de la regla supera a la línea base en +0,12 ATR a +20 y en 7 de 11 años con casos suficientes, pero la mediana y la proporción de casos que suben quedan por debajo. Controles a +20: solo filtro +0,28, solo trigger +0,32, orden en cada vela sin filtro ni trigger +0,28: el filtro y el trigger no aportan nada visible (la regla supera al control de «orden en cada vela» en 6 de 12 años). En comparación, en el oro la regla daba +0,51 a +20 contra +0,08 de la línea base: la huella en US100 es mucho más débil.
Supuestos: sin pre-registro; línea base = cualquier vela con el mismo ATR; activación = el trigger pasa de falso a verdadero con el filtro verdadero en esa vela; sin costes, spread ni stop (eso es de la fase 04); retornos sobre Bid. La muestra incluye una larga subida del índice (2011 a 2021), que explica buena parte de la media de todas las variantes; 2022 tiene solo 4 casos y no cuenta.
Veredicto: APRUEBA (con reserva fuerte: la ventaja sobre la línea base es pequeña, el filtro y el trigger no se distinguen de un control sin ellos, y la mediana y los aciertos no superan a la línea base)
Datos: datos/us100_1m_mt5.csv (M1) · NO APTA según el umbral provisional (5,5 % de minutos M1 faltantes dentro del horario; el límite es 5 %) · informe en resultados/us100_1m_mt5_calidad.md. Son minutos sin ticks (2011 a 2014 tienen entre 83 % y 89 % de los minutos; desde 2018 más del 95 %). Con esos M1 se armó datos/us100_30m_mt5.csv (180.678 velas de 30 minutos, agregadas como dice la ficha, con la marca HH:00 y HH:30 de la hora del servidor): APTA CON AVISOS · faltan el 2,8 % de las velas de 30 minutos dentro del horario (5.045, sin rellenar) y hay 1.854 saltos para revisar. Las velas faltantes se concentran en cierres anticipados y festivos de EE.UU. (3 y 4 de julio, 24 de diciembre, Viernes Santo, el viernes después de Acción de Gracias), en el huracán Sandy (2012-10-29 y 30) y en marzo de 2020; son mercado cerrado, no datos perdidos (revisión del 2026-10-28, sin cifra exacta: mi conteo de 1.847 faltantes no coincide con las 5.045 del informe porque define distinto el horario típico) · informe en resultados/us100_30m_mt5_calidad.md. El M1 se conserva porque el backtest resuelve el orden del stop y del nivel con los minutos. Zona: las fechas son hora del servidor del bróker, no UTC; las etiquetas «Nueva York» de los informes no valen.
Siguiente paso: fase 03 (reglas) con el agente reglas, sin tocar ningún parámetro; la fase 04 decide con costes y datos fuera de muestra, y es el filtro real.

## Fase 03 · Reglas · MOTOR
Agente / skill: reglas (manual seguido por el director)
Qué se hizo: se tomó el pseudocódigo aprobado de la ficha del oro (7 pasos, 22 supuestos) y se reutilizó tal cual, sin cambiar ningún parámetro ni regla. Solo se cambió lo propio del activo, con las especificaciones reales que entregó el trader: US100, punto de 0,1, 1 USD por lote por unidad de índice, lote 0,01 a 300, stops level de 5 puntos (0,5 unidades), horario operable desde las 01:01 y modelo de costes (spread del CSV, comisión 0, deslizamiento 0, swap largo).
Resultado: pseudocódigo de 7 pasos con 30 supuestos decididos (abajo). Sin huecos: orden de salidas fijo, vigencia de 10 velas contada desde la VELA DE COLOCACIÓN y qué pasa si no se cumple nada.
Supuestos: los 30 de la lista de abajo; los que más pesan son el 24 y el 26 (stops level 5 y horario 01:01 en lugar de 4 y 01:05 del texto, por ser datos del símbolo), el 30 (el spread del CSV puede ser optimista), el 10 (el trailing solo sube), el 6 (activación) y el 13 (sin órdenes nuevas con posición abierta).
Veredicto: APRUEBA (pseudocódigo sin huecos; las especificaciones del símbolo son datos del trader)
Siguiente paso: fase 04 con costes sobre datos/us100_1m_mt5.csv y datos/us100_30m_mt5.csv (70 % dentro de muestra, 30 % fuera).

> NOTA. La hipótesis no cierra posiciones el viernes: la posición sigue hasta que la toca el stop. MI_PLAN.md dice que el trader no deja operaciones abiertas el fin de semana. La regla manda tal como el trader la escribió; no se agregó ningún cierre.

### Pseudocódigo · US100 ruptura Donchian con eficiencia (M30, solo compras)

```
DATOS: US100, velas de 30 minutos, solo compras. Horas = las del servidor del bróker
  (hora de Nueva York + 7 h); las del CSV son esas mismas. Horario operable de US100
  (dato del trader): lunes a viernes 01:01–23:59, inicio incluido, fin excluido. (La hipótesis
  textual dice 01:05 porque se copió del oro; para US100 manda el dato del símbolo.)
  Precios: los indicadores se calculan sobre Bid. COMPRA se hace al Ask; SALGO se hace al Bid.
  Ask = Bid + spread de la vela (la columna spread del CSV, en puntos de 0,1 unidades).
  PUNTO = 0,1 unidades de índice (tick_size 0,1). STOPS_LEVEL = 5 puntos = 0,5 unidades
  (dato del bróker; la hipótesis textual dice 4 porque se escribió para el oro).
  Velas: se arman con TODAS las M1 del archivo (también las de horas cerradas) y los
  indicadores usan esa serie completa. Solo existen velas con M1; no se rellenan minutos.
  MERCADO ABIERTO en un minuto = lunes a viernes, de 01:01 (incluido) a 23:59 (excluido).
  Cada acción (colocar, borrar, tocar un stop) vale según el minuto real en que ocurre.
  Capital inicial = 100.000 USD (cuenta en USD, apalancamiento 1:100). RIESGO = 1 % del capital inicial = 1.000.
  VALOR_UNIDAD = 1 USD por lote por cada unidad de índice (contract_size 1, point_value 0,1
  por punto de 0,1; dato del trader). Paso de lote 0,01, mínimo 0,01, máximo 300.
  COSTES (modelo; el cálculo y la prueba son de la fase 04):
    - Spread: el de la última columna del CSV en cada vela, en puntos de 0,1. Si falta,
      5 puntos (la mediana). Es el único coste de entrada y salida (Ask = Bid + spread).
    - Comisión = 0. Deslizamiento = 0.
    - Swap (solo compras, así que aplica el largo): -6,9 % anual, base 365 días, sobre el valor
      nocional de la posición (precio x lote x contract_size). Se cobra una vez por cada noche
      de lunes a viernes, al pasar el rollover de las 00:00 hora del servidor, con coeficiente 1
      (sin día triple). El corto (+1,9 %) no se usa.
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
                * SI NO, SI NIVEL_SEÑAL - Ask < 5 puntos enteros (0,5 unidades): el bróker
                  rechaza la orden y no se reintenta; no queda ORDEN VIVA (la anterior ya no está).
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
       DISTANCIA = PRECIO_ENTRADA - STOP_SWING (con el precio real, no con NIVEL), en unidades de índice.
       SI DISTANCIA < 5 puntos enteros (0,5 unidades): la entrada se descarta (no hay operación). Ve al paso 6.
       LOTE = RIESGO / (DISTANCIA x VALOR_UNIDAD), redondeado hacia ABAJO al paso de lote del
              símbolo (0,01) y acotado entre su lote mínimo (0,01) y máximo (300).
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

Lo que viene del texto del trader y se aplicó tal cual (no son supuestos): ATR = SMA del rango verdadero; nivel Donchian congelado; vigencia de 10 velas de la serie completa desde la de colocación incluida y borrado en el primer tick de la vela siguiente (el fill va primero); entrada a mercado si el precio ya está en el nivel o más allá; fill con gap a la apertura y distancia/lote con el precio real; stop por swing de 20 leído en la vela de entrada y excluyendo la vela en curso; trailing con el ATR(30) de la vela recién cerrada, sin exigir avance previo; entra al Ask y sale al Bid; reemplazo con borrado confirmado antes de colocar; con mercado cerrado se pide una sola vez y no se reintenta; stops level sin reintento (4 puntos en el texto; para US100 se usa 5, ver supuesto 24); horario de lunes a viernes (01:05 en el texto; para US100 se usa 01:01, ver supuesto 26); reentrada desde la vela siguiente a la de salida; capital 100.000 y 1 % de riesgo con el lote redondeado hacia abajo. En real, el EA recuerda el stop del trailing si el bróker lo rechaza y lo reintenta en cada tick (solo con sesión abierta); el backtest da por hecho que el stop nuevo rige desde la apertura siguiente y que un toque solo cuenta con el mercado abierto.

Supuestos del pseudocódigo (todos decididos; solo lo que el texto no dice):
1. US100 y velas de 30 min vienen del trader (la ficha lo indica); mismos parámetros y reglas que la ficha del oro, sin cambiar nada.
2. Solo compras: la orden stop está en el borde superior del canal.
3. «rising(x)» = el valor de la vela cerrada es mayor que el de la vela anterior; igual no cuenta.
4. Estocástico %K(7,3) = %K crudo de 7 velas (incluida la actual) suavizado con media simple de 3; si el rango es 0 se repite el %K crudo anterior.
5. Eficiencia(50) = avance neto de 50 velas / camino total (suma de cambios absolutos de cierre); si el camino es 0, EF = 0.
6. Activación = FILTRO verdadero y DISPARO pasando de falso a verdadero en la misma vela; el FILTRO no se vigila por separado.
7. Donchian(55).upper = el mayor de los máximos (Bid) de las 55 velas cerradas, incluida la de señal. Swing de 20 = el menor de los mínimos (Bid) de las 20 velas cerradas anteriores a la de entrada.
8. Los indicadores necesitan sus velas completas; antes de eso no hay señal.
9. Los costes están en el bloque DATOS (spread del CSV, comisión 0, deslizamiento 0, swap largo); su cálculo y prueba son de la fase 04; el toque del NIVEL se mide con el Ask (Bid + spread de la vela).
10. Stop vigente = el mayor entre el swing de 20 y el trailing; el trailing solo sube (el stop nunca se afloja). El texto no dice «solo sube».
11. Si una vela posterior abre con el Bid por debajo del stop, se sale a esa apertura (hueco); si no, en el nivel del stop. El texto lo da para entradas, no para salidas.
12. Si la compra y el toque del stop caen en la misma vela, se recorren las M1 desde el minuto de la compra; en el mismo minuto gana el stop (mismo criterio que SL y TP).
13. Con posición abierta no se arman órdenes nuevas; las activaciones de ese tiempo se ignoran, pero los indicadores se calculan igual para saber si el DISPARO estaba falso en la vela anterior.
14. El lote lo da el texto: lotaje = riesgo / distancia al SL, con el precio real de entrada, redondeado hacia abajo (paso 4). El ATR fotografiado (atr_ref: signal) se guarda con la orden armada y no entra en esa cuenta ni en el trailing, que usa el ATR de la vela recién cerrada.
15. Sin objetivo de ganancia ni salida por tiempo: salen solo el stop swing y el trailing.
16. Sin límite de operaciones por día; la posición puede pasar de un día a otro y de una semana a otra (ver NOTA). Sin cierre del viernes.
17. Si al reemplazar, la vela de colocación abre en el NIVEL de la orden vieja o más allá, la vieja se llena primero (paso 2a), como en el caso del vencimiento.
18. En el backtest, un borrado o un reemplazo con mercado abierto se confirma siempre; solo falla por mercado cerrado.
19. «Punto» = el punto del símbolo (0,1 unidades); las comparaciones del stops level (5 puntos) se hacen con enteros.
20. Si la entrada se descarta por stops level (paso 4), la orden queda consumida y no hay operación.
21. Si faltan datos (huecos), las velas se cuentan tal como están en el CSV, sin rellenar (en M30 faltan el 2,8 % de las velas dentro del horario, ver la nota de calidad de la Fase 02).
22. Los indicadores se calculan siempre, también con posición abierta y con mercado cerrado.
23. Símbolo (dato del trader): punto 0,1; tick_size 0,1; contract_size 1; point_value 0,1, o sea 1 lote gana o pierde 1 USD por cada unidad de índice; paso de lote 0,01, mínimo 0,01, máximo 300; cuenta en USD, apalancamiento 1:100.
24. Stops level (dato del bróker): 5 puntos = 0,5 unidades. La hipótesis textual dice 4 porque se escribió para el oro; para US100 se usa 5 y el texto textual no se toca. La regla es la misma.
25. La columna spread del CSV está en puntos de 0,1 unidades; el Ask de una vela = Bid + spread x 0,1. Si falta el dato, 5 puntos (la mediana). Comisión 0, deslizamiento 0.
26. Horario operable (dato del símbolo): lunes a viernes 01:01–23:59 hora del servidor, inicio incluido, fin excluido; cotiza 24 h. La hipótesis textual dice 01:05 (copiada del oro); para US100 se usa 01:01 y se declara la diferencia. Hora del servidor = Nueva York + 7 h (confirmado por el export: GMT+3 en septiembre).
27. Swap (dato del trader): largo -6,9 % anual (cuesta), corto +1,9 %; base 365 días; una vez por cada noche de lunes a viernes (coeficiente 1, sin día triple) al pasar el rollover de las 00:00 hora del servidor, sobre el valor nocional (precio x lote x contract_size). Como la regla es solo compras, aplica el largo. Decido: la noche del viernes al sábado cuenta como una noche; el precio del nocional es el cierre Bid de la última vela antes del rollover.
28. Datos: M1 en datos/us100_1m_mt5.csv (curado, resuelve el orden del stop y del nivel) y velas M30 en datos/us100_30m_mt5.csv; la nota de calidad está en la Fase 02.
29. AVISO de datos (dato del trader): los precios mezclan fuentes (2011-2014 de Admirals, 2015-2026 de Dukascopy, la rueda asiática 2015-2018 de OANDA). El CSV tiene barras fuera de la tabla operable (por ejemplo 01:00), que cuentan para velas e indicadores pero no para operar, y le faltan barras donde la tabla dice que debería haber; es normal por ser de otro feed y las velas se cuentan como están (supuesto 21).
30. AVISO de spread (dato del trader): la columna de spread es de RoboForex, medida de 2017-12 a 2026; antes es un perfil fabricado (42,5 % de las barras). En promedio es 10 a 15 % más barata que lo que cotiza OANDA hoy; el spread de 2018 y 2019 puede quedar optimista y 2011 y 2012 tienen solo dos valores de spread. La fase 04 y la 06 deben leer sus costes con esta reserva.

## Fase 04 · Backtest · MOTOR
Agente / skill: validador · validador-4de4 (código: codigo/us100_ruptura_donchian_eficiencia.py, derivado del motor del oro; reporte: resultados/us100_ruptura_donchian_eficiencia_reporte.md)
Qué se hizo: backtest con datos/us100_1m_mt5.csv (M1, 5.213.359 velas, 2011-01-03 a 2026-09-17) y el spread por minuto de datos/US100.csv; 180.678 velas M30. Corte 70/30 por velas: dentro de muestra hasta 2022-01-05 17:00, fuera de muestra 2022-01-05 17:30 a 2026-09-17 (54.204 velas). Costes: spread real del CSV (Ask = Bid + spread × 0,1), comisión 0, deslizamiento 0 y swap largo −6,9 % anual (base 365, sobre el nocional, una vez por noche de lunes a viernes a las 00:00 del servidor) incluido en cada operación, en el factor de beneficio y en la caída. Pseudocódigo tal cual, sin tocar parámetros. Cordura: 3 operaciones fuera de muestra reconstruidas a mano (stop, nivel, lote, salida y swap) coinciden con el motor.
Resultado: fuera de muestra y con costes, factor de beneficio 1,18 (✕, mínimo 1,3) · 610 operaciones (✓, mínimo 30) · caída máxima 8,58 % (✓, máximo 20 %) · factor de beneficio sin la mejor operación 1,15 (✓, mayor que 1) → 3/4. Sin swap el factor de beneficio sería 1,22 (el swap resta 5.758 USD, pero no explica el fallo). Por tramo: primeros 3 años fuera de muestra FB 1,29 (386 operaciones, +28.226 USD); resto FB 0,99 (224 operaciones, −590 USD); 2024 con FB 1,66 sostiene el resultado y 2023, 2025 y 2026 quedan entre 0,99 y 1,03. Dentro de muestra (solo referencia): FB 1,22, caída 20,10 %. Frecuencia: 129,9 operaciones al año = 10,8 al mes (el plan dice unas 6). Con MI_PLAN.md: la caída de 8,58 % supera el 6 % aceptado en backtest, así que no encaja con el plan aunque pase el método.
Supuestos: datos con aviso (el M1 figura NO APTA por 5,5 % de minutos faltantes y se usó igual para resolver el orden del stop, sin rellenar; las velas M30 son APTA CON AVISOS, 2,8 % de velas faltantes); el spread es de RoboForex medido de 2017-12 a 2026, antes es un perfil fabricado, y puede ser optimista (supuesto 30); precio del nocional del swap = cierre Bid de la última vela M30 antes de las 00:00; cada tramo se corre por separado desde 100.000, con la posición abierta al final del tramo cerrada al Bid de la última vela; la posición puede pasar el fin de semana (la hipótesis no cierra el viernes).
Veredicto: NO APRUEBA (3/4; falla el factor de beneficio ≥ 1,3 con 1,18)
Siguiente paso: la fase 05 no procede; idea para la siguiente hipótesis (una sola): la misma ruptura de 55 velas pero cerrando todo antes del cierre del viernes, que encaja con MI_PLAN.md y recorta el swap; el número no se baja.
