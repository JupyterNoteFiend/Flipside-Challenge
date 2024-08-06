from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash_bootstrap_templates import load_figure_template

# Load the data
df = pd.read_excel("NEAR_01012024_07282024_data.xlsx")
df.columns = df.columns.str.lower()

# Calculate additional metrics
df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
df['date'] = df['block_timestamp'].dt.date
df['week'] = df['block_timestamp'].dt.isocalendar().week

# Define Grail program dates
program_start_date = pd.to_datetime('2024-06-24')
program_end_date = pd.to_datetime('2024-07-14')

# Filter data for the program period
program_data = df[(df['block_timestamp'] >= program_start_date) & (df['block_timestamp'] <= program_end_date)]
before_program_data = df[df['block_timestamp'] < program_start_date]
after_program_data = df[df['block_timestamp'] > program_end_date]

# Initialize the Dash app
load_figure_template('morph')
app = Dash(__name__, external_stylesheets=[dbc.themes.MORPH])

# Define the layout of the dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Grail Program 2024 Analytics Dashboard", className="text-center mb-4"), width=12)
    ]),
    dbc.Tabs([
        dbc.Tab(label='Overview', tab_id='tab-overview'),
        dbc.Tab(label='User Behavior', tab_id='tab-user-behavior'),
        dbc.Tab(label='Grail Program Impact', tab_id='tab-grail-impact'),
    ], id='tabs', active_tab='tab-overview', className="mb-4"),
    html.Div(id='content', className="p-4")
])

# Callback to render the content of each tab
@app.callback(Output('content', 'children'), [Input('tabs', 'active_tab')])
def render_content(tab):
    if tab == 'tab-overview':
        return render_overview()
    elif tab == 'tab-user-behavior':
        return render_user_behavior()
    elif tab == 'tab-grail-impact':
        return render_grail_impact()

def render_overview():
    total_volume = program_data['amount_usd'].sum()
    
    # Aggregate data by day to reduce clutter
    daily_volume = program_data.groupby('date')['amount_usd'].sum().reset_index()
    volume_over_time = px.line(daily_volume, x='date', y='amount_usd', title='Bridging Volume Over Time')
    
    # Group by direction and calculate sum
    inbound_outbound = program_data.groupby('direction')['amount_usd'].sum().reset_index()
    
    # Create horizontal stacked bar chart
    inbound_outbound_bar = go.Figure()
    inbound_outbound_bar.add_trace(go.Bar(
        y=['Capital Flow'], 
        x=inbound_outbound[inbound_outbound['direction'] == 'inbound']['amount_usd'],
        name='Inbound',
        orientation='h'
    ))
    inbound_outbound_bar.add_trace(go.Bar(
        y=['Capital Flow'], 
        x=inbound_outbound[inbound_outbound['direction'] == 'outbound']['amount_usd'],
        name='Outbound',
        orientation='h'
    ))
    inbound_outbound_bar.update_layout(
        title='Capital Flow Inbound vs Outbound',
        barmode='stack',
        xaxis_title='Amount (USD)',
        yaxis_title=''
    )
    
    # Group by source chain and calculate sum
    top_chains = program_data.groupby('source_chain')['amount_usd'].sum().nlargest(3).reset_index()
    top_chains_bar = px.bar(
        top_chains, 
        x='amount_usd', 
        y='source_chain', 
        orientation='h', 
        title='Top Source Chains',
        color='source_chain'
    )

    # Group by token and calculate sum
    top_tokens = program_data.groupby('symbol')['amount_usd'].sum().nlargest(5).reset_index()
    top_tokens_bar = px.bar(
        top_tokens, 
        x='amount_usd', 
        y='symbol', 
        orientation='h', 
        title='Top 5 Bridged Tokens',
        color='symbol'
    )

    return html.Div([
        dbc.Row([
            dbc.Col(html.H2(f"Total Bridged Volume During Program: ${total_volume:,.2f}"), className="mb-4")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=volume_over_time), width=6, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
            dbc.Col(dcc.Graph(figure=inbound_outbound_bar), width=6, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=top_chains_bar), width=6, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
            dbc.Col(dcc.Graph(figure=top_tokens_bar), width=6, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
        ]),
    ], style={"padding": "20px", "border": "1px solid #ccc", "border-radius": "10px"})

