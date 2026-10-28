//+------------------------------------------------------------------+
//| xauusd_ruptura_donchian_eficiencia_mt5_indicador.mq5              |
//| Ficha: fichas/xauusd_ruptura_donchian_eficiencia.md                |
//| Plataforma: MetaTrader 5 (indicador) · XAUUSD · M30 · solo compras  |
//| Fecha: 2026-10-28 · generado desde la fase 03 (pseudocódigo)       |
//| Solo dibuja: flecha verde = entrada, flecha roja = salida,          |
//| línea azul = nivel de la orden viva, línea naranja = stop vigente.  |
//| No opera.                                                           |
//|                                                                    |
//| SUPUESTOS DE LA FICHA: los mismos que la estrategia (ver su cabecera)|
//| SUPUESTOS DE PLATAFORMA                                              |
//|  P1. El indicador trabaja con velas de 30 min (no con M1): el Ask de |
//|      cada vela = precio + spread de la vela. Si en una misma vela se |
//|      llena la orden y se toca el stop, gana el stop (peor caso).     |
//|      Puede diferir un poco del Probador, que mira tick a tick.       |
//|  P2. Mercado abierto = lunes a viernes; la vela cuenta si alguna     |
//|      parte cae entre 01:05 y 23:59 de la hora del servidor.          |
//|  P3. La orden stop es virtual, como en la estrategia (lote y stop    |
//|      con el precio real de entrada).                                 |
//+------------------------------------------------------------------+
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   4
#property indicator_type1   DRAW_ARROW
#property indicator_color1  clrLimeGreen
#property indicator_label1  "Entrada"
#property indicator_type2   DRAW_ARROW
#property indicator_color2  clrRed
#property indicator_label2  "Salida"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrOrange
#property indicator_label3  "Stop vigente"
#property indicator_type4   DRAW_LINE
#property indicator_color4  clrDodgerBlue
#property indicator_label4  "Nivel de la orden"

// ---- PARÁMETROS (mismos números y nombres que la ficha) ----
input int    n_donchian         = 55;
input int    n_swing            = 20;
input int    n_atr              = 30;
input int    n_eficiencia       = 50;
input int    k_periodo          = 7;
input int    k_suavizado        = 3;
input double mult_atr           = 3.0;
input int    vida_orden         = 10;
input int    stops_level_puntos = 4;
input int    apertura_min       = 65;
input int    cierre_min         = 1439;
input int    desfase_horas      = 0;

double entradas[], salidas[], stops[], niveles[];

