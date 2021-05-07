import pandas as pd


def data_frame_to_html_simple(df: pd.DataFrame) -> str:
    html = df.to_html(index=True)
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


data_frame_to_html = data_frame_to_html_simple
generate_display_page = generate_display_page_simple
