import pandas as pd


def data_frame_to_html_simple(df: pd.DataFrame) -> str:
    html = df.to_html(index=True)
    html = html.replace('\\n', '<br>')
    return html


def data_frame_to_html_pretty(df: pd.DataFrame) -> str:
    pd.set_option('colheader_justify', 'center')  # FOR TABLE <th>
    html = df.to_html(index=True, classes='df_style')
    html = html.replace('\\n', '<br>')
    return html


def generate_display_page_simple(title: str, contents: str) -> str:
    SIMPLE_TEMPLATE = '''
<html>
<header>%s</header>
<body>
%s
</body>
</html>
'''
    return SIMPLE_TEMPLATE % (title, contents)


def generate_display_page_pretty(title: str, contents: str) -> str:
    PRETTY_TEMPLATE = '''
<html>

  <style type="text/css">
    .df_style {
        font-size: 11pt; 
        font-family: Arial;
        border-collapse: collapse; 
        border: 1px solid silver;
    
    }
    
    .df_style td, th {
        padding: 5px;
    }
    
    .df_style tr:nth-child(even) {
        background: #E0E0E0;
    }
    
    .df_style tr:hover {
        background: silver;
        cursor: pointer;
    }
  </style>
    
  <head><title>%s</title></head>
  <link rel="stylesheet" type="text/css" href="df_style.css"/>
  <body>
    %s
  </body>
</html>'''
    return PRETTY_TEMPLATE % (title, contents)


data_frame_to_html = data_frame_to_html_pretty
generate_display_page = generate_display_page_pretty


def format_report_data_frame(stock_identity: str, df: pd.DataFrame) -> str:
    if stock_identity is None or stock_identity == '':
        stock_identity = '' if df.empty else df['stock_identity']

    text = []
    for analyzer, score, reason in zip(df['analyzer'], df['score'], df['reason']):
        pass

