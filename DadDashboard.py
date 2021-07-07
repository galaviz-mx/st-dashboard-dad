#%%
from numpy.core.numerictypes import obj2sctype
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import datetime

@st.cache
def get_data_v():
    libro = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS97LrfjABDIYNcpmilR916ORtEk7-6gjEb32SwYjy0OHivnp-pUGRZDH_x3_RXlZU0oTEdV1XUgLhj/pub?output=xlsx'
    hoja_data = 'DATA'
    hoja_obj = 'OBJECTS'

    datos = pd.read_excel(libro, sheet_name=hoja_data, dtype={'VALUE': np.int64})
    datos_objetos = pd.read_excel(libro, sheet_name=hoja_obj)
    datos_objetos.set_index('ID', inplace=True)
    datos_objetos = datos_objetos.loc[datos_objetos.TYPE=='VEHICLE'].copy()

    datos_t = pd.DataFrame(columns=['DATE','DIST','OBJECT','Month','Year'])
    datos_t.set_index('DATE',inplace = True)

    datos_odmt = pd.DataFrame(columns=['DATE','ODM','OBJECT','Month','Year'])
    datos_odmt.set_index('DATE', inplace=True)

    objetos = datos_objetos.index

    for objeto in objetos:
        datos_o = datos.loc[(datos.OBJECT==objeto)&(datos.EVENT=='ODOMETER')].copy()
        datos_o = datos_o[['DATE', 'VALUE']]
        datos_odm = datos_o.copy()
        
        datos_o['DATE_P'], datos_o['VALUE_P'] = datos_o.DATE.shift(1), datos_o.VALUE.shift(1)
        datos_o['DAYS'], datos_o['DIST'] = (datos_o['DATE']-datos_o['DATE_P']).dt.days, (datos_o['VALUE']-datos_o['VALUE_P'])
        datos_o['DD'] = datos_o['DIST']/datos_o['DAYS']
        datos_o = datos_o[datos_o['DATE_P'].notna()]

        fecha_ini = np.min(datos_o.DATE_P)
        fecha_fin = np.max(datos_o.DATE) + pd.DateOffset(days=-1)

        datos_o = datos_o[['DATE_P', 'DD']]
        datos_o.loc[len(datos_o)] = [fecha_fin, datos_o['DD']. iloc[-1]]
        datos_o.rename(columns={'DATE_P': 'DATE','DD': 'DIST'}, inplace=True)
        datos_o.set_index('DATE', inplace=True)
        datos_o = datos_o.resample('1D').ffill()
        datos_o = datos_o.resample('1M').sum()
        datos_o['OBJECT'], datos_o['DIST'] = objeto, datos_o['DIST'].astype(np.int64)
        
        # --- fecha_mes_ini (fecha de primer mes completo) y fecha_mes_fin (fecha de ultimo mes completo) ---
        fecha_mes_ini = fecha_ini + pd.offsets.MonthEnd(0) if fecha_ini.day == 1 else (fecha_ini + pd.DateOffset(months=1)) + pd.offsets.MonthEnd(0)
        fecha_mes_fin = ((fecha_fin + pd.DateOffset(months=-1)) + pd.offsets.MonthEnd(0)) if fecha_fin.month == (fecha_fin + pd.DateOffset(days=1)).month else fecha_fin

        datos_o = datos_o.loc[(datos_o.index>=fecha_mes_ini) & (datos_o.index<=fecha_mes_fin)]
        datos_o['Month'], datos_o['Year'] = datos_o.index.month, datos_o.index.year

        datos_t = datos_t.append(datos_o, ignore_index=False)

        datos_odm.set_index('DATE', inplace=True)
        datos_odm = datos_odm.resample('1M').bfill()
        datos_odm = datos_odm[datos_odm['VALUE'].notna()]
        datos_odm.rename(columns={'VALUE': 'ODM'}, inplace=True)
        datos_odm['OBJECT'], datos_odm['Month'], datos_odm['Year'] = objeto, datos_odm.index.month, datos_odm.index.year
        datos_odmt = datos_odmt.append(datos_odm, ignore_index=False)

    objetos = dict(datos_objetos.NAME)
    datos_t['OBJECT'] = datos_t['OBJECT'].map(objetos)
    datos_odmt['OBJECT'] = datos_odmt['OBJECT'].map(objetos)

    return datos_t, datos_odmt

