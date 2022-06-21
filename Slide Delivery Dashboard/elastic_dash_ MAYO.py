import pandas as pd
import numpy as np
import datetime
from datetime import datetime as dt
import pathlib
import statistics as stat
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc 
import requests
import json

query = {"query": {"match_all": {}},"size": 10000,"sort": [{"data.time_stamp": {"order": "desc"}}]}
password = "=YZ=203Dkj5HG3HZ+fXh"
host_name = '10.104.16.22'

index_name = "basket_data"
url = "https://elastic:{}@{}:9200/{}/_search".format(password, host_name, index_name)
response5 = requests.get(url,json = query, verify = '/etc/elasticsearch/certs/http_ca.crt')
response_json5 = json.loads(response5.text)
basket_data = pd.json_normalize(response_json5['hits']['hits'])
basket_data = basket_data.sort_values(by = ['_source.data.row_index'], ascending = True)
basket_data = basket_data.sort_values(by = ['_source.data.col_index'], ascending = True)
basket_data['row_col'] = (basket_data['_source.data.row_index']+1).astype(str)+"_"+(basket_data['_source.data.col_index']+1).astype(str)
basket_data['_source.data.date'] = pd.to_datetime(basket_data['_source.data.time_stamp']).dt.date


app = dash.Dash(__name__, external_stylesheets = [dbc.themes.LUX],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Slide Delivery Dashboard", className = 'text-center text-primary, mb-4'), width = 12)   
    ]),
    dbc.Row([
        dbc.Col([
            html.P('Select Cluster ID:', style = {'textDecoration':'underline'}, className = 'text-primary, mb-2'),
            dcc.Dropdown(id = 'cluster', multi = False,  value = 'CS001',
                        options = [{'label':x, 'value':x}
                                  for x in sorted(basket_data['_source.data.cluster_name'].unique())])
        ], width = {'size':6}),
        
        dbc.Col([
            html.H6('Select Station Number:', style = {'textDecoration':'underline'}, className = 'text-primary, mb-2'),
            dcc.RadioItems(id = 'station',options = [{'label':x, 'value':x}
                                  for x in sorted(basket_data['_source.data.scanner_position'].unique())],  
                           value = 1,labelClassName = 'mr-5')
        ], width = {'size':6})
    ]),
    html.Br(),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.P('Select Date:', style = {'textDecoration':'underline'}, className = 'text-center text-primary, mb-2'),
            dcc.Dropdown(id = 'date', multi = False, value = sorted(basket_data['_source.data.date'].unique())[-1],
                        options = [{'label':x, 'value':x}
                                  for x in sorted(basket_data['_source.data.date'].unique(), reverse = True)])
        ], width = {'size':12})
    ]),
    html.Br(),
    html.Br(),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id = 'inline',figure = {})
        ], width = {'size':12})
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id = 'x_off',figure = {})
        ], width = {'size':12})
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id = 'y_off',figure = {})
        ], width = {'size':12})
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id = 'locking',figure = {})
        ], width = {'size':12})
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id = 'picking',figure = {})
        ], width = {'size':12})
    ]), 
    dbc.Row([
        dbc.Col([
            dcc.Graph(id = 'thickness',figure = {})
        ], width = {'size':12})
    ])

],fluid = True)