int OnInit()
{
   SetIndexBuffer(0, entradas, INDICATOR_DATA); PlotIndexSetInteger(0, PLOT_ARROW, 233);
   SetIndexBuffer(1, salidas,  INDICATOR_DATA); PlotIndexSetInteger(1, PLOT_ARROW, 234);
   SetIndexBuffer(2, stops,    INDICATOR_DATA);
   SetIndexBuffer(3, niveles,  INDICATOR_DATA);
   for(int p = 0; p < 4; p++) PlotIndexSetDouble(p, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   return INIT_SUCCEEDED;
}

// ---------------------------------------------------------------- indicadores sobre la vela cerrada i (0 = la más antigua)
double KCrudo(int i, const double &high[], const double &low[], const double &close[])
{
   for(int t = i; t > i - 20 && t - k_periodo + 1 >= 0; t--)      // rango 0: repito el K crudo anterior
   {
      double ll = low[t], hh = high[t];
      for(int q = t - k_periodo + 1; q < t; q++) { ll = MathMin(ll, low[q]); hh = MathMax(hh, high[q]); }
      if(hh - ll > 0) return 100.0 * (close[t] - ll) / (hh - ll);
   }
   return EMPTY_VALUE;
}

double K(int i, const double &high[], const double &low[], const double &close[])
{
   double suma = 0;
   for(int q = i; q > i - k_suavizado; q--)
   {
      if(q < 0) return EMPTY_VALUE;
      double kc = KCrudo(q, high, low, close);
      if(kc == EMPTY_VALUE) return EMPTY_VALUE;
      suma += kc;
   }
   return suma / k_suavizado;
}

double Eficiencia(int i, const double &close[])
{
   if(i - n_eficiencia < 0) return EMPTY_VALUE;
   double camino = 0;
   for(int t = i; t > i - n_eficiencia; t--) camino += MathAbs(close[t] - close[t - 1]);
   if(camino <= 0) return 0.0;
   return MathAbs(close[i] - close[i - n_eficiencia]) / camino;
}

double Atr(int i, const double &high[], const double &low[], const double &close[])
{
   if(i - n_atr < 0) return EMPTY_VALUE;
   double suma = 0;
   for(int t = i; t > i - n_atr; t--)
      suma += MathMax(high[t] - low[t], MathMax(MathAbs(high[t] - close[t - 1]), MathAbs(low[t] - close[t - 1])));
   return suma / n_atr;
}

bool MercadoAbierto(datetime inicio_vela)
{
   MqlDateTime d;
   TimeToStruct(inicio_vela - desfase_horas * 3600, d);
   if(d.day_of_week < 1 || d.day_of_week > 5) return false;
   int minuto = d.hour * 60 + d.min;
   int duracion = PeriodSeconds(_Period) / 60;
   return minuto + duracion > apertura_min && minuto < cierre_min;      // P2
}

int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[],
                const double &open[], const double &high[], const double &low[], const double &close[],
                const long &tick_volume[], const long &volume[], const int &spread[])
{
   static int ultimo_total = 0;
   if(rates_total == ultimo_total && prev_calculated > 0) return rates_total;     // solo al formarse una vela nueva
   ultimo_total = rates_total;

   ArrayInitialize(entradas, EMPTY_VALUE); ArrayInitialize(salidas, EMPTY_VALUE);
   ArrayInitialize(stops, EMPTY_VALUE);    ArrayInitialize(niveles, EMPTY_VALUE);

   bool   dentro = false, orden_viva = false, senal = false;
   double stop = 0, orden_nivel = 0, senal_nivel = 0;
   int    orden_vida = 0;

   for(int i = 1; i < rates_total - 1; i++)           // solo velas cerradas (la última no se usa)
   {
      bool abierto = MercadoAbierto(time[i]);
      double ask_ap = open[i] + spread[i] * _Point;
      double ask_max = high[i] + spread[i] * _Point;
      bool compra = false;
      double px = 0;

      if(!dentro)
      {
         if(orden_viva) orden_vida++;                                              // Paso 1
         if(orden_viva && abierto && ask_ap >= orden_nivel) { compra = true; px = ask_ap; senal = false; }   // 2a
         else
         {
            if(orden_viva && orden_vida > vida_orden && abierto) orden_viva = false;                    // 2b
            if(senal)                                                                                   // 2c
            {
               if(abierto)
               {
                  orden_viva = false;
                  if(ask_ap >= senal_nivel) { compra = true; px = ask_ap; }
                  else if((int)MathRound((senal_nivel - ask_ap) / _Point) >= stops_level_puntos)
                  { orden_viva = true; orden_nivel = senal_nivel; orden_vida = 1; }
               }
               senal = false;
            }
            if(!compra && orden_viva && abierto && ask_max >= orden_nivel)                              // Paso 3
            { compra = true; px = MathMax(orden_nivel, ask_ap); }
         }
         if(compra)                                                                                     // Paso 4
         {
            orden_viva = false;
            double sw = low[i - 1];
            for(int t = i - n_swing; t < i; t++) { if(t < 0) { sw = EMPTY_VALUE; break; } sw = MathMin(sw, low[t]); }
            if(sw != EMPTY_VALUE && (int)MathRound((px - sw) / _Point) >= stops_level_puntos)
            {
               dentro = true; stop = sw;
               entradas[i] = low[i] - 2 * _Point;
               if(low[i] <= stop)                      // misma vela: gana el stop (P1)
               {
                  salidas[i] = high[i] + 2 * _Point;
                  dentro = false;
               }
            }
         }
      }
      else if(low[i] <= stop)                          // Paso 5a · el stop se toca antes del trailing
      {
         salidas[i] = high[i] + 2 * _Point;
         dentro = false;
      }

      if(dentro)                                       // Paso 5b · trailing al cierre
      {
         double atr = Atr(i, high, low, close);
         if(atr != EMPTY_VALUE) stop = MathMax(stop, close[i] - mult_atr * atr);
         stops[i] = stop;
      }
      if(orden_viva) niveles[i] = orden_nivel;

      if(!dentro)                                      // Paso 6 · señal al cierre de la vela
      {
         double k1 = K(i, high, low, close), k2 = K(i - 1, high, low, close);
         double e1 = Eficiencia(i, close), e2 = Eficiencia(i - 1, close), e3 = Eficiencia(i - 2, close);
         double atr = Atr(i, high, low, close);
         if(k1 != EMPTY_VALUE && k2 != EMPTY_VALUE && e1 != EMPTY_VALUE && e2 != EMPTY_VALUE && e3 != EMPTY_VALUE
            && atr != EMPTY_VALUE && i - n_donchian + 1 >= 0)
         {
            if(k1 > k2 && e1 > e2 && !(e2 > e3))
            {
               senal = true;
               senal_nivel = high[i];
               for(int t = i - n_donchian + 1; t < i; t++) senal_nivel = MathMax(senal_nivel, high[t]);
            }
         }
      }
   }
   return rates_total;
}