@st.cache
def get_data_s():
    libro = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS97LrfjABDIYNcpmilR916ORtEk7-6gjEb32SwYjy0OHivnp-pUGRZDH_x3_RXlZU0oTEdV1XUgLhj/pub?output=xlsx'
    hoja_data = 'DATA'
    hoja_obj = 'OBJECTS'

    datos = pd.read_excel(libro, sheet_name=hoja_data, dtype={'VALUE': np.int64})
    datos_objetos = pd.read_excel(libro, sheet_name=hoja_obj)
    datos_objetos.set_index('ID', inplace=True)
    datos_objetos = datos_objetos.loc[datos_objetos.TYPE=='SERVICE'].copy()

    datos_s = pd.DataFrame(columns=['DATE','CONSUMPTION','OBJECT','Month','Year'])
    datos_s.set_index('DATE',inplace = True)

    objetos = datos_objetos.index
    
    for objeto in objetos:
        datos_t = datos.loc[(datos.OBJECT==objeto)&(datos.EVENT=='METER')].copy()
        datos_t = datos_t[['DATE', 'VALUE']]
        
        datos_t['DATE_P'], datos_t['VALUE_P'] = datos_t.DATE.shift(1), datos_t.VALUE.shift(1)
        datos_t['DAYS'], datos_t['CONSUMPTION'] = (datos_t['DATE']-datos_t['DATE_P']).dt.days, (datos_t['VALUE']-datos_t['VALUE_P'])
        datos_t['DC'] = datos_t['CONSUMPTION']/datos_t['DAYS']
        datos_t = datos_t[datos_t['DATE_P'].notna()]

        fecha_ini = np.min(datos_t.DATE_P)
        fecha_fin = np.max(datos_t.DATE) + pd.DateOffset(days=-1)

        datos_t = datos_t[['DATE_P', 'DC']]
        datos_t.loc[len(datos_t)] = [fecha_fin, datos_t['DC']. iloc[-1]]
        datos_t.rename(columns={'DATE_P': 'DATE','DC': 'CONSUMPTION'}, inplace=True)
        datos_t.set_index('DATE', inplace=True)
        datos_t = datos_t.resample('1D').ffill()
        datos_t = datos_t.resample('1M').sum()
        datos_t['OBJECT'], datos_t['CONSUMPTION'] = objeto, datos_t['CONSUMPTION'].astype(np.int64)

        # --- fecha_mes_ini (fecha de primer mes completo) y fecha_mes_fin (fecha de ultimo mes completo) ---
        fecha_mes_ini = fecha_ini + pd.offsets.MonthEnd(0) if fecha_ini.day == 1 else (fecha_ini + pd.DateOffset(months=1)) + pd.offsets.MonthEnd(0)
        fecha_mes_fin = ((fecha_fin + pd.DateOffset(months=-1)) + pd.offsets.MonthEnd(0)) if fecha_fin.month == (fecha_fin + pd.DateOffset(days=1)).month else fecha_fin

        datos_t = datos_t.loc[(datos_t.index>=fecha_mes_ini) & (datos_t.index<=fecha_mes_fin)]
        datos_t['Month'], datos_t['Year'] = datos_t.index.month, datos_t.index.year
    
        datos_s = datos_s.append(datos_t, ignore_index=False)

    objetos = dict(datos_objetos.NAME)
    datos_s['OBJECT'] = datos_s['OBJECT'].map(objetos)
    print(datos_s)
    return datos_s

# --- STREAMLIT CONFIGURATION ---
st.set_page_config(layout="wide")
header_container = st.beta_container()
vehicles_container = st.beta_container()
services_container = st.beta_container()

with header_container:
	st.image('logo chg.png')
	st.title('Dad\'s vehicles & services dashboard')
	#st.header("Welcome!")
	#st.subheader('Believed or not, my dad keep records every two week of all his odometers car\'s and services meters')
	st.write('Believed or not, my dad keep records every two week of all his odometers vehicles and services meters. Let see how the look like.')