# Multiple Input, multiple Output, dash.no_update
@app.callback(
    [Output(component_id='thickness', component_property='figure'),
    Output(component_id='inline', component_property='figure'),
    Output(component_id='x_off', component_property='figure'),
    Output(component_id='y_off', component_property='figure'),
     Output(component_id='locking', component_property='figure'),
    Output(component_id='picking', component_property='figure')],
    [Input(component_id='cluster', component_property='value'),
     Input(component_id='station', component_property='value'),
    Input(component_id='date', component_property='value')],
    prevent_initial_call=False
)
def update_graph(cluster_chosen, station_chosen, date_chosen): 
    df = basket_data[basket_data['_source.data.cluster_name'] == cluster_chosen]
    dff = df[df['_source.data.scanner_position'] == station_chosen]
    dff['_source.data.date'] = pd.to_datetime(dff['_source.data.date'])
    dfff = dff[dff['_source.data.date'] == date_chosen]
    if len(dfff) > 0:
        dfff = dfff.sort_values(by = ['_source.data.load_identifier'], ascending = False)
        load = dfff['_source.data.load_identifier'].iloc[0]

        #basket
        final_df1 = basket_data[basket_data['_source.data.load_identifier'] == load]
        final_df1 = final_df1.sort_values(["_source.data.row_index","_source.data.col_index"], ascending = (True, True))
        fig1 = px.scatter(final_df1, y='row_col',x="_source.data.slide_thickness",color="_source.data.scanner_name",marginal_x="histogram")
        fig1.update_yaxes(title='Slot Position')
        fig1.update_xaxes(title='Thickness in mm')
        fig1.update_layout(legend_title="Scanner",title="Slide Thickness Plot",height=800,yaxis1=dict(title="Slot Position"),xaxis1=dict(title="Slide Thickness(mm)"))  
        fig1.add_annotation(text="<b>"+final_df1['_source.data.scanner_name'].iloc[0],xref="paper", yref="paper",showarrow=False,x=0, y=0,opacity=0.5,font=dict(family="Courier New, monospace",
            size=24,color="RebeccaPurple"))
        
        #inline 
        index_name = "slide_placement"
        url = "https://elastic:{}@{}:9200/{}/_search".format(password, host_name, index_name)
        query1 = {"size":10000,"query": {"match_phrase": {"data.load_identifier": load}}}
        response1 = requests.get(url,json = query1, verify = '/etc/elasticsearch/certs/http_ca.crt')
        response_json1 = json.loads(response1.text)
        slide_placement = pd.json_normalize(response_json1['hits']['hits'])
        slide_placement = slide_placement.sort_values(by = ['_source.data.row_index'], ascending = True)
        slide_placement = slide_placement.sort_values(by = ['_source.data.col_index'], ascending = True)
        slide_placement['row_col'] = (slide_placement['_source.data.row_index']+1).astype(str)+"_"+(slide_placement['_source.data.col_index']+1).astype(str)
        slide_placement['_source.data.date'] = pd.to_datetime(slide_placement['_source.data.time_stamp']).dt.date


        index_name = "inline_corrections"
        url = "https://elastic:{}@{}:9200/{}/_search".format(password, host_name, index_name)
        query1 = {"size":10000,"query": {"match_phrase": {"data.load_identifier": load}}}
        response2 = requests.get(url,json = query1, verify = '/etc/elasticsearch/certs/http_ca.crt')
        response_json2 = json.loads(response2.text)
        inline_corrections = pd.json_normalize(response_json2['hits']['hits'])
        inline_corrections = inline_corrections.sort_values(by = ['_source.data.row_index'], ascending = True)
        inline_corrections = inline_corrections.sort_values(by = ['_source.data.col_index'], ascending = True)
        inline_corrections['_source.data.date'] = pd.to_datetime(inline_corrections['_source.data.time_stamp']).dt.date
        inline_corrections['row_col'] = (inline_corrections['_source.data.row_index']+1).astype(str)+"_"+(inline_corrections['_source.data.col_index']+1).astype(str)

        both2 = pd.merge(slide_placement,inline_corrections,on=["_source.data.slide_id","_source.data.scanner_name",
                          "_source.data.load_identifier","_source.data.row_index","_source.data.col_index","row_col",
                          "_source.data.cluster_name"])

        both2 = both2.drop_duplicates(subset="_source.data.slide_id",keep="last")
        both2['computed_angle'] = both2['_source.data.computed_angle']*(180/3.14)
        both2['angle_difference'] = round(both2['_source.data.actual_angle'] - both2['computed_angle'],2)

        both = both2[both2["_source.data.load_identifier"] == load]
        fig2 = make_subplots(
                    rows=1, cols=4,
                    subplot_titles=("<b>Row : 1 ","<b>Row : 2 ","<b>Row : 3 ","<b>Row : 4 "))
        for i in range(4):
            fig2.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==i]['_source.data.actual_angle'],2),y=both[both['_source.data.row_index']==i]['row_col'],
                                    name="Actual Angle",showlegend=False,mode="markers",marker=dict(color="MediumPurple")),row=1,col=(i+1))
            fig2.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==i]['computed_angle'],2),y=both[both['_source.data.row_index']==i]['row_col'],
                                    name="Computed Angle",showlegend=False,mode="markers",marker=dict(color="salmon")),row=1,col=(i+1))
            fig2.add_annotation(y=-3,text="<b>Postive Adjustments : "+str(len(both[(both['_source.data.row_index']==i)&(both['angle_difference']>0)]))+\
                        "<br>Negative Adjustments : "+str(len(both[(both['_source.data.row_index']==i)&(both['angle_difference']<0)]))+\
                            "<br>μ Postive Adjustments : "+str(round(np.mean(both[(both['_source.data.row_index']==i)&(both['angle_difference']>0)]['angle_difference']),2))+\
                            "<br>μ Negative Adjustments : "+str(round(np.mean(both[(both['_source.data.row_index']==i)&(both['angle_difference']<0)]['angle_difference']),2)),
                            showarrow=False,row=1,col=(i+1))

        fig2.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==0]['computed_angle'],2),y=both[both['_source.data.row_index']==0]['row_col'],
                                name="Incoming Angle",mode="markers",marker=dict(color="salmon")),row=1,col=1)
        fig2.add_trace(go.Scatter(x=round(both[both['_source.data.row_index']==0]['_source.data.actual_angle'],2),y=both[both['_source.data.row_index']==0]['row_col'],
                                name="Corrected Angle",mode="markers",marker=dict(color="MediumPurple")),row=1,col=1)
        fig2.update_layout(title="<b>Angle Adjustment Plot",height=800,width=1750,hovermode="y unified")
        fig2.update_yaxes(autorange="reversed")
        fig2.update_yaxes(title="Slot Position",row=1,col=1)
        fig2.update_xaxes(title="Slide Angle")
        fig2.update_xaxes(range=[-4.3,4.3])
        fig2.add_vline(x=-4, line_width=3, line_dash="dash", line_color="red")
        fig2.add_vline(x=4, line_width=3, line_dash="dash", line_color="red")
        fig2.add_annotation(x=1.14,y=0.9,xref="paper",yref="paper",
                text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(both[both['angle_difference']>0]))+\
                        "<br>-ve Adjustments : "+str(len(both[both['angle_difference']<0]))+\
                            "<br>μ +ve Adjustments : "+str(round(np.mean(both[both['angle_difference']>0]['angle_difference']),2))+\
                            "<br>μ -ve Adjustments :"+str(round(np.mean(both[both['angle_difference']<0]['angle_difference']),2)),
                showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="white",
                opacity=0.8
                )
        fig2.add_annotation(text="<b>"+both['_source.data.scanner_name'].iloc[0],xref="paper", yref="paper",showarrow=False,x=0, y=0,opacity=0.5,font=dict(family="Courier New, monospace",
                    size=24,color="RebeccaPurple"))


        #X offset
        slide_placement = slide_placement[slide_placement["_source.data.load_identifier"] == load]
        fig3 = make_subplots(
                        rows=1, cols=4,
                        subplot_titles=("<b>Row : 1 ","<b>Row : 2 ","<b>Row : 3 ","<b>Row : 4 "))
        for i in range(4):
            fig3.add_trace(go.Scatter(x=slide_placement[slide_placement['_source.data.row_index']==i]['_source.data.offset_pos_x_um'],y=slide_placement[slide_placement['_source.data.row_index']==i]['row_col'],
                                    name="X-Offset",showlegend=False,mode="markers",marker=dict(color="MediumPurple")),row=1,col=(i+1))

            fig3.add_annotation(y=-3,text="<b>Postive Adjustments : "+str(len(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']>0)]))+\
                        "<br>Negative Adjustments : "+str(len(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']<0)]))+\
                            "<br>μ Postive Adjustments : "+str(round(np.mean(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']>0)]['_source.data.offset_pos_x_um']),2))+\
                            "<br>μ Negative Adjustments : "+str(round(np.mean(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_x_um']<0)]['_source.data.offset_pos_x_um']),2)),
                            showarrow=False,row=1,col=(i+1))

        fig3.add_trace(go.Scatter(x=slide_placement[slide_placement['_source.data.row_index']==0]['_source.data.offset_pos_x_um'],y=slide_placement[slide_placement['_source.data.row_index']==0]['row_col'],
                                name="X-Offset                      ",mode="markers",marker=dict(color="MediumPurple")),row=1,col=1)
        ##########################################################################
        fig3.add_scatter(y=slide_placement[slide_placement['_source.data.offset_pos_x_um']<-3500]['row_col'],
                        x=slide_placement[slide_placement['_source.data.offset_pos_x_um']<-3500]['_source.data.offset_pos_x_um'],
                    marker=dict(color="red",size=10),mode="markers", showlegend = False)
    
        fig3.add_scatter(y=slide_placement[slide_placement['_source.data.offset_pos_x_um']>3500]['row_col'],
                        x=slide_placement[slide_placement['_source.data.offset_pos_x_um']>3500]['_source.data.offset_pos_x_um'],
                    marker=dict(color="red",size=10),mode="markers", showlegend = False)
        ##########################################################################

        fig3.update_layout(title="<b>X-Offset Plot",height=800,width=1750)
        fig3.update_yaxes(autorange="reversed")
        fig3.update_yaxes(title="Slot Position",row=1,col=1)
        fig3.update_xaxes(title="X-Offset(um)",range=[-5000,5000])
        fig3.add_vline(x=-3500, line_width=3, line_dash="dash", line_color="red")
        fig3.add_vline(x=3500, line_width=3, line_dash="dash", line_color="red")
        fig3.add_vline(x=-2963.7351, line_width=3, line_dash="dash", line_color="orange")
        fig3.add_vline(x=3068.36766, line_width=3, line_dash="dash", line_color="orange")
        #############
        fig3.add_annotation(x=1.158,y=0.9,xref="paper",yref="paper",
                text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_x_um']>0]))+\
                        "<br>-ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_x_um']<0]))+\
                            "<br>μ +ve Adjustments : "+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_x_um']>0]['_source.data.offset_pos_x_um']),2))+\
                            "<br>μ -ve Adjustments :"+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_x_um']<0]['_source.data.offset_pos_x_um']),2)),
                showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="white",
                opacity=0.8)
        fig3.add_annotation(text="<b>"+slide_placement['_source.data.scanner_name'].iloc[0],xref="paper", yref="paper",showarrow=False,x=0, y=0,opacity=0.5,font=dict(family="Courier New, monospace",
            size=24,color="RebeccaPurple"))


        #Y Offset        
        slide_placement = slide_placement[slide_placement["_source.data.load_identifier"] == load]
        fig4 = make_subplots(
                            rows=4, cols=1,
                            subplot_titles=("<b>Row : 1 ","<b>Row : 2 ","<b>Row : 3 ","<b>Row : 4 "))
        for i in range(4):
            fig4.add_trace(go.Scatter(y=slide_placement[slide_placement['_source.data.row_index']==i]['_source.data.offset_pos_y_um'],x=slide_placement[slide_placement['_source.data.row_index']==i]['row_col'],
                                    name="X-Offset",showlegend=False,mode="markers",marker=dict(color="MediumPurple")),row=(i+1),col=1)

            fig4.add_annotation(x=-4,xref="x",yref="y",text="<b>Postive Adjustments : "+str(len(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_y_um']>0)]))+\
                            "<br>μ Postive Adjustments : "+str(round(np.mean(slide_placement[(slide_placement['_source.data.row_index']==i)&(slide_placement['_source.data.offset_pos_y_um']>0)]['_source.data.offset_pos_y_um']),2)),
                            showarrow=False,row=(i+1),col=1)

        fig4.add_trace(go.Scatter(y=slide_placement[slide_placement['_source.data.row_index']==0]['_source.data.offset_pos_y_um'],x=slide_placement[slide_placement['_source.data.row_index']==0]['row_col'],
                                name="Y-Offset                ",mode="markers",marker=dict(color="MediumPurple")),row=1,col=1)

        fig4.update_layout(title="<b>Y-Offset Plot",height=800,width=1750)
        # fig.update_xaxes(autorange="reversed")
        fig4.update_xaxes(tickangle=55)
        fig4.update_xaxes(title="Slot Position",row=4,col=1)
        fig4.update_yaxes(title="Y-Offset(um)",range=[0,6000])
        fig4.add_hline(y=0, line_width=3, line_dash="dash", line_color="red")
        fig4.add_hline(y=5000, line_width=3, line_dash="dash", line_color="red")
        fig4.add_hline(y=951.07712, line_width=3, line_dash="dash", line_color="orange")
        fig4.add_hline(y=4192.457517, line_width=3, line_dash="dash", line_color="orange")
        #########
        fig4.add_annotation(x=1.158,y=0.9,xref="paper",yref="paper",
                text="<br><b>Basket Level Details <br>"+"<b>+ve Adjustments : "+str(len(slide_placement[slide_placement['_source.data.offset_pos_y_um']>0]))+\
                            "<br>μ +ve Adjustments : "+str(round(np.mean(slide_placement[slide_placement['_source.data.offset_pos_y_um']>0]['_source.data.offset_pos_y_um']),2)),
                showarrow=False,font=dict(family="Courier New, monospace",size=10,color="black"),align="center",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="white",
                opacity=0.8)
        fig4.add_annotation(text="<b>"+slide_placement['_source.data.scanner_name'].iloc[0],xref="paper", yref="paper",showarrow=False,x=0, y=0,opacity=0.5,font=dict(family="Courier New, monospace",
            size=24,color="RebeccaPurple"))


        # Locking
        index_name = "slide_locking"
        url = "https://elastic:{}@{}:9200/{}/_search".format(password, host_name, index_name)
        query1 = {"size":10000,"query": {"match_phrase": {"data.load_identifier": load}}}
        response3 = requests.get(url,json = query1, verify = '/etc/elasticsearch/certs/http_ca.crt')
        response_json3 = json.loads(response3.text)
        slide_locking = pd.json_normalize(response_json3['hits']['hits'])
        slide_locking = slide_locking.sort_values(by = ['_source.data.row_index'], ascending = True)
        slide_locking = slide_locking.sort_values(by = ['_source.data.col_index'], ascending = True)
        slide_locking['_source.data.date'] = pd.to_datetime(slide_locking['_source.data.time_stamp']).dt.date
        slide_locking['row_col'] = (slide_locking['_source.data.row_index']+1).astype(str)+"_"+(slide_locking['_source.data.col_index']+1).astype(str)
        slide_locking = slide_locking[slide_locking["_source.data.load_identifier"] == load]

        slide_locking = slide_locking.sort_values(["_source.data.row_index","_source.data.col_index"], ascending = (True, True))
        fig5 = px.scatter(slide_locking, x='row_col',y="_source.data.first_current_diff",marginal_y="violin")
        # fig.add_hline(y=0.2,line_color="red")
        # fig.add_scatter(x=x1[x1['_source.data.slide_thickness']<0.2]['row_col'],
        #                 y=x1[x1['_source.data.slide_thickness']<0.2]['_source.data.slide_thickness'],
        #             marker=dict(color="red",size=12),mode="markers")
        fig5.update_layout(title="<b>Slide Locking Current Plot",height=800,width=1750)
        fig5.update_xaxes(title="Row_col",tickangle=45)
        fig5.update_yaxes(showticklabels=True)
        fig5.update_yaxes(title='',showticklabels=False)
        fig5.update_layout(legend_title="Scanner Name",yaxis1=dict(title="First Current Difference(mA)",showticklabels=True),xaxis2=dict(title=""))
        fig5.add_annotation(text="<b>"+slide_locking['_source.data.scanner_name'].iloc[0],xref="paper", yref="paper",showarrow=False,x=0, y=0,opacity=0.5,font=dict(family="Courier New, monospace",
            size=24,color="RebeccaPurple"))


        #Picking
        index_name = "slide_picking_from_scanner"
        url = "https://elastic:{}@{}:9200/{}/_search".format(password, host_name, index_name)
        query1 = {"size":10000,"query": {"match_phrase": {"data.load_identifier": load}}}
        response4 = requests.get(url,json = query1, verify = '/etc/elasticsearch/certs/http_ca.crt')
        response_json4 = json.loads(response4.text)
        slide_picking_from_scanner = pd.json_normalize(response_json4['hits']['hits'])
        slide_picking_from_scanner = slide_picking_from_scanner.sort_values(by = ['_source.data.row_index'], ascending = True)
        slide_picking_from_scanner = slide_picking_from_scanner.sort_values(by = ['_source.data.col_index'], ascending = True)
        slide_picking_from_scanner['row_col'] = (slide_picking_from_scanner['_source.data.row_index']+1).astype(str)+"_"+(slide_picking_from_scanner['_source.data.col_index']+1).astype(str)
        slide_picking_from_scanner['_source.data.date'] = pd.to_datetime(slide_picking_from_scanner['_source.data.time_stamp']).dt.date

        slide_picking = slide_picking_from_scanner[slide_picking_from_scanner["_source.data.load_identifier"] == load]
        slide_picking = slide_picking.sort_values(["_source.data.row_index","_source.data.col_index"], ascending = (True, True))
        fig6 = px.scatter(slide_picking, x='row_col',y="_source.data.actual_angle", marginal_y = 'histogram')
        fig6.add_hline(y=1.5,line_color="red")
        fig6.add_hline(y=-1.5,line_color="red")
        fig6.add_scatter(x=slide_picking[slide_picking['_source.data.actual_angle']<-1.5]['row_col'],
                        y=slide_picking[slide_picking['_source.data.actual_angle']<-1.5]['_source.data.actual_angle'],
                    marker=dict(color="red",size=12),mode="markers")
        fig6.add_scatter(x=slide_picking[slide_picking['_source.data.actual_angle']>1.5]['row_col'],
                        y=slide_picking[slide_picking['_source.data.actual_angle']>1.5]['_source.data.actual_angle'],
                    marker=dict(color="red",size=12),mode="markers", showlegend = False)
        fig6.update_layout(title="<b>Picking from Scanner Angle Plot",height=800,width=1750)
        fig6.update_xaxes(title="Row_Col",tickangle=45)
        fig6.update_yaxes(title="Pick-up Angle",range=[-4,4])
        fig6.add_annotation(text="<b>"+slide_picking['_source.data.scanner_name'].iloc[0],xref="paper", yref="paper",showarrow=False,x=0, y=0,opacity=0.5,font=dict(family="Courier New, monospace",
            size=24,color="RebeccaPurple"))
        fig6.update_layout(showlegend=False)  
    
    else:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x = [], y = [], mode = 'markers'))
        fig1.add_annotation(text = "No Data found for the selected date", showarrow = False, 
                           font = dict(family = 'Courier New',size = 35, color = "#000000")
                           ,x = 1, y = 1, xref="paper",yref="paper")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x = [], y = [], mode = 'markers'))
        fig2.add_annotation(text = "No Data found for the selected date", showarrow = False, 
                           font = dict(family = 'Courier New',size = 35, color = "#000000")
                           ,x = 1, y = 1, xref="paper",yref="paper")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x = [], y = [], mode = 'markers'))
        fig3.add_annotation(text = "No Data found for the selected date", showarrow = False, 
                           font = dict(family = 'Courier New',size = 35, color = "#000000")
                           ,x = 1, y = 1, xref="paper",yref="paper")
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x = [], y = [], mode = 'markers'))
        fig4.add_annotation(text = "No Data found for the selected date", showarrow = False, 
                           font = dict(family = 'Courier New',size = 35, color = "#000000")
                           ,x = 1, y = 1, xref="paper",yref="paper")
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x = [], y = [], mode = 'markers'))
        fig5.add_annotation(text = "No Data found for the selected date", showarrow = False, 
                           font = dict(family = 'Courier New',size = 35, color = "#000000")
                           ,x = 1, y = 1, xref="paper",yref="paper")
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x = [], y = [], mode = 'markers'))
        fig6.add_annotation(text = "No Data found for the selected date", showarrow = False, 
                           font = dict(family = 'Courier New',size = 35, color = "#000000")
                           ,x = 1, y = 1, xref="paper",yref="paper")
            
    return fig1, fig2, fig3, fig4, fig5, fig6

if __name__ == '__main__':
    app.run_server(port = 5000)