def render_user_behavior():
    # Filter the data to include only the Grail program period and 'inbound' direction
    program_inbound_data = df[(df['direction'] == 'inbound') & 
                              (df['block_timestamp'] >= program_start_date) & 
                              (df['block_timestamp'] <= program_end_date)]

    # Calculate holding period distribution based on the filtered data
    holding_periods_df = program_inbound_data.groupby('source_address').agg(
        first_bridge_in=('block_timestamp', 'min'),
        last_bridge_out=('block_timestamp', 'max')
    ).reset_index()
    
    holding_periods_df['duration_seconds'] = (holding_periods_df['last_bridge_out'] - holding_periods_df['first_bridge_in']).dt.total_seconds()
    holding_periods_df['duration_minutes'] = holding_periods_df['duration_seconds'] / 60
    # Remove zero values from the dataframe
    non_zero_holding_periods_df = holding_periods_df[holding_periods_df['duration_minutes'] > 0]
    # Create histogram for holding periods
    holding_periods_distribution = px.histogram(
        non_zero_holding_periods_df, 
        x='duration_minutes', 
        nbins=30, # Increased number of bins for better granularity
        title='Holding Period Length Distribution (Minutes)'
    )

    # Identify the initial bridging date for each user
    initial_bridge_date = df.groupby('source_address')['block_timestamp'].min().reset_index()
    initial_bridge_date.columns = ['source_address', 'initial_bridge_date']

    # Merge initial bridging date with the main dataframe
    df_merged = df.merge(initial_bridge_date, on='source_address')

    # Calculate the retention post-program
    df_merged['retained_post_program'] = df_merged['block_timestamp'] > program_end_date

    # Group by user and check if they have bridged again after the program period
    user_retention = df_merged.groupby('source_address')['retained_post_program'].any().mean()

   # Cohort Analysis during the program
    cohort_data = program_data.groupby(['week', 'source_address']).agg({'amount_usd': 'sum'}).reset_index()
    cohort_pivot = cohort_data.pivot(index='source_address', columns='week', values='amount_usd').fillna(0)
    cohort_pivot = cohort_pivot.sum().reset_index()
    cohort_pivot.columns = ['week', 'amount_usd']

    # Calculate week-over-week percentage change
    cohort_pivot['pct_change'] = cohort_pivot['amount_usd'].pct_change() * 100
    cohort_pivot['arrow'] = cohort_pivot['pct_change'].apply(lambda x: '⬆️' if x > 0 else '⬇️')

    # Create the bar chart with annotations
    cohort_chart = go.Figure()
    cohort_chart.add_trace(go.Bar(
        x=cohort_pivot['week'], 
        y=cohort_pivot['amount_usd'], 
        text=cohort_pivot.apply(lambda row: f"{row['pct_change']:.2f}% {row['arrow']}", axis=1),
        textposition='outside'
    ))
    cohort_chart.update_layout(
        title='Weekly Bridging Volume During Program',
        xaxis_title='Week of Calendar Year',
        yaxis_title='Amount (USD)'
    )

    return html.Div([
        dbc.Row([
            dbc.Col(html.H4(f"User Retention Rate Post Program: {user_retention:.2%}"), className="mb-4")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=holding_periods_distribution), width=12, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=cohort_chart), width=12, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
        ]),
    ], style={"padding": "20px", "border": "1px solid #ccc", "border-radius": "10px"})

def render_grail_impact():
    # Calculate the number of weeks in each period
    before_weeks = (program_start_date - before_program_data['block_timestamp'].min()).days / 7
    during_weeks = (program_end_date - program_start_date).days / 7
    after_weeks = (after_program_data['block_timestamp'].max() - program_end_date).days / 7

    # Calculate the total volume for each period
    before_volume = before_program_data['amount_usd'].sum()
    during_volume = program_data['amount_usd'].sum()
    after_volume = after_program_data['amount_usd'].sum()

    # Normalize volume per week
    before_volume_per_week = before_volume / before_weeks
    during_volume_per_week = during_volume / during_weeks
    after_volume_per_week = after_volume / after_weeks

    # Create a DataFrame for the normalized volumes
    program_impact = pd.DataFrame({
        'Phase': ['Before Program', 'During Program', 'After Program'],
        'Volume per Week': [before_volume_per_week, during_volume_per_week, after_volume_per_week]
    })

    # Create the bar chart
    volume_comparison_chart = px.bar(program_impact, x='Phase', y='Volume per Week', title='Weekly Bridging Volume Comparison')
    volume_comparison_chart.update_layout(
        annotations=[
            dict(
                x=0, 
                y=before_volume_per_week + 0.5 * before_volume_per_week, 
                xref="x", 
                yref="y", 
                text=f"{before_program_data['block_timestamp'].min().date()} to {program_start_date.date()}", 
                showarrow=False,
                yshift=10,
                font=dict(size=10),
                align="center"
            ),
            dict(
                x=1, 
                y=during_volume_per_week + 0.5 * during_volume_per_week, 
                xref="x", 
                yref="y", 
                text=f"{program_start_date.date()} to {program_end_date.date()}", 
                showarrow=False,
                yshift=10,
                font=dict(size=10),
                align="center"
            ),
            dict(
                x=2, 
                y=after_volume_per_week + 0.5 * after_volume_per_week, 
                xref="x", 
                yref="y", 
                text=f"{program_end_date.date()} to {after_program_data['block_timestamp'].max().date()}", 
                showarrow=False,
                yshift=10,
                font=dict(size=10),
                align="center"
            )
        ]
    )

    # Placeholder for anomaly detection (implement as needed)
    anomaly_chart = px.line(df, x='block_timestamp', y='amount_usd', title='Anomaly Detection')

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=volume_comparison_chart), width=12, className="p-2", style={"border": "1px solid #ddd", "border-radius": "5px"}),
        ]),
    ], style={"padding": "20px", "border": "1px solid #ccc", "border-radius": "10px"})

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