with vehicles_container:
    st.header('Vehicles data')
    datos_t, datos_odmt = get_data_v()
    col_1, col_2 = st.beta_columns(2)

    #col_1.subheader('Monthly distance per vehicle')
    fig = px.line(datos_t, x=datos_t.index, y='DIST', color='OBJECT', color_discrete_sequence=px.colors.qualitative.G10, line_shape='spline')
    nota1 = datetime.datetime(2020,5,1).timestamp() * 1000
    fig.add_vline(x=nota1, line_width=3, line_dash='dash', line_color='white', annotation_text='confinement', annotation_position='top right')
    fig['layout']['yaxis'].update(showgrid=True, side='left', title= 'Distance KM')
    fig.update_layout(title=dict(text='Monthly distance', y=0.925, x=0.5, xanchor='center', yanchor='top') ,legend=dict(yanchor='top', xanchor='left', x=1, y=1))
    col_1.write(fig)
    #col_2.subheader('Vehicle\'s odometer')
    fig1 = px.line(datos_odmt, x=datos_odmt.index, y='ODM', color='OBJECT', color_discrete_sequence=px.colors.qualitative.G10, line_shape='spline')
    fig1.add_vline(x=nota1, line_width=3, line_dash='dash', line_color='white', annotation_text='confinement', annotation_position='top right')
    fig1['layout']['yaxis'].update(showgrid=True, side='left', title= 'Odometer KM')
    fig1.update_layout(title=dict(text='Monthly odometer', y=0.925, x=0.5, xanchor='center', yanchor='top') ,legend=dict(yanchor='top', xanchor='left', x=1, y=1))
    col_2.write(fig1)
    st.write('Observations: Before pandemic confinement the XTRAIL and lastly the SIENNA were used to make travels, after confinement just essentials travels were made by the DAKOTA and more recently XTRAIL start to make travels. VENTO daily basis use.')

with services_container:
    st.header('Services data')
    datos_s = get_data_s()
    col_1, col_2 = st.beta_columns(2)

    datos_fig3 = datos_s.loc[(datos_s.OBJECT=='Electricity CFE')].copy()
    fig3 = px.line(datos_fig3, x='Month', y='CONSUMPTION', color='Year', color_discrete_sequence=px.colors.sequential.Plasma_r, line_shape='spline')
    fig3['layout']['yaxis'].update(showgrid=True, side='left', title= 'Electric Energy KWH')
    fig3.update_layout(title=dict(text='Monthly Electric Energy Consumption', y=0.925, x=0.5, xanchor='center', yanchor='top') ,legend=dict(yanchor='top', xanchor='left', x=1, y=1))
    fig3.update_layout(xaxis = dict(tickmode = 'array', tickvals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
    fig3_n = datos_s.loc[(datos_s.OBJECT=='Electricity CFE') & (datos_s.Year==2020) & (datos_s.Month==5)]
    fig3_n = fig3_n.iloc[0]['CONSUMPTION']
    fig3.add_annotation(x=5, y=fig3_n, text='confinement', showarrow=True, arrowhead=2, arrowcolor='white', arrowsize=1, arrowwidth=2)
    col_1.write(fig3)
    st.write('Observations: After pandemic confinement my father\'s stay more time in home, but despite they live in a very hot weather they avoid temperatures changes so they minimize the use of AC, and so the lover energy consumption. About the potable water consumption, I guess less activities mean less consumption, the last 2 months they have a leak that just was repaired.')

    datos_fig4 = datos_s.loc[(datos_s.OBJECT=='Water COMAPA')].copy()
    fig4 = px.line(datos_fig4, x='Month', y='CONSUMPTION', color='Year', color_discrete_sequence=px.colors.sequential.Plasma_r, line_shape='spline')
    fig4['layout']['yaxis'].update(showgrid=True, side='left', title= 'Potable Water M3')
    fig4.update_layout(title=dict(text='Monthly Potable Water Consumption', y=0.925, x=0.5, xanchor='center', yanchor='top') ,legend=dict(yanchor='top', xanchor='left', x=1, y=1))
    fig4.update_layout(xaxis = dict(tickmode = 'array', tickvals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
    fig4_n = datos_s.loc[(datos_s.OBJECT=='Water COMAPA') & (datos_s.Year==2020) & (datos_s.Month==5)]
    fig4_n = fig4_n.iloc[0]['CONSUMPTION']
    fig4.add_annotation(x=5, y=fig4_n, text='confinement', showarrow=True, arrowhead=2, arrowcolor='white', arrowsize=1, arrowwidth=2)
    col_2.write(fig4)

# %%